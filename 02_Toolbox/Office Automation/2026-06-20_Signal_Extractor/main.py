"""
Signal Extractor — distil research notes into journalistic signals.
Extracts: key claims, attributed quotes, open questions, recurring themes.
No external dependencies.
"""
import re
import sys
import argparse
from collections import Counter

ATTRIBUTION = ["said", "says", "told", "according to", "explains", "argues",
               "claims", "noted", "added", "confirmed", "revealed", "admitted"]
STRONG_VERBS = ["proves", "shows", "reveals", "confirms", "finds", "discovers",
                "launches", "announces", "warns", "predicts", "demands",
                "rejects", "backs", "opposes", "calls for"]
STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","was","are","were","be","been","have","has","had","do",
    "does","did","will","would","could","should","may","might","this","that",
    "these","those","it","its","he","she","they","we","i","you","as","not",
    "no","so","if","then","than","when","where","who","which","what","how",
    "all","also","said","says","told","their","there","about","into","more",
    "other","such","through","up","out","after","before","just","very","any",
}


def _score(sentence: str, freq: Counter) -> float:
    words = re.findall(r'\b\w+\b', sentence.lower())
    if not words:
        return 0.0
    density = sum(freq.get(w, 0) for w in words) / len(words)
    numbers = 0.3 * len(re.findall(r'\b\d[\d,\.%]*\b', sentence))
    verbs = 0.4 * sum(1 for v in STRONG_VERBS if v in sentence.lower())
    proper = 0.15 * len(re.findall(r'(?<!\.\s)\b[A-Z][a-z]{2,}\b', sentence))
    return density + numbers + verbs + proper


def _key_claims(sentences: list, freq: Counter, n: int = 4) -> list:
    scored = []
    for s in sentences:
        if len(s.split()) < 6:
            continue
        sc = _score(s, freq) + (0.5 if re.search(r'\b\d', s) else 0)
        scored.append((sc, s.strip()))
    scored.sort(reverse=True)
    seen, out = set(), []
    for sc, s in scored:
        key = s[:45]
        if key not in seen and sc > 0.2:
            seen.add(key)
            out.append(s)
        if len(out) >= n:
            break
    return out


def _quotes(sentences: list, n: int = 3) -> list:
    out = []
    for s in sentences:
        sl = s.lower()
        if any(f" {m} " in sl or sl.startswith(m) for m in ATTRIBUTION):
            if len(s.split()) >= 7:
                out.append(s.strip())
                if len(out) >= n:
                    break
    return out


def _questions(sentences: list, n: int = 4) -> list:
    explicit = [s.strip() for s in sentences
                if s.strip().endswith('?') and len(s.split()) >= 4]
    gap_words = ["unclear", "unknown", "uncertain", "remains to be",
                 "yet to", "still", "not yet", "no word", "unconfirmed"]
    implicit = [s.strip() for s in sentences
                if any(g in s.lower() for g in gap_words)
                and not s.strip().endswith('?')]
    return (explicit + implicit)[:n]


def _themes(words: list, n: int = 5) -> list:
    content = [w for w in words if w not in STOPWORDS and len(w) > 3]
    freq = Counter(content)
    return [w for w, c in freq.most_common(n) if c >= 2]


def process(text: str) -> str:
    """Extract journalistic signals: claims, quotes, questions, themes."""
    if not text.strip():
        return ("Paste research notes, interview transcript, or article draft "
                "to extract editorial signals.")

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s.strip()]
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    freq = Counter(w for w in words if w not in STOPWORDS)

    claims = _key_claims(sentences, freq)
    quotes = _quotes(sentences)
    questions = _questions(sentences)
    themes = _themes(words)

    sep = "-" * 42
    lines = [
        "SIGNAL EXTRACTION REPORT",
        "=" * 42,
        f"Input: {len(sentences)} sentences  |  {len(words)} words",
        "",
        "KEY CLAIMS  (highest information density)",
        sep,
    ]
    lines += [f"{i}. {c}" for i, c in enumerate(claims, 1)] or ["No strong claims detected."]
    lines += [
        "",
        "ATTRIBUTED QUOTES  (on-record sources)",
        sep,
    ]
    lines += [f"{i}. {q}" for i, q in enumerate(quotes, 1)] or ["No attribution found — story needs human sources."]
    lines += [
        "",
        "OPEN QUESTIONS  (story gaps)",
        sep,
    ]
    lines += [f"{i}. {q}" for i, q in enumerate(questions, 1)] or ["No explicit gaps detected."]
    lines += [
        "",
        "RECURRING THEMES  (potential angles)",
        sep,
    ]
    lines.append("  ->  ".join(themes) if themes else "Text too short to detect themes.")
    lines += ["", "EDITORIAL NOTE", sep]

    dominant = themes[0] if themes else "the topic"
    lines.append(f"{len(claims)} substantive claims clustered around '{dominant}'.")
    if not quotes:
        lines.append("No on-record sources — needs human attribution before publication.")
    if len(questions) >= 3:
        lines.append(f"{len(questions)} unresolved questions — this is early-stage research.")
    if len(sentences) < 5:
        lines.append("Short input — paste more text for richer signal extraction.")

    return "\n".join(lines)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract journalistic signals from notes")
    parser.add_argument("text", nargs="?", default="", help="Research notes or transcript")
    parser.add_argument("--file", "-f", default="", help="Read input from file")
    args = parser.parse_args()
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            inp = f.read()
    elif args.text:
        inp = args.text
    elif not sys.stdin.isatty():
        inp = sys.stdin.read()
    else:
        inp = ""
    print(process(inp))
