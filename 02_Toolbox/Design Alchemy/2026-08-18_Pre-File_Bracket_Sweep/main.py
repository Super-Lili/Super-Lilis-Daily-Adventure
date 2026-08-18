"""Pre-File Bracket Sweep - copy-ready open-items memo.

Requirements: Python 3.9+ (standard library only).
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple, Set

ACTION_VERBS = {
    "insert", "add", "replace", "update", "remove", "move", "check",
    "verify", "confirm", "find", "pull", "search", "source", "link",
    "fact-check", "trim", "tighten", "expand", "reword", "call",
    "email", "send", "ask", "fix",
}
HARD_ACTION_VERBS = {
    "insert", "add", "update", "check", "verify", "confirm", "source",
    "link", "find", "fix", "replace",
}
CUE_LIST = [
    "headline", "hed", "dek", "subhead", "nut graf", "lede", "photo",
    "image", "art", "caption", "credit", "embed", "pull quote", "url",
    "link", "byline", "bio", "email", "phone", "date", "time", "name",
    "stat", "number",
]
HARD_CUES = {
    "headline", "byline", "credit", "photo", "source", "url",
    "stat", "number", "date", "time", "name",
}
STATUS_MARKERS = {
    "tk", "tbd", "tba", "todo", "fixme", "xxx", "eta", "n/a",
}
SAMPLE_DRAFT = (
    "The piece on library closures is nearly there. [TK] for the opening stat. "
    "The city said the shortfall is [NUMBER] percent. [Photo credit: TBD] [HEADLINE]"
)


def _tokens(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower()))


def _contains_any(text: str, words: Set[str] | List[str]) -> bool:
    tokens = _tokens(text)
    for word in words:
        if " " in word:
            if word in text:
                return True
        elif word in tokens:
            return True
    return False


def _classify(content: str) -> Tuple[str, str]:
    clean = content.strip()
    low = clean.lower()

    if not clean:
        return "empty", "blocker"

    if "?" in low or re.match(r"(who|what|where|when|why|how)\b", low):
        return "question", "blocker"

    if low in STATUS_MARKERS:
        return "status-marker", "blocker"

    matched_verbs = [verb for verb in ACTION_VERBS if _contains_any(low, [verb])]
    if matched_verbs:
        hard = any(verb in HARD_ACTION_VERBS for verb in matched_verbs)
        return "action-item", "blocker" if hard else "soft"

    matched_cues = [cue for cue in CUE_LIST if _contains_any(low, [cue])]
    if matched_cues:
        hard = any(cue in HARD_CUES for cue in matched_cues)
        return "missing-material", "blocker" if hard else "soft"

    if ":" in low and len(low.split()) > 3:
        hard = (
            _contains_any(low, HARD_ACTION_VERBS)
            or _contains_any(low, HARD_CUES)
            or "?" in low
        )
        return "editorial-instruction", "blocker" if hard else "soft"

    return "unclassified", "review"


def _format_row(row: Dict[str, object]) -> str:
    return f"- line {row['line']} ({row['type']}): [{row['content']}]"


def process(text: str) -> str:
    """Parse bracketed placeholders into a pre-send blocker checklist."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    rows: List[Dict[str, object]] = []
    stack: List[Tuple[int, int]] = []
    line = 1

    for pos, ch in enumerate(text):
        if ch == "[":
            stack.append((pos, line))
        elif ch == "]":
            if stack:
                start_pos, start_line = stack.pop()
                bracket_content = text[start_pos + 1:pos]
                rtype, severity = _classify(bracket_content)
                rows.append({
                    "content": bracket_content,
                    "line": start_line,
                    "type": rtype,
                    "severity": severity,
                    "pos": start_pos,
                })
        if ch == "\n":
            line += 1

    unmatched: List[Dict[str, object]] = []
    while stack:
        start_pos, start_line = stack.pop()
        rest = text[start_pos + 1:].strip().replace("\n", " ")
        if len(rest) > 140:
            rest = rest[:140] + "..."
        unmatched.append({
            "content": rest,
            "line": start_line,
            "pos": start_pos,
        })

    rows.sort(key=lambda r: (int(r["line"]), int(r["pos"])))
    unmatched.sort(key=lambda r: (int(r["line"]), int(r["pos"])))

    total = len(rows)
    blockers = [r for r in rows if r["severity"] == "blocker"]
    blocker_count = len(blockers)
    soft_section = [r for r in rows if r["severity"] == "soft"]
    question_section = [r for r in rows if r["type"] == "question"]
    unclassified_section = [r for r in rows if r["severity"] == "review"]

    memo: List[str] = []
    memo.append(f"TOTAL BRACKET COUNT: {total}")
    memo.append(f"BLOCKER COUNT: {blocker_count}")
    memo.append("")
    memo.append("Your pre-send checklist:")
    memo.append("")

    memo.append("BLOCKERS--RESOLVE BEFORE SENDING")
    if blockers:
        memo.extend(_format_row(r) for r in blockers)
    else:
        memo.append("- (none)")
    memo.append("")

    memo.append("OPEN QUESTIONS")
    if question_section:
        memo.extend(_format_row(r) for r in question_section)
    else:
        memo.append("- (none)")
    memo.append("")

    memo.append("SOFT PLACEHOLDERS")
    if soft_section:
        memo.extend(_format_row(r) for r in soft_section)
    else:
        memo.append("- (none)")
    memo.append("")

    memo.append("UNCLASSIFIED")
    if unclassified_section:
        memo.extend(_format_row(r) for r in unclassified_section)
    else:
        memo.append("- (none)")
    memo.append("")

    memo.append("UNMATCHED OPEN BRACKETS")
    if unmatched:
        memo.extend(
            f"- line {r['line']} (unmatched-open-bracket): [{r['content']}]"
            for r in unmatched
        )
    else:
        memo.append("- (none)")
    memo.append("")

    if blocker_count > 0:
        memo.append(f"NOT SEND-READY: {blocker_count} unresolved blocker(s).")
    else:
        memo.append("SEND-READY: no blockers detected.")

    return "\n".join(memo)


def _cli_main() -> None:
    import sys
    print("Paste the draft before you send (Ctrl-D to end):")
    print(process(sys.stdin.read()))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
