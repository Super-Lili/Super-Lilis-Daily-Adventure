"""Tests for _apply_category_floor (P0 fix, 2026-08-03): three independent
ban sources (recent-use, recent-failure, evolution-gate) merge into one
banned_cats list with no idea the others exist. Their union could eliminate
every real choice, forcing SCOUT into whatever's left regardless of topic
fit - 2026-08-03 ledger data showed Office Automation absorbing 56% of all
attempts at a 3% pass rate, consistent with being the last category standing.
"""

import unittest

import _bootstrap  # noqa: F401

from lili_prompts import _apply_category_floor, ALL_CATEGORIES


class CategoryFloorTests(unittest.TestCase):
    def test_no_bans_returns_empty(self):
        self.assertEqual(_apply_category_floor([[], [], []]), [])

    def test_bans_under_floor_pass_through_unchanged(self):
        result = _apply_category_floor([["Office Automation"], ["Design Alchemy"], []])
        self.assertEqual(set(result), {"Office Automation", "Design Alchemy"})

    def test_union_exceeding_floor_is_trimmed(self):
        # 4 total categories, floor of 2 available means max 2 can be banned.
        # Here 3 distinct categories are flagged across sources - must trim to 2.
        result = _apply_category_floor([
            ["Office Automation"], ["Design Alchemy"], ["Education Evolution"],
        ])
        self.assertLessEqual(len(result), len(ALL_CATEGORIES) - 2)

    def test_multi_source_evidence_kept_over_single_source(self):
        # Office Automation flagged by 2 sources (stronger evidence), Design
        # Alchemy and Education Evolution each flagged by only 1. With only
        # room for 2 bans, the single-source ones should be dropped first,
        # keeping the doubly-flagged one - this directly guards against the
        # bug pattern (weak evidence still able to help eliminate everything).
        result = _apply_category_floor([
            ["Office Automation", "Design Alchemy"],
            ["Office Automation", "Education Evolution"],
            ["Healing Inventions"],
        ])
        self.assertIn("Office Automation", result)
        self.assertLessEqual(len(result), 2)

    def test_never_bans_more_than_leaves_min_available(self):
        # Every category flagged by every source - still must leave 2 open.
        result = _apply_category_floor([list(ALL_CATEGORIES)] * 3)
        self.assertEqual(len(result), len(ALL_CATEGORIES) - 2)
        remaining = set(ALL_CATEGORIES) - set(result)
        self.assertEqual(len(remaining), 2)


if __name__ == "__main__":
    unittest.main()
