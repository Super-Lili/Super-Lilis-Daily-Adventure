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
    "Education Evolution": "教育 Education",
    "Design Alchemy":      "设计 Design",
    "Office Automation":   "效率 Office",
    "Healing Inventions":  "疗愈 Healing",
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
    background: #ffffff;
    color: #1a1a1a;
    line-height: 1.6;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }

/* ── Layout ── */
.container { max-width: 1080px; margin: 0 auto; padding: 0 40px; }

/* ── Nav ── */
.site-nav {
    background: #fff;
    border-bottom: 1px solid #ebebeb;
    position: sticky;
    top: 0;
    z-index: 100;
}
.nav-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 52px;
}
.nav-logo {
    font-size: 0.82rem;
    font-weight: 600;
    color: #1a1a1a;
    letter-spacing: 0.01em;
}
.nav-logo .dot { color: #2ABBA8; }
.nav-links { display: flex; gap: 32px; list-style: none; }
.nav-links a {
    font-size: 0.78rem;
    color: #999;
    transition: color 0.15s;
}
.nav-links a:hover { color: #1a1a1a; }

/* ── Hero: today's diary, reads like a letter opener ── */
.site-hero {
    padding: 72px 0 64px;
    border-bottom: 1px solid #ebebeb;
}
.hero-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 20px;
}
.hero-title {
    font-size: clamp(1.8rem, 4.5vw, 3rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.15;
    color: #1a1a1a;
    max-width: 680px;
    margin-bottom: 16px;
}
.hero-title-zh {
    font-size: 0.95rem;
    color: #aaa;
    margin-bottom: 20px;
    font-weight: 400;
}
.hero-excerpt {
    font-size: 1rem;
    color: #555;
    line-height: 1.75;
    max-width: 560px;
    margin-bottom: 32px;
}
.hero-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* ── Buttons ── */
.btn {
    display: inline-block;
    padding: 10px 22px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    border: 1px solid transparent;
    cursor: pointer;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
    text-decoration: none;
}
.btn:hover { text-decoration: none; }
.btn-dark { background: #1a1a1a; color: #fff; border-color: #1a1a1a; }
.btn-dark:hover { background: #2ABBA8; border-color: #2ABBA8; }
.btn-ghost { background: transparent; color: #888; border-color: #d8d8d8; }
.btn-ghost:hover { color: #1a1a1a; border-color: #1a1a1a; }
.btn-teal { background: #2ABBA8; color: #fff; border-color: #2ABBA8; }
.btn-teal:hover { background: #229990; border-color: #229990; }

/* ── Section label ── */
.section-label {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 28px;
}
.section-label h2 {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #1a1a1a;
}
.section-label .label-zh {
    font-size: 0.72rem;
    color: #bbb;
    font-weight: 400;
}
.section-label .label-count {
    font-size: 0.72rem;
    color: #ccc;
    margin-left: auto;
}

/* ── Tool grid ── */
.tools-section {
    padding: 56px 0;
    border-bottom: 1px solid #ebebeb;
}
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: #ebebeb;
    border: 1px solid #ebebeb;
}
.tool-card {
    background: #fff;
    display: flex;
    flex-direction: column;
    padding: 24px;
    text-decoration: none;
    color: inherit;
    border-left: 3px solid transparent;
    transition: border-color 0.15s, background 0.15s;
}
.tool-card:hover {
    border-left-color: #2ABBA8;
    background: #fafffe;
}
.tc-date {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: #2ABBA8;
    margin-bottom: 10px;
}
.tc-name {
    font-size: 0.98rem;
    font-weight: 700;
    line-height: 1.35;
    letter-spacing: -0.01em;
    color: #1a1a1a;
    margin-bottom: 8px;
    flex: 1;
}
.tc-desc {
    font-size: 0.8rem;
    color: #888;
    line-height: 1.55;
    margin-bottom: 14px;
}
.tc-cat {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    color: #ccc;
    text-transform: uppercase;
    margin-top: auto;
}

/* ── Evolution list ── */
.evo-section { padding: 56px 0; }
.evo-list { list-style: none; }
.evo-item {
    display: flex;
    gap: 24px;
    padding: 16px 0;
    border-bottom: 1px solid #ebebeb;
    align-items: baseline;
}
.evo-date {
    font-size: 0.72rem;
    color: #2ABBA8;
    font-weight: 600;
    letter-spacing: 0.05em;
    flex-shrink: 0;
    min-width: 90px;
}
.evo-title { font-size: 0.92rem; color: #444; }
.evo-title a { color: #444; transition: color 0.15s; }
.evo-title a:hover { color: #1a1a1a; }

/* ── Footer ── */
.site-footer {
    background: #fafafa;
    border-top: 1px solid #ebebeb;
    padding: 36px 0;
}
.footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.footer-copy { font-size: 0.75rem; color: #bbb; }
.footer-copy strong { color: #888; font-weight: 600; }
.footer-links { display: flex; gap: 20px; }
.footer-links a { font-size: 0.75rem; color: #bbb; transition: color 0.15s; }
.footer-links a:hover { color: #2ABBA8; }

/* ── Tool detail page ── */
.detail-nav-bar {
    background: #fff;
    border-bottom: 1px solid #ebebeb;
    padding: 14px 0;
}
.back-link {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #bbb;
    transition: color 0.15s;
}
.back-link:hover { color: #2ABBA8; }
.detail-hero {
    padding: 60px 0 52px;
    border-bottom: 1px solid #ebebeb;
}
.detail-eyebrow {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #2ABBA8;
    margin-bottom: 16px;
}
.detail-hero h1 {
    font-size: clamp(1.8rem, 4vw, 2.8rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.1;
    color: #1a1a1a;
    max-width: 720px;
    margin-bottom: 12px;
}
.detail-meta {
    font-size: 0.72rem;
    color: #bbb;
    letter-spacing: 0.05em;
}
.detail-section {
    padding: 44px 0;
    border-bottom: 1px solid #ebebeb;
}
.detail-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #bbb;
    margin-bottom: 14px;
}
.description-text {
    font-size: 1rem;
    line-height: 1.8;
    color: #333;
    max-width: 620px;
    margin-bottom: 24px;
}
.req-list { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; }
.req-list li {
    background: #f5f5f5;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #555;
    border: 1px solid #e8e8e8;
}

/* ── Pyodide runner ── */
.runner-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.16em;
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
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 12px;
    transition: background 0.15s;
    font-family: inherit;
}
#run-btn:hover { background: #1a1a1a; }
#run-btn:disabled { background: #ccc; cursor: not-allowed; }
#pyodide-status { font-size: 0.82rem; color: #bbb; padding: 12px 0; font-style: italic; }
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

/* ── Responsive ── */
@media (max-width: 860px) {
    .card-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
    .container { padding: 0 20px; }
    .card-grid { grid-template-columns: 1fr; }
    .nav-links { display: none; }
    .footer-inner { flex-direction: column; gap: 10px; align-items: flex-start; }
    .evo-item { flex-direction: column; gap: 4px; }
    .hero-title { font-size: 1.8rem; }
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

def render_hero(diaries: list[dict], tools: list[dict]) -> str:
    if not diaries:
        return ""
    d = diaries[0]

    tool_btn = ""
    for t in tools:
        if t["date"] == d["date"]:
            tool_btn = f'<a class="btn btn-ghost" href="tools/{h(t["slug"])}/index.html">今日工具 →</a>'
            break

    title_zh = f'<div class="hero-title-zh">{h(d["title_zh"])}</div>' if d.get("title_zh") else ""
    excerpt  = f'<p class="hero-excerpt">{h(d["excerpt"])}</p>' if d.get("excerpt") else ""

    return f"""
<section class="site-hero">
  <div class="container">
    <div class="hero-label">{h(d["date"])} &nbsp;·&nbsp; 今日日记</div>
    <h1 class="hero-title">{h(d["title"])}</h1>
    {title_zh}
    {excerpt}
    <div class="hero-actions">
      <a class="btn btn-dark" href="{h(d['github'])}" target="_blank" rel="noopener">读日记 Read Diary</a>
      {tool_btn}
    </div>
  </div>
</section>"""


def render_tool_grid(tools: list[dict]) -> str:
    if not tools:
        return "<p style='color:#bbb;padding:20px 0;font-size:0.9rem;'>No tools yet.</p>"

    cards = []
    for t in tools:
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        desc_html = f'<div class="tc-desc">{h(t["description"][:120])}{"…" if len(t["description"]) > 120 else ""}</div>' if t["description"] else ""
        cards.append(f"""<a class="tool-card" href="tools/{h(t['slug'])}/index.html">
  <div class="tc-date">{h(t['date'])}</div>
  <div class="tc-name">{h(t['name'])}</div>
  {desc_html}
  <div class="tc-cat">{h(cat_label)}</div>
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
</li>""")

    return f'<ul class="evo-list">{"".join(items)}</ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    hero_html     = render_hero(diaries, tools)
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

{hero_html}

<section class="tools-section" id="tools">
  <div class="container">
    <div class="section-label">
      <h2>Tool Archive</h2>
      <span class="label-zh">工具库</span>
      <span class="label-count">{len(tools)} tools</span>
    </div>
    {tool_grid_html}
  </div>
</section>

<section class="evo-section" id="evolution">
  <div class="container">
    <div class="section-label">
      <h2>Evolution Journal</h2>
      <span class="label-zh">成长日志</span>
    </div>
    {evo_list_html}
  </div>
</section>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <span class="footer-copy"><strong>Super-Lili</strong> &copy; 2026 &nbsp;·&nbsp; 由超级莉莉精心策划</span>
      <div class="footer-links">
        <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </div>
</footer>
"""
    return page_shell("Super-Lili · Daily Adventure", body)


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

<div class="detail-nav-bar">
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

<div>
  <div class="container">

    <section class="detail-section">
      <div class="detail-label">What it does · 工具说明</div>
      <p class="description-text">{h(description)}</p>
      <a class="btn btn-dark" href="{h(t['github'])}" target="_blank" rel="noopener">View Source Code</a>
    </section>

    <section class="detail-section">
      <div class="detail-label">Dependencies · 依赖</div>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      <div class="detail-label">Try it in browser · 浏览器运行</div>
      <div class="try-it">
        {pyodide_section}
      </div>
    </section>

  </div>
</div>

<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <span class="footer-copy"><strong>Super-Lili</strong> &nbsp;·&nbsp; {h(t['date'])}</span>
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
