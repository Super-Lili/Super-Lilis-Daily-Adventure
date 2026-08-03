"""Tests for the self-correction inner loop (harness plan A, 2026-08-04):
BUILD's just-written code is actually EXECUTED before the expensive
validation chain, and if syntax breaks, execution crashes, or the spec's own
promise fails, the model gets ONE MORE targeted turn with the real observed
output/error - instead of submitting 200+ lines blind and finding out only
after Critic/browser-ground-truth/quality-scoring have all run.
"""

import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

import lili_pipeline
from lili_pipeline import self_correct_code


def _make_skill_dir(main_py_source: str) -> str:
    d = tempfile.mkdtemp()
    (Path(d) / "main.py").write_text(main_py_source, encoding="utf-8")
    return d


def _spec(**overrides):
    spec = {
        "test_input": "Please help me organize my quarterly review notes for the team meeting.",
        "must_contain": [],
        "must_not_contain": [],
    }
    spec.update(overrides)
    return spec


_SCOUT = {"solution": "Test Tool", "category": "Office Automation", "description": "a test tool"}

def _pad(n: int) -> str:
    # parse_build_response() treats code under 50 lines as truncated/empty
    # (a real, deliberate contract - see test_promise_check.py). Mock LLM
    # responses in these tests must be realistically sized to survive it.
    return "\n".join(f"# padding line {i} - keeps this a realistic BUILD-sized file" for i in range(n))


_CORRECT_CODE = '''
def process(text: str) -> str:
    return "Summary: " + text[:40] + "\\nStatus: processed"

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_SYNTAX_BROKEN_CODE = '''
def process(text: str) -> str
    return "broken"

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_CRASHING_CODE = '''
def process(text: str) -> str:
    return text.this_attribute_does_not_exist()

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_BROKEN_PROMISE_CODE = '''
def process(text: str) -> str:
    return 'Result: fill="none" was not removed.\\nStatus: done'

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''


class _RaisingClient:
    """A stand-in for call_gemini_simple that fails the test if ever called -
    proves the zero-LLM-call fast path for already-correct code."""
    def __call__(self, *args, **kwargs):
        raise AssertionError("call_gemini_simple must NOT be called for code with no problems")


class SelfCorrectAlreadyCorrectTests(unittest.TestCase):
    def test_correct_code_returned_unchanged_with_zero_llm_calls(self):
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertIn("def process", result)
        self.assertEqual(result, Path(skill_dir, "main.py").read_text(encoding="utf-8"))


class SelfCorrectSyntaxTests(unittest.TestCase):
    def test_syntax_error_triggers_one_patch_round(self):
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)
        calls = []

        def fake_call(prompt, deepseek_prompt=None):
            calls.append(prompt)
            self.assertIn("SyntaxError", prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertEqual(len(calls), 1)
        self.assertIn("Summary:", result)
        # File on disk must reflect the patch, not just the return value.
        self.assertIn("Summary:", Path(skill_dir, "main.py").read_text(encoding="utf-8"))


class SelfCorrectCrashTests(unittest.TestCase):
    def test_runtime_crash_triggers_patch_with_real_traceback(self):
        skill_dir = _make_skill_dir(_CRASHING_CODE)
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any("AttributeError" in p or "crashed" in p.lower() for p in seen_feedback))
        self.assertIn("Summary:", result)


class SelfCorrectPromiseTests(unittest.TestCase):
    def test_broken_must_not_contain_triggers_patch(self):
        skill_dir = _make_skill_dir(_BROKEN_PROMISE_CODE)
        spec = _spec(must_not_contain=['fill="none"'])
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any('fill="none"' in p for p in seen_feedback))
        self.assertIn("Summary:", result)

    def test_fixed_code_that_still_breaks_promise_is_re_checked(self):
        # The patch model returns code that FIXES the syntax/crash but still
        # violates the promise - the loop must catch this on round 2, not
        # declare victory after round 1 just because it got new code.
        skill_dir = _make_skill_dir(_BROKEN_PROMISE_CODE)
        spec = _spec(must_not_contain=['fill="none"'])
        call_count = [0]

        def fake_call(prompt, deepseek_prompt=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # "fixed" version still contains the forbidden string
                return ("---CODE---\n" + _BROKEN_PROMISE_CODE + "\n---TEST---\n"
                        "assert True\n---BUILD_END---")
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-04", max_rounds=2)
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertEqual(call_count[0], 2)  # both rounds actually spent
        self.assertIn("Summary:", result)


class SelfCorrectDegradesGracefullyTests(unittest.TestCase):
    def test_max_rounds_exhausted_returns_last_attempt_without_crashing(self):
        # The patch model NEVER fixes it - the loop must give up cleanly
        # after max_rounds and hand off to the full validation chain
        # (which will correctly reject it), not raise or hang.
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)

        def fake_call(prompt, deepseek_prompt=None):
            return "---CODE---\n" + _SYNTAX_BROKEN_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04", max_rounds=2)
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertIsInstance(result, str)  # returned something, didn't raise

    def test_no_llm_response_keeps_previous_code(self):
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)
        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = lambda *a, **k: None
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertEqual(result, _SYNTAX_BROKEN_CODE)


if __name__ == "__main__":
    unittest.main()
