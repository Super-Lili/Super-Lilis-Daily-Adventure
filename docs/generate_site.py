"""
generate_site.py — Super-Lili's GitHub Pages site generator
Reads all diary, tool, and evolution content and produces a beautiful static site.

Usage:
    python docs/generate_site.py

Output:
    docs/index.html
    docs/tools/YYYY-MM-DD-toolname/index.html  (one per tool)
"""

from __future__ import annotations

import os
import re
import html
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR  = REPO_ROOT / "docs"
WORK_LOG  = REPO_ROOT / "01_Work_Log"
TOOLBOX   = REPO_ROOT / "02_Toolbox"
EVOL_LOG  = REPO_ROOT / "03_Evolution_Log"

REPO_URL  = "https://github.com/Super-Lili/Super-Lilis-Daily-Adventure"
SITE_URL  = "https://super-lili.github.io/Super-Lilis-Daily-Adventure/"

CATEGORY_LABELS = {
    "Education Evolution": "Education",
    "Design Alchemy":      "Design",
    "Office Automation":   "Office",
    "Healing Inventions":  "Healing",
}


# ── Data readers ───────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """Convert a string to a URL-safe slug."""
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    return name.strip("-")


def read_diaries() -> list[dict]:
    """Parse all diary .md files from 01_Work_Log/."""
    diaries = []
    if not WORK_LOG.exists():
        return diaries

    for f in sorted(WORK_LOG.glob("*-Diary.md"), reverse=True):
        try:
            text = f.read_text(encoding="utf-8")
            lines = text.splitlines()

            # Title: first line stripped of #
            title = lines[0].lstrip("#").strip() if lines else f.stem

            # Chinese title: optional second line starting with ###
            title_zh = ""
            if len(lines) > 1 and lines[1].startswith("###"):
                title_zh = lines[1].lstrip("#").strip()

            # Mood: first line containing ** ... *
            mood = ""
            for line in lines:
                m = re.search(r"\*([^*]+)\*", line)
                if m and len(m.group(1)) > 10:
                    mood = m.group(1)
                    break

            # Excerpt: first substantial paragraph after the --- separator
            # Skip metadata lines: **, #, *(source badges), →, emoji-only lines
            excerpt = ""
            past_separator = False
            for line in lines:
                if line.strip() == "---":
                    past_separator = True
                    continue
                if not past_separator:
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(("**", "#", "*(", "*Note", "➡️", "→", "🇨🇳")):
                    continue
                if len(stripped) > 40:
                    excerpt = stripped
                    break

            date_str = f.stem.replace("-Diary", "")
            diaries.append({
                "date":     date_str,
                "title":    title,
                "title_zh": title_zh,
                "mood":     mood,
                "excerpt":  excerpt[:220] + ("..." if len(excerpt) > 220 else ""),
                "filename": f.name,
                "github":   f"{REPO_URL}/blob/main/01_Work_Log/{f.name}",
            })
        except Exception as exc:
            print(f"  ⚠ Could not parse diary {f.name}: {exc}")

    return diaries


