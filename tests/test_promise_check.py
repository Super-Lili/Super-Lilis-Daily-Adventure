"""Tests for the SPEC promise-commitment mechanism (MUST_CONTAIN / MUST_NOT_CONTAIN):
parsing, the validate_spec gate requiring at least one commitment, and the
validate_tool() mechanical check that runs process(test_input) for real and
verifies the spec's own claim against the ACTUAL output.

This closes the exact hole that shipped "SVG Path Purifier" broken: it claimed
(in its own README) to remove fill="none" from <g> elements, its removal code
silently matched zero elements due to an XML namespace bug, and nothing ever
checked the promise against the real output - the Critic judged it "clean" on
vibes. See docs/FINDINGS.md and the 2026-07-28 tool's fix commit.
"""

import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from lili_validators import _parse_literal_list, parse_spec_response, validate_spec, validate_tool


class ParseLiteralListTests(unittest.TestCase):
    def test_comma_separated_values(self):
        self.assertEqual(_parse_literal_list('fill="none", opacity="0"'),
                         ['fill="none"', 'opacity="0"'])

    def test_none_is_empty_list(self):
        self.assertEqual(_parse_literal_list("none"), [])
        self.assertEqual(_parse_literal_list("None."), [])
        self.assertEqual(_parse_literal_list("  NONE  "), [])

    def test_empty_string_is_empty_list(self):
        self.assertEqual(_parse_literal_list(""), [])

    def test_strips_quotes_and_whitespace(self):
        self.assertEqual(_parse_literal_list('"hello world" ,  \'foo\'  '), ["hello world", "foo"])

    def test_single_item(self):
        self.assertEqual(_parse_literal_list('fill="none"'), ['fill="none"'])


class ParseSpecPromiseFieldsTests(unittest.TestCase):
    def test_parses_both_fields(self):
        raw = (
            "---SPEC_START---\nFORMAT: A - text\nMODE: 1 - reliable\n"
            "INPUT_MODEL: raw svg\nOUTPUT_MODEL: cleaned svg\n"
            "TRANSFORMATION: remove fill=none from g tags\n"
            'ALGORITHMIC_DEPTH: split on g tags; remove fill="none"\n'
            "Q1_PASS: yes\nQ2_PASS: yes\nQ3_PASS: yes\n"
            "TEST_INPUT: a realistic svg input string here for validation\n"
            'MUST_NOT_CONTAIN: fill="none"\n'
            "MUST_CONTAIN: none\n---SPEC_END---"
        )
        p = parse_spec_response(raw)
        self.assertEqual(p["must_not_contain"], ['fill="none"'])
        self.assertEqual(p["must_contain"], [])

    def test_missing_fields_default_to_empty_list(self):
        raw = "---SPEC_START---\nFORMAT: A - text\n---SPEC_END---"
        p = parse_spec_response(raw)
        self.assertEqual(p["must_not_contain"], [])
        self.assertEqual(p["must_contain"], [])


def _good_spec(**overrides):
    spec = {
        "input_model": "raw meeting notes as free text",
        "output_model": "ranked table of action items with owners",
        "transformation": "extract action items and rank by urgency",
        "algorithmic_depth": (
            "split into sentences; detect imperative verbs; group by owner; "
            "rank by deadline proximity computed from relative date words"
        ),
        "q1_pass": "yes - addresses the exact moment notes go stale",
        "q2_pass": "yes - an editor recognises their own meeting notes",
        "q3_pass": "yes - the ranked list is actionable immediately",
        "test_input": "Alice will draft the brief by Friday. Bob reviews it next week.",
        "must_not_contain": [],
        "must_contain": [],
        "common_roles": ["Editor", "Podcast Producer"],
    }
    spec.update(overrides)
    return spec


