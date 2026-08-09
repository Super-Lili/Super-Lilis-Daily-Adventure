"""Tests for run_retrospective_review's wiring in super_lili_weekly_evolution.py
(F-029) - the actual comparison logic lives in and is tested by
lili_evolution_gate.retrospective_check_knobs; this just confirms the
weekly-evolution entry point calls it correctly and handles the no-prior-knobs
case."""

import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from super_lili_weekly_evolution import run_retrospective_review
import lili_evolution_gate as geval


class RunRetrospectiveReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp_knobs = Path(tempfile.mkdtemp()) / "knobs.json"
        self._original_knobs_path = geval.KNOBS_PATH
        geval.KNOBS_PATH = self.tmp_knobs
        self.addCleanup(lambda: setattr(geval, "KNOBS_PATH", self._original_knobs_path))

    def test_no_prior_knobs_reports_nothing_to_review(self):
        result = run_retrospective_review("2026-08-12")
        self.assertIn("no active knobs", result)

    def test_prior_knobs_get_reviewed(self):
        geval.save_evolution_knobs({
            "week_start": "2026-08-01", "deprioritized_categories": [],
            "banned_concepts": [], "format_bias": {},
        })
        result = run_retrospective_review("2026-08-12")
        self.assertIn("2026-08-01", result)


if __name__ == "__main__":
    unittest.main()