def read_tools() -> list[dict]:
    """Collect all tools from 02_Toolbox/Category/YYYY-MM-DD_ToolName/."""
    tools = []
    if not TOOLBOX.exists():
        return tools

    for cat_dir in sorted(TOOLBOX.iterdir()):
        if not cat_dir.is_dir():
            continue
        category = cat_dir.name

        for tool_dir in sorted(cat_dir.iterdir(), reverse=True):
            if not tool_dir.is_dir():
                continue

            dir_name = tool_dir.name
            if len(dir_name) < 11:
                continue

            try:
                date_str  = dir_name[:10]
                datetime.strptime(date_str, "%Y-%m-%d")
                tool_name = dir_name[11:].replace("_", " ")
            except (ValueError, IndexError):
                continue

            # Description from README
            description = ""
            readme_path = tool_dir / "README.md"
            try:
                if readme_path.exists():
                    readme = readme_path.read_text(encoding="utf-8")
                    for line in readme.splitlines():
                        if line.startswith("**What it does:**"):
                            description = line.replace("**What it does:**", "").strip()
                            break
                    if not description:
                        for line in readme.splitlines():
                            stripped = line.strip()
                            if stripped and not stripped.startswith("#") and not stripped.startswith(">") and not stripped.startswith("---"):
                                description = stripped[:200]
                                break
            except Exception:
                pass

            # Requirements
            requirements: list[str] = []
            req_path = tool_dir / "requirements.txt"
            try:
                if req_path.exists():
                    requirements = [
                        r.strip() for r in req_path.read_text(encoding="utf-8").splitlines()
                        if r.strip() and not r.startswith("#")
                    ]
            except Exception:
                pass

            tool_slug = f"{date_str}-{slugify(tool_name)}"

            tools.append({
                "date":         date_str,
                "name":         tool_name,
                "category":     category,
                "description":  description,
                "slug":         tool_slug,
                "dir_name":     dir_name,
                "requirements": requirements,
                "readme_path":  readme_path,
                "github":       f"{REPO_URL}/blob/main/02_Toolbox/{category}/{dir_name}/main.py",
            })

    return tools


def read_evolutions() -> list[dict]:
    """Parse weekly evolution .md files from 03_Evolution_Log/."""
    entries = []
    if not EVOL_LOG.exists():
        return entries

    for f in sorted(EVOL_LOG.glob("*.md"), reverse=True):
        try:
            text  = f.read_text(encoding="utf-8")
            lines = text.splitlines()
            date_str = f.stem[:10]
            title = lines[0].lstrip("#").strip() if lines else f.stem
            entries.append({
                "date":   date_str,
                "title":  title,
                "github": f"{REPO_URL}/blob/main/03_Evolution_Log/{f.name}",
            })
        except Exception as exc:
            print(f"  ⚠ Could not parse evolution {f.name}: {exc}")

    return entries


# ── CSS (shared) ───────────────────────────────────────────────────────────────