class ValidateSpecPromiseGateTests(unittest.TestCase):
    def test_both_empty_rejected(self):
        ok, reason = validate_spec(_good_spec())
        self.assertFalse(ok)
        self.assertIn("MUST_NOT_CONTAIN", reason)

    def test_must_not_contain_alone_passes(self):
        ok, reason = validate_spec(_good_spec(must_not_contain=['fill="none"']))
        self.assertTrue(ok, reason)

    def test_must_contain_alone_passes(self):
        ok, reason = validate_spec(_good_spec(must_contain=["total: 42"]))
        self.assertTrue(ok, reason)

    def test_both_present_passes(self):
        ok, reason = validate_spec(_good_spec(must_not_contain=["x"], must_contain=["y"]))
        self.assertTrue(ok, reason)


# ── End-to-end regression test: the exact SVG Path Purifier incident ────────

_BUGGY_MAIN_PY = '''
import xml.etree.ElementTree as ET

def process(text: str) -> str:
    if not text.strip():
        return ""
    root = ET.fromstring(text)
    # BUG (the real 2026-07-28 incident): root.iter('g') matches nothing once
    # the SVG declares a default namespace, because the real tag name becomes
    # '{http://www.w3.org/2000/svg}g'. This silently no-ops the whole tool.
    for elem in root.iter('g'):
        if elem.attrib.get('fill') == 'none':
            del elem.attrib['fill']
    cleaned = ET.tostring(root, encoding='unicode')
    return cleaned + "\\n<!-- cleaned by SVG Path Purifier -->"

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_FIXED_MAIN_PY = '''
import xml.etree.ElementTree as ET

def process(text: str) -> str:
    if not text.strip():
        return ""
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(text)
    for elem in root.iter():
        local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if local == 'g' and elem.attrib.get('fill') == 'none':
            del elem.attrib['fill']
    cleaned = ET.tostring(root, encoding='unicode')
    return cleaned + "\\n<!-- cleaned by SVG Path Purifier -->"

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''

_TEST_SVG = ('<svg xmlns="http://www.w3.org/2000/svg"><g fill="none">'
            '<rect x="1" y="1" width="10" height="10"/></g></svg>')


class PromiseCheckRegressionTests(unittest.TestCase):
    """Runs the REAL validate_tool() against a minimal fixture reproducing the
    exact bug class that shipped SVG Path Purifier broken, end to end."""

    def _make_skill_dir(self, main_py_source: str) -> str:
        d = tempfile.mkdtemp()
        (Path(d) / "main.py").write_text(main_py_source, encoding="utf-8")
        return d

    def test_buggy_tool_caught_by_promise_check(self):
        skill_dir = self._make_skill_dir(_BUGGY_MAIN_PY)
        ok, reason = validate_tool(
            skill_dir,
            test_input=_TEST_SVG,
            must_not_contain=['fill="none"'],
        )
        self.assertFalse(ok, "the buggy no-op removal must be caught")
        self.assertIn("PROMISE BROKEN", reason)
        self.assertIn('fill="none"', reason)

    def test_fixed_tool_passes_promise_check(self):
        skill_dir = self._make_skill_dir(_FIXED_MAIN_PY)
        ok, reason = validate_tool(
            skill_dir,
            test_input=_TEST_SVG,
            must_not_contain=['fill="none"'],
        )
        self.assertTrue(ok, reason)

    def test_must_contain_failure_is_caught(self):
        # A tool that claims to compute/add something but doesn't.
        stub = '''
def process(text: str) -> str:
    return ("Processed action items from the meeting notes below.\\n"
            "Summary: " + text[:60] + "\\nNo urgency score was computed here.")

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
'''
        skill_dir = self._make_skill_dir(stub)
        ok, reason = validate_tool(
            skill_dir,
            test_input="Alice will draft the brief by Friday. Bob reviews it next week.",
            must_contain=["URGENCY_SCORE:"],
        )
        self.assertFalse(ok)
        self.assertIn("PROMISE BROKEN", reason)
        self.assertIn("URGENCY_SCORE", reason)


if __name__ == "__main__":
    unittest.main()
