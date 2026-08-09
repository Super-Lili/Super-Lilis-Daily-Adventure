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

from datetime import datetime, timedelta

from lili_ledger_report import load_entries, load_entries_range

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


_MIN_DAYS_BEFORE_RETROSPECTIVE = 3


def retrospective_check_knobs(knobs: dict, today: str, window_days: int = 7) -> tuple[dict, list[str]]:
    """Close the loop the gate itself doesn't: gate_evolution_proposal only
    checks a proposal AGAINST PAST DATA before applying it - nothing
    previously checked whether an applied knob actually did anything once it
    was live. Knobs accumulated forever with no mechanism to notice one
    wasn't working and drop it.

    Compares the `window_days` BEFORE a knob's week_start against the
    `window_days` (or however many have elapsed) AFTER it, using the same
    ledger data the gate itself trusts, and drops any knob whose real-world
    effect didn't match its stated intent:
      - deprioritized_categories should show a DROP in that category's share
        of total attempts after application (the knob's whole point is fewer
        attempts land there) - a category still or MORE picked than before is
        proof the knob isn't being respected/effective.
      - banned_concepts should stop recurring as a repeat offender after
        application - still recurring 2+ times means the ban isn't working.
      - format_bias should see the format's pass rate move in the direction
        the bias intended (positive bias -> rate up, negative -> rate down) -
        a delta in the wrong direction contradicts the bias's own premise.

    Returns (surviving_knobs, log) - surviving_knobs keeps only what the
    retrospective check actually supports; log explains every keep/drop
    decision for transparency in the evolution report, same principle as
    backtest_knobs' rejection log.
    """
    week_start = knobs.get("week_start", "")
    if not week_start:
        return knobs, ["no active knobs with a week_start - nothing to review"]

    try:
        start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
    except ValueError:
        return knobs, [f"unparseable week_start '{week_start}' - skipping retrospective"]

    days_elapsed = (today_dt - start_dt).days
    if days_elapsed < _MIN_DAYS_BEFORE_RETROSPECTIVE:
        return knobs, [f"only {days_elapsed} day(s) since {week_start} - too soon to judge, keeping as-is"]

    pre_start = (start_dt - timedelta(days=window_days)).strftime("%Y-%m-%d")
    post_end = today
    pre_entries = load_entries_range(pre_start, week_start)
    post_entries = load_entries_range(week_start, post_end)

    surviving = {"deprioritized_categories": [], "banned_concepts": [], "format_bias": {}}
    log: list[str] = []

    if pre_entries and post_entries:
        pre_total, post_total = len(pre_entries), len(post_entries)
        for cat in knobs.get("deprioritized_categories", []):
            pre_share = sum(1 for e in pre_entries if e.get("category") == cat) / pre_total
            post_share = sum(1 for e in post_entries if e.get("category") == cat) / post_total
            if post_share < pre_share:
                surviving["deprioritized_categories"].append(cat)
                log.append(f"deprioritized_categories: kept '{cat}' - attempt share dropped "
                          f"{pre_share:.2f} -> {post_share:.2f} since {week_start}")
            else:
                log.append(f"deprioritized_categories: DROPPED '{cat}' - attempt share did not "
                          f"decrease ({pre_share:.2f} -> {post_share:.2f}), knob had no measurable effect")
    else:
        surviving["deprioritized_categories"] = list(knobs.get("deprioritized_categories", []))
        log.append("deprioritized_categories: insufficient pre/post data to judge - keeping as-is")

    if post_entries:
        from collections import Counter
        post_fail_counts = Counter(e.get("tool", "")[:60] for e in post_entries if not e.get("passed"))
        for concept in knobs.get("banned_concepts", []):
            recurrence = sum(n for name, n in post_fail_counts.items()
                            if concept.lower() in name.lower() or name.lower() in concept.lower())
            if recurrence < 2:
                surviving["banned_concepts"].append(concept)
                log.append(f"banned_concepts: kept '{concept[:50]}' - not recurring since {week_start}")
            else:
                log.append(f"banned_concepts: DROPPED '{concept[:50]}' - still recurred {recurrence}x "
                          f"since {week_start}, ban had no measurable effect")
    else:
        surviving["banned_concepts"] = list(knobs.get("banned_concepts", []))
        log.append("banned_concepts: insufficient post-application data to judge - keeping as-is")

    if pre_entries and post_entries:
        def _fmt_rate(entries, fmt):
            matching = [e for e in entries if (e.get("format") or "").strip()[:1].upper() == fmt]
            return (sum(1 for e in matching if e.get("passed")) / len(matching)) if matching else None

        for fmt, bias in (knobs.get("format_bias") or {}).items():
            pre_rate = _fmt_rate(pre_entries, fmt)
            post_rate = _fmt_rate(post_entries, fmt)
            if pre_rate is None or post_rate is None:
                log.append(f"format_bias: insufficient data for '{fmt}' - keeping as-is")
                surviving["format_bias"][fmt] = bias
                continue
            moved_as_intended = (post_rate >= pre_rate) if bias > 0 else (post_rate <= pre_rate)
            if moved_as_intended:
                surviving["format_bias"][fmt] = bias
                log.append(f"format_bias: kept '{fmt}' - pass rate moved as intended "
                          f"({pre_rate:.2f} -> {post_rate:.2f})")
            else:
                log.append(f"format_bias: DROPPED '{fmt}' - pass rate moved opposite to the "
                          f"bias direction ({pre_rate:.2f} -> {post_rate:.2f})")
    else:
        surviving["format_bias"] = dict(knobs.get("format_bias") or {})
        log.append("format_bias: insufficient pre/post data to judge - keeping as-is")

    if not log:
        log.append("no active knobs to review")
    return surviving, log
