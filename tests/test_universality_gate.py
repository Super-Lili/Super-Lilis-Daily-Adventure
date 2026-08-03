"""Tests for the COMMON_ROLES universality gate (Rule 20, 2026-08-03).

190+ days of "never repeat a topic" pressure was pushing SCOUT into an
increasingly narrow long tail - a real incident: "label invoice dates by
accrual vs cash-basis tax treatment" was specific and never done before, but
only a sliver of freelancers doing their own bookkeeping in that one method
would ever recognize it. This gate requires the spec to name 2+ clearly
distinct professional roles who'd all hit the same friction point, forcing
an explicit, checkable signal instead of the model's own (demonstrably
unreliable) sense of "is this common enough."
"""

import unittest

import _bootstrap  # noqa: F401

from lili_validators import validate_spec, parse_spec_response


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
        "must_contain": ["Alice"],
        "common_roles": ["Editor", "Podcast Producer"],
    }
    spec.update(overrides)
    return spec


class UniversalityGateTests(unittest.TestCase):
    def test_two_distinct_roles_passes(self):
        ok, reason = validate_spec(_good_spec(common_roles=["Journalist", "Brand Designer"]))
        self.assertTrue(ok, reason)

    def test_empty_roles_rejected(self):
        ok, reason = validate_spec(_good_spec(common_roles=[]))
        self.assertFalse(ok)
        self.assertIn("COMMON_ROLES", reason)

    def test_single_role_rejected(self):
        ok, reason = validate_spec(_good_spec(common_roles=["Freelance Bookkeeper"]))
        self.assertFalse(ok)
        self.assertIn("fewer than 2", reason)

    def test_exact_duplicate_roles_rejected(self):
        ok, reason = validate_spec(_good_spec(common_roles=["Editor", "editor"]))
        self.assertFalse(ok)
        self.assertIn("same role twice", reason)

    def test_three_distinct_roles_passes(self):
        ok, reason = validate_spec(_good_spec(
            common_roles=["Journalist", "Podcast Producer", "Brand Designer"]))
        self.assertTrue(ok, reason)


class ParseCommonRolesTests(unittest.TestCase):
    def test_parses_comma_separated_roles(self):
        raw = (
            "---SPEC_START---\n"
            "COMMON_ROLES: Journalist, Brand Designer, Podcast Producer\n"
            "---SPEC_END---"
        )
        p = parse_spec_response(raw)
        self.assertEqual(p["common_roles"], ["Journalist", "Brand Designer", "Podcast Producer"])

    def test_missing_field_defaults_to_empty_list(self):
        raw = "---SPEC_START---\nFORMAT: A\n---SPEC_END---"
        p = parse_spec_response(raw)
        self.assertEqual(p["common_roles"], [])

    def test_none_value_is_empty_list(self):
        raw = "---SPEC_START---\nCOMMON_ROLES: none\n---SPEC_END---"
        p = parse_spec_response(raw)
        self.assertEqual(p["common_roles"], [])


if __name__ == "__main__":
    unittest.main()
