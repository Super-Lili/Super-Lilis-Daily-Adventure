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
# Muted, editorial cover colors — not saturated badges
CATEGORY_COVER = {
    "Education Evolution": "#d4e8e1",  # sage
    "Design Alchemy":      "#dce0ec",  # slate
    "Office Automation":   "#e8e4d8",  # sand
    "Healing Inventions":  "#ecdde0",  # blush
}
CATEGORY_COVER_TEXT = {
    "Education Evolution": "#2a5a4a",
    "Design Alchemy":      "#2a3a5a",
    "Office Automation":   "#5a4a2a",
    "Healing Inventions":  "#5a2a36",
}
CATEGORY_DEFAULT_COVER      = "#e8e8e8"
CATEGORY_DEFAULT_COVER_TEXT = "#444444"


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
            excerpt = ""
            past_separator = False
            for line in lines:
                if line.strip() == "---":
                    past_separator = True
                    continue
                if past_separator and line.strip() and not line.startswith("**") and not line.startswith("#"):
                    excerpt = line.strip()
                    if len(excerpt) > 20:
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
                # Validate date format loosely
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
                        # Fallback: second non-empty, non-heading line
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

            # Tool slug for URL (date + tool slug)
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
                "category_color": CATEGORY_DEFAULT_COVER,
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
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }
a:hover { color: #2ABBA8; }

/* ── Layout ── */
.container { max-width: 1120px; margin: 0 auto; padding: 0 40px; }

/* ── Top nav ── */
.site-nav {
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    position: sticky;
    top: 0;
    z-index: 100;
}
.site-nav .nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
}
.nav-logo {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #1a1a1a;
}
.nav-logo .dot { color: #2ABBA8; }
.nav-links {
    display: flex;
    gap: 32px;
    list-style: none;
}
.nav-links a {
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    color: #888;
    transition: color 0.15s;
}
.nav-links a:hover { color: #1a1a1a; }

/* ── Hero ── */
.site-hero {
    padding: 80px 0 64px;
    border-bottom: 1px solid #e0e0e0;
    background: #fff;
}
.hero-eyebrow {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 20px;
}
.hero-title {
    font-size: clamp(2.4rem, 6vw, 4.2rem);
    font-weight: 700;
    letter-spacing: -0.04em;
    line-height: 1.05;
    color: #1a1a1a;
    max-width: 760px;
    margin-bottom: 20px;
}
.hero-sub {
    font-size: 1rem;
    color: #777;
    max-width: 480px;
    line-height: 1.65;
}

/* ── Section headers ── */
.section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    border-top: 2px solid #1a1a1a;
    padding-top: 14px;
    margin-bottom: 36px;
    gap: 12px;
}
.section-head-left { display: flex; align-items: baseline; gap: 10px; }
.section-head h2 {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #1a1a1a;
}
.section-head .label-zh {
    font-size: 0.72rem;
    color: #bbb;
    font-weight: 400;
    letter-spacing: 0.02em;
}
.section-head .section-count {
    font-size: 0.72rem;
    color: #ccc;
    letter-spacing: 0.05em;
    margin-left: auto;
}

/* ── Featured latest entry ── */
.featured-row {
    padding: 64px 0;
    border-bottom: 1px solid #e0e0e0;
}
.featured-inner {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
}
.featured-cover {
    aspect-ratio: 4/3;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 28px;
}
.featured-cover .cover-date {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 8px;
    opacity: 0.6;
}
.featured-cover .cover-label {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.featured-body {
    padding: 40px 48px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border-left: 1px solid #e0e0e0;
}
.featured-tag {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 16px;
}
.featured-body h3 {
    font-size: clamp(1.2rem, 2.5vw, 1.7rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.2;
    margin-bottom: 10px;
    color: #1a1a1a;
}
.featured-title-zh {
    font-size: 0.9rem;
    color: #888;
    margin-bottom: 18px;
}
.featured-excerpt {
    font-size: 0.92rem;
    color: #555;
    line-height: 1.7;
    margin-bottom: 28px;
}
.featured-links { display: flex; gap: 12px; flex-wrap: wrap; }

/* ── Buttons ── */
.btn {
    display: inline-block;
    padding: 9px 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.btn:hover { text-decoration: none; }
.btn-primary { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
.btn-primary:hover { background: #2ABBA8; border-color: #2ABBA8; }
.btn-outline { background: transparent; color: #1a1a1a; border-color: #ccc; }
.btn-outline:hover { border-color: #1a1a1a; }
.btn-teal { background: #2ABBA8; color: #fff; border-color: #2ABBA8; }
.btn-teal:hover { background: #229990; border-color: #229990; }

/* ── Tool card grid ── */
.section-block { padding: 56px 0; border-bottom: 1px solid #e0e0e0; }
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: #e0e0e0;
    border: 1px solid #e0e0e0;
}
.tool-card {
    background: #fff;
    display: block;
    color: inherit;
    text-decoration: none;
    transition: background 0.15s;
}
.tool-card:hover { background: #f5f5f5; }
.tool-card:hover .tc-name { color: #2ABBA8; }
.tc-cover {
    aspect-ratio: 16/9;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 16px 20px;
}
.tc-cover-date {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.55;
}
.tc-body { padding: 16px 20px 20px; }
.tc-cat {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 6px;
}
.tc-name {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.3;
    margin-bottom: 6px;
    transition: color 0.15s;
    color: #1a1a1a;
}
.tc-desc {
    font-size: 0.8rem;
    color: #777;
    line-height: 1.5;
}

/* ── Evolution list ── */
.evo-list { list-style: none; }
.evo-item {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 24px;
    padding: 20px 0;
    border-bottom: 1px solid #e8e8e8;
    align-items: baseline;
}
.evo-date { font-size: 0.75rem; color: #2ABBA8; font-weight: 600; font-variant-numeric: tabular-nums; }
.evo-title { font-size: 0.92rem; color: #1a1a1a; }
.evo-title a { transition: color 0.15s; }
.evo-title a:hover { color: #2ABBA8; }

/* ── Footer ── */
.site-footer {
    background: #fff;
    border-top: 2px solid #1a1a1a;
    padding: 40px 0;
}
.footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.footer-left { font-size: 0.72rem; color: #aaa; }
.footer-left strong { color: #1a1a1a; font-weight: 700; }
.footer-right { font-size: 0.72rem; }
.footer-right a { color: #aaa; transition: color 0.15s; letter-spacing: 0.05em; }
.footer-right a:hover { color: #2ABBA8; }

/* ── Tool detail ── */
.detail-nav {
    background: #fff;
    border-bottom: 1px solid #e0e0e0;
    padding: 16px 0;
}
.back-link {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #999;
    transition: color 0.15s;
}
.back-link:hover { color: #2ABBA8; }
.detail-hero {
    padding: 56px 0 52px;
    border-bottom: 1px solid #e0e0e0;
}
.detail-eyebrow {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 16px;
}
.detail-hero h1 {
    font-size: clamp(1.8rem, 4vw, 3rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.1;
    color: #1a1a1a;
    margin-bottom: 12px;
    max-width: 700px;
}
.detail-meta {
    font-size: 0.75rem;
    color: #aaa;
    margin-top: 8px;
}
.detail-section { padding: 48px 0; border-bottom: 1px solid #e0e0e0; }
.detail-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 16px;
}
.description-text {
    font-size: 1rem;
    line-height: 1.75;
    color: #333;
    max-width: 640px;
    margin-bottom: 28px;
}
.req-list { list-style: none; display: flex; flex-wrap: wrap; gap: 8px; }
.req-list li {
    background: #f5f5f5;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #444;
    border: 1px solid #e8e8e8;
}

/* ── Pyodide runner ── */
.runner-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #aaa;
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
    font-size: 0.84rem;
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
    background: #2ABBA8;
    color: #fff;
    border: none;
    padding: 11px 28px;
    cursor: pointer;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 12px;
    transition: background 0.15s;
    font-family: inherit;
}
#run-btn:hover { background: #229990; }
#run-btn:disabled { background: #ccc; cursor: not-allowed; }
#pyodide-status {
    font-size: 0.82rem;
    color: #aaa;
    padding: 12px 0;
    font-style: italic;
}
#output {
    background: #f8f8f8;
    color: #1a1a1a;
    border: 1px solid #e0e0e0;
    border-left: 3px solid #2ABBA8;
    padding: 20px;
    min-height: 100px;
    white-space: pre-wrap;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    margin-top: 12px;
    line-height: 1.65;
}

/* ── Responsive ── */
@media (max-width: 900px) {
    .card-grid { grid-template-columns: repeat(2, 1fr); }
    .featured-inner { grid-template-columns: 1fr; }
    .featured-body { border-left: none; border-top: 1px solid #e0e0e0; padding: 28px 0 0; }
}
@media (max-width: 600px) {
    .container { padding: 0 20px; }
    .card-grid { grid-template-columns: 1fr; }
    .nav-links { display: none; }
    .evo-item { grid-template-columns: 1fr; gap: 4px; }
    .footer-inner { flex-direction: column; gap: 12px; align-items: flex-start; }
    .hero-title { font-size: 2rem; }
    .section-head { flex-direction: column; gap: 4px; }
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
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
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

def render_featured_row(diaries: list[dict], tools: list[dict]) -> str:
    if not diaries:
        return ""
    d = diaries[0]

    tool_link = ""
    for t in tools:
        if t["date"] == d["date"]:
            tool_link = f'<a class="btn btn-outline" href="tools/{h(t["slug"])}/index.html">今日工具 →</a>'
            break

    cover_bg   = CATEGORY_COVER.get("Education Evolution", "#e8e8e8")
    cover_text = CATEGORY_COVER_TEXT.get("Education Evolution", "#333")

    title_zh_html = f'<div class="featured-title-zh">{h(d["title_zh"])}</div>' if d["title_zh"] else ""
    excerpt_html  = f'<p class="featured-excerpt">{h(d["excerpt"])}</p>' if d["excerpt"] else ""

    return f"""
<section class="featured-row">
  <div class="container">
    <div class="section-head">
      <div class="section-head-left">
        <h2>Latest Entry</h2>
        <span class="label-zh">今日日记</span>
      </div>
      <span class="section-count">{h(d["date"])}</span>
    </div>
    <div class="featured-inner">
      <div class="featured-cover" style="background:{cover_bg};color:{cover_text};">
        <div class="cover-date">{h(d["date"])}</div>
        <div class="cover-label">今日日记<br><span style="font-size:0.7em;font-weight:400;opacity:0.6;">Daily Diary</span></div>
      </div>
      <div class="featured-body">
        <div class="featured-tag">今日日记 · Latest Entry</div>
        <h3>{h(d["title"])}</h3>
        {title_zh_html}
        {excerpt_html}
        <div class="featured-links">
          <a class="btn btn-primary" href="{h(d['github'])}" target="_blank" rel="noopener">读日记 Read Diary</a>
          {tool_link}
        </div>
      </div>
    </div>
  </div>
</section>"""


def render_tool_grid(tools: list[dict]) -> str:
    if not tools:
        return "<p style='color:#aaa;font-size:0.9rem;padding:20px 0;'>No tools forged yet.</p>"

    cards = []
    for t in tools:
        cat_label  = CATEGORY_LABELS.get(t["category"], t["category"])
        cover_bg   = CATEGORY_COVER.get(t["category"], CATEGORY_DEFAULT_COVER)
        cover_text = CATEGORY_COVER_TEXT.get(t["category"], CATEGORY_DEFAULT_COVER_TEXT)
        desc_html  = f'<div class="tc-desc">{h(t["description"][:110])}{"…" if len(t["description"]) > 110 else ""}</div>' if t["description"] else ""
        cards.append(f"""<a class="tool-card" href="tools/{h(t['slug'])}/index.html">
  <div class="tc-cover" style="background:{cover_bg};color:{cover_text};">
    <div class="tc-cover-date">{h(t['date'])}</div>
  </div>
  <div class="tc-body">
    <div class="tc-cat">{h(cat_label)}</div>
    <div class="tc-name">{h(t['name'])}</div>
    {desc_html}
  </div>
</a>""")

    return f'<div class="card-grid">{"".join(cards)}</div>'


def render_evolution_list(evolutions: list[dict]) -> str:
    if not evolutions:
        return "<p style='color:#aaa;font-size:0.9rem;padding:20px 0;'>No evolution entries yet.</p>"

    items = []
    for e in evolutions:
        items.append(f"""<li class="evo-item">
  <span class="evo-date">{h(e['date'])}</span>
  <span class="evo-title"><a href="{h(e['github'])}" target="_blank" rel="noopener">{h(e['title'])}</a></span>
</li>""")

    return f'<ul class="evo-list">{"".join(items)}</ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    featured_html = render_featured_row(diaries, tools)
    tool_grid_html = render_tool_grid(tools)
    evo_list_html  = render_evolution_list(evolutions)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">Super-Lili<span class="dot">.</span></div>
      <ul class="nav-links">
        <li><a href="#tools">工具库</a></li>
        <li><a href="#evolution">成长日志</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

<section class="site-hero">
  <div class="container">
    <div class="hero-eyebrow">超级莉莉 · Daily Adventure</div>
    <h1 class="hero-title">One friction point.<br>One tool.<br>Every day.</h1>
    <p class="hero-sub">超级莉莉每天在社区发现真实的人类痛点，并为每个痛点构建一个小而可用的工具。</p>
  </div>
</section>

{featured_html}

<section class="section-block" id="tools">
  <div class="container">
    <div class="section-head">
      <div class="section-head-left">
        <h2>Tool Archive</h2>
        <span class="label-zh">工具库</span>
      </div>
      <span class="section-count">{len(tools)} 个工具</span>
    </div>
    {tool_grid_html}
  </div>
</section>

<section class="section-block" id="evolution">
  <div class="container">
    <div class="section-head">
      <div class="section-head-left">
        <h2>Evolution Journal</h2>
        <span class="label-zh">成长日志</span>
      </div>
      <span class="section-count">{len(evolutions)} 篇</span>
    </div>
    {evo_list_html}
  </div>
</section>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left"><strong>Super-Lili</strong> &copy; 2026 &nbsp;·&nbsp; 由超级莉莉精心策划</div>
      <div class="footer-right"><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></div>
    </div>
  </div>
</footer>
"""
    return page_shell("Super-Lili's Daily Adventure · 超级莉莉每日冒险", body)


# ── Tool detail page ────────────────────────────────────────────────────────────

def read_readme_description(readme_path: Path) -> str:
    """Read the full description block from a README."""
    if not readme_path.exists():
        return ""
    try:
        text = readme_path.read_text(encoding="utf-8")
        # Return everything between the intro and the Quick Start section
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
        # Escape for JS template literal: backslashes first, then backticks, then ${
        code = code.replace("\\", "\\\\")
        code = code.replace("`", "\\`")
        code = code.replace("${", "\\${")
        return code
    except Exception:
        return ""


def build_pyodide_section(t: dict) -> str:
    """Return HTML+JS for the Pyodide Try-it section."""
    tool_code = read_tool_code(t)
    if not tool_code:
        return '<p style="color:#999;font-size:0.85rem;font-style:italic;">Source code not found — cannot load runner.</p>'

    # Browser preamble injected before tool code
    preamble = (
        "# Browser adaptation - USER_INPUT is provided by the browser\\n"
        "import sys\\n"
        "sys.argv = ['tool']  # Reset argv to prevent argparse errors\\n"
    )

    return f"""
<div id="pyodide-status">&#x23F3; Loading Python engine&hellip;</div>
<div id="pyodide-ui" style="display:none">
  <span class="runner-label">Input</span>
  <textarea id="user-input" rows="6" placeholder="Paste your text here..."></textarea>
  <button id="run-btn" onclick="runTool()">&#x25B6;&nbsp; Run</button>
  <span class="runner-label">Output</span>
  <pre id="output"></pre>
</div>

<script src="https://cdn.jsdelivr.net/pyodide/v0.27.0/full/pyodide.js"></script>
<script>
let pyodide = null;

const TOOL_CODE = `{preamble}
{tool_code}`;

async function loadPyodide_() {{
  try {{
    pyodide = await loadPyodide();
    document.getElementById('pyodide-status').style.display = 'none';
    document.getElementById('pyodide-ui').style.display = 'block';
  }} catch(e) {{
    document.getElementById('pyodide-status').textContent = '❌ Failed to load Python engine. Please refresh.';
  }}
}}

async function runTool() {{
  if (!pyodide) return;
  const userInput = document.getElementById('user-input').value;
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Running...';

  try {{
    // Redirect stdout
    pyodide.runPython(`
import sys
from io import StringIO
sys.stdout = StringIO()
`);

    // Inject user input and run tool
    pyodide.globals.set('USER_INPUT', userInput);
    pyodide.runPython(TOOL_CODE);

    const output = pyodide.runPython('sys.stdout.getvalue()');
    document.getElementById('output').textContent = output || '(no output)';
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

    pyodide_section = build_pyodide_section(t)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">Super-Lili<span class="dot">.</span></div>
      <ul class="nav-links">
        <li><a href="../../index.html#tools">工具库</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

<div class="detail-nav">
  <div class="container">
    <a class="back-link" href="../../index.html">← 返回工具库</a>
  </div>
</div>

<div class="detail-hero">
  <div class="container">
    <div class="detail-eyebrow">{h(cat_label)}</div>
    <h1>{h(t['name'])}</h1>
    <div class="detail-meta">{h(t['date'])}</div>
  </div>
</div>

<main>
  <div class="container">

    <section class="detail-section">
      <div class="detail-label">What it does · 工具说明</div>
      <p class="description-text">{h(description)}</p>
      <a class="btn btn-primary" href="{h(t['github'])}" target="_blank" rel="noopener">查看源码 View Code</a>
    </section>

    <section class="detail-section">
      <div class="detail-label">Dependencies · 依赖库</div>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      <div class="detail-label">Try it in browser · 在线运行</div>
      <div class="try-it">
        {pyodide_section}
      </div>
    </section>

  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left"><strong>Super-Lili</strong> &nbsp;·&nbsp; 由超级莉莉精心策划 &nbsp;·&nbsp; {h(t['date'])}</div>
      <div class="footer-right"><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></div>
    </div>
  </div>
</footer>
"""
    return page_shell(f"{t['name']} — Super-Lili", body)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("🌸 Generating Super-Lili's GitHub Pages site...")

    # Read all content
    diaries    = read_diaries()
    tools      = read_tools()
    evolutions = read_evolutions()

    print(f"  📖 {len(diaries)} diary entries")
    print(f"  🛠️  {len(tools)} tools")
    print(f"  📈 {len(evolutions)} evolution entries")

    # Ensure docs/ exists
    DOCS_DIR.mkdir(exist_ok=True)

    # Build index.html
    index_html = build_index(diaries, tools, evolutions)
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("  ✓ docs/index.html written")

    # Build tool pages
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
