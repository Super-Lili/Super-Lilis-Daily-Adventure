"""Tests for the weekly-evolution self-modification guardrail and the
ledger report - the two defenses added after the 2026-07-12 incident
(evolution wrote a triple-quoted example into its own carrier file,
leaving a SyntaxError that poisoned every import for a day)."""

import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from super_lili_weekly_evolution import _sanitize_embedded, _guarded_write
from lili_ledger_report import classify_reason, build_ledger_report


class SanitizeTests(unittest.TestCase):
    def test_triple_quotes_escaped(self):
        # The exact 2026-07-12 failure: a lesson containing a docstring example.
        lesson = 'RULE: use docstrings\nHOW: def f():\n    """example"""\n    pass'
        safe = _sanitize_embedded(lesson)
        content = f'X = """\n{safe}\n"""\n'
        import ast
        ast.parse(content)  # must not raise
        ns: dict = {}
        exec(compile(content, "<t>", "exec"), ns)
        self.assertIn("example", ns["X"])

    def test_trailing_backslash_stripped(self):
        # Python 3.11 (our CI target) forbids a backslash inside an f-string's
        # {} expression - compute it first, then interpolate the plain value.
        raw_with_trailing_backslash = "ends with backslash " + "\\"
        safe = _sanitize_embedded(raw_with_trailing_backslash)
        content = f'X = """{safe}"""\n'
        import ast
        ast.parse(content)

    def test_plain_text_unchanged(self):
        self.assertEqual(_sanitize_embedded("normal rule text"), "normal rule text")


class GuardedWriteTests(unittest.TestCase):
    def test_refuses_syntax_error_and_keeps_old_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mod.py"
            p.write_text("GOOD = 1\n", encoding="utf-8")
            ok = _guarded_write(p, 'X = """broken\n', ["X"], "test")
            self.assertFalse(ok)
            self.assertEqual(p.read_text(), "GOOD = 1\n")  # last week's file intact

    def test_refuses_missing_required_name(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mod.py"
            ok = _guarded_write(p, "Y = 1\n", ["X"], "test")
            self.assertFalse(ok)
            self.assertFalse(p.exists())

    def test_writes_valid_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mod.py"
            ok = _guarded_write(p, 'X = "hello"\n', ["X"], "test")
            self.assertTrue(ok)
            self.assertIn("hello", p.read_text())

    def test_refuses_exec_crash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mod.py"
            ok = _guarded_write(p, "X = 1/0\n", ["X"], "test")
            self.assertFalse(ok)
            self.assertFalse(p.exists())


class LedgerReportTests(unittest.TestCase):
    def test_classify_known_buckets(self):
        cases = {
            "Browser ground-truth: DOM did not react to input": "browser-ground-truth",
            "Syntax error at line 63: unterminated string": "syntax-error",
            "The tool is fundamentally fake and does nothing with input": "fake-static",
            "hallucinating a generic Conclusion at an arbitrary timecode": "hallucination-padding",
            "interpretations are nearly identical across words": "identical-output",
            "Output too weak: 70 chars. Got: 'please check the format'": "refusal-weak-output",
            "The tool has no real algorithmic depth, trivial regex": "no-algorithmic-depth",
            "completely unrelated novel failure": "other",
        }
        for reason, expected in cases.items():
            self.assertEqual(classify_reason(reason), expected, reason)

    def test_report_from_sample_ledger(self):
        entries = [
            {"date": "2026-07-15", "tool": "Screenshot organizer", "category": "Office Automation",
             "passed": False, "reason": "fundamentally fake and does nothing with input"},
            {"date": "2026-07-15", "tool": "Screenshot organizer", "category": "Office Automation",
             "passed": False, "reason": "fundamentally fake again"},
            {"date": "2026-07-16", "tool": "Screenshot organizer", "category": "Office Automation",
             "passed": False, "reason": "fundamentally fake third time"},
            {"date": "2026-07-16", "tool": "Headline scale", "category": "Design Alchemy",
             "passed": True, "reason": ""},
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ledger.jsonl"
            p.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
            report = build_ledger_report(days=3650, ledger_path=p)
        self.assertIn("attempts: 4", report)
        self.assertIn("fake-static: 3", report)
        self.assertIn("Repeat-offender", report)
        self.assertIn("Screenshot organizer", report)

    def test_empty_ledger(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "none.jsonl"
            self.assertIn("empty", build_ledger_report(ledger_path=p))


if __name__ == "__main__":
    unittest.main()
