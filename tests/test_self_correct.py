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


_HTML_OUTPUT_CODE = '''
def process(text: str) -> str:
    return "<html><body><h1>Tool</h1><p>Static, ignores input</p></body></html>"

''' + "\n".join(f"# padding line {i}" for i in range(50)) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''


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

_MISSING_USER_INPUT_CODE = '''
def process(text: str) -> str:
    return "Summary: hardcoded, ignores whatever you actually typed"

''' + _pad(50) + '''

print(process("nothing"))
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


_EDGE_CASE_FRAGILE_CODE = '''
def process(text: str) -> str:
    parts = text.split(",")
    return "Owner: " + parts[1].strip()

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''


class SelfCorrectUserInputPatternTests(unittest.TestCase):
    """2026-08-18 incident: a candidate can pass every EXECUTION-based
    self-correction check (run_tool_output injects USER_INPUT as a real
    global, so hardcoded/input-ignoring code can still produce SOME output
    and satisfy MUST_CONTAIN by coincidence) yet still get rejected by
    validate_tool()'s separate structural check, which self-correction had
    never mirrored. Same class of gap as the Mode 3 browser check (F-021)."""

    def test_missing_user_input_triggers_patch(self):
        skill_dir = _make_skill_dir(_MISSING_USER_INPUT_CODE)
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-18")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any("USER_INPUT dual-mode pattern" in p for p in seen_feedback))
        self.assertIn("Summary:", result)

    def test_missing_user_input_never_reaches_execution(self):
        # The structural check must fire BEFORE any subprocess execution -
        # verified indirectly: even though the hardcoded output would
        # satisfy must_contain, the tool must still be rejected for the
        # missing pattern, not silently accepted.
        skill_dir = _make_skill_dir(_MISSING_USER_INPUT_CODE)
        spec = _spec(must_contain=["Summary:"])  # would trivially pass by coincidence
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            self_correct_code(skill_dir, _SCOUT, spec, "2026-08-18")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any("USER_INPUT dual-mode pattern" in p for p in seen_feedback))

    def test_correct_code_with_user_input_not_flagged(self):
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-18")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertIn("Summary:", result)


class SelfCorrectEdgeCaseInputTests(unittest.TestCase):
    """Harness plan #2 (2026-08-09): a tool that only satisfies its promise
    on the clean TEST_INPUT but breaks on a messier, more realistic input is
    a happy-path illusion. EDGE_CASE_INPUT reuses the same MUST_CONTAIN/
    MUST_NOT_CONTAIN promise, checked against a second adversarial sample."""

    def test_edge_case_failure_triggers_patch_after_primary_passes(self):
        # Primary test_input has a comma (works); edge case input has none
        # (IndexError) - the tool must be patched, not declared clean just
        # because the happy-path input worked.
        skill_dir = _make_skill_dir(_EDGE_CASE_FRAGILE_CODE)
        spec = _spec(
            test_input="Alice, Marketing Lead",
            must_contain=["Owner:"],
            edge_case_input="Bob Solo Freelancer no comma here",
        )
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-09")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any("EDGE CASE INPUT" in p for p in seen_feedback))
        self.assertIn("Summary:", result)

    def test_no_edge_case_input_skips_the_extra_check(self):
        # _spec() default has no edge_case_input - primary-clean code must
        # still be declared clean with zero LLM calls (backward compatible).
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertIn("def process", result)

    def test_none_edge_case_input_treated_as_absent(self):
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        spec = _spec(edge_case_input="none")
        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-09")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertIn("def process", result)


class SelfCorrectReferenceRetrievalTests(unittest.TestCase):
    """Harness plan #3 (2026-08-09): from round 2+ (still broken after one
    real-feedback round), include a concrete shipped-tool reference in the
    patch prompt - on-demand only, to control token cost per the owner's
    explicit cost discussion."""

    def test_round_one_does_not_fetch_reference(self):
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)
        calls = []

        def fake_call(prompt, deepseek_prompt=None):
            calls.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        def _fail_if_called(category=""):
            raise AssertionError("reference lookup must not run on round 1")

        import lili_prompts
        original_ref = lili_prompts.get_reference_tool_snippet
        lili_prompts.get_reference_tool_snippet = _fail_if_called
        original_call = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09", max_rounds=1)
        finally:
            lili_prompts.get_reference_tool_snippet = original_ref
            lili_pipeline.call_gemini_simple = original_call
        self.assertEqual(len(calls), 1)

    def test_round_two_includes_reference_when_available(self):
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            # Keep returning broken code so round 2 is reached.
            return "---CODE---\n" + _SYNTAX_BROKEN_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        import lili_prompts
        original_ref = lili_prompts.get_reference_tool_snippet
        lili_prompts.get_reference_tool_snippet = lambda category="": "Reference (real shipped tool, 'Example') - study the STRUCTURE"
        original_call = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09", max_rounds=2)
        finally:
            lili_prompts.get_reference_tool_snippet = original_ref
            lili_pipeline.call_gemini_simple = original_call
        self.assertEqual(len(seen_feedback), 2)
        self.assertNotIn("Reference (real shipped tool", seen_feedback[0])
        self.assertIn("Reference (real shipped tool", seen_feedback[1])


