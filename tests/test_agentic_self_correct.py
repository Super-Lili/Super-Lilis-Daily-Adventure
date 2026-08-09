"""Tests for the agentic self-correction loop (harness plan #1, 2026-08-09):
BUILD gets a real debug-execute-decide loop via native tool-calling instead
of the engine hard-sequencing fixed write-then-patch rounds. The model
decides when to test a hypothesis (run_and_check) and when it believes it's
done (submit_final_code) - but every submission is mechanically re-verified,
never trusted blindly. Falls back to the proven fixed-round self_correct_code
on any tool-calling error, so this path can never make things worse.
"""

import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

import lili_llm
import lili_pipeline
from lili_pipeline import agentic_self_correct_code


def _make_skill_dir(main_py_source: str) -> str:
    d = tempfile.mkdtemp()
    (Path(d) / "main.py").write_text(main_py_source, encoding="utf-8")
    return d


def _pad(n: int) -> str:
    return "\n".join(f"# padding line {i} - keeps this a realistic BUILD-sized file" for i in range(n))


_CORRECT_CODE = '''
def process(text: str) -> str:
    return "Summary: " + text[:40] + "\\nStatus: processed"

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_BROKEN_CODE = '''
def process(text: str) -> str:
    return "Result: nothing useful here"

''' + _pad(50) + '''

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_SCOUT = {"solution": "Test Tool", "category": "Office Automation", "description": "a test tool"}


def _spec(**overrides):
    spec = {
        "test_input": "Please summarize this quarterly report for the team.",
        "must_contain": ["Summary:"],
        "must_not_contain": [],
        "transformation": "summarize the input",
        "mode": "1",
    }
    spec.update(overrides)
    return spec


class _FakeFunction:
    def __init__(self, name, arguments_dict):
        self.name = name
        self.arguments = json.dumps(arguments_dict)


class _FakeToolCall:
    def __init__(self, call_id, name, arguments_dict):
        self.id = call_id
        self.function = _FakeFunction(name, arguments_dict)


class _FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(self, message):
        self.message = message


class _FakeResp:
    def __init__(self, message):
        self.choices = [_FakeChoice(message)]


class _RaisingClient:
    """Fails the test if called - proves the zero-LLM-call fast path."""
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                raise AssertionError("the model must NOT be called for already-correct code")


class _ScriptedClient:
    """Replays a list of _FakeResp objects, one per call to create()."""
    def __init__(self, responses):
        self._responses = iter(responses)
        self.call_count = 0

        outer = self

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    outer.call_count += 1
                    return next(outer._responses)
        self.chat = chat


class AgenticFastPathTests(unittest.TestCase):
    def test_already_correct_code_returned_with_zero_llm_calls(self):
        skill_dir = _make_skill_dir(_CORRECT_CODE)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = _RaisingClient()
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_llm._deepseek_client = original
        self.assertIn("Summary:", result)


class AgenticToolCallingLoopTests(unittest.TestCase):
    def test_run_and_check_then_submit_accepted(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)
        responses = [
            _FakeResp(_FakeMessage(tool_calls=[
                _FakeToolCall("call_1", "run_and_check", {"code": _CORRECT_CODE, "input_text": "test"}),
            ])),
            _FakeResp(_FakeMessage(tool_calls=[
                _FakeToolCall("call_2", "submit_final_code", {"code": _CORRECT_CODE}),
            ])),
        ]
        client = _ScriptedClient(responses)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = client
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_llm._deepseek_client = original
        self.assertIn("Summary:", result)
        self.assertEqual(client.call_count, 2)

    def test_submit_with_still_broken_code_is_rejected_and_loop_continues(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)
        responses = [
            _FakeResp(_FakeMessage(tool_calls=[
                # Model claims this is fixed, but it's still the broken code.
                _FakeToolCall("call_1", "submit_final_code", {"code": _BROKEN_CODE}),
            ])),
            _FakeResp(_FakeMessage(tool_calls=[
                _FakeToolCall("call_2", "submit_final_code", {"code": _CORRECT_CODE}),
            ])),
        ]
        client = _ScriptedClient(responses)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = client
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_llm._deepseek_client = original
        # Rejection must be mechanical, not trust the model's claim.
        self.assertEqual(client.call_count, 2)
        self.assertIn("Summary:", result)

    def test_model_stops_without_submitting_returns_last_seen_code(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)
        responses = [
            _FakeResp(_FakeMessage(content="I give up.", tool_calls=None)),
        ]
        client = _ScriptedClient(responses)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = client
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_llm._deepseek_client = original
        self.assertIsInstance(result, str)  # degraded gracefully, did not raise

    def test_edge_case_input_checked_on_submit(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)
        spec = _spec(edge_case_input="a totally different edge case input")
        responses = [
            _FakeResp(_FakeMessage(tool_calls=[
                _FakeToolCall("call_1", "submit_final_code", {"code": _CORRECT_CODE}),
            ])),
        ]
        client = _ScriptedClient(responses)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = client
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, spec, "2026-08-09", max_rounds=1)
        finally:
            lili_llm._deepseek_client = original
        # _CORRECT_CODE's "Summary:" prefix means the edge case also passes -
        # this just confirms the check runs without crashing and the result
        # is still the accepted code.
        self.assertIn("Summary:", result)

    def test_max_rounds_exhausted_returns_last_code_without_crashing(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)
        responses = [
            _FakeResp(_FakeMessage(tool_calls=[
                _FakeToolCall(f"call_{i}", "submit_final_code", {"code": _BROKEN_CODE}),
            ])) for i in range(3)
        ]
        client = _ScriptedClient(responses)
        original = lili_llm._deepseek_client
        lili_llm._deepseek_client = client
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09", max_rounds=3)
        finally:
            lili_llm._deepseek_client = original
        self.assertIsInstance(result, str)
        self.assertEqual(client.call_count, 3)


class AgenticFallbackTests(unittest.TestCase):
    def test_tool_calling_error_falls_back_to_fixed_round_self_correct(self):
        skill_dir = _make_skill_dir(_BROKEN_CODE)

        class _ErroringClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise RuntimeError("Unsupported parameter: 'tools'")

        original_deepseek = lili_llm._deepseek_client
        lili_llm._deepseek_client = _ErroringClient()

        def fake_call_gemini_simple(prompt, deepseek_prompt=None):
            return "---CODE---\n" + _CORRECT_CODE + "\n---TEST---\nassert True\n---BUILD_END---"

        original_call = lili_pipeline.call_gemini_simple
        lili_pipeline.call_gemini_simple = fake_call_gemini_simple
        try:
            result = agentic_self_correct_code(skill_dir, _SCOUT, _spec(), "2026-08-09")
        finally:
            lili_llm._deepseek_client = original_deepseek
            lili_pipeline.call_gemini_simple = original_call
        self.assertIn("Summary:", result)


if __name__ == "__main__":
    unittest.main()
