"""Tests for the BUILD retry-feedback branch router in lili_pipeline.py.

This logic has been verified ad hoc via bash one-liners several times during
debugging (2026-07-03 ~ 07-24) instead of being a real test - exactly the kind
of drift that causes a new branch to accidentally shadow or be shadowed by an
older one. This file makes routing a first-class, regression-tested contract.

The router itself lives inline inside evolve()'s BUILD loop (not a standalone
function), so we re-implement the same keyword-matching order here and assert
it matches the real branch conditions in lili_pipeline.py. If someone edits
the branch order there without updating this file, the two independent
descriptions will disagree and a human should reconcile them.
"""

import unittest

import _bootstrap  # noqa: F401


def route(build_reason: str) -> str:
    """Mirrors the elif chain in lili_pipeline.py's BUILD retry loop, in order."""
    r = build_reason.lower()
    if "unrendered template placeholder" in r:
        return "unrendered-template"
    if any(s in r for s in (
        "line continuation", "was never closed", "unexpected character", "invalid syntax",
        "unmatched", "f-string", "invalid escape",
    )):
        return "string-escaping"
    if "unterminated" in r or "syntax error" in r:
        return "truncation"
    if "browser ground-truth" in r:
        return "browser-ground-truth"
    if any(s in r for s in ("filler", "padded", "padding", "add no value", "adds no value",
                            "hallucinat", "invented", "arbitrary")):
        return "padding"
    if "generic" in r or "static" in r or "same regardless" in r:
        return "generic-static"
    if "identical" in r or "nearly identical" in r or ("generic" in r and "same" in r):
        return "identical-output"
    if any(s in r for s in ("hardcoded", "data-*", "pre-populated")):
        return "hardcoded"
    if (any(s in r for s in ("must contain", "input must", "error: input", "check the format",
                             "please provide", "please check"))
            or ("output too weak" in r and any(s in r for s in ("not found", "no valid", "found in", "format", "please")))):
        return "rigid-input"
    if "mode 3 is temporarily disabled" in r:
        return "mode3-disabled"
    if "import crashed" in r:
        return "import-crash"
    return "other"


class RetryRoutingTests(unittest.TestCase):
    def test_browser_ground_truth_routes_correctly(self):
        # 2026-07-22~24: this exact reason repeated across 4 patch attempts
        # with zero routing to a dedicated branch before this fix.
        reason = ("Browser ground-truth check: the tool's DOM did NOT change when the "
                  "test input was entered and controls were clicked (fields_filled=1, "
                  "text_changed=False, nodes 21->21)")
        self.assertEqual(route(reason), "browser-ground-truth")

    def test_browser_ground_truth_with_console_errors_still_routes(self):
        reason = ("Browser ground-truth check: DOM did NOT change (nodes 21->21), "
                  "console_errors=['TypeError: Cannot read properties of null']")
        self.assertEqual(route(reason), "browser-ground-truth")

    def test_truncation_not_shadowed_by_browser_check(self):
        reason = "Syntax error at line 255: unterminated triple-quoted string literal"
        self.assertEqual(route(reason), "truncation")

    def test_string_escaping_not_shadowed_by_truncation(self):
        reason = "Syntax error at line 63: unexpected character after line continuation character"
        self.assertEqual(route(reason), "string-escaping")

    def test_padding_not_shadowed_by_identical(self):
        reason = ("Critic: The output is padded with filler sentences that add no value "
                  "(hallucinating a generic Conclusion chapter at an arbitrary timecode)")
        self.assertEqual(route(reason), "padding")

    def test_rigid_input_refusal_routes_correctly(self):
        reason = ("Output too weak: 70 chars, 1 lines. Got: 'No speaker-turn segments found "
                  "in transcript. Please check the format.'")
        self.assertEqual(route(reason), "rigid-input")

    def test_fake_static_without_browser_prefix_still_generic(self):
        # Critic-only fake-interactivity call (no browser probe ran) should NOT be
        # mistaken for the browser-verified branch - different confidence, different advice.
        reason = "Critic: the JavaScript does nothing with user input, this is a static tool"
        self.assertEqual(route(reason), "generic-static")


if __name__ == "__main__":
    unittest.main()
