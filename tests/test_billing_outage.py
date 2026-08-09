"""Tests for billing-outage detection and visibility (2026-08-07).

Real incident: Qwen (DashScope) went into payment arrears and DeepSeek ran
out of balance simultaneously for 2+ days (2026-08-06/07). SCOUT failed on
the very first call every single run, so none of this session's harness
work (F-019~F-023) ever got a chance to run - but the diary just said
"Phase 1 failed", indistinguishable from an ordinary creative rest day,
so the real cause (an unpaid bill) went unnoticed until someone read the
raw Action logs by hand. These tests lock in the fix: a billing-outage
rest day must be classified and diarized distinctly from a normal one.
"""

import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from lili_llm import is_billing_error
from lili_pipeline import classify_scout_failure, save_rest_day, check_billing_outage_preflight
import lili_pipeline as _pipeline_mod


class IsBillingErrorTests(unittest.TestCase):
    def test_qwen_arrearage_detected(self):
        msg = ("Error code: 400 - {'error': {'message': 'Access denied, please make sure "
              "your account is in good standing. For details, see: https://help.aliyun.com/"
              "zh/model-studio/error-code#overdue-payment', 'type': 'Arrearage'}}")
        self.assertTrue(is_billing_error(msg))

    def test_deepseek_insufficient_balance_detected(self):
        msg = "Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error'}}"
        self.assertTrue(is_billing_error(msg))

    def test_openai_style_quota_exceeded_detected(self):
        msg = "Error code: 429 - You exceeded your current quota, please check your plan and billing details."
        self.assertTrue(is_billing_error(msg))

    def test_ordinary_network_error_not_flagged(self):
        msg = "Connection timed out after 30000ms"
        self.assertFalse(is_billing_error(msg))

    def test_ordinary_server_error_not_flagged(self):
        msg = "Error code: 500 - Internal server error, please retry"
        self.assertFalse(is_billing_error(msg))

    def test_empty_string_not_flagged(self):
        self.assertFalse(is_billing_error(""))


class ClassifyScoutFailureTests(unittest.TestCase):
    def test_qwen_billing_error_alone_triggers_outage_classification(self):
        reason = classify_scout_failure("Arrearage: overdue payment", "")
        self.assertTrue(reason.startswith("INFRASTRUCTURE OUTAGE"))

    def test_deepseek_billing_error_alone_triggers_outage_classification(self):
        reason = classify_scout_failure("", "Insufficient Balance")
        self.assertTrue(reason.startswith("INFRASTRUCTURE OUTAGE"))

    def test_both_billing_errors_included_in_reason(self):
        reason = classify_scout_failure("Arrearage error", "Insufficient Balance error")
        self.assertIn("Arrearage", reason)
        self.assertIn("Insufficient Balance", reason)

    def test_ordinary_failures_do_not_trigger_outage_classification(self):
        reason = classify_scout_failure("Connection timed out", "Connection timed out")
        self.assertFalse(reason.startswith("INFRASTRUCTURE OUTAGE"))
        self.assertIn("Phase 1 failed", reason)


class SaveRestDayVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_cwd = Path.cwd()
        import os
        os.chdir(self.tmpdir)

    def tearDown(self):
        import os
        os.chdir(self._orig_cwd)

    def test_infrastructure_outage_gets_distinct_banner(self):
        save_rest_day("2026-08-07", classify_scout_failure("Arrearage", "Insufficient Balance"))
        content = Path("01_Work_Log/2026-08-07-Diary.md").read_text(encoding="utf-8")
        self.assertIn("基础设施故障", content)
        self.assertNotIn("今天莉莉在休息", content)

    def test_ordinary_rest_day_keeps_original_template(self):
        save_rest_day("2026-08-07", "Critic review failed: output is generic.")
        content = Path("01_Work_Log/2026-08-07-Diary.md").read_text(encoding="utf-8")
        self.assertIn("今天莉莉在休息", content)
        self.assertNotIn("基础设施故障", content)


class PreflightHealthCheckTests(unittest.TestCase):
    """Harness plan #4 (2026-08-07): a cheap pre-flight probe should skip the
    full SCOUT->SPEC->BUILD cycle ONLY when NEITHER provider can work - a
    single healthy provider must be allowed through, since the fallback
    chains can carry the whole pipeline alone (proven 2026-08-07: Qwen in
    arrears, DeepSeek alone shipped a real tool)."""

    def _patch_health(self, health: dict):
        original = _pipeline_mod.check_provider_health
        _pipeline_mod.check_provider_health = lambda: health
        return original

    def test_both_billing_dead_returns_outage_reason(self):
        original = self._patch_health({
            "qwen": (False, "Arrearage: overdue payment"),
            "deepseek": (False, "Insufficient Balance"),
        })
        try:
            reason = check_billing_outage_preflight()
        finally:
            _pipeline_mod.check_provider_health = original
        self.assertIsNotNone(reason)
        self.assertTrue(reason.startswith("INFRASTRUCTURE OUTAGE"))

    def test_one_healthy_provider_does_not_skip(self):
        original = self._patch_health({
            "qwen": (False, "Arrearage: overdue payment"),
            "deepseek": (True, ""),
        })
        try:
            reason = check_billing_outage_preflight()
        finally:
            _pipeline_mod.check_provider_health = original
        self.assertIsNone(reason)

    def test_both_healthy_does_not_skip(self):
        original = self._patch_health({"qwen": (True, ""), "deepseek": (True, "")})
        try:
            reason = check_billing_outage_preflight()
        finally:
            _pipeline_mod.check_provider_health = original
        self.assertIsNone(reason)

    def test_both_down_for_non_billing_reason_does_not_skip(self):
        # A transient network blip on both providers simultaneously is not
        # evidence of a billing outage - let the real SCOUT/BUILD calls
        # retry normally instead of prematurely declaring a rest day.
        original = self._patch_health({
            "qwen": (False, "Connection timed out"),
            "deepseek": (False, "Connection timed out"),
        })
        try:
            reason = check_billing_outage_preflight()
        finally:
            _pipeline_mod.check_provider_health = original
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
