"""
lili_evolution_gate.py - Sealed-regression gate for weekly self-evolution.

The old flow: weekly evolution writes prose rules straight into a prompt
that's already saturated with dozens of rules - no check on whether the
change actually helps, and 4 straight weeks of ledger data (2026-W28~W31,
4->3->4->3 passes/week) show no measurable effect from any of it.

This module is the harness half of a two-part fix: evolution proposes
STRUCTURED, MACHINE-READABLE knobs (deprioritized categories, banned repeat-
offender concepts, format bias) instead of unaccountable prose, and this gate
mechanically backtests each proposal against the actual ledger data BEFORE
it's allowed to take effect - inspired by EverMind/Raven's "Evolver" pattern
(diagnose failure trajectories -> design a patch -> only promote patches that
pass a statistical gate), adapted for the fact that our evolution proposals
are numeric/categorical knobs, not deterministic code patches, so the gate is
a backtest against historical ledger data rather than a live benchmark rerun.

Unlike F-013's _guarded_write() (which only checks "does this Python file
still parse"), this gate checks "does this PROPOSAL actually match what the
data shows" - a category can only be deprioritized if its measured pass rate
is actually below the field median; a concept can only be banned if it's
actually a repeat offender in the ledger; a format can only get positive bias
if its measured pass rate is actually above median. Proposals that fail their
specific check are dropped individually (not all-or-nothing) so a partially-
sound proposal doesn't get thrown out for one bad item.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from lili_ledger_report import load_entries

KNOBS_PATH = Path("lili_evolution_knobs.json")

# Hard safety ceiling: evolution must never be able to talk itself into
# deprioritizing so many categories that SCOUT has nothing left to pick from.
# Note: by definition of a median, at most half the field can be strictly
# below it, so this must be set below 0.5 to ever actually constrain anything.
_MAX_DEPRIORITIZED_FRACTION = 0.34


def load_evolution_knobs() -> dict:
    """Read the currently-active, gate-approved evolution knobs. Returns an
    empty-but-valid structure if none exist yet or the file is corrupt -
    never let a bad knobs file break the daily pipeline that reads it."""
    empty = {"week_start": "", "deprioritized_categories": [], "banned_concepts": [],
             "format_bias": {}}
    if not KNOBS_PATH.exists():
        return empty
    try:
        data = json.loads(KNOBS_PATH.read_text(encoding="utf-8"))
        for key in empty:
            data.setdefault(key, empty[key])
        return data
    except Exception:
        return empty


def save_evolution_knobs(knobs: dict) -> None:
    KNOBS_PATH.write_text(json.dumps(knobs, indent=2, ensure_ascii=False), encoding="utf-8")


def _category_pass_rates(entries: list[dict]) -> dict[str, float]:
    """category -> pass rate, only for categories with enough volume (5+
    attempts) to be a meaningful signal rather than noise from 1-2 tries."""
    from collections import defaultdict
    counts: dict[str, list[bool]] = defaultdict(list)
    for e in entries:
        cat = e.get("category", "")
        if cat:
            counts[cat].append(bool(e.get("passed")))
    return {c: sum(v) / len(v) for c, v in counts.items() if len(v) >= 5}


def _format_pass_rates(entries: list[dict]) -> dict[str, float]:
    from collections import defaultdict
    counts: dict[str, list[bool]] = defaultdict(list)
    for e in entries:
        fmt = (e.get("format") or "").strip()[:1].upper()
        if fmt:
            counts[fmt].append(bool(e.get("passed")))
    return {f: sum(v) / len(v) for f, v in counts.items() if len(v) >= 5}


def _repeat_offender_concepts(entries: list[dict], threshold: int = 3) -> set[str]:
    from collections import Counter
    fails = Counter(
        (e.get("tool", "")[:60]) for e in entries if not e.get("passed") and e.get("tool")
    )
    return {name for name, n in fails.items() if n >= threshold}


def backtest_knobs(proposed: dict, entries: list[dict]) -> tuple[dict, list[str]]:
    """Mechanically filter a proposed knobs dict down to only the parts the
    ledger data actually supports. Returns (accepted_knobs, rejection_log) -
    rejection_log entries explain what was dropped and why, for transparency
    in the evolution report (a rejected proposal is still useful information,
    not a silent failure).
    """
    accepted: dict = {"deprioritized_categories": [], "banned_concepts": [], "format_bias": {}}
    log: list[str] = []

    cat_rates = _category_pass_rates(entries)
    if cat_rates:
        cat_median = median(cat_rates.values())
        all_cats = set(cat_rates.keys())
        proposed_cats = proposed.get("deprioritized_categories", []) or []
        sound_cats = [c for c in proposed_cats if cat_rates.get(c, 1.0) < cat_median]
        # Safety ceiling: never deprioritize more than half the field.
        max_allowed = max(1, int(len(all_cats) * _MAX_DEPRIORITIZED_FRACTION))
        if len(sound_cats) > max_allowed:
            log.append(f"deprioritized_categories: proposed {len(sound_cats)} sound candidates "
                      f"but capped at {max_allowed} (safety ceiling, {_MAX_DEPRIORITIZED_FRACTION*100:.0f}% of field)")
            sound_cats = sound_cats[:max_allowed]
        accepted["deprioritized_categories"] = sound_cats
        for c in proposed_cats:
            if c not in sound_cats and c not in accepted["deprioritized_categories"]:
                if c in cat_rates and cat_rates[c] >= cat_median:
                    log.append(f"deprioritized_categories: rejected '{c}' - measured pass rate "
                              f"{cat_rates[c]:.2f} is not below field median {cat_median:.2f}")
                elif c not in cat_rates:
                    log.append(f"deprioritized_categories: rejected '{c}' - fewer than 5 "
                              f"attempts on record, not enough signal")
    elif proposed.get("deprioritized_categories"):
        log.append("deprioritized_categories: rejected all - insufficient ledger data to backtest")

    offenders = _repeat_offender_concepts(entries)
    proposed_concepts = proposed.get("banned_concepts", []) or []
    for concept in proposed_concepts:
        # Substring match: the proposed concept text should overlap a real offender.
        if any(concept.lower() in o.lower() or o.lower() in concept.lower() for o in offenders):
            accepted["banned_concepts"].append(concept)
        else:
            log.append(f"banned_concepts: rejected '{concept[:50]}' - not found among "
                      f"repeat-offender concepts (3+ failures) in the ledger")

    fmt_rates = _format_pass_rates(entries)
    if fmt_rates:
        fmt_median = median(fmt_rates.values())
        for fmt, bias in (proposed.get("format_bias", {}) or {}).items():
            rate = fmt_rates.get(fmt)
            if rate is None:
                log.append(f"format_bias: rejected '{fmt}' - fewer than 5 attempts on record")
                continue
            if bias > 0 and rate >= fmt_median:
                accepted["format_bias"][fmt] = bias
            elif bias < 0 and rate < fmt_median:
                accepted["format_bias"][fmt] = bias
            else:
                direction = "positive" if bias > 0 else "negative"
                log.append(f"format_bias: rejected {direction} bias for '{fmt}' - measured pass "
                          f"rate {rate:.2f} does not support this direction (median {fmt_median:.2f})")
    elif proposed.get("format_bias"):
        log.append("format_bias: rejected all - insufficient ledger data to backtest")

    return accepted, log


def run_test_suite() -> tuple[bool, str]:
    """Run the full unit test suite as a behavioral safety net, mirroring
    F-013's _guarded_write() syntax check but for the evolution gate's own
    knobs file - if a proposal somehow produces something that breaks the
    pipeline's own tests, refuse it outright regardless of the backtest."""
    import subprocess
    import sys
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            capture_output=True, text=True, timeout=120,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        return result.returncode == 0, (result.stderr or result.stdout)[-500:]
    except Exception as e:
        return False, f"test suite could not run: {type(e).__name__}: {e}"


def gate_evolution_proposal(proposed: dict, week_start: str, ledger_days: int = 28) -> tuple[dict | None, list[str]]:
    """The full gate: backtest against ledger data, run the test suite as a
    safety net, and return (accepted_knobs_or_None, log). accepted_knobs is
    None only if the test suite itself is broken (a hard stop); an empty-but-
    valid knobs dict with a full rejection log is a normal, healthy outcome
    when the LLM's proposal didn't hold up to the data - that is the gate
    working as intended, not a failure of the gate.
    """
    tests_ok, test_detail = run_test_suite()
    if not tests_ok:
        return None, [f"GATE REFUSED ALL PROPOSALS: test suite is not currently green, "
                      f"refusing to layer evolution changes on top of a broken baseline. "
                      f"{test_detail}"]

    entries = load_entries(days=ledger_days)
    accepted, log = backtest_knobs(proposed, entries)
    accepted["week_start"] = week_start
    if not log:
        log.append("all proposed knobs backed by ledger data - accepted in full")
    return accepted, log
