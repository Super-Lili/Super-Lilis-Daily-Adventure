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
# FO-style bold card colors — top graphic area + bottom band
# Each category: (graphic_bg, graphic_text, band_bg, band_text)
CATEGORY_CARD = {
    "Education Evolution": ("#2ABBA8", "#ffffff", "#e8f8f6", "#1a4a44"),
    "Design Alchemy":      ("#333333", "#ffffff", "#f0f0f0", "#333333"),
    "Office Automation":   ("#F4E842", "#1a1a1a", "#fefce8", "#1a1a1a"),
    "Healing Inventions":  ("#f0c4c4", "#5a1a1a", "#fdf0f0", "#5a1a1a"),
}
CATEGORY_CARD_DEFAULT = ("#cccccc", "#333333", "#f5f5f5", "#333333")


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
                "category_color": "#cccccc",
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
    background: #f5f5f3;
    color: #1a1a1a;
    line-height: 1.5;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }
a:hover { opacity: 0.75; }

/* ── Layout ── */
.container { max-width: 1280px; margin: 0 auto; padding: 0 32px; }

/* ── Top nav ── */
.site-nav {
    background: #ffffff;
    border-bottom: 1px solid #d8d8d8;
    position: sticky;
    top: 0;
    z-index: 100;
}
.site-nav .nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 52px;
}
.nav-logo {
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1a1a1a;
}
.nav-links {
    display: flex;
    gap: 40px;
    list-style: none;
}
.nav-links a {
    font-size: 0.78rem;
    font-weight: 500;
    color: #1a1a1a;
}

