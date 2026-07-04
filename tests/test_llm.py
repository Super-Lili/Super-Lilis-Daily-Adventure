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