def shared_css() -> str:
    return """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    background: #ffffff;
    color: #1a1a1a;
    line-height: 1.6;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }

/* ── Layout ── */
.container { max-width: 1120px; margin: 0 auto; padding: 0 48px; }

/* ── Nav ── */
.site-nav {
    background: #fff;
    border-bottom: 2px solid #1a1a1a;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
}
.nav-logo {
    font-size: 0.78rem;
    font-weight: 700;
    color: #1a1a1a;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.nav-logo .dot { color: #2ABBA8; }
.nav-links { display: flex; gap: 36px; list-style: none; }
.nav-links a {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #999;
    transition: color 0.15s;
}
.nav-links a:hover { color: #1a1a1a; }

/* ── Hero ── */
.site-hero {
    padding: 0 0 80px;
    border-bottom: 1px solid #e0e0e0;
}
.hero-bar {
    border-top: 2px solid #1a1a1a;
    border-bottom: 1px solid #e0e0e0;
    padding: 10px 0;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 56px;
}
.hero-bar-today {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #2ABBA8;
}
.hero-bar-date {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #bbb;
}
.hero-bar-rule {
    flex: 1;
    height: 1px;
    background: #e8e8e8;
}
.hero-bar-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ccc;
}
.hero-title {
    font-size: clamp(2rem, 5.5vw, 3.8rem);
    font-weight: 800;
    letter-spacing: -0.035em;
    line-height: 1.0;
    color: #1a1a1a;
    max-width: 820px;
    margin-bottom: 28px;
}
.hero-excerpt {
    font-size: 1rem;
    color: #666;
    line-height: 1.8;
    max-width: 540px;
    margin-bottom: 40px;
}
.hero-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* ── Buttons ── */
.btn {
    display: inline-block;
    padding: 11px 24px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    text-decoration: none;
}
.btn:hover { text-decoration: none; }
.btn-dark { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
.btn-dark:hover { background: #2ABBA8; border-color: #2ABBA8; }
.btn-ghost { background: transparent; color: #999; border-color: #d0d0d0; }
.btn-ghost:hover { color: #1a1a1a; border-color: #1a1a1a; }
.btn-teal { background: #2ABBA8; color: #fff; border-color: #2ABBA8; }
.btn-teal:hover { background: #229990; border-color: #229990; }

/* ── Section header ── */
.section-block {
    padding: 72px 0 0;
}
.section-block + .section-block { border-top: 1px solid #e0e0e0; }
.section-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 36px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e0e0e0;
}
.section-num {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #2ABBA8;
    flex-shrink: 0;
}
.section-title {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #1a1a1a;
}
.section-rule {
    flex: 1;
    height: 1px;
    background: #e8e8e8;
}
.section-count {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #ccc;
    flex-shrink: 0;
}

/* ── Tool grid ── */
.tools-block {
    padding-bottom: 80px;
}
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: #e0e0e0;
    border: 1px solid #e0e0e0;
}
.tool-card {
    background: #fff;
    display: flex;
    flex-direction: column;
    padding: 28px 24px 24px;
    text-decoration: none;
    color: inherit;
    transition: background 0.15s;
    position: relative;
}
.tool-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: #2ABBA8;
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.2s ease;
}
.tool-card:hover { background: #f9fffe; }
.tool-card:hover::after { transform: scaleX(1); }
.tc-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
}
.tc-index {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #2ABBA8;
    font-variant-numeric: tabular-nums;
}
.tc-cat {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #ccc;
    text-transform: uppercase;
}
.tc-name {
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.015em;
    color: #1a1a1a;
    margin-bottom: 10px;
    flex: 1;
}
.tc-desc {
    font-size: 0.8rem;
    color: #888;
    line-height: 1.6;
    margin-bottom: 20px;
}
.tc-date {
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #ccc;
    margin-top: auto;
}

/* ── Evolution list ── */
.evo-block { padding-bottom: 80px; }
.evo-list { list-style: none; }
.evo-item {
    display: grid;
    grid-template-columns: 100px 1fr 24px;
    gap: 24px;
    padding: 18px 0;
    border-bottom: 1px solid #ebebeb;
    align-items: baseline;
}
.evo-date {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #2ABBA8;
    font-variant-numeric: tabular-nums;
}
.evo-title { font-size: 0.92rem; color: #444; }
.evo-title a { color: #444; transition: color 0.15s; }
.evo-title a:hover { color: #1a1a1a; }
.evo-arrow { font-size: 0.75rem; color: #ccc; text-align: right; }
.evo-item:hover .evo-arrow { color: #2ABBA8; }

/* ── Footer ── */
.site-footer {
    border-top: 2px solid #1a1a1a;
    padding: 32px 0;
    margin-top: 0;
}
.footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.footer-left { display: flex; flex-direction: column; gap: 6px; }
.footer-tagline {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #1a1a1a;
}
.footer-tagline .tagline-dot { color: #2ABBA8; }
.footer-copy { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: #ccc; }
.footer-links { display: flex; gap: 24px; }
.footer-links a { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: #bbb; transition: color 0.15s; }
.footer-links a:hover { color: #2ABBA8; }

/* ── Tool detail page ── */
.detail-nav-bar {
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    padding: 14px 0;
}
.back-link {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #ccc;
    transition: color 0.15s;
}
.back-link:hover { color: #2ABBA8; }
.detail-hero {
    padding: 64px 0 56px;
    border-bottom: 1px solid #e0e0e0;
}
.detail-eyebrow {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 20px;
}
.detail-hero h1 {
    font-size: clamp(1.8rem, 4vw, 3rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.05;
    color: #1a1a1a;
    max-width: 760px;
    margin-bottom: 16px;
}
.detail-meta {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: #ccc;
}
.detail-section {
    padding: 48px 0;
    border-bottom: 1px solid #e0e0e0;
}
.detail-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #bbb;
    margin-bottom: 16px;
}
.description-text {
    font-size: 1rem;
    line-height: 1.8;
    color: #333;
    max-width: 620px;
    margin-bottom: 28px;
}
.req-list { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; }
.req-list li {
    background: #f5f5f5;
    padding: 4px 14px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #555;
    border: 1px solid #e8e8e8;
}

/* ── Pyodide runner ── */
.runner-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #bbb;
    display: block;
    margin-top: 24px;
    margin-bottom: 8px;
}
.runner-label:first-child { margin-top: 0; }
.try-it textarea {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid #e0e0e0;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.82rem;
    background: #fafafa;
    color: #1a1a1a;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
    line-height: 1.6;
}
.try-it textarea:focus { border-color: #2ABBA8; }
#run-btn {
    display: inline-block;
    background: #1a1a1a;
    color: #fff;
    border: none;
    padding: 11px 28px;
    cursor: pointer;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-top: 12px;
    transition: background 0.15s;
    font-family: inherit;
}
#run-btn:hover { background: #2ABBA8; }
#run-btn:disabled { background: #ccc; cursor: not-allowed; }
#pyodide-status { font-size: 0.78rem; color: #bbb; padding: 12px 0; font-style: italic; }
#output {
    background: #fafafa;
    color: #1a1a1a;
    border: 1px solid #e8e8e8;
    border-left: 3px solid #2ABBA8;
    padding: 20px;
    min-height: 80px;
    white-space: pre-wrap;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    margin-top: 12px;
    line-height: 1.65;
}

/* ── Local run instructions ── */
.local-run-note {
    font-size: 0.88rem;
    color: #666;
    line-height: 1.7;
    margin-bottom: 16px;
}
.local-run-note em { color: #aaa; }
.code-block {
    background: #f7f7f7;
    border: 1px solid #e8e8e8;
    border-left: 3px solid #2ABBA8;
    padding: 18px 20px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.82rem;
    line-height: 1.8;
    color: #333;
}
.code-comment { color: #bbb; }

/* ── Responsive ── */
@media (max-width: 900px) {
    .card-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 580px) {
    .container { padding: 0 24px; }
    .card-grid { grid-template-columns: 1fr; }
    .nav-links { display: none; }
    .footer-inner { flex-direction: column; gap: 16px; align-items: flex-start; }
    .footer-tagline { font-size: 0.88rem; }
    .evo-item { grid-template-columns: 80px 1fr; }
    .evo-arrow { display: none; }
    .hero-title { font-size: 2rem; }
    .hero-bar { flex-wrap: wrap; }
}
"""


