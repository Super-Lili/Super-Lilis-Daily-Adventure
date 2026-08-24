# Requirements: Python 3.10+
# Input: free-form "war story" paragraphs. Output: structured markdown Decision Logic Map.
import re, math, sys
from collections import Counter
from itertools import combinations
from typing import List, Set, Tuple

DECISION_CUES = {
    "decided": "ship_move", "chose": "ship_move", "picked": "ship_move", "went with": "ship_move",
    "cut": "scope_cut", "killed": "risk_stop", "dropped": "scope_cut", "delayed": "resource_trade",
    "postponed": "resource_trade", "pushed back": "stakeholder_push", "said no": "stakeholder_push",
    "rejected": "stakeholder_push", "prioritized": "resource_trade", "deferred": "resource_trade",
    "stopped": "risk_stop", "reverted": "risk_stop", "launched": "ship_move", "shipped": "ship_move",
    "scaled": "ship_move", "negotiated": "stakeholder_push", "escalated": "stakeholder_push",
    "standardized on": "ship_move",
}
OUTCOME_CUES = ("resulted", "led to", "worked", "failed", "backfired", "improved", "dropped",
                "increased", "decreased", "retained", "lost", "churn", "retention", "engagement",
                "upsell", "tickets", "errors", "fine", "avoided")
POSITIVE_CUES = ("worked", "improved", "increased", "avoided", "no issues", "no spike", "upsell",
                 "zero compliance", "on time", "flat", "did not spike")
NEGATIVE_CUES = ("failed", "backfired", "dropped", "lost", "churn", "fine", "errors")
CONSTRAINT_CUES = ("deadline","budget","time","headcount","team","engineers","dependency","risk",
                   "legal","compliance","data","user","scope","quality","revenue","cost",
                   "vendor","client","testing","qa")
STOPWORDS = set("""a about above after again against all almost alone along already also although
always among another any anybody anyone anything anyway anywhere around as at back be because been
before behind below beside besides between beyond both but by came can cannot come could did do
does doing done down each eight either every everybody everyone everything except few find first
five for four from further get give go had has have he her here hers herself him himself his how
however i if in into is it its itself just keep last let like made make many may me might mine
more most much must my myself never no nobody none nor not nothing now of off often on once one
only onto or other others ought our out over own part people per perhaps please put rather
same saw see seem several shall she should since so some somebody someone something sometimes
still such take than that the their theirs them themselves then there these they this those
though three through to together too toward two under until up upon us use very via want was way
we well went were what when where whether which while who whole whom whose why will with within
without would yes yet you your yours""".split())
MOVE_LABELS = {
    "scope_cut": "cut scope",
    "stakeholder_push": "push back on stakeholders",
    "resource_trade": "trade resources or time",
    "risk_stop": "stop or revert to control risk",
    "ship_move": "ship or launch",
}

def _split_episodes(text: str) -> List[str]:
    t = text.strip()
    if not t:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    if len(parts) >= 2:
        return parts
    parts = [p.strip() for p in re.split(r"(?:^|\n)\s*(?:[-*•]|\d+[.)])\s*", t) if p.strip()]
    if len(parts) >= 2:
        return parts
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", t) if p.strip()]
    if len(parts) >= 2:
        return parts
    parts = [t[i:i+400].strip() for i in range(0, len(t), 400)]
    if len(parts) >= 2:
        return parts
    return [t]

def _split_clauses(ep: str) -> List[str]:
    parts = re.split(r";\s*|\s*,\s*(?=(?:so|but|because|which|and)\b)", ep)
    return [p.strip() for p in parts if p.strip()]

