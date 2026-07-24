"""Unit tests for lili_validators: validate_spec gates, parsers, extractors,
and the browser probe's fail-open behaviour."""

import unittest

import _bootstrap  # noqa: F401  (must run before importing src modules)

from lili_validators import (
    validate_spec,
    parse_scout_response,
    parse_spec_response,
    parse_build_response,
    extract_format,
    extract_test_input,
    _strip_fences,
    _browser_interactivity_check,
    _is_environment_noise,
)


def good_spec(**overrides):
    spec = {
        "format": "A - text analysis",
        "mode": "1",
        "input_model": "raw meeting notes as free text",
        "output_model": "ranked table of action items with owners",
        "transformation": "extract action items and rank by urgency",
        "algorithmic_depth": (
            "split into sentences; detect imperative verbs; group by owner; "
            "rank by deadline proximity computed from relative date words"
        ),
        "q1_pass": "yes - addresses the exact moment notes go stale",
        "q2_pass": "yes - an editor recognises their own meeting notes",
        "q3_pass": "yes - the ranked list is actionable immediately",
        "test_input": "Alice will draft the brief by Friday. Bob reviews it next week.",
    }
    spec.update(overrides)
    return spec


class ValidateSpecTests(unittest.TestCase):
    def test_valid_spec_passes(self):
        ok, reason = validate_spec(good_spec())
        self.assertTrue(ok, reason)

    def test_missing_input_model_rejected(self):
        ok, reason = validate_spec(good_spec(input_model=""))
        self.assertFalse(ok)

    def test_identical_io_rejected(self):
        ok, reason = validate_spec(
            good_spec(input_model="plain text", output_model="plain text")
        )
        self.assertFalse(ok)

    def test_missing_algo_depth_rejected(self):
        ok, reason = validate_spec(good_spec(algorithmic_depth=""))
        self.assertFalse(ok)

    def test_aspirational_depth_rejected(self):
        ok, reason = validate_spec(
            good_spec(algorithmic_depth="intelligently understand the debate and produce insightful chapters")
        )
        self.assertFalse(ok)
        self.assertIn("aspirational", reason.lower())

    def test_numbered_steps_pass_concreteness(self):
        ok, reason = validate_spec(
            good_spec(algorithmic_depth="1. tokenize input 2. compute per-sentence readability 3. flag outliers")
        )
        self.assertTrue(ok, reason)

    def test_corpus_promise_rejected(self):
        ok, reason = validate_spec(
            good_spec(algorithmic_depth="split sentences and compare against a curated corpus of brand-voice exemplars")
        )
        self.assertFalse(ok)
        self.assertIn("self-contained", reason.lower())

    def test_pretrained_model_promise_rejected(self):
        ok, reason = validate_spec(
            good_spec(algorithmic_depth="split sentences then use a pretrained model to classify tone")
        )
        self.assertFalse(ok)

    def test_mode3_format_is_kept_not_overridden(self):
        spec = good_spec(format="D - live canvas", mode="3")
        ok, reason = validate_spec(spec)
        self.assertTrue(ok, reason)
        self.assertTrue(spec["format"].startswith("D"), spec["format"])

    def test_dead_format_b_remapped_to_a(self):
        # B shipped 0/25 over 28 days; the model ignores prompt bans, so
        # validate_spec rewrites deterministically rather than rejecting.
        spec = good_spec(format="B - multi-field form", mode="3")
        ok, reason = validate_spec(spec)
        self.assertTrue(ok, reason)
        self.assertTrue(spec["format"].startswith("A"), spec["format"])
        self.assertEqual(spec["mode"], "1")

    def test_dead_format_f_remapped_to_d(self):
        spec = good_spec(format="F - generator with inline editor", mode="3")
        ok, reason = validate_spec(spec)
        self.assertTrue(ok, reason)
        self.assertTrue(spec["format"].startswith("D"), spec["format"])
        self.assertEqual(spec["mode"], "3")

    def test_live_formats_untouched(self):
        for letter in ("A", "C", "D", "E"):
            spec = good_spec(format=f"{letter} - some rationale", mode="3")
            ok, reason = validate_spec(spec)
            self.assertTrue(ok, reason)
            self.assertTrue(spec["format"].startswith(letter), spec["format"])

    def test_short_test_input_rejected(self):
        ok, reason = validate_spec(good_spec(test_input="hi"))
        self.assertFalse(ok)

    def test_vague_q_answers_rejected(self):
        ok, reason = validate_spec(good_spec(q2_pass="yes"))
        self.assertFalse(ok)


