"""Unit tests for lili_llm: retry-on-empty, cross-provider fallback chain,
and the reasoner chain - the exact failure modes that caused rest days."""

import unittest
import time as _time

import _bootstrap
from _bootstrap import make_scripted_client

import lili_llm

_time.sleep = lambda s: None  # never wait in tests
lili_llm.time.sleep = lambda s: None


class CallChainTests(unittest.TestCase):
    def setUp(self):
        self._ds, self._qw = lili_llm._deepseek_client, lili_llm._qwen_client

    def tearDown(self):
        lili_llm._deepseek_client, lili_llm._qwen_client = self._ds, self._qw

    def test_empty_response_is_retried_not_fatal(self):
        # 2026-07-03 regression: one empty response used to abort the model.
        lili_llm._deepseek_client = make_scripted_client([None, None, "code"])
        lili_llm._qwen_client = None
        self.assertEqual(lili_llm.call_gemini_simple("p"), "code")

    def test_cross_provider_fallback_to_qwen(self):
        lili_llm._deepseek_client = make_scripted_client(["ERR", "ERR", "ERR"])
        lili_llm._qwen_client = make_scripted_client(["qwen result"])
        self.assertEqual(lili_llm.call_gemini_simple("p"), "qwen result")

    def test_reasoner_falls_back_to_v4_pro(self):
        # R1 empty x3, then v4-pro succeeds on the same DeepSeek client.
        lili_llm._deepseek_client = make_scripted_client([None, None, None, "spec"])
        lili_llm._qwen_client = None
        self.assertEqual(lili_llm.call_gemini_simple("p", use_reasoner=True), "spec")

    def test_total_failure_returns_none(self):
        lili_llm._deepseek_client = make_scripted_client(["ERR"] * 6)
        lili_llm._qwen_client = make_scripted_client([None] * 3)
        self.assertIsNone(lili_llm.call_gemini_simple("p"))

    def test_no_clients_returns_none(self):
        lili_llm._deepseek_client = None
        lili_llm._qwen_client = None
        self.assertIsNone(lili_llm.call_gemini_simple("p"))

    def test_whitespace_only_response_treated_as_empty(self):
        lili_llm._deepseek_client = make_scripted_client(["   \n  ", "real"])
        lili_llm._qwen_client = None
        self.assertEqual(lili_llm.call_gemini_simple("p"), "real")


class CallWithRetryTests(unittest.TestCase):
    """The shared retry primitive (2026-08-20, deepseek-harness-inspired
    'capability seam' pattern): every provider call goes through one retry
    contract instead of each call site hand-rolling its own, so a fix to
    retry behavior doesn't need to be re-derived per call site."""

    def test_succeeds_first_try(self):
        calls = []
        def fn():
            calls.append(1)
            return "result"
        self.assertEqual(lili_llm.call_with_retry(fn, "test"), "result")
        self.assertEqual(len(calls), 1)

    def test_retries_on_empty_then_succeeds(self):
        results = iter([None, "", "result"])
        fn = lambda: next(results)
        self.assertEqual(lili_llm.call_with_retry(fn, "test"), "result")

    def test_retries_on_exception_then_succeeds(self):
        results = iter([Exception("boom"), "result"])
        def fn():
            r = next(results)
            if isinstance(r, Exception):
                raise r
            return r
        self.assertEqual(lili_llm.call_with_retry(fn, "test", max_attempts=2), "result")

    def test_exhausts_attempts_returns_none(self):
        fn = lambda: None
        self.assertIsNone(lili_llm.call_with_retry(fn, "test", max_attempts=3))

    def test_on_error_callback_receives_error_text(self):
        seen = []
        def fn():
            raise RuntimeError("specific failure")
        lili_llm.call_with_retry(fn, "test", max_attempts=1, on_error=lambda e: seen.append(e))
        self.assertEqual(len(seen), 1)
        self.assertIn("specific failure", seen[0])


class DeepSeekScoutFallbackTests(unittest.TestCase):
    """2026-08-19/20 incident: DeepSeek's SCOUT fallback used to be a single
    bare call with no retry - a transient empty response (an established,
    documented DeepSeek behavior per FINDINGS F-003) cost a full rest day
    instead of succeeding on a retry, exactly like Qwen's own search already
    handled. Now goes through the same call_with_retry primitive."""

    def setUp(self):
        self._ds = lili_llm._deepseek_client

    def tearDown(self):
        lili_llm._deepseek_client = self._ds

    def test_empty_response_is_retried_not_immediately_fatal(self):
        lili_llm._deepseek_client = make_scripted_client([None, "real scout content"])
        self.assertEqual(lili_llm.call_deepseek_scout_fallback("p"), "real scout content")

    def test_exhausted_retries_returns_none(self):
        lili_llm._deepseek_client = make_scripted_client([None, None, None])
        self.assertIsNone(lili_llm.call_deepseek_scout_fallback("p"))

    def test_no_client_returns_none(self):
        lili_llm._deepseek_client = None
        self.assertIsNone(lili_llm.call_deepseek_scout_fallback("p"))

    def test_error_recorded_for_later_billing_classification(self):
        lili_llm._deepseek_client = make_scripted_client(["ERR", "ERR", "ERR"])
        lili_llm.call_deepseek_scout_fallback("p")
        self.assertIn("scripted failure", lili_llm.get_last_deepseek_scout_error())


class CriticTests(unittest.TestCase):
    def setUp(self):
        self._ds, self._qw = lili_llm._deepseek_client, lili_llm._qwen_client

    def tearDown(self):
        lili_llm._deepseek_client, lili_llm._qwen_client = self._ds, self._qw

    def test_critic_uses_qwen(self):
        lili_llm._qwen_client = make_scripted_client(["PASS:"])
        self.assertEqual(lili_llm.call_qwen_critic("p"), "PASS:")

    def test_critic_falls_back_to_deepseek_without_qwen(self):
        lili_llm._qwen_client = None
        lili_llm._deepseek_client = make_scripted_client(["REJECT: fake"])
        self.assertEqual(lili_llm.call_qwen_critic("p"), "REJECT: fake")


if __name__ == "__main__":
    unittest.main()