# ── HTML helpers ───────────────────────────────────────────────────────────────

def h(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text), quote=True)


def page_shell(title: str, body: str, css_extra: str = "", root_prefix: str = "") -> str:
    """Wrap body in a full HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{h(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
{shared_css()}
{css_extra}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


# ── Index page ─────────────────────────────────────────────────────────────────

def render_hero(diaries: list[dict], tools: list[dict]) -> str:
    if not diaries:
        return ""
    d = diaries[0]

    tool_btn = ""
    for t in tools:
        if t["date"] == d["date"]:
            tool_btn = f'<a class="btn btn-teal" href="tools/{h(t["slug"])}/index.html">Today\'s Tool &rarr;</a>'
            break

    excerpt = f'<p class="hero-excerpt">{h(d["excerpt"])}</p>' if d.get("excerpt") else ""

    return f"""
<section class="site-hero">
  <div class="container">
    <div class="hero-bar">
      <span class="hero-bar-today">Today</span>
      <span class="hero-bar-date">{h(d["date"])}</span>
      <span class="hero-bar-rule"></span>
      <span class="hero-bar-label">Daily Diary</span>
    </div>
    <h1 class="hero-title">{h(d["title"])}</h1>
    {excerpt}
    <div class="hero-actions">
      <a class="btn btn-dark" href="{h(d['github'])}" target="_blank" rel="noopener">Read Diary &rarr;</a>
      {tool_btn}
    </div>
  </div>