class ParserTests(unittest.TestCase):
    SCOUT = (
        "---TITLE---\nT\n---TITLE_ZH---\nTZ\n---MOOD---\nm\n---MOOD_ZH---\nmz\n"
        "---SOURCE---\nhttps://example.com/story\n---DIARY---\nd\n---DIARY_ZH---\ndz\n"
        "---SUMMARY---\ns\n---SUMMARY_ZH---\nsz\n---DESCRIPTION---\ndesc\n"
        "---SOLUTION---\nsol\n---CATEGORY---\nDesign Alchemy\n---PATTERN---\nextract\n"
        "---PAIN_PORTRAIT---\nWHO: an editor\nMOMENT: deadline\nTRIED: templates\n---SCOUT_END---"
    )

    def test_parse_scout_fields(self):
        p = parse_scout_response(self.SCOUT)
        self.assertEqual(p["title"], "T")
        self.assertEqual(p["solution"], "sol")
        self.assertEqual(p["category"], "Design Alchemy")
        self.assertEqual(p["pain_who"], "an editor")

    def test_parse_spec_multiline_continuation(self):
        raw = (
            "---SPEC_START---\nFORMAT: A - text\nMODE: 1 - reliable\n"
            "INPUT_MODEL: free text notes\nOUTPUT_MODEL: ranked table\n"
            "TRANSFORMATION: extract and rank\n"
            "ALGORITHMIC_DEPTH: split sentences\n  then rank by verb density\n"
            "Q1_PASS: yes specific moment\nQ2_PASS: yes they recognise it\n"
            "Q3_PASS: yes actionable now\nTEST_INPUT: a realistic input line\n---SPEC_END---"
        )
        p = parse_spec_response(raw)
        self.assertEqual(p["format"], "A - text")
        self.assertIn("verb density", p["algorithmic_depth"])

    def test_parse_spec_fallback_without_tags(self):
        raw = "FORMAT: B - form\nMODE: 3 - interactive\nINPUT_MODEL: fields\nOUTPUT_MODEL: page"
        p = parse_spec_response(raw)
        self.assertEqual(p["format"], "B - form")

    def test_parse_build_response(self):
        body = "\n".join(f"x{i} = {i}" for i in range(60))  # >=50 lines = real code
        raw = f"---CODE---\n{body}\n---TEST---\nassert True\n---BUILD_END---"
        p = parse_build_response(raw)
        self.assertIn("x59 = 59", p["code"])
        self.assertEqual(p["test"].strip(), "assert True")

    def test_parse_build_short_code_treated_as_truncated(self):
        # Documented contract: <50 lines of code = truncated/empty -> retry.
        raw = "---CODE---\nprint('x')\n---TEST---\nassert True\n---BUILD_END---"
        self.assertEqual(parse_build_response(raw)["code"], "")


class ExtractorTests(unittest.TestCase):
    def test_extract_format(self):
        self.assertEqual(extract_format("FORMAT: B - form"), "B")
        self.assertEqual(extract_format("no format here"), "")

    def test_extract_test_input_stops_at_next_block(self):
        spec = "TEST_INPUT: hello world sample\nQ1-PASS: yes"
        self.assertEqual(extract_test_input(spec), "hello world sample")

    def test_strip_fences(self):
        self.assertEqual(_strip_fences("```python\nx = 1\n```"), "x = 1")
        self.assertEqual(_strip_fences("x = 1"), "x = 1")


class BrowserProbeTests(unittest.TestCase):
    def test_fail_open_without_playwright(self):
        # This environment has no playwright installed: the probe must report
        # ran=False (inconclusive) and never raise - a browser flake must not
        # be able to cause a false rest-day.
        ran, changed, detail = _browser_interactivity_check("<html><body>x</body></html>", "input")
        self.assertFalse(ran)
        self.assertIsInstance(detail, str)


class EnvironmentNoiseFilterTests(unittest.TestCase):
    # 2026-07-24: a "select an intent/tone from options" tool was rejected as
    # fake because the probe couldn't find any text field to fill AND the
    # only console error was a headless-sandbox clipboard permission denial -
    # an environment artifact, not a code bug. This filter keeps such noise
    # out of retry feedback so the model isn't told to "fix" the unfixable.
    def test_clipboard_denial_is_noise(self):
        self.assertTrue(_is_environment_noise(
            "Failed to execute 'writeText' on 'Clipboard': Write permission denied."))

    def test_real_type_error_is_not_noise(self):
        self.assertFalse(_is_environment_noise(
            "TypeError: Cannot read properties of null (reading 'value')"))

    def test_case_insensitive(self):
        self.assertTrue(_is_environment_noise("CLIPBOARD write blocked"))


if __name__ == "__main__":
    unittest.main()
