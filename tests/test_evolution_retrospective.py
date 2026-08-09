"""Tests for the retrospective knobs review (F-029): the gate only ever
validated a proposal AGAINST PAST DATA before applying it - nothing
previously checked whether an APPLIED knob's real-world effect matched its
stated intent, so knobs accumulated forever with no mechanism to drop one
that wasn't working. retrospective_check_knobs closes that loop.
"""

import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

import lili_evolution_gate as geval
from lili_evolution_gate import retrospective_check_knobs


def _make_ledger(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "ledger.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            row = {"date": "2026-08-01", "tool": "Test Tool", "category": "Office Automation",
                   "format": "A", "passed": True, "reason": ""}
            row.update(r)
            f.write(json.dumps(row) + "\n")
    return p


class _PatchedLedger(unittest.TestCase):
    def _patch(self, rows):
        tmp = Path(tempfile.mkdtemp())
        ledger_path = _make_ledger(tmp, rows)
        original = geval.load_entries_range
        from lili_ledger_report import load_entries_range as real_range

        def _patched(start, end, ledger_path_arg=None):
            return real_range(start, end, ledger_path=ledger_path)
        geval.load_entries_range = _patched
        self.addCleanup(lambda: setattr(geval, "load_entries_range", original))


class DeprioritizedCategoryRetrospectiveTests(_PatchedLedger):
    def test_kept_when_attempt_share_dropped(self):
        rows = (
            # Pre-window (before week_start 2026-08-08): Office Automation is 8/10 = 80% of attempts
            [{"date": "2026-08-03", "category": "Office Automation"}] * 8
            + [{"date": "2026-08-03", "category": "Design Alchemy"}] * 2
            # Post-window (after week_start): Office Automation drops to 1/10 = 10%
            + [{"date": "2026-08-09", "category": "Office Automation"}] * 1
            + [{"date": "2026-08-09", "category": "Design Alchemy"}] * 9
        )
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": ["Office Automation"],
                 "banned_concepts": [], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertIn("Office Automation", surviving["deprioritized_categories"])
        self.assertTrue(any("kept" in l and "Office Automation" in l for l in log))

    def test_dropped_when_attempt_share_did_not_decrease(self):
        rows = (
            [{"date": "2026-08-03", "category": "Office Automation"}] * 2
            + [{"date": "2026-08-03", "category": "Design Alchemy"}] * 8
            + [{"date": "2026-08-09", "category": "Office Automation"}] * 8
            + [{"date": "2026-08-09", "category": "Design Alchemy"}] * 2
        )
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": ["Office Automation"],
                 "banned_concepts": [], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertNotIn("Office Automation", surviving["deprioritized_categories"])
        self.assertTrue(any("DROPPED" in l and "Office Automation" in l for l in log))


class BannedConceptRetrospectiveTests(_PatchedLedger):
    def test_kept_when_not_recurring(self):
        rows = [
            {"date": "2026-08-03", "tool": "Phone Screenshot Organizer", "passed": False},
            {"date": "2026-08-09", "tool": "Something Totally Different", "passed": False},
        ]
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": [],
                 "banned_concepts": ["Phone Screenshot Organizer"], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertIn("Phone Screenshot Organizer", surviving["banned_concepts"])

    def test_dropped_when_still_recurring(self):
        rows = [
            {"date": "2026-08-09", "tool": "Phone Screenshot Organizer", "passed": False},
            {"date": "2026-08-10", "tool": "Phone Screenshot Organizer", "passed": False},
        ]
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": [],
                 "banned_concepts": ["Phone Screenshot Organizer"], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertNotIn("Phone Screenshot Organizer", surviving["banned_concepts"])
        self.assertTrue(any("DROPPED" in l for l in log))


class FormatBiasRetrospectiveTests(_PatchedLedger):
    def test_kept_when_moved_as_intended(self):
        rows = (
            [{"date": "2026-08-03", "format": "D", "passed": False}] * 8
            + [{"date": "2026-08-03", "format": "D", "passed": True}] * 2
            + [{"date": "2026-08-09", "format": "D", "passed": True}] * 8
            + [{"date": "2026-08-09", "format": "D", "passed": False}] * 2
        )
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": [],
                 "banned_concepts": [], "format_bias": {"D": 0.1}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertEqual(surviving["format_bias"].get("D"), 0.1)

    def test_dropped_when_moved_opposite(self):
        rows = (
            [{"date": "2026-08-03", "format": "D", "passed": True}] * 8
            + [{"date": "2026-08-03", "format": "D", "passed": False}] * 2
            + [{"date": "2026-08-09", "format": "D", "passed": False}] * 8
            + [{"date": "2026-08-09", "format": "D", "passed": True}] * 2
        )
        self._patch(rows)
        knobs = {"week_start": "2026-08-08", "deprioritized_categories": [],
                 "banned_concepts": [], "format_bias": {"D": 0.1}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertNotIn("D", surviving["format_bias"])


class RetrospectiveEdgeCaseTests(_PatchedLedger):
    def test_no_week_start_returns_unchanged(self):
        self._patch([])
        knobs = {"deprioritized_categories": ["X"], "banned_concepts": [], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertEqual(surviving, knobs)
        self.assertIn("nothing to review", log[0])

    def test_too_soon_since_application_keeps_as_is(self):
        self._patch([])
        knobs = {"week_start": "2026-08-11", "deprioritized_categories": ["X"],
                 "banned_concepts": [], "format_bias": {}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertEqual(surviving, knobs)
        self.assertTrue(any("too soon" in l for l in log))

    def test_insufficient_data_keeps_as_is(self):
        self._patch([])  # empty ledger entirely
        knobs = {"week_start": "2026-08-01", "deprioritized_categories": ["X"],
                 "banned_concepts": ["Y"], "format_bias": {"D": 0.1}}
        surviving, log = retrospective_check_knobs(knobs, "2026-08-12")
        self.assertEqual(surviving["deprioritized_categories"], ["X"])
        self.assertEqual(surviving["banned_concepts"], ["Y"])
        self.assertEqual(surviving["format_bias"], {"D": 0.1})


if __name__ == "__main__":
    unittest.main()