/* ── Hero (full-width dark band like FO Journal) ── */
.site-hero {
    background: #2e2e2e;
    padding: 56px 32px 52px;
}
.site-hero .container { padding: 0; }
.hero-title {
    font-size: clamp(3rem, 8vw, 7rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 0.95;
    color: #2ABBA8;
    text-transform: uppercase;
    margin-bottom: 24px;
}
.hero-sub {
    font-size: 0.88rem;
    color: #aaa;
    letter-spacing: 0.04em;
}

/* ── Featured cards: FO-style image+band ── */
.featured-row {
    background: #ffffff;
}
.featured-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border-bottom: 1px solid #d8d8d8;
}
.feat-card {
    display: block;
    color: inherit;
    text-decoration: none;
    border-right: 1px solid #d8d8d8;
}
.feat-card:last-child { border-right: none; }
.feat-card:hover { opacity: 1; }
.feat-card:hover .feat-title { text-decoration: underline; }
.feat-graphic {
    /* "image" area — large typographic placeholder */
    display: flex;
    align-items: flex-end;
    padding: 24px 28px;
    min-height: 280px;
    position: relative;
    overflow: hidden;
}
.feat-graphic-bg {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: clamp(5rem, 14vw, 11rem);
    font-weight: 900;
    letter-spacing: -0.05em;
    text-transform: uppercase;
    line-height: 1;
    opacity: 0.12;
    user-select: none;
    pointer-events: none;
}
.feat-graphic-date {
    position: relative;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.feat-band {
    padding: 20px 28px 24px;
}
.feat-meta {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.feat-title {
    font-size: clamp(1.1rem, 2.2vw, 1.5rem);
    font-weight: 700;
    line-height: 1.25;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
}
.feat-excerpt {
    font-size: 0.84rem;
    line-height: 1.6;
    margin-bottom: 16px;
    opacity: 0.8;
}
.feat-date-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    opacity: 0.65;
}

/* ── Section title: huge all-caps like "RESEARCH UPDATES" ── */
.big-section-title {
    background: #f5f5f3;
    padding: 36px 0 28px;
    border-top: 1px solid #d8d8d8;
    border-bottom: 1px solid #d8d8d8;
}
.big-section-title h2 {
    font-size: clamp(2.2rem, 7vw, 5.5rem);
    font-weight: 900;
    letter-spacing: -0.02em;
    text-transform: uppercase;
    color: #1a1a1a;
    line-height: 1;
}

/* ── Tool card grid (3 → 4 col) ── */
.tool-section { background: #ffffff; padding-bottom: 0; }
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0;
    border-left: 1px solid #d8d8d8;
    border-top: 1px solid #d8d8d8;
}
.tool-card {
    background: #fff;
    display: block;
    color: inherit;
    text-decoration: none;
    border-right: 1px solid #d8d8d8;
    border-bottom: 1px solid #d8d8d8;
    transition: opacity 0.15s;
}
.tool-card:hover { opacity: 1; }
.tool-card:hover .tc-title { text-decoration: underline; }
.tc-graphic {
    min-height: 160px;
    display: flex;
    align-items: flex-end;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
}
.tc-graphic-num {
    position: absolute;
    top: 0; right: 0;
    font-size: 4.5rem;
    font-weight: 900;
    line-height: 1;
    opacity: 0.12;
    letter-spacing: -0.04em;
    user-select: none;
}
.tc-graphic-date {
    position: relative;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.6;
}
.tc-band { padding: 12px 18px 18px; }
.tc-cat {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 6px;
    opacity: 0.6;
}
.tc-title {
    font-size: 0.95rem;
    font-weight: 700;
    line-height: 1.3;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
}
.tc-desc { font-size: 0.78rem; line-height: 1.5; opacity: 0.65; }

/* ── Evolution section ── */
.evo-section {
    background: #f5f5f3;
    padding: 0;
}
.evo-list { list-style: none; }
.evo-item {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 0;
    border-bottom: 1px solid #d8d8d8;
}
.evo-date {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
    padding: 22px 24px 22px 0;
    border-right: 1px solid #d8d8d8;
}
.evo-title {
    font-size: 0.92rem;
    font-weight: 600;
    padding: 22px 0 22px 28px;
}
.evo-title a { color: #1a1a1a; }
.evo-title a:hover { text-decoration: underline; opacity: 1; }

/* ── Buttons ── */
.btn {
    display: inline-block;
    padding: 10px 22px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border: 1.5px solid transparent;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
}
.btn:hover { opacity: 1; text-decoration: none; }
.btn-dark { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
.btn-dark:hover { background: #2ABBA8; border-color: #2ABBA8; }
.btn-ghost { background: transparent; color: #1a1a1a; border-color: #1a1a1a; }
.btn-ghost:hover { background: #1a1a1a; color: #fff; }

/* ── Footer ── */
.site-footer {
    background: #1a1a1a;
    padding: 32px 0;
}
.footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.footer-left {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #888;
}
.footer-right { font-size: 0.72rem; }
.footer-right a { color: #888; letter-spacing: 0.06em; text-transform: uppercase; }
.footer-right a:hover { color: #2ABBA8; opacity: 1; }

/* ── Tool detail ── */
.detail-nav {
    background: #fff;
    border-bottom: 1px solid #d8d8d8;
    padding: 14px 0;
}
.back-link {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #888;
}
.back-link:hover { color: #2ABBA8; opacity: 1; }
.detail-hero {
    background: #2e2e2e;
    padding: 52px 0 48px;
}
.detail-eyebrow {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 14px;
}
.detail-hero h1 {
    font-size: clamp(1.8rem, 4.5vw, 3.5rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.05;
    color: #ffffff;
    text-transform: uppercase;
    margin-bottom: 12px;
    max-width: 800px;
}
.detail-meta {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #666;
}
.detail-body { background: #ffffff; }
.detail-section {
    padding: 44px 0;
    border-bottom: 1px solid #d8d8d8;
}
.detail-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 14px;
}
.description-text {
    font-size: 1rem;
    line-height: 1.75;
    color: #333;
    max-width: 640px;
    margin-bottom: 24px;
}
.req-list { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; }
.req-list li {
    background: #f5f5f3;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #444;
    border: 1px solid #d8d8d8;
}

/* ── Pyodide runner ── */
.runner-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #aaa;
    display: block;
    margin-top: 20px;
    margin-bottom: 8px;
}
.runner-label:first-child { margin-top: 0; }
.try-it textarea {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid #d8d8d8;
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
    padding: 12px 28px;
    cursor: pointer;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 12px;
    transition: background 0.15s;
    font-family: inherit;
}
#run-btn:hover { background: #1a1a1a; }
#run-btn:disabled { background: #ccc; cursor: not-allowed; }
#pyodide-status { font-size: 0.82rem; color: #aaa; padding: 12px 0; font-style: italic; }
#output {
    background: #f5f5f3;
    color: #1a1a1a;
    border: 1px solid #d8d8d8;
    border-top: 3px solid #2ABBA8;
    padding: 20px;
    min-height: 100px;
    white-space: pre-wrap;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    margin-top: 12px;
    line-height: 1.65;
}

/* ── Responsive ── */
@media (max-width: 960px) {
    .card-grid { grid-template-columns: repeat(2, 1fr); }
    .featured-grid { grid-template-columns: 1fr; }
    .feat-card { border-right: none; border-bottom: 1px solid #d8d8d8; }
}
@media (max-width: 600px) {
    .container { padding: 0 16px; }
    .card-grid { grid-template-columns: 1fr; }
    .nav-links { display: none; }
    .footer-inner { flex-direction: column; gap: 10px; align-items: flex-start; }
    .evo-item { grid-template-columns: 1fr; }
    .evo-date { border-right: none; padding: 14px 0 4px; }
    .evo-title { padding: 0 0 14px; }
    .hero-title { font-size: 3rem; }
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

def render_featured_cards(diaries: list[dict], tools: list[dict]) -> str:
    """Two featured cards (latest diary + matching tool), FO-style."""
    if not diaries:
        return ""

    # Card 1: latest diary
    d = diaries[0]
    cat_cards   = CATEGORY_CARD.get("Healing Inventions", CATEGORY_CARD_DEFAULT)
    g_bg, g_fg, b_bg, b_fg = cat_cards
    title_zh = f'<div style="font-size:0.82rem;opacity:0.6;margin-bottom:8px;">{h(d["title_zh"])}</div>' if d.get("title_zh") else ""
    excerpt  = f'<p class="feat-excerpt">{h(d["excerpt"])}</p>' if d.get("excerpt") else ""

    card1 = f"""<a class="feat-card" href="{h(d['github'])}" target="_blank" rel="noopener">
  <div class="feat-graphic" style="background:{g_bg};color:{g_fg};">
    <div class="feat-graphic-bg" aria-hidden="true">DIARY</div>
    <div class="feat-graphic-date">{h(d["date"])}</div>
  </div>
  <div class="feat-band" style="background:{b_bg};color:{b_fg};">
    <div class="feat-meta">Latest Diary Entry</div>
    <div class="feat-title">{h(d["title"])}</div>
    {title_zh}
    {excerpt}
    <div class="feat-date-label">Published {h(d["date"])}</div>
  </div>
</a>"""

    # Card 2: latest tool
    card2 = ""
    for t in tools:
        g_bg2, g_fg2, b_bg2, b_fg2 = CATEGORY_CARD.get(t["category"], CATEGORY_CARD_DEFAULT)
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        desc = f'<p class="feat-excerpt">{h(t["description"][:160])}{"…" if len(t["description"]) > 160 else ""}</p>' if t["description"] else ""
        card2 = f"""<a class="feat-card" href="tools/{h(t['slug'])}/index.html">
  <div class="feat-graphic" style="background:{g_bg2};color:{g_fg2};">
    <div class="feat-graphic-bg" aria-hidden="true">TOOL</div>
    <div class="feat-graphic-date">{h(t['date'])}</div>
  </div>
  <div class="feat-band" style="background:{b_bg2};color:{b_fg2};">
    <div class="feat-meta">{h(cat_label)}</div>
    <div class="feat-title">{h(t['name'])}</div>
    {desc}
    <div class="feat-date-label">Try it in browser</div>
  </div>
</a>"""
        break

    return f"""
<section class="featured-row">
  <div class="featured-grid">
    {card1}
    {card2}
  </div>
</section>"""


def render_tool_grid(tools: list[dict]) -> str:
    if not tools:
        return "<p style='color:#aaa;padding:20px 0;'>No tools yet.</p>"

    cards = []
    for i, t in enumerate(tools):
        g_bg, g_fg, b_bg, b_fg = CATEGORY_CARD.get(t["category"], CATEGORY_CARD_DEFAULT)
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        desc_html = f'<div class="tc-desc">{h(t["description"][:100])}{"…" if len(t["description"]) > 100 else ""}</div>' if t["description"] else ""
        # Show a short day-number in the graphic area
        day_num = t["date"][8:10]  # e.g. "25"
        cards.append(f"""<a class="tool-card" href="tools/{h(t['slug'])}/index.html">
  <div class="tc-graphic" style="background:{g_bg};color:{g_fg};">
    <div class="tc-graphic-num" aria-hidden="true">{day_num}</div>
    <div class="tc-graphic-date">{h(t['date'])}</div>
  </div>
  <div class="tc-band" style="background:{b_bg};color:{b_fg};">
    <div class="tc-cat">{h(cat_label)}</div>
    <div class="tc-title">{h(t['name'])}</div>
    {desc_html}
  </div>
</a>""")

    return f'<div class="card-grid">{"".join(cards)}</div>'


def render_evolution_list(evolutions: list[dict]) -> str:
    if not evolutions:
        return "<p style='color:#aaa;padding:20px 0;'>No evolution entries yet.</p>"

    items = []
    for e in evolutions:
        items.append(f"""<li class="evo-item">
  <div class="evo-date">{h(e['date'])}</div>
  <div class="evo-title"><a href="{h(e['github'])}" target="_blank" rel="noopener">{h(e['title'])}</a></div>
</li>""")

    return f'<ul class="evo-list">{"".join(items)}<li style="border-bottom:none;"></li></ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    featured_html  = render_featured_cards(diaries, tools)
    tool_grid_html = render_tool_grid(tools)
    evo_list_html  = render_evolution_list(evolutions)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">Super-Lili's Daily Adventure</div>
      <ul class="nav-links">
        <li><a href="#tools">Tools</a></li>
        <li><a href="#evolution">Evolution</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

<section class="site-hero">
  <div class="container">
    <h1 class="hero-title">Super-Lili's<br>Daily<br>Adventure</h1>
    <p class="hero-sub">One friction point · One tool · Every day · 每日一工具</p>
  </div>
</section>

{featured_html}

<div class="big-section-title" id="tools">
  <div class="container">
    <h2>Daily Tools &mdash; {len(tools)}</h2>
  </div>
</div>

<section class="tool-section">
  <div class="container" style="padding-top:0;padding-bottom:0;">
    {tool_grid_html}
  </div>
</section>

<div class="big-section-title" id="evolution">
  <div class="container">
    <h2>Evolution Journal</h2>
  </div>
</div>

<section class="evo-section">
  <div class="container" style="padding:0;">
    {evo_list_html}
  </div>
</section>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left">Super-Lili &copy; 2026 &mdash; 由超级莉莉精心策划</div>
      <div class="footer-right"><a href="{h(REPO_URL)}" target="_blank" rel="noopener">View on GitHub</a></div>
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
      <div class="nav-logo">Super-Lili's Daily Adventure</div>
      <ul class="nav-links">
        <li><a href="../../index.html#tools">All Tools</a></li>
        <li><a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

<div class="detail-nav">
  <div class="container">
    <a class="back-link" href="../../index.html">← All Tools</a>
  </div>
</div>

<div class="detail-hero">
  <div class="container">
    <div class="detail-eyebrow">{h(cat_label)}</div>
    <h1>{h(t['name'])}</h1>
    <div class="detail-meta">Published {h(t['date'])}</div>
  </div>
</div>

<div class="detail-body">
  <div class="container">

    <section class="detail-section">
      <div class="detail-label">What it does</div>
      <p class="description-text">{h(description)}</p>
      <a class="btn btn-dark" href="{h(t['github'])}" target="_blank" rel="noopener">View Source Code</a>
    </section>

    <section class="detail-section">
      <div class="detail-label">Dependencies</div>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      <div class="detail-label">Try it in browser</div>
      <div class="try-it">
        {pyodide_section}
      </div>
    </section>

  </div>
</div>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <div class="footer-left">Super-Lili &mdash; Forged on {h(t['date'])}</div>
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
