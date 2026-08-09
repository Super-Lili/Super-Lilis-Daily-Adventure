"""Unit tests for lili_prompts: the three phase prompts must contain the
gates and rules the pipeline depends on, and the mode-aware line caps."""

import unittest

import _bootstrap  # noqa: F401

from lili_prompts import build_scout_prompt, build_spec_prompt, build_code_prompt, get_reference_tool_snippet


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


class ReferenceToolSnippetTests(unittest.TestCase):
    """Harness plan #3 (2026-08-09): a concrete shipped tool as grounding,
    on-demand only (see self_correct_code, called starting round 2+)."""

    def test_empty_memory_returns_empty_string(self):
        import lili_prompts
        original = lili_prompts.load_memory if hasattr(lili_prompts, "load_memory") else None
        import lili_memory
        original_load = lili_memory.load_memory
        lili_memory.load_memory = lambda: {"tools": []}
        try:
            self.assertEqual(get_reference_tool_snippet(), "")
        finally:
            lili_memory.load_memory = original_load

    def test_unreadable_memory_returns_empty_string_not_raise(self):
        import lili_memory
        original_load = lili_memory.load_memory
        lili_memory.load_memory = lambda: (_ for _ in ()).throw(Exception("broken"))
        try:
            self.assertEqual(get_reference_tool_snippet(), "")
        finally:
            lili_memory.load_memory = original_load

    def test_prefers_same_category_tool(self):
        import tempfile
        from pathlib import Path as _P
        d1 = tempfile.mkdtemp()
        (_P(d1) / "main.py").write_text("def process(t): return 'A'\n", encoding="utf-8")
        d2 = tempfile.mkdtemp()
        (_P(d2) / "main.py").write_text("def process(t): return 'B'\n", encoding="utf-8")

        import lili_memory
        original_load = lili_memory.load_memory
        lili_memory.load_memory = lambda: {"tools": [
            {"name": "Older Different Category", "category": "Healing Inventions", "path": d1},
            {"name": "Newer Same Category", "category": "Design Alchemy", "path": d2},
        ]}
        try:
            snippet = get_reference_tool_snippet(category="Design Alchemy")
        finally:
            lili_memory.load_memory = original_load
        self.assertIn("Newer Same Category", snippet)
        self.assertIn("def process(t): return 'B'", snippet)

    def test_falls_back_to_most_recent_when_no_category_match(self):
        import tempfile
        from pathlib import Path as _P
        d1 = tempfile.mkdtemp()
        (_P(d1) / "main.py").write_text("def process(t): return 'first'\n", encoding="utf-8")
        d2 = tempfile.mkdtemp()
        (_P(d2) / "main.py").write_text("def process(t): return 'second'\n", encoding="utf-8")

        import lili_memory
        original_load = lili_memory.load_memory
        lili_memory.load_memory = lambda: {"tools": [
            {"name": "First", "category": "Healing Inventions", "path": d1},
            {"name": "Second", "category": "Healing Inventions", "path": d2},
        ]}
        try:
            snippet = get_reference_tool_snippet(category="Office Automation")
        finally:
            lili_memory.load_memory = original_load
        self.assertIn("Second", snippet)  # most recent overall

    def test_truncates_to_max_chars(self):
        import tempfile
        from pathlib import Path as _P
        d1 = tempfile.mkdtemp()
        (_P(d1) / "main.py").write_text("x = 1\n" * 2000, encoding="utf-8")

        import lili_memory
        original_load = lili_memory.load_memory
        lili_memory.load_memory = lambda: {"tools": [{"name": "Big", "category": "", "path": d1}]}
        try:
            snippet = get_reference_tool_snippet(max_chars=100)
        finally:
            lili_memory.load_memory = original_load
        self.assertLess(len(snippet), 300)  # header text + 100-char code snippet