</section>"""


def render_tool_grid(tools: list[dict]) -> str:
    if not tools:
        return "<p style='color:#bbb;padding:20px 0;font-size:0.9rem;'>No tools yet.</p>"

    cards = []
    for i, t in enumerate(tools):
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        idx = str(len(tools) - i).zfill(2)
        desc_html = f'<div class="tc-desc">{h(t["description"][:110])}{"…" if len(t["description"]) > 110 else ""}</div>' if t["description"] else ""
        cards.append(f"""<a class="tool-card" href="tools/{h(t['slug'])}/index.html">
  <div class="tc-top">
    <span class="tc-index">{idx}</span>
    <span class="tc-cat">{h(cat_label)}</span>
  </div>
  <div class="tc-name">{h(t['name'])}</div>
  {desc_html}
  <div class="tc-date">{h(t['date'])}</div>
</a>""")

    return f'<div class="card-grid">{"".join(cards)}</div>'


def render_evolution_list(evolutions: list[dict]) -> str:
    if not evolutions:
        return "<p style='color:#bbb;padding:20px 0;font-size:0.9rem;'>No evolution entries yet.</p>"

    items = []
    for e in evolutions:
        items.append(f"""<li class="evo-item">
  <span class="evo-date">{h(e['date'])}</span>
  <span class="evo-title"><a href="{h(e['github'])}" target="_blank" rel="noopener">{h(e['title'])}</a></span>
  <span class="evo-arrow">&rarr;</span>
</li>""")

    return f'<ul class="evo-list">{"".join(items)}</ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    hero_html      = render_hero(diaries, tools)
    tool_grid_html = render_tool_grid(tools)
    evo_list_html  = render_evolution_list(evolutions)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">Super-Lili's Daily Adventure<span class="dot">.</span></div>
      <ul class="nav-links">
        <li><a href="#tools">Tool Archive</a></li>
        <li><a href="#evolution">Evolution Journal</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

{hero_html}

<div class="section-block" id="tools">
  <div class="container">
    <div class="section-header">
      <span class="section-num">01</span>
      <span class="section-title">Tool Archive</span>
      <span class="section-rule"></span>
      <span class="section-count">{len(tools)} tools</span>
    </div>
    <div class="tools-block">
      {tool_grid_html}
    </div>
  </div>
</div>

<div class="section-block" id="evolution">
  <div class="container">
    <div class="section-header">
      <span class="section-num">02</span>
      <span class="section-title">Evolution Journal</span>
      <span class="section-rule"></span>
      <span class="section-count">{len(evolutions)} entries</span>
    </div>
    <div class="evo-block">
      {evo_list_html}
    </div>
  </div>
</div>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left">
        <div class="footer-tagline">One friction point<span class="tagline-dot">.</span> One tool<span class="tagline-dot">.</span> Every day<span class="tagline-dot">.</span></div>
        <span class="footer-copy">Super-Lili's Daily Adventure &copy; 2026</span>
      </div>
      <div class="footer-links">
        <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </div>
</footer>
"""
    return page_shell("Super-Lili's Daily Adventure", body)


# ── Tool detail page ────────────────────────────────────────────────────────────

def read_readme_description(readme_path: Path) -> str:
    """Read the full description block from a README."""
    if not readme_path.exists():
        return ""
    try:
        text = readme_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        collecting = False
        desc_lines: list[str] = []
        for line in lines:
            if line.startswith("## Quick Start") or line.startswith("## Dependencies"):
                break
            if line.startswith("**What it does:**"):
                desc_lines.append(line.replace("**What it does:**", "").strip())
                collecting = True
                continue
            if collecting and line.strip() and not line.startswith("**Born from:**") and not line.startswith("---"):
                desc_lines.append(line.strip())
        return " ".join(desc_lines).strip()
    except Exception:
        return ""


def read_tool_code(t: dict) -> str:
    """Read main.py for a tool, escape it for embedding in a JS template literal."""
    main_py = TOOLBOX / t["category"] / t["dir_name"] / "main.py"
    if not main_py.exists():
        return ""
    try:
        code = main_py.read_text(encoding="utf-8")
        code = code.replace("\\", "\\\\")
        code = code.replace("`", "\\`")
        code = code.replace("${", "\\${")
        return code
    except Exception:
        return ""


