# Rate Anchor Calculator
# Requirements: Python 3.8+, standard library only

import re
import math
import statistics
from collections import Counter
from typing import List, Dict, Optional, Tuple, Any

# -------------------------------------------------------------------
# Helper: simple Porter-lite stemmer (removes common suffixes)
def stem(word: str) -> str:
    w = word.lower()
    if len(w) <= 3:
        return w
    for suf in ('ing', 'ed', 'ly', 's'):
        if w.endswith(suf) and len(w[:-len(suf)]) >= 2:
            return w[:-len(suf)]
    return w

def tokenize(text: str) -> List[str]:
    return [stem(t) for t in re.findall(r'\w+', text.lower()) if t.isalpha()]

def split_past_new(raw: str) -> Tuple[List[str], Optional[str]]:
    lines = raw.strip().split('\n')
    past_lines = []
    new_line = None
    delimiter_found = False
    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("NEW PROJECT:"):
            delimiter_found = True
            after = stripped.split(":", 1)[1].strip()
            if '|' in after:
                new_line = after
            continue
        if delimiter_found:
            if '|' in stripped:
                new_line = stripped
                break
        else:
            if stripped:
                past_lines.append(stripped)
    if not delimiter_found:
        past_lines = [l for l in lines if l.strip()]
    return past_lines, new_line

def parse_project(line: str) -> Optional[Dict[str, Any]]:
    parts = line.strip().split('|')
    if len(parts) < 7:
        return None
    name, client, scope, hours_str, rate_str, hidden, concessions = parts[:7]
    try:
        hours = float(hours_str)
    except ValueError:
        return None
    rate = None
    if rate_str.strip() not in ('', '?', 'None', 'none'):
        try:
            rate = float(rate_str)
        except ValueError:
            rate = None
    return {
        'name': name.strip(),
        'client': client.strip(),
        'scope': scope.strip(),
        'hours': hours,
        'rate': rate,
        'hidden': hidden.strip(),
        'concessions': concessions.strip(),
    }

def parse_input(text: str) -> Tuple[List[Dict], Optional[Dict]]:
    past_lines, new_line = split_past_new(text)
    past_projects = [parse_project(l) for l in past_lines]
    past_projects = [p for p in past_projects if p is not None]
    new_project = None
    if new_line:
        new_project = parse_project(new_line)
    return past_projects, new_project

# -------------------------------------------------------------------
# Algorithmic steps
def rate_summary(past: List[Dict]) -> str:
    rates = [p['rate'] for p in past if p['rate'] is not None]
    if not rates:
        return "No valid past rate data available."
    hours = [p['hours'] for p in past if p['rate'] is not None]
    weighted = sum(r*h for r,h in zip(rates, hours)) / sum(hours) if sum(hours) > 0 else 0.0
    mean_r = statistics.mean(rates)
    median_r = statistics.median(rates)
    return (f"Past projects with rate data: {len(rates)}\n"
            f"Mean rate: ${mean_r:.2f}/hr\n"
            f"Median rate: ${median_r:.2f}/hr\n"
            f"Hours-weighted mean rate: ${weighted:.2f}/hr")

def hidden_labor_analysis(past: List[Dict]) -> Tuple[str, float]:
    keywords = {"unpaid", "extra round", "scope creep", "discovery", "training", "explain"}
    total_unbilled = 0.0
    total_billed = 0.0
    per_project = []
    for p in past:
        hidden = p['hidden'].lower()
        # count occurrences of each keyword phrase
        kw_hits = 0
        for kw in keywords:
            kw_hits += len(re.findall(re.escape(kw), hidden))
        unb = 0.0
        for match in re.finditer(r'(\d+\.?\d*)\s*(hours?|h)', hidden):
            try:
                unb += float(match.group(1))
            except ValueError:
                pass
        total_unbilled += unb
        total_billed += p['hours']
        per_project.append((p['name'], kw_hits, unb))
    ratio = total_unbilled / total_billed if total_billed > 0 else 0.0
    report = (f"Total billed hours: {total_billed:.1f}\n"
              f"Estimated unbilled hours (from hidden notes): {total_unbilled:.1f}\n"
              f"Hidden labor ratio: {ratio:.2%}\n"
              "Per-project hidden labor signals:")
    for name, cnt, unb in per_project:
        report += f"\n  {name}: {cnt} keyword hits, ~{unb:.1f} unbilled hours"
    return report, ratio