def _tag_clause(clause: str) -> Tuple[str, str]:
    lower = clause.lower()
    if lower.startswith("context:"):
        return "CONTEXT", clause.split(":", 1)[1].strip()
    if lower.startswith("decision:"):
        return "DECISION", clause.split(":", 1)[1].strip()
    if lower.startswith("outcome:"):
        return "OUTCOME", clause.split(":", 1)[1].strip()
    for cue in sorted(DECISION_CUES, key=len, reverse=True):
        if cue in lower:
            return "DECISION", clause
    for cue in OUTCOME_CUES:
        if cue in lower:
            return "OUTCOME", clause
    return "CONTEXT", clause

def _tokens(s: str) -> Set[str]:
    return {t for t in re.findall(r"[a-z]{4,}", s.lower()) if t not in STOPWORDS}

def _raw_tokens(s: str) -> List[str]:
    return re.findall(r"[a-z]+", s.lower())

def _constraint_phrases(clause: str) -> List[str]:
    toks = _raw_tokens(clause)
    found = []
    for cue in CONSTRAINT_CUES:
        for i, w in enumerate(toks):
            if w == cue:
                phrase = " ".join(toks[max(0, i-3):i+7])
                found.append(phrase)
    return found

def _moves_in_clause(clause: str) -> Set[str]:
    lower = clause.lower()
    return {move for cue, move in DECISION_CUES.items() if cue in lower}

def _classify_outcome(text: str) -> str:
    lower = text.lower()
    pos = sum(1 for cue in POSITIVE_CUES if cue in lower)
    neg = sum(1 for cue in NEGATIVE_CUES if cue in lower)
    if pos > neg:
        return "validated"
    if neg > pos:
        return "revisit"
    return "unknown"

def _apriori(term_sets: List[Set[str]], min_sup: int) -> List[Tuple[Tuple[str, ...], int]]:
    freq1 = Counter()
    for ts in term_sets:
        freq1.update(ts)
    result = []
    frequent_terms = [t for t, c in freq1.items() if c >= min_sup]
    for t, c in freq1.items():
        if c >= min_sup:
            result.append(((t,), c))
    for a, b in combinations(frequent_terms, 2):
        count = sum(1 for ts in term_sets if a in ts and b in ts)
        if count >= min_sup:
            result.append(((a, b), count))
    return result

def _clean_quote(s: str, limit: int = 260) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > limit:
        s = s[:limit-3].rstrip() + "..."
    return s

def _get_input() -> str:
    user_input = globals().get('USER_INPUT')
    if user_input is not None:
        return user_input
    return sys.stdin.read()

def _cli_main() -> None:
    print(process(_get_input()))

