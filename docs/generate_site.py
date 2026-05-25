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
CATEGORY_DEFAULT_COLOR = "#888888"


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
                "category_color": CATEGORY_DEFAULT_COLOR,
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
    background: #fafafa;
    color: #111111;
    line-height: 1.6;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }
a:hover { color: #2ABBA8; }

/* ── Layout ── */
.container { max-width: 1080px; margin: 0 auto; padding: 0 40px; }

/* ── Header ── */
.site-header {
    background: #111111;
    padding: 0;
    border-bottom: none;
}
.site-header .header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 28px 0;
    border-bottom: 1px solid #222;
}
.site-header .wordmark {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #ffffff;
}
.site-header .wordmark span { color: #2ABBA8; }
.site-header .tagline {
    font-size: 0.75rem;
    color: #666;
    letter-spacing: 0.05em;
}
.hero {
    padding: 80px 0 72px;
    background: #111111;
}
.hero-date {
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 20px;
}
.hero h1 {
    font-size: clamp(2rem, 5vw, 3.6rem);
    font-weight: 700;
    line-height: 1.1;
    color: #ffffff;
    letter-spacing: -0.03em;
    max-width: 720px;
    margin-bottom: 16px;
}
.hero .subtitle {
    font-size: 1rem;
    color: #888;
    max-width: 480px;
    line-height: 1.6;
    margin-bottom: 32px;
}
.hero .hero-links { display: flex; gap: 16px; flex-wrap: wrap; }

/* ── Buttons ── */
.btn {
    display: inline-block;
    padding: 10px 22px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    text-decoration: none;
}
.btn:hover { text-decoration: none; }
.btn-primary { background: #2ABBA8; color: #fff; border-color: #2ABBA8; }
.btn-primary:hover { background: #229990; border-color: #229990; color: #fff; }
.btn-secondary { background: transparent; color: #ffffff; border-color: #444; }
.btn-secondary:hover { border-color: #2ABBA8; color: #2ABBA8; }
.btn-dark { background: transparent; color: #111; border-color: #ccc; }
.btn-dark:hover { border-color: #2ABBA8; color: #2ABBA8; }

/* ── Section layout ── */
.section { padding: 72px 0; border-top: 1px solid #e8e8e8; }
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 36px;
}

/* ── Today's entry (featured) ── */
.featured {
    padding: 72px 0;
    border-top: 1px solid #222;
    background: #111111;
}
.featured .section-label { color: #2ABBA8; }
.featured-grid {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 60px;
    align-items: start;
}
.featured-meta .entry-date {
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 12px;
}
.featured-meta .entry-category {
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 8px;
}
.featured-content h2 {
    font-size: clamp(1.4rem, 3vw, 2rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #ffffff;
    line-height: 1.2;
    margin-bottom: 8px;
}
.featured-content .title-zh {
    font-size: 0.95rem;
    color: #666;
    margin-bottom: 20px;
}
.featured-content .excerpt {
    color: #aaa;
    font-size: 0.95rem;
    line-height: 1.75;
    margin-bottom: 28px;
    max-width: 560px;
}
.featured-content .links { display: flex; gap: 14px; flex-wrap: wrap; }

/* ── Tool list (editorial, not grid) ── */
.tool-list { list-style: none; }
.tool-item {
    border-top: 1px solid #e8e8e8;
    display: grid;
    grid-template-columns: 100px 1fr auto;
    gap: 32px;
    align-items: start;
    padding: 24px 0;
    text-decoration: none;
    color: inherit;
    transition: background 0.1s;
    position: relative;
}
.tool-item::before {
    content: '';
    position: absolute;
    left: -40px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #2ABBA8;
    opacity: 0;
    transition: opacity 0.15s;
}
.tool-item:hover::before { opacity: 1; }
.tool-item:hover { color: inherit; }
.tool-item:hover .tool-item-name { color: #2ABBA8; }
.tool-item-date {
    font-size: 0.75rem;
    color: #999;
    letter-spacing: 0.05em;
    padding-top: 3px;
}
.tool-item-name {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 4px;
    transition: color 0.15s;
    letter-spacing: -0.01em;
}
.tool-item-desc {
    font-size: 0.85rem;
    color: #666;
    line-height: 1.5;
}
.tool-item-cat {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #999;
    padding-top: 3px;
    text-align: right;
    white-space: nowrap;
}

/* ── Evolution list ── */
.evolution-list { list-style: none; }
.evolution-list li {
    padding: 18px 0;
    border-top: 1px solid #e8e8e8;
    display: grid;
    grid-template-columns: 100px 1fr;
    gap: 32px;
    align-items: baseline;
}
.evo-date { font-size: 0.75rem; color: #999; }
.evo-title { font-size: 0.95rem; }
.evo-title a { color: #111; transition: color 0.15s; }
.evo-title a:hover { color: #2ABBA8; }

/* ── Footer ── */
.site-footer {
    background: #111111;
    padding: 40px 0;
    border-top: none;
}
.site-footer .footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.site-footer .footer-copy {
    font-size: 0.75rem;
    color: #555;
    letter-spacing: 0.05em;
}
.site-footer a { color: #555; transition: color 0.15s; }
.site-footer a:hover { color: #2ABBA8; }

/* ── Tool detail page ── */
.tool-detail-header {
    background: #111111;
    padding: 0;
    border-bottom: none;
}
.tool-detail-hero {
    padding: 72px 0 60px;
    background: #111111;
    border-top: 1px solid #222;
}
.back-link {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555;
    display: inline-block;
    margin-bottom: 32px;
    transition: color 0.15s;
}
.back-link:hover { color: #2ABBA8; }
.back-arrow { margin-right: 6px; }
.tool-detail-hero h1 {
    font-size: clamp(1.6rem, 4vw, 2.8rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 16px;
}
.tool-detail-hero .meta {
    display: flex;
    gap: 20px;
    align-items: center;
    flex-wrap: wrap;
}
.tool-detail-hero .meta-date {
    font-size: 0.75rem;
    color: #555;
    letter-spacing: 0.1em;
}
.tool-detail-hero .meta-cat {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #2ABBA8;
}
.detail-section { padding: 48px 0; border-top: 1px solid #e8e8e8; }
.detail-section h2 {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 20px;
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
    background: #f0f0f0;
    padding: 4px 12px;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #333;
    border: 1px solid #ddd;
}

/* ── Pyodide Try-it UI ── */
.try-it { }
.try-it .try-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #999;
    display: block;
    margin-top: 20px;
    margin-bottom: 8px;
}
.try-it textarea {
    width: 100%;
    padding: 14px 16px;
    border: 1px solid #ddd;
    border-radius: 0;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.85rem;
    background: #fafafa;
    color: #111;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
}
.try-it textarea:focus { border-color: #2ABBA8; }
#run-btn {
    background: #2ABBA8;
    color: white;
    border: none;
    padding: 12px 28px;
    cursor: pointer;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 12px;
    transition: background 0.15s;
    font-family: inherit;
}
#run-btn:hover { background: #229990; }
#run-btn:disabled { background: #ccc; cursor: not-allowed; }
#pyodide-status {
    font-size: 0.82rem;
    color: #999;
    padding: 12px 0;
    font-style: italic;
}
#output {
    background: #111111;
    color: #e0e0e0;
    padding: 20px;
    min-height: 100px;
    white-space: pre-wrap;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    margin-top: 12px;
    border-left: 2px solid #2ABBA8;
    line-height: 1.6;
}

/* ── Responsive ── */
@media (max-width: 768px) {
    .container { padding: 0 20px; }
    .featured-grid { grid-template-columns: 1fr; gap: 20px; }
    .tool-item { grid-template-columns: 1fr; gap: 4px; }
    .tool-item-date { font-size: 0.7rem; }
    .tool-item-cat { text-align: left; }
    .tool-item::before { left: -20px; }
    .site-header .header-inner { flex-direction: column; gap: 8px; align-items: flex-start; }
    .site-footer .footer-inner { flex-direction: column; gap: 12px; align-items: flex-start; }
    .evolution-list li { grid-template-columns: 1fr; gap: 4px; }
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

def render_featured(diaries: list[dict], tools: list[dict]) -> str:
    if not diaries:
        return ""

    d = diaries[0]  # most recent

    tool_link = ""
    for t in tools:
        if t["date"] == d["date"]:
            tool_link = f'<a class="btn btn-secondary" href="tools/{h(t["slug"])}/index.html">View Tool</a>'
            break

    title_zh_html = f'<div class="title-zh">{h(d["title_zh"])}</div>' if d["title_zh"] else ""
    excerpt_html  = f'<p class="excerpt">{h(d["excerpt"])}</p>' if d["excerpt"] else ""

    return f"""
<section class="featured">
  <div class="container">
    <div class="section-label">Latest Entry</div>
    <div class="featured-grid">
      <div class="featured-meta">
        <div class="entry-date">{h(d["date"])}</div>
      </div>
      <div class="featured-content">
        <h2>{h(d["title"])}</h2>
        {title_zh_html}
        {excerpt_html}
        <div class="links">
          <a class="btn btn-primary" href="{h(d['github'])}" target="_blank" rel="noopener">Read Diary</a>
          {tool_link}
        </div>
      </div>
    </div>
  </div>
</section>"""


def render_tool_list(tools: list[dict]) -> str:
    if not tools:
        return "<p style='color:#999;font-size:0.9rem;padding:20px 0;'>No tools forged yet.</p>"

    items = []
    for t in tools:
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        desc_html = f'<div class="tool-item-desc">{h(t["description"][:140])}{"..." if len(t["description"]) > 140 else ""}</div>' if t["description"] else ""
        items.append(f"""<a class="tool-item" href="tools/{h(t['slug'])}/index.html">
  <div class="tool-item-date">{h(t['date'])}</div>
  <div>
    <div class="tool-item-name">{h(t['name'])}</div>
    {desc_html}
  </div>
  <div class="tool-item-cat">{h(cat_label)}</div>
</a>""")

    return f'<ul class="tool-list" style="list-style:none;">{"".join(items)}\n<li style="border-top:1px solid #e8e8e8;"></li></ul>'


def render_evolution_list(evolutions: list[dict]) -> str:
    if not evolutions:
        return "<p style='color:#999;font-size:0.9rem;padding:20px 0;'>No evolution entries yet.</p>"

    items = []
    for e in evolutions:
        items.append(f"""
  <li>
    <span class="evo-date">{h(e['date'])}</span>
    <span class="evo-title"><a href="{h(e['github'])}" target="_blank" rel="noopener">{h(e['title'])}</a></span>
  </li>""")

    return f'<ul class="evolution-list">{"".join(items)}\n</ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    featured_html   = render_featured(diaries, tools)
    tool_list_html  = render_tool_list(tools)
    evo_list_html   = render_evolution_list(evolutions)

    body = f"""
<header class="site-header">
  <div class="container">
    <div class="header-inner">
      <div class="wordmark">Super-Lili's <span>Daily Adventure</span></div>
      <div class="tagline">One friction point. One tool. Every day.</div>
    </div>
  </div>
</header>

{featured_html}

<main>
  <div class="container">

    <section class="section">
      <div class="section-label">Tool Archive — {len(tools)} tools</div>
      {tool_list_html}
    </section>

    <section class="section">
      <div class="section-label">Evolution Journal</div>
      {evo_list_html}
    </section>

  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <span class="footer-copy">Super-Lili &copy; 2026 · One friction point. One tool. Every day.</span>
      <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
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
<div class="try-it">
  <div id="pyodide-status">&#x23F3; Loading Python engine&hellip;</div>
  <div id="pyodide-ui" style="display:none">
    <span class="try-label">Input</span>
    <textarea id="user-input" rows="6" placeholder="Paste your text here..."></textarea>
    <button id="run-btn" onclick="runTool()">&#x25B6;&nbsp; Run</button>
    <span class="try-label">Output</span>
    <pre id="output"></pre>
  </div>
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

    req_items = "".join(f"<li>{h(r)}</li>" for r in t["requirements"]) if t["requirements"] else "<li style='font-size:0.8rem;color:#999;list-style:none;padding:4px 0;'>None required — runs in browser</li>"

    pyodide_section = build_pyodide_section(t)

    body = f"""
<header class="tool-detail-header">
  <div class="container">
    <div class="header-inner">
      <div class="wordmark">Super-Lili's <span>Daily Adventure</span></div>
      <div class="tagline">One friction point. One tool. Every day.</div>
    </div>
  </div>
</header>

<div class="tool-detail-hero">
  <div class="container">
    <a class="back-link" href="../../index.html"><span class="back-arrow">←</span> All Tools</a>
    <h1>{h(t['name'])}</h1>
    <div class="meta">
      <span class="meta-cat">{h(cat_label)}</span>
      <span class="meta-date">{h(t['date'])}</span>
    </div>
  </div>
</div>

<main>
  <div class="container">

    <section class="detail-section">
      <h2>What it does</h2>
      <p class="description-text">{h(description)}</p>
      <a class="btn btn-dark" href="{h(t['github'])}" target="_blank" rel="noopener">View Source Code</a>
    </section>

    <section class="detail-section">
      <h2>Dependencies</h2>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      <h2>Try it in browser</h2>
      {pyodide_section}
    </section>

  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <span class="footer-copy">Forged by Super-Lili on {h(t['date'])}</span>
      <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
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
