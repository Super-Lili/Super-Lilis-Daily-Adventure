"""Tests for differential testing (harness plan F, 2026-08-04): running
process() on two inputs from unrelated domains and rejecting a tool whose
output barely changes - mechanizing what used to be an LLM Critic's
subjective "output is generic" call into a quantified, evidence-backed check.
"""

import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

import lili_llm
lili_llm.time.sleep = lambda s: None  # skip real waits in the mocked LLM retry chain

from lili_validators import _differential_test, validate_tool, run_tool_output


_GENERIC_TEMPLATE_MAIN_PY = '''
def process(text: str) -> str:
    # Ignores the actual content of `text` - a template-filling tool.
    return ("Thank you for your submission.\\n"
            "Your request has been processed successfully.\\n"
            "A member of our team will follow up shortly.")

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_REAL_COMPUTATION_MAIN_PY = '''
def process(text: str) -> str:
    words = text.split()
    unique = sorted(set(w.strip(".,!?").lower() for w in words if len(w) > 4))
    return ("Word count: " + str(len(words)) + "\\n"
            "Longer words found: " + ", ".join(unique[:8]) + "\\n"
            "First word: " + (words[0] if words else "(none)"))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''


def _make_skill_dir(main_py_source: str) -> str:
    d = tempfile.mkdtemp()
    (Path(d) / "main.py").write_text(main_py_source, encoding="utf-8")
    return d


class DifferentialTestUnitTests(unittest.TestCase):
    def test_identical_output_across_samples_is_caught(self):
        skill_dir = _make_skill_dir(_GENERIC_TEMPLATE_MAIN_PY)
        main_py = f"{skill_dir}/main.py"
        # Use the tool's REAL output for a third (spec test_input-equivalent)
        # sample, not a hand-typed approximation - a slightly-off guess string
        # would under-measure similarity and mask exactly the bug this test
        # exists to catch.
        primary_output, _, _ = run_tool_output(
            main_py, "Please help me organize my project timeline for the client review.")
        ok, reason = _differential_test(main_py, primary_output)
        self.assertFalse(ok)
        self.assertIn("generic", reason.lower())
        self.assertIn("%", reason)  # quantified evidence, not a vibe

    def test_diverging_output_passes(self):
        skill_dir = _make_skill_dir(_REAL_COMPUTATION_MAIN_PY)
        main_py = f"{skill_dir}/main.py"
        primary_output, _, _ = run_tool_output(
            main_py, "Please help me organize my project timeline for the client review.")
        ok, reason = _differential_test(main_py, primary_output)
        self.assertTrue(ok, reason)

    def test_crashing_secondary_input_fails_open(self):
        # A tool that only accepts a specific structured format (e.g. valid
        # XML) will crash on the plain-English differential samples. That is
        # NOT evidence of genericness - it's a different failure mode already
        # caught elsewhere. The differential test must skip, not reject.
        strict_xml_tool = '''
import xml.etree.ElementTree as ET
def process(text: str) -> str:
    root = ET.fromstring(text)  # raises on non-XML input - by design
    return "parsed: " + root.tag

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''
        skill_dir = _make_skill_dir(strict_xml_tool)
        main_py = f"{skill_dir}/main.py"
        ok, reason = _differential_test(main_py, "parsed: svg")
        self.assertTrue(ok, f"must fail open on secondary-input crash, got: {reason}")


class DifferentialTestEndToEndTests(unittest.TestCase):
    """Runs the real validate_tool() to prove a generic tool is rejected and
    a genuinely computing tool ships, via the full validation chain."""

    def test_generic_template_tool_rejected_end_to_end(self):
        skill_dir = _make_skill_dir(_GENERIC_TEMPLATE_MAIN_PY)
        ok, reason = validate_tool(
            skill_dir,
            test_input="I need help organizing my quarterly budget review meeting notes please.",
        )
        self.assertFalse(ok)
        self.assertIn("generic", reason.lower())

    def test_real_computation_tool_passes_end_to_end(self):
        skill_dir = _make_skill_dir(_REAL_COMPUTATION_MAIN_PY)
        ok, reason = validate_tool(
            skill_dir,
            test_input="I need help organizing my quarterly budget review meeting notes please.",
        )
        self.assertTrue(ok, reason)


if __name__ == "__main__":
    unittest.main()
