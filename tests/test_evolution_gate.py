"""Tests for the sealed-regression gate on weekly self-evolution knobs
(lili_evolution_gate.py). Uses synthetic ledger data written to a temp file
so the backtest logic is exercised against real, controllable numbers rather
than whatever happens to be in the live ledger.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import _bootstrap  # noqa: F401

import lili_evolution_gate as geval
from lili_evolution_gate import backtest_knobs, load_evolution_knobs, save_evolution_knobs


def _today(offset_days: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _make_ledger(tmp_path: Path, rows: list[dict]) -> Path:
    p = tmp_path / "ledger.jsonl"
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            row = {"date": _today(), "tool": "Test Tool", "category": "Office Automation",
                   "format": "A", "passed": True, "reason": ""}
            row.update(r)
            f.write(json.dumps(row) + "\n")
    return p


class CategoryBacktestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _entries(self, rows):
        path = _make_ledger(Path(self.tmp), rows)
        from lili_ledger_report import load_entries
        return load_entries(days=28, ledger_path=path)

    def test_deprioritize_accepted_when_below_median(self):
        rows = (
            [{"category": "Office Automation", "passed": False}] * 8
            + [{"category": "Office Automation", "passed": True}] * 2
            + [{"category": "Design Alchemy", "passed": True}] * 9
            + [{"category": "Design Alchemy", "passed": False}] * 1
        )
        entries = self._entries(rows)
        proposed = {"deprioritized_categories": ["Office Automation"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertIn("Office Automation", accepted["deprioritized_categories"])

    def test_deprioritize_rejected_when_actually_above_median(self):
        rows = (
            [{"category": "Office Automation", "passed": True}] * 9
            + [{"category": "Office Automation", "passed": False}] * 1
            + [{"category": "Design Alchemy", "passed": False}] * 8
            + [{"category": "Design Alchemy", "passed": True}] * 2
        )
        entries = self._entries(rows)
        proposed = {"deprioritized_categories": ["Office Automation"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertNotIn("Office Automation", accepted["deprioritized_categories"])
        self.assertTrue(any("Office Automation" in line for line in log))

    def test_safety_ceiling_caps_deprioritized_fraction(self):
        # 4 categories: A,B below median; C,D above - both A and B are
        # individually sound, but the 0.34 ceiling on a 4-category field
        # allows at most 1, so the cap must trim the sound list further.
        rates = {"A": 0.1, "B": 0.15, "C": 0.8, "D": 0.9}
        rows = []
        for cat, rate in rates.items():
            n_pass = round(rate * 20)
            rows += [{"category": cat, "passed": True}] * n_pass
            rows += [{"category": cat, "passed": False}] * (20 - n_pass)
        entries = self._entries(rows)
        proposed = {"deprioritized_categories": ["A", "B", "C", "D"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertLessEqual(len(accepted["deprioritized_categories"]), 1)
        self.assertTrue(any("safety ceiling" in line for line in log))

    def test_insufficient_volume_category_rejected(self):
        rows = [{"category": "Design Alchemy", "passed": True}] * 6
        entries = self._entries(rows)
        proposed = {"deprioritized_categories": ["Nonexistent Category"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertNotIn("Nonexistent Category", accepted["deprioritized_categories"])
        self.assertTrue(any("not enough signal" in line for line in log))


class ConceptBacktestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _entries(self, rows):
        path = _make_ledger(Path(self.tmp), rows)
        from lili_ledger_report import load_entries
        return load_entries(days=28, ledger_path=path)

    def test_repeat_offender_concept_accepted(self):
        rows = [{"tool": "Screenshot Organizer", "passed": False}] * 4
        entries = self._entries(rows)
        proposed = {"banned_concepts": ["Screenshot Organizer"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertIn("Screenshot Organizer", accepted["banned_concepts"])

    def test_non_offender_concept_rejected(self):
        rows = [{"tool": "Screenshot Organizer", "passed": False}] * 4
        entries = self._entries(rows)
        proposed = {"banned_concepts": ["Some Totally Different Idea"]}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertNotIn("Some Totally Different Idea", accepted["banned_concepts"])
        self.assertTrue(any("not found among" in line for line in log))


class FormatBiasBacktestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _entries(self, rows):
        path = _make_ledger(Path(self.tmp), rows)
        from lili_ledger_report import load_entries
        return load_entries(days=28, ledger_path=path)

    def test_positive_bias_accepted_for_above_median_format(self):
        rows = (
            [{"format": "D", "passed": True}] * 8 + [{"format": "D", "passed": False}] * 2
            + [{"format": "A", "passed": False}] * 8 + [{"format": "A", "passed": True}] * 2
        )
        entries = self._entries(rows)
        proposed = {"format_bias": {"D": 0.1}}
        accepted, log = backtest_knobs(proposed, entries)
        self.assertEqual(accepted["format_bias"].get("D"), 0.1)

    def test_positive_bias_rejected_for_below_median_format(self):
        rows = (
            [{"format": "D", "passed": True}] * 8 + [{"format": "D", "passed": False}] * 2
            + [{"format": "A", "passed": False}] * 8 + [{"format": "A", "passed": True}] * 2
        )
        entries = self._entries(rows)
        proposed = {"format_bias": {"A": 0.1}}  # wrong direction - A is below median
        accepted, log = backtest_knobs(proposed, entries)
        self.assertNotIn("A", accepted["format_bias"])
        self.assertTrue(any("does not support this direction" in line for line in log))


class KnobsPersistenceTests(unittest.TestCase):
    def test_load_missing_file_returns_empty_valid_structure(self):
        import lili_evolution_gate as mod
        original = mod.KNOBS_PATH
        mod.KNOBS_PATH = Path(tempfile.mkdtemp()) / "nonexistent.json"
        try:
            knobs = load_evolution_knobs()
        finally:
            mod.KNOBS_PATH = original
        self.assertEqual(knobs["deprioritized_categories"], [])
        self.assertEqual(knobs["format_bias"], {})

    def test_save_then_load_roundtrip(self):
        import lili_evolution_gate as mod
        original = mod.KNOBS_PATH
        mod.KNOBS_PATH = Path(tempfile.mkdtemp()) / "knobs.json"
        try:
            save_evolution_knobs({"week_start": "2026-08-09", "deprioritized_categories": ["X"],
                                   "banned_concepts": [], "format_bias": {"D": 0.1}})
            knobs = load_evolution_knobs()
        finally:
            mod.KNOBS_PATH = original
        self.assertEqual(knobs["deprioritized_categories"], ["X"])
        self.assertEqual(knobs["format_bias"]["D"], 0.1)

    def test_corrupt_file_returns_empty_valid_structure(self):
        import lili_evolution_gate as mod
        original = mod.KNOBS_PATH
        mod.KNOBS_PATH = Path(tempfile.mkdtemp()) / "corrupt.json"
        mod.KNOBS_PATH.write_text("{not valid json", encoding="utf-8")
        try:
            knobs = load_evolution_knobs()
        finally:
            mod.KNOBS_PATH = original
        self.assertEqual(knobs["deprioritized_categories"], [])


class FullGateTests(unittest.TestCase):
    def test_gate_refuses_all_when_test_suite_broken(self):
        original = geval.run_test_suite
        geval.run_test_suite = lambda: (False, "3 failures")
        try:
            accepted, log = geval.gate_evolution_proposal({"deprioritized_categories": ["X"]}, "2026-08-09")
        finally:
            geval.run_test_suite = original
        self.assertIsNone(accepted)
        self.assertTrue(any("GATE REFUSED ALL" in line for line in log))

    def test_gate_accepts_sound_proposal_when_tests_green(self):
        tmp = Path(tempfile.mkdtemp())
        rows = (
            [{"category": "Office Automation", "passed": False}] * 8
            + [{"category": "Office Automation", "passed": True}] * 2
            + [{"category": "Design Alchemy", "passed": True}] * 9
            + [{"category": "Design Alchemy", "passed": False}] * 1
        )
        ledger_path = _make_ledger(tmp, rows)

        original_suite = geval.run_test_suite
        original_load = geval.load_entries
        geval.run_test_suite = lambda: (True, "")
        from lili_ledger_report import load_entries as real_load_entries
        geval.load_entries = lambda days=28: real_load_entries(days=days, ledger_path=ledger_path)
        try:
            accepted, log = geval.gate_evolution_proposal(
                {"deprioritized_categories": ["Office Automation"]}, "2026-08-09")
        finally:
            geval.run_test_suite = original_suite
            geval.load_entries = original_load
        self.assertIsNotNone(accepted)
        self.assertIn("Office Automation", accepted["deprioritized_categories"])
        self.assertEqual(accepted["week_start"], "2026-08-09")


if __name__ == "__main__":
    unittest.main()
