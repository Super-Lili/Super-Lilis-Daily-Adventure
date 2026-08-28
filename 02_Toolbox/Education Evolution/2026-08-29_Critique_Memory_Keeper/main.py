import re
from collections import defaultdict

STOPWORDS = set("""
a about after again all also an and any are as at
be because been before being between both but by
can could did do does doing down during
each even ever every few for from get gets give go goes going got
had has have he her here hers herself him himself his how
i if in into is it its itself
just like make makes many may me might more most much must my myself
need needs never not now of off on once only or other our ours ourselves out over own
put puts quite rather really same she should so some such
than that the their theirs them themselves then there these they this those through to too under until up very
was we were what when where which while who whom why will with would
you your yours yourself yourselves
""".split())


def _split_prefix(line: str) -> tuple[str, str, str]:
    """Return (source, body, date) after removing a leading source/date tag."""
    line = line.strip()
    m = re.match(r'^(?:[a-zA-Z ]+?\s+)?\d{4}[-/]\d{2}[-/]\d{2}.*?[:—-]\s+', line)
    if m:
        tag = m.group(0).strip()
        body = line[m.end():].strip()
        d = re.search(r'\d{4}[-/]\d{2}[-/]\d{2}', tag)
        date = d.group(0) if d else ''
        src = re.sub(r'\d{4}[-/]\d{2}[-/]\d{2}.*$', '', tag).strip(' :—-')
        return src, body, date

    m2 = re.match(r'^([A-Z][A-Za-z ]{0,40}?)\s*[:—-]\s+(.+)$', line)
    if m2:
        return m2.group(1).strip(), m2.group(2).strip(), ''
    return '', line, ''


def _norm(text: str) -> list[str]:
    """Lowercase, replace non-alphabetic with spaces, and drop stopwords."""
    text = re.sub(r'[^a-z\s]', ' ', text.lower())
    return [w for w in text.split() if w not in STOPWORDS]


def _terms(tokens: list[str]) -> tuple[set[str], set[str]]:
    """Extract unigram and adjacent-bigram content tokens."""
    unigrams = set(tokens)
    bigrams = set()
    for i in range(len(tokens) - 1):
        bigrams.add(tokens[i] + ' ' + tokens[i + 1])
    return unigrams, bigrams


def _md(value: str) -> str:
    """Make a value safe for Markdown table cells."""
    return value.replace('|', '/')


def _build_report(items: list[dict], parsed_count: int, themes: list[dict], orphans: list[dict]) -> str:
    """Build the final portable Markdown ledger report."""
    lines: list[str] = []
    lines.append('# Critique Feedback Ledger + Pre-flight Checklist')
    lines.append('')
    lines.append(f'Parsed {parsed_count} snippets, clustering {len(themes)} recurring themes.')
    lines.append('')
    lines.append('## Feedback Ledger')
    lines.append('')
    lines.append('| Theme | Count | Sources | Top Example Excerpt |')
    lines.append('|---|---|---|---|')

    for theme in themes:
        srcs = []
        for item_id in theme['assigned']:
            item = items[item_id]
            srcs.append(item['src_display'] or 'note')
        src_str = '; '.join(dict.fromkeys(srcs))
        lines.append(
            f"| {_md(theme['label'])} | {theme['count']} | {_md(src_str)} | {_md(theme['excerpt'])} |"
        )

    lines.append('')
    lines.append('## Pre-flight Checklist')
    lines.append('')
    for theme in themes:
        if theme['count'] >= 2:
            lines.append(
                f"- [ ] Review \"{_md(theme['label'])}\" — see \"{_md(theme['excerpt'])}\""
            )

    lines.append('')
    lines.append('## Orphan Items')
    lines.append('')
    if orphans:
        for item in orphans:
            prefix = f"{item['src_display']}: " if item['src_display'] else ''
            lines.append(f"- {prefix}{_md(item['body'])}")
    else:
        lines.append('- None')

    return '\n'.join(lines)


def process(text: str) -> str:
    """Parse raw critique snippets into a recurring-feedback ledger plus checklist."""
    if not text.strip():
        return 'Paste a critique dump to build a feedback ledger.'

    items: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        for segment in re.split(r';\s*', line):
            part = segment.strip()
            if not part:
                continue

            src, body, date = _split_prefix(part)
            tokens = _norm(body)
            if len(tokens) < 3:
                continue

            src_display = (src + ' ' + date).strip() if src or date else ''
            items.append({
                'id': len(items),
                'src': src,
                'body': body,
                'date': date,
                'src_display': src_display,
                'tokens': tokens,
            })

    if not items:
        return 'No actionable critique snippets found after normalization.'

    term_items: defaultdict[str, set[int]] = defaultdict(set)
    for item in items:
        unigrams, bigrams = _terms(item['tokens'])
        for token in unigrams:
            term_items[token].add(item['id'])
        for token in bigrams:
            term_items[token].add(item['id'])

    seeds = {token: set(ids) for token, ids in term_items.items() if len(ids) >= 2}
    themes: list[dict] = []

    if seeds:
        seed_names = list(seeds)
        parent = {s: s for s in seed_names}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            root_a, root_b = find(a), find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for i in range(len(seed_names)):
            for j in range(i + 1, len(seed_names)):
                a, b = seed_names[i], seed_names[j]
                set_a, set_b = seeds[a], seeds[b]
                denom = len(set_a | set_b)
                if denom and len(set_a & set_b) / denom > 0.6:
                    union(a, b)

        groups: defaultdict[str, list[str]] = defaultdict(list)
        for seed in seed_names:
            groups[find(seed)].append(seed)

        for group in groups.values():
            assigned: set[int] = set()
            for seed in group:
                assigned |= seeds[seed]

            scored = []
            for seed in group:
                scored.append((seed, len(term_items[seed] & assigned)))
            scored.sort(key=lambda x: (-x[1], 0 if ' ' in x[0] else 1, x[0]))

            label = ' '.join(x[0] for x in scored[:3])

            tagged = [item for item in items if item['id'] in assigned and item['date']]
            if tagged:
                chosen = max(tagged, key=lambda x: (x['date'], len(x['body'])))
            else:
                candidates = [item for item in items if item['id'] in assigned]
                chosen = max(candidates, key=lambda x: len(x['body']), default=items[0])

            themes.append({
                'label': label,
                'count': len(assigned),
                'assigned': assigned,
                'excerpt': chosen['body'][:90],
            })

        themes.sort(key=lambda x: (-x['count'], x['label']))

    assigned_any: set[int] = set()
    for theme in themes:
        assigned_any |= theme['assigned']

    orphans = [item for item in items if item['id'] not in assigned_any]
    return _build_report(items, len(items), themes, orphans)


def _cli_main() -> None:
    import sys
    print(process(sys.stdin.read()))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
