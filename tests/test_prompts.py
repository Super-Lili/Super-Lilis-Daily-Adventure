"""Unit tests for lili_prompts: the three phase prompts must contain the
gates and rules the pipeline depends on, and the mode-aware line caps."""

import unittest

import _bootstrap  # noqa: F401

from lili_prompts import build_scout_prompt, build_spec_prompt, build_code_prompt


SCOUT = {
    "solution": "Deadline Diff",
    "category": "Office Automation",
    "pain_who": "an editor",
    "pain_moment": "handoff chaos",
    "pain_tried": "spreadsheets",
    "description": "diff two brief versions",
}


def spec(mode="1", fmt="A - text"):
    return {
        "format": fmt,
        "mode": mode,
        "input_model": "two versions of a brief",
        "output_model": "table of changed clauses",
        "transformation": "diff and rank changes",
        "algorithmic_depth": "split into clauses; align by similarity; rank changes",
        "ui_state_entry": "paste area",
        "ui_state_active": "live diff",
        "ui_state_result": "ranked list",
        "test_input": "v1 text ... v2 text ...",
    }


class ScoutPromptTests(unittest.TestCase):
    def test_contains_output_tags(self):
        p = build_scout_prompt("2026-07-04")
        for tag in ("---TITLE---", "---DIARY---", "---SOLUTION---", "---SCOUT_END---"):
            self.assertIn(tag, p)


class SpecPromptTests(unittest.TestCase):
    def setUp(self):
        self.p = build_spec_prompt("2026-07-04", SCOUT)

    def test_self_containment_rule_present(self):
        self.assertIn("SELF-CONTAINMENT", self.p)

    def test_reliability_routing_present(self):
        self.assertIn("FORMAT ROUTING", self.p)
        self.assertIn("Litmus test", self.p)

    def test_concrete_algorithm_requirement_present(self):
        self.assertIn("CONCRETE step-by-step mechanical procedure", self.p)


class CodePromptTests(unittest.TestCase):
    def test_mode1_line_caps(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(mode="1", fmt="A - text"))
        self.assertIn("under 200 lines", p)
        self.assertIn("150+ lines", p)

    def test_mode3_line_caps_are_larger(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(mode="3", fmt="D - canvas"))
        self.assertIn("under 320 lines", p)
        self.assertIn("220+ lines", p)

    def test_anti_hallucination_rule_present(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec())
        self.assertIn("NEVER assert external facts", p)

    def test_raw_string_jinja_guidance_present(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(mode="3", fmt="B - form"))
        self.assertIn("Template(r'''", p)

    def test_implement_every_step_rule_present(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec())
        self.assertIn("Implement EVERY step", p)

    def test_feedback_block_injected(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(), feedback="fix the crash")
        self.assertIn("fix the crash", p)

    def test_patch_mode_includes_previous_code(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(),
                              feedback="the title is hallucinated",
                              prev_code="def process(text):\n    return text")
        self.assertIn("PATCH MODE", p)
        self.assertIn("def process(text):", p)
        self.assertIn("do NOT start over", p)

    def test_no_patch_mode_without_prev_code(self):
        p = build_code_prompt("2026-07-04", SCOUT, spec(), feedback="fix it")
        self.assertNotIn("PATCH MODE", p)

    def test_no_patch_mode_without_feedback(self):
        # First attempt: prev_code alone must not trigger patch mode.
        p = build_code_prompt("2026-07-04", SCOUT, spec(), prev_code="x = 1")
        self.assertNotIn("PATCH MODE", p)

    def test_smoke_no_unescaped_fstring_braces(self):
        # If someone adds an unescaped {var} to a prompt template, building
        # any prompt raises - these three calls are the regression net.
        build_scout_prompt("2026-07-04")
        build_spec_prompt("2026-07-04", SCOUT, feedback="x")
        build_code_prompt("2026-07-04", SCOUT, spec(), feedback="y", slim=True)


if __name__ == "__main__":
    unittest.main()