def concession_patterns(past: List[Dict]) -> str:
    kw = {"discount", "deferred", "equity", "referral"}
    total = 0
    details = []
    for p in past:
        field = p['concessions'].lower()
        c = sum(len(re.findall(re.escape(w), field)) for w in kw)
        total += c
        details.append((p['name'], c))
    lines = [f"Total concession mentions: {total}"]
    for name, cnt in details:
        lines.append(f"  {name}: {cnt}")
    return '\n'.join(lines)

def build_bow(doc: str) -> Counter:
    return Counter(tokenize(doc))

def tfidf_cosine(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    dot = sum(w * v2.get(t, 0) for t, w in v1.items())
    n1 = math.sqrt(sum(v**2 for v in v1.values()))
    n2 = math.sqrt(sum(v**2 for v in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)

def similar_projects(past: List[Dict], new: Optional[Dict]) -> str:
    if new is None:
        return "No new project to compare."
    docs = [f"{p['scope']} {p['client']}" for p in past]
    doc_bows = [build_bow(d) for d in docs]
    N = len(docs)
    if N == 0:
        return "No past projects to compare."
    df = Counter()
    for bow in doc_bows:
        for term in set(bow.keys()):
            df[term] += 1
    idf = {term: math.log(N / df[term]) if df[term] > 0 else 0 for term in df}
    tfidf_vecs = []
    for bow in doc_bows:
        vec = {t: f * idf[t] for t, f in bow.items()}
        tfidf_vecs.append(vec)
    new_scope = f"{new['scope']} {new['client']}" if new else ""
    new_bow = build_bow(new_scope)
    new_tfidf = {t: f * idf.get(t, 0) for t, f in new_bow.items() if idf.get(t, 0) > 0}
    if not new_tfidf:
        return "No overlapping terms between new project and past projects."
    scores = []
    for i, vec in enumerate(tfidf_vecs):
        sim = tfidf_cosine(new_tfidf, vec)
        scores.append((sim, i))
    scores.sort(reverse=True)
    top = scores[:3]
    lines = []
    for rank, (sim, idx) in enumerate(top, 1):
        p = past[idx]
        lines.append(f"{rank}. {p['name']} (similarity {sim:.3f}) - Rate: ${p['rate']}/hr")
        lines.append(f"   Hidden notes: {p['hidden']}")
    return '\n'.join(lines) if lines else "No similar projects found."

def recommendation(past: List[Dict], hidden_ratio: float) -> str:
    rates = sorted([p['rate'] for p in past if p['rate'] is not None])
    if not rates:
        return "No past rate data to anchor recommendation."
    if len(rates) < 2:
        return f"Only one past project ({rates[0]}), cannot compute a range."
    p25 = rates[int(0.25 * len(rates))]
    p75 = rates[int(0.75 * len(rates))]
    uplift = hidden_ratio * 100
    return (f"Past rate range (25th-75th percentile): ${p25:.0f}–${p75:.0f}/hr\n"
            f"Suggested uplift for hidden labor: +{uplift:.0f}%")

def process(text: str) -> str:
    """Compute a rate anchor report from project log + new project description."""
    if not text.strip():
        return "Please paste your project log and new project details (pipe-delimited format)."
    past, new_project = parse_input(text)
    if not past and not new_project:
        return "No valid project data found. Please check the format."
    report = []
    report.append("RATE SUMMARY")
    report.append(rate_summary(past))
    hidden_report, hidden_ratio = hidden_labor_analysis(past)
    report.append("\nHIDDEN LABOR ANALYSIS")
    report.append(hidden_report)
    report.append("\nCONCESSION PATTERNS")
    report.append(concession_patterns(past))
    report.append("\nSIMILAR PAST PROJECTS")
    report.append(similar_projects(past, new_project))
    report.append("\nANCHORED RATE RECOMMENDATION")
    report.append(recommendation(past, hidden_ratio))
    return '\n'.join(report)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            print(process(f.read()))
    else:
        print(process(sys.stdin.read()))