class SelfCorrectDefaultRoundsTests(unittest.TestCase):
    """Harness plan #1, scoped increment (2026-08-07): raised the default
    self-correction budget from 2 to 4 rounds - still a hard cap (cost
    discussion with owner: uncapped agentic loops risk runaway spend), just
    more room for the model to converge on real observed feedback before
    handing off to the expensive outer validate_tool() chain."""

    def test_default_max_rounds_is_four(self):
        import inspect
        sig = inspect.signature(self_correct_code)
        self.assertEqual(sig.parameters["max_rounds"].default, 4)

    def test_uses_all_four_rounds_when_never_fixed(self):
        skill_dir = _make_skill_dir(_SYNTAX_BROKEN_CODE)
        call_count = [0]

        def fake_call(prompt, deepseek_prompt=None):
            call_count[0] += 1
            return "---CODE---\n" + _SYNTAX_BROKEN_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-04")  # default rounds
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertEqual(call_count[0], 4)


class SelfCorrectMode3BrowserCheckTests(unittest.TestCase):
    """P1 fix (2026-08-03): Mode 3 tools previously got no execution feedback
    at all in this inner loop - their real defect class (DOM not reacting to
    clicks) only surfaced later in the expensive validate_tool() chain. This
    was the single largest failure bucket (47% of 298 ledger attempts:
    fake-static + browser-ground-truth combined)."""

    def test_mode3_static_html_triggers_patch_when_playwright_available(self):
        import lili_pipeline as lp
        ran, _, detail = lp._browser_interactivity_check("<html><body>x</body></html>", "test")
        if not ran:
            self.skipTest(f"Real browser probe unavailable in this environment ({detail[:80]}) "
                          "- fail-open path covered separately")

        skill_dir = _make_skill_dir(_HTML_OUTPUT_CODE)
        spec = _spec(mode="3 - interactive HTML tool")
        seen_feedback = []

        def fake_call(prompt, deepseek_prompt=None):
            seen_feedback.append(prompt)
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call
        try:
            self_correct_code(skill_dir, _SCOUT, spec, "2026-08-04")
        finally:
            lili_pipeline.call_gemini_simple = original
        self.assertTrue(any("did NOT react" in p for p in seen_feedback))

    def test_mode3_check_fails_open_when_playwright_unavailable(self):
        # Simulate the fail-open path directly: patch the check to report
        # ran=False (Playwright unavailable), which must NOT be treated as a
        # defect - the loop should accept the code as clean, zero patches.
        import lili_pipeline as lp
        skill_dir = _make_skill_dir(_HTML_OUTPUT_CODE)
        spec = _spec(mode="3 - interactive HTML tool")

        original_check = lp._browser_interactivity_check
        lp._browser_interactivity_check = lambda html, inp: (False, False, "playwright unavailable (ImportError)")
        original_call = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-04")
        finally:
            lp._browser_interactivity_check = original_check
            lili_pipeline.call_gemini_simple = original_call
        self.assertIn("<html>", result)

    def test_mode1_tools_skip_browser_check_entirely(self):
        # A Mode 1 tool must never be sent through the browser probe, even if
        # its text output happens to contain HTML-like characters - only
        # spec["mode"] starting with "3" should trigger it.
        import lili_pipeline as lp
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        spec = _spec(mode="1 - plain text")

        def _fail_if_called(html, inp):
            raise AssertionError("browser check must not run for Mode 1 tools")

        original_check = lp._browser_interactivity_check
        lp._browser_interactivity_check = _fail_if_called
        original_call = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = _RaisingClient()
        try:
            result = self_correct_code(skill_dir, _SCOUT, spec, "2026-08-04")
        finally:
            lp._browser_interactivity_check = original_check
            lili_pipeline.call_gemini_simple = original_call
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
