"""Tests for weekly evolution's truncation detection and retry (2026-08-27):
the response format has ~14 sequential tagged sections ending in ---END---.
A response that returns non-empty text but never reaches ---END--- silently
drops every section after wherever it stopped - most consequentially
EVOLUTION_KNOBS, which is last. This was invisible for two straight weeks
(2026-08-16, 2026-08-23) because the old retry logic only checked for an
exception or fully-empty text, never an incomplete-but-non-empty response.

Also covers the call_gemini -> call_deepseek_evolution rename (a Gemini-era
leftover name; the implementation had already been DeepSeek-only since the
2026-07-03 migration, only the name was stale).
"""

import time as _time
import unittest

import _bootstrap
from _bootstrap import make_scripted_client

import super_lili_weekly_evolution as evo
from super_lili_weekly_evolution import _is_truncated_evolution_response, call_deepseek_evolution

_time.sleep = lambda s: None
evo.time.sleep = lambda s: None

_FULL_RESPONSE = """---REFLECTION---
This week was fine.
---BLINDSPOT---
A. CATEGORY IMBALANCE: none notable.
---STRENGTHS---
- Shipped two real tools.
---GROWTH_AREAS---
- Diversify categories more.
---OSS_TOOL---
pdfplumber
---EVOLVED_PERSONALITY---
Same as before.
---EVOLVED_SKILLS---
["skill 1"]
---EVOLUTION_NOTES---
No major changes.
---ENGINEERING_LESSONS---
RULE: be careful.
---LETTER---
Dear next week's Lili, do well.
---DIARY---
Today was a good week.
---DOMAIN_EXPANSION---
TOOL: something
---SOURCE_PROPOSALS---
SOURCE: somewhere
---EVOLUTION_KNOBS---
{}
---END---
"""

_TRUNCATED_RESPONSE = """---REFLECTION---
This week was fine.
---BLINDSPOT---
A. CATEGORY IMBALANCE: none notable, but then the response just stops mid
"""


class TruncationDetectionTests(unittest.TestCase):
    def test_full_response_not_truncated(self):
        self.assertFalse(_is_truncated_evolution_response(_FULL_RESPONSE))

    def test_cut_off_response_is_truncated(self):
        self.assertTrue(_is_truncated_evolution_response(_TRUNCATED_RESPONSE))

    def test_empty_string_is_truncated(self):
        self.assertTrue(_is_truncated_evolution_response(""))


class CallDeepseekEvolutionTests(unittest.TestCase):
    def setUp(self):
        self._original = evo.deepseek_client

    def tearDown(self):
        evo.deepseek_client = self._original

    def test_full_response_accepted_first_try(self):
        evo.deepseek_client = make_scripted_client([_FULL_RESPONSE])
        self.assertEqual(call_deepseek_evolution("p"), _FULL_RESPONSE)

    def test_truncated_response_is_retried_not_accepted(self):
        # 2026-08-16/08-23 regression: a truncated-but-non-empty response
        # used to be accepted as "success" on the first attempt.
        evo.deepseek_client = make_scripted_client([_TRUNCATED_RESPONSE, _FULL_RESPONSE])
        self.assertEqual(call_deepseek_evolution("p"), _FULL_RESPONSE)

    def test_all_truncated_falls_back_to_last_partial_rather_than_none(self):
        # Real content (Reflection/Blindspot/etc.) must not be discarded
        # entirely just because Knobs never arrived - matches the pre-fix
        # behavior of saving whatever sections were reached.
        evo.deepseek_client = make_scripted_client(
            [_TRUNCATED_RESPONSE, _TRUNCATED_RESPONSE, _TRUNCATED_RESPONSE])
        result = call_deepseek_evolution("p")
        self.assertEqual(result, _TRUNCATED_RESPONSE)

    def test_exception_still_retried_and_recovers(self):
        evo.deepseek_client = make_scripted_client(["ERR", _FULL_RESPONSE])
        self.assertEqual(call_deepseek_evolution("p"), _FULL_RESPONSE)

    def test_total_failure_with_no_content_at_all_returns_none(self):
        evo.deepseek_client = make_scripted_client(["ERR", "ERR", "ERR"])
        self.assertIsNone(call_deepseek_evolution("p"))


if __name__ == "__main__":
    unittest.main()