class MissionAreaScopeTests(unittest.TestCase):
    """P0.2 fix (2026-08-05): Office Automation's own description was written
    as an unbounded catch-all ('ANY repetitive professional production task')
    that also duplicated items already owned by Education Evolution
    (transcripts) and Design Alchemy (briefs/handoff) - a real, independent
    cause of category concentration that the category-floor ban-guard
    (F-021) cannot fix, because SCOUT was freely CHOOSING it, not being
    forced into it. 28-day ledger data: Office Automation absorbed 175/304
    attempts (58%) despite the floor guard being active."""

    def setUp(self):
        from lili_prompts import _build_context_block, _build_mission_section
        ctx = _build_context_block("2026-08-05")
        self.mission = _build_mission_section(ctx)

    def test_office_automation_is_not_an_unbounded_catchall(self):
        self.assertNotIn("ANY repetitive", self.mission)

    def test_office_automation_explicitly_excludes_transcripts(self):
        # Transcripts/podcast workflows belong to Education Evolution only -
        # the section may mention the word to explicitly rule it out, but
        # must not list it as something Office Automation itself handles.
        office_section = self.mission.split("OFFICE AUTOMATION")[1].split("HEALING")[0].lower()
        self.assertIn("not transcripts", office_section)

    def test_office_automation_explicitly_excludes_briefs(self):
        # Briefs/spec-handoff belong to Design Alchemy only.
        office_section = self.mission.split("OFFICE AUTOMATION")[1].split("HEALING")[0].lower()
        self.assertIn("not briefs", office_section)


class ScoutPromptTests(unittest.TestCase):
    def test_contains_output_tags(self):
        p = build_scout_prompt("2026-07-04")
        for tag in ("---TITLE---", "---DIARY---", "---SOLUTION---", "---SCOUT_END---"):
            self.assertIn(tag, p)

    def test_mechanical_fit_check_present(self):
        # Rule 22 (2026-08-09): a SELECTION filter applied before DESCRIPTION/
        # SOLUTION - is this friction point measurable/countable, or does it
        # need real judgment a mechanical single-file tool can't fake?
        p = build_scout_prompt("2026-08-09")
        self.assertIn("MECHANICAL FIT CHECK", p)
        self.assertIn("Hemingway App", p)

    def test_daily_offender_concepts_injected_when_present(self):
        # P2 fix (2026-08-03): concept-level repeat offenders should reach the
        # SCOUT prompt every day, not just after Sunday's gate. Uses a temp
        # ledger with a concept failing 3+ times to avoid depending on
        # whatever's in the real repo's ledger at test time.
        import tempfile
        from pathlib import Path as _Path
        import json as _json
        import lili_evolution_gate as _geval

        tmp_ledger = _Path(tempfile.mkdtemp()) / "ledger.jsonl"
        with tmp_ledger.open("w", encoding="utf-8") as f:
            for _ in range(4):
                f.write(_json.dumps({
                    "date": "2026-08-01", "tool": "Phone Screenshot Organizer",
                    "category": "Office Automation", "format": "C",
                    "passed": False, "reason": "no real algorithmic depth",
                }) + "\n")

        import lili_ledger_report as _report
        original_path = _report.LEDGER_PATH
        _report.LEDGER_PATH = tmp_ledger
        try:
            p = build_scout_prompt("2026-08-04")
        finally:
            _report.LEDGER_PATH = original_path
        self.assertIn("Phone Screenshot Organizer", p)
        self.assertIn("DO NOT propose a tool resembling", p)

    def test_no_offender_block_when_ledger_clean(self):
        import tempfile
        from pathlib import Path as _Path
        import lili_ledger_report as _report

        tmp_ledger = _Path(tempfile.mkdtemp()) / "empty_ledger.jsonl"
        original_path = _report.LEDGER_PATH
        _report.LEDGER_PATH = tmp_ledger
        try:
            p = build_scout_prompt("2026-08-04")
        finally:
            _report.LEDGER_PATH = original_path
        self.assertNotIn("DO NOT propose a tool resembling", p)


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

    def test_no_padding_rule_present(self):
        # F-009: models invent entries to complete a structure's expected shape.
        p = build_code_prompt("2026-07-04", SCOUT, spec())
        self.assertIn("NEVER invent entries", p)
        self.assertIn("traceable to a specific span of the input", p)

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