def process(text: str) -> str:
    """Turn pasted war stories into a structured, evidence-backed Decision Logic Map."""
    if not text.strip():
        return "Paste at least two decision stories separated by blank lines, bullets, or sentences."

    episodes = _split_episodes(text)
    if len(episodes) < 2:
        return "Please paste at least two decision stories separated by blank lines, bullets, or sentences. I need enough examples to find a pattern."

    min_sup = max(2, math.ceil(0.3 * len(episodes)))
    rows = []
    move_evidence = {}
    move_freq = Counter()
    constraint_counter = Counter()

    for idx, ep in enumerate(episodes, 1):
        clauses = _split_clauses(ep)
        terms: Set[str] = set()
        decisions = []
        outcomes = []
        row_moves: Set[str] = set()
        for clause in clauses:
            tag, content = _tag_clause(clause)
            if tag == "CONTEXT":
                terms.update(_tokens(content))
                for phrase in _constraint_phrases(content):
                    constraint_counter[phrase] += 1
            elif tag == "DECISION":
                moves = _moves_in_clause(content)
                decisions.append((content, moves))
                row_moves.update(moves)
                for m in moves:
                    move_evidence.setdefault(m, []).append(content)
                    move_freq[m] += 1
            elif tag == "OUTCOME":
                outcomes.append(content)
        if not outcomes:
            outcomes = [ep]
        label = _classify_outcome(" ".join(outcomes))
        rows.append({
            "idx": idx, "ep": ep, "terms": terms, "decisions": decisions,
            "outcomes": outcomes, "label": label, "moves": row_moves,
        })

    lines = [
        "# Decision Logic Map",
        "",
        "Here is the judgment map I found in your stories. Each rule is tied to your own words, so you can trace it back to a real episode.",
        "",
    ]
    lines.append(f"Episodes analyzed: {len(episodes)}; minimum support = {min_sup}.")
    lines += [
        "",
        "How to read this map: outcome labels are `validated` (the decision worked), `revisit` (it did not), or `unknown` (unclear). Decision cues include `cut`, `pushed back`, `prioritized`, and `shipped`; constraints include `deadline`, budget, team, scope, legal, and client signals.",
        "",
    ]

    lines += ["", "## Recurring situations", ""]
    lines.append("These context patterns kept showing up across your episodes:")
    freq = _apriori([r["terms"] for r in rows], min_sup)
    if freq:
        for combo, count in sorted(freq, key=lambda x: (-x[1], x[0])):
            lines.append(f"- {' + '.join(combo)} ({count} episode{'s' if count != 1 else ''})")
    else:
        lines.append("- No single situation repeated above the support threshold. Add more stories to see stronger patterns.")

    lines += ["", "## Constraints that shaped decisions", ""]
    lines.append("These contextual constraints appeared often enough to be part of your judgment map:")
    if constraint_counter:
        for phrase, count in constraint_counter.most_common(8):
            lines.append(f'- "{_clean_quote(phrase, 220)}" — seen {count} time{"s" if count != 1 else ""}')
    else:
        lines.append("- No constraint phrases detected. Look for deadline, budget, team, scope, or client language.")

    lines += ["", "## Decision moves by type", ""]
    lines.append("These are the move classes I observed, with the actual decision clauses as evidence:")
    for move in ("scope_cut", "stakeholder_push", "resource_trade", "risk_stop", "ship_move"):
        evidence = move_evidence.get(move, [])
        lines.append(f"- {MOVE_LABELS[move]} ({move}): {len(evidence)} decision clause{'s' if len(evidence) != 1 else ''}")
        seen = set()
        for clause in evidence:
            if clause not in seen:
                seen.add(clause)
                lines.append(f'    example: "{_clean_quote(clause)}"')
        if not evidence:
            lines.append("    example: none in these episodes")

    lines += ["", "## Conditional principles with counts and evidence", ""]
    lines.append("These are the when/then rules that emerge from the recurring situations:")
    if freq:
        for combo, count in sorted(freq, key=lambda x: (-x[1], x[0])):
            itemset = set(combo)
            matches = [r for r in rows if itemset.issubset(r["terms"])]
            n = len(matches)
            move_counts = Counter()
            for r in matches:
                move_counts.update(r["moves"])
            if move_counts:
                dominant = max(move_counts.items(), key=lambda kv: (kv[1], move_freq[kv[0]]))[0]
                evidence = ""
                for r in matches:
                    for clause, moves in r["decisions"]:
                        if dominant in moves:
                            evidence = clause
                            break
                    if evidence:
                        break
                if not evidence:
                    evidence = "(no decision clause captured, but the move appears in the episode)"
                lines.append(
                    f"- When {' + '.join(combo)}, I tend to {dominant} ({n}/{len(rows)} episodes). "
                    f"Evidence: \"{_clean_quote(evidence)}\""
                )
            else:
                lines.append(f"- When {' + '.join(combo)}, no move class was captured in the matching episodes ({n}/{len(rows)}).")
    else:
        lines.append("- When no single situation repeated above the support threshold, no conditional rule was generated; individual episodes are listed below instead.")

    lines += ["", "## Episode index", ""]
    lines.append("This is the story list I worked from:")
    for r in rows:
        lines.append(f"{r['idx']}. [{r['label']}] \"{_clean_quote(r['ep'], 200)}\"")

    return "\n".join(lines)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