def build_local_run_section(t: dict) -> str:
    """Return 'run locally' instructions for tools without browser support."""
    reqs = t.get("requirements", [])
    req_str = " ".join(reqs) if reqs else "see requirements.txt"
    install_cmd = f"pip install {req_str}" if reqs else "pip install -r requirements.txt"
    github_raw = (
        f"https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure"
        f"/main/02_Toolbox/{t['category']}/{t['dir_name']}/main.py"
    )

    return f"""
<p class="local-run-note">这个工具需要在本地运行 — 在你的电脑终端执行以下命令：<br>
<em>This tool runs locally. Open a terminal and run:</em></p>
<div class="code-block" translate="no">
  <div><span class="code-comment"># 1. 安装依赖 Install dependencies</span></div>
  <div>{h(install_cmd)}</div>
  <div>&nbsp;</div>
  <div><span class="code-comment"># 2. 下载工具 Download the tool</span></div>
  <div>curl -O {h(github_raw)}</div>
  <div>&nbsp;</div>
  <div><span class="code-comment"># 3. 运行 Run</span></div>
  <div>python main.py --help</div>
</div>
<a class="btn btn-dark" href="{h(t['github'])}" target="_blank" rel="noopener" style="margin-top:20px;display:inline-block;">查看源码 View Source</a>"""


def build_pyodide_section(t: dict) -> str:
    """Return Pyodide runner HTML+JS, or local-run fallback for tools without USER_INPUT."""
    import json as _json

    tool_code = read_tool_code(t)
    if not tool_code:
        return '<p style="color:#999;font-size:0.85rem;font-style:italic;">Source code not found — cannot load runner.</p>'

    if "USER_INPUT" not in tool_code:
        return build_local_run_section(t)

    preamble = (
        "import sys\n"
        "sys.argv = ['tool']  # browser mode: reset argv so argparse never fires\n"
    )
    full_code = preamble + "\n" + tool_code

    # JSON-encode the code so backticks, ${...}, and any special chars are safe in JS
    code_json = _json.dumps(full_code)

    # Placeholder hint derived from category
    cat = t.get("category", "")
    placeholder_hints = {
        "Education Evolution": "Paste your study notes, article, or learning material here…",
        "Design Alchemy":      "Paste your brief, content, or design description here…",
        "Office Automation":   "Paste your meeting notes, task list, or work text here…",
        "Healing Inventions":  "Paste a few sentences about how you're feeling or what's on your mind…",
    }
    placeholder = placeholder_hints.get(cat, "Paste your text here…")

    return f"""
<div id="pyodide-status">&#x23F3; Loading Python engine&hellip; (first load ~5s)</div>
<div id="pyodide-ui" style="display:none">
  <span class="runner-label">Input</span>
  <textarea id="user-input" rows="6" placeholder="{placeholder}"></textarea>
  <button id="run-btn" onclick="runTool()">&#x25B6;&nbsp; Run</button>
  <span class="runner-label">Output</span>
  <pre id="output"></pre>
</div>

<script src="https://cdn.jsdelivr.net/pyodide/v0.27.0/full/pyodide.js"></script>
<script>
let pyodide = null;
const TOOL_CODE = {code_json};

async function loadPyodide_() {{
  try {{
    pyodide = await loadPyodide();
    // Pre-load any packages the tool imports (pandas, numpy, etc.)
    try {{ await pyodide.loadPackagesFromImports(TOOL_CODE); }} catch(e) {{}}
    document.getElementById('pyodide-status').style.display = 'none';
    document.getElementById('pyodide-ui').style.display = 'block';
  }} catch(e) {{
    document.getElementById('pyodide-status').textContent = '❌ Failed to load Python engine. Please refresh.';
  }}
}}

async function runTool() {{
  if (!pyodide) return;
  const userInput = document.getElementById('user-input').value.trim();
  if (!userInput) {{
    document.getElementById('output').textContent = '⬆ Paste some text above, then click Run.';
    return;
  }}
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Running...';

  try {{
    pyodide.runPython('import sys; from io import StringIO; sys.stdout = StringIO()');
    pyodide.globals.set('USER_INPUT', userInput);
    pyodide.runPython(TOOL_CODE);
    const output = pyodide.runPython('sys.stdout.getvalue()');
    document.getElementById('output').textContent = output.trim() || '(no output — tool may write to a file instead)';
  }} catch(e) {{
    document.getElementById('output').textContent = '❌ Error:\\n' + e.message;
  }}

  btn.disabled = false;
  btn.textContent = '▶ Run';
}}

loadPyodide_();
</script>"""


