"""
lili_ledger_report.py - Aggregate tool_quality_ledger.jsonl into a
failure-mode report so weekly evolution reflects on STATISTICS, not
impressions of the last few days.

Buckets are keyword-matched against the ledger 'reason' field - the same
failure taxonomy the retry-feedback branches in lili_pipeline.py use.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LEDGER_PATH = Path("tool_quality_ledger.jsonl")

# Ordered: first match wins. Keep in sync with lili_pipeline retry branches.
FAILURE_BUCKETS = [
    ("browser-ground-truth", ("browser ground-truth", "dom did not react")),
    ("syntax-error",         ("syntax error", "unterminated", "was never closed", "line continuation")),
    ("fake-static",          ("fundamentally fake", "does nothing with", "static", "fake interactiv")),
    ("hallucination-padding", ("hallucinat", "invented", "arbitrary", "filler", "padded", "fabricat")),
    ("identical-output",     ("identical", "nearly identical", "repeated", "same regardless")),
    ("refusal-weak-output",  ("check the format", "output too weak", "must contain", "please provide")),
    ("no-algorithmic-depth", ("no real algorithmic depth", "trivial regex", "boilerplate")),
    ("generic-shallow",      ("generic", "template-like", "could apply to anyone", "10 seconds")),
    ("hardcoded",            ("hardcoded", "lookup table", "data-*", "pre-populated", "pre-filled")),
    ("unrendered-template",  ("unrendered",)),
]


def classify_reason(reason: str) -> str:
    r = (reason or "").lower()
    for bucket, keywords in FAILURE_BUCKETS:
        if any(k in r for k in keywords):
            return bucket
    return "other"


def load_entries(days: int = 28, ledger_path: Path | None = None) -> list[dict]:
    path = ledger_path or LEDGER_PATH
    if not path.exists():
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("date", "") >= cutoff:
            entries.append(e)
    return entries


def build_ledger_report(days: int = 28, ledger_path: Path | None = None) -> str:
    """One-page statistical report: pass rate by week, failure buckets,
    category performance, repeat-offender concepts."""
    entries = load_entries(days, ledger_path)
    if not entries:
        return "(quality ledger empty for this period)"

    total = len(entries)
    passed = sum(1 for e in entries if e.get("passed"))

    # Pass rate by ISO week
    weeks: dict[str, list[bool]] = defaultdict(list)
    for e in entries:
        try:
            wk = datetime.strptime(e["date"], "%Y-%m-%d").strftime("%G-W%V")
        except (KeyError, ValueError):
            continue
        weeks[wk].append(bool(e.get("passed")))
    week_lines = [
        f"    {wk}: {sum(v)}/{len(v)} attempts passed"
        for wk, v in sorted(weeks.items())
    ]

    # Failure buckets (failed entries only)
    buckets = Counter(classify_reason(e.get("reason", ""))
                      for e in entries if not e.get("passed"))
    bucket_lines = [f"    {name}: {count}" for name, count in buckets.most_common()]

    # Per-category attempts/passes
    cats: dict[str, list[bool]] = defaultdict(list)
    for e in entries:
        cats[e.get("category", "?") or "?"].append(bool(e.get("passed")))
    cat_lines = [
        f"    {c}: {sum(v)}/{len(v)} passed"
        for c, v in sorted(cats.items(), key=lambda kv: -len(kv[1]))
    ]

    # Repeat offenders: same tool concept failing on 3+ attempts
    concept_fails = Counter(
        (e.get("tool", "")[:60]) for e in entries if not e.get("passed") and e.get("tool")
    )
    offenders = [f"    {n}x  {name}" for name, n in concept_fails.most_common(5) if n >= 3]

    parts = [
        f"  Window: last {days} days | attempts: {total} | passed: {passed} "
        f"({passed / total * 100:.0f}% per attempt)",
        "  Pass rate by week:",
        *week_lines,
        "  Failure modes (keyword-bucketed):",
        *bucket_lines,
        "  By category:",
        *cat_lines,
    ]
    if offenders:
        parts += ["  Repeat-offender concepts (3+ failed attempts):", *offenders]
    return "\n".join(parts)


if __name__ == "__main__":
    print(build_ledger_report())