def build_tool_page(t: dict) -> str:
    description = read_readme_description(t["readme_path"]) or t["description"] or "A tool forged by Super-Lili."
    cat_label   = CATEGORY_LABELS.get(t["category"], t["category"])

    req_items = "".join(f"<li>{h(r)}</li>" for r in t["requirements"]) if t["requirements"] else "<li style='color:#aaa;font-style:italic;list-style:none;'>None — runs entirely in browser</li>"

    tool_code = read_tool_code(t)
    is_browser = bool(tool_code) and "USER_INPUT" in tool_code
    run_label = "Try in Browser" if is_browser else "Run Locally"

    pyodide_section = build_pyodide_section(t)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">Super-Lili's Daily Adventure<span class="dot">.</span></div>
      <ul class="nav-links">
        <li><a href="../../index.html#tools">Tool Archive</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

<div class="detail-nav-bar">
  <div class="container">
    <a class="back-link" href="../../index.html">&larr; Tool Archive</a>
  </div>
</div>

<div class="detail-hero">
  <div class="container">
    <div class="detail-eyebrow">{h(cat_label)}</div>
    <h1>{h(t['name'])}</h1>
    <div class="detail-meta">{h(t['date'])}</div>
  </div>
</div>

<div>
  <div class="container">

    <section class="detail-section">
      <div class="detail-label">What it does</div>
      <p class="description-text">{h(description)}</p>
      <a class="btn btn-dark" href="{h(t['github'])}" target="_blank" rel="noopener">View Source &rarr;</a>
    </section>

    <section class="detail-section">
      <div class="detail-label">Dependencies</div>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      <div class="detail-label">{h(run_label)}</div>
      <div class="try-it">
        {pyodide_section}
      </div>
    </section>

  </div>
</div>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left">
        <div class="footer-tagline">One friction point<span class="tagline-dot">.</span> One tool<span class="tagline-dot">.</span> Every day<span class="tagline-dot">.</span></div>
        <span class="footer-copy">Super-Lili's Daily Adventure &nbsp;·&nbsp; {h(t['date'])}</span>
      </div>
      <div class="footer-links">
        <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </div>
</footer>
"""
    return page_shell(f"{t['name']} · Super-Lili", body)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("🌸 Generating Super-Lili's GitHub Pages site...")

    diaries    = read_diaries()
    tools      = read_tools()
    evolutions = read_evolutions()

    print(f"  📖 {len(diaries)} diary entries")
    print(f"  🛠️  {len(tools)} tools")
    print(f"  📈 {len(evolutions)} evolution entries")

    DOCS_DIR.mkdir(exist_ok=True)

    index_html = build_index(diaries, tools, evolutions)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("  ✓ docs/index.html written")

    tools_dir = DOCS_DIR / "tools"
    tools_dir.mkdir(exist_ok=True)

    for t in tools:
        tool_out = tools_dir / t["slug"]
        tool_out.mkdir(exist_ok=True)
        tool_html = build_tool_page(t)
        (tool_out / "index.html").write_text(tool_html, encoding="utf-8")

    print(f"  ✓ {len(tools)} tool pages written to docs/tools/")
    print(f"\n✨ Site ready at {DOCS_DIR}/index.html")
    print(f"   Live at {SITE_URL}")


if __name__ == "__main__":
    main()
