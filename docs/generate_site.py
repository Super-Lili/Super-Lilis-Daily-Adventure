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

CATEGORY_COLORS = {
    "Education Evolution": "#2ABBA8",
    "Design Alchemy":      "#2B5EA7",
    "Office Automation":   "#5BC5F0",
    "Healing Inventions":  "#E87BB0",
}
CATEGORY_DEFAULT_COLOR = "#4a6a8a"


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
                "category_color": CATEGORY_COLORS.get(category, CATEGORY_DEFAULT_COLOR),
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
    font-family: 'Georgia', 'Times New Roman', serif;
    background: #EBF7FD;
    color: #1a2a3a;
    line-height: 1.7;
    font-size: 16px;
}

a { color: #2B5EA7; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Layout ── */
.container { max-width: 960px; margin: 0 auto; padding: 0 24px; }

/* ── Header ── */
.site-header {
    background: linear-gradient(135deg, #2B5EA7 0%, #2ABBA8 100%);
    padding: 48px 0 40px;
    text-align: center;
    border-bottom: 1px solid #C8E8F5;
}
.site-header h1 {
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    font-weight: normal;
    letter-spacing: -0.5px;
    color: #ffffff;
}
.site-header .tagline {
    margin-top: 8px;
    color: #C8E8F5;
    font-style: italic;
    font-size: 1.05rem;
}

/* ── Section headings ── */
.section { padding: 48px 0; }
.section + .section { border-top: 1px solid #C8E8F5; }
.section-title {
    font-size: 1.4rem;
    font-weight: normal;
    color: #2B5EA7;
    margin-bottom: 28px;
    letter-spacing: 0.3px;
}

/* ── Today's Entry ── */
.today-card {
    background: #FFFFFF;
    border: 1px solid #C8E8F5;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 2px 12px rgba(43,94,167,0.08);
}
.today-card .entry-date {
    font-size: 0.85rem;
    color: #4a6a8a;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.today-card h2 { font-size: 1.5rem; font-weight: normal; margin-bottom: 4px; color: #1a2a3a; }
.today-card .title-zh { color: #2ABBA8; font-size: 1rem; margin-bottom: 10px; }
.today-card .mood {
    font-style: italic;
    color: #4a6a8a;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px dashed #C8E8F5;
}
.today-card .excerpt { color: #1a2a3a; line-height: 1.75; margin-bottom: 20px; }
.today-card .links { display: flex; gap: 12px; flex-wrap: wrap; }
.btn {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 20px;
    font-size: 0.9rem;
    transition: opacity 0.15s;
}
.btn:hover { opacity: 0.8; text-decoration: none; }
.btn-primary { background: #2B5EA7; color: #fff; }
.btn-secondary { background: #EBF7FD; color: #2B5EA7; border: 1px solid #C8E8F5; }

/* ── Tool Grid ── */
.tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
}
.tool-card {
    background: #FFFFFF;
    border: 1px solid #C8E8F5;
    border-radius: 10px;
    padding: 20px 22px;
    cursor: pointer;
    transition: box-shadow 0.2s, transform 0.15s;
    text-decoration: none;
    display: block;
    color: inherit;
}
.tool-card:hover {
    box-shadow: 0 4px 20px rgba(43,94,167,0.14);
    transform: translateY(-2px);
    text-decoration: none;
}
.tool-card .card-date {
    font-size: 0.78rem;
    color: #4a6a8a;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tool-card h3 {
    font-size: 1rem;
    font-weight: bold;
    margin-bottom: 8px;
    line-height: 1.4;
    color: #1a2a3a;
}
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 0.75rem;
    margin-bottom: 10px;
    font-style: normal;
    color: #fff;
}
.tool-card p { font-size: 0.88rem; color: #4a6a8a; line-height: 1.55; }

/* ── Evolution list ── */
.evolution-list { list-style: none; }
.evolution-list li {
    padding: 14px 0;
    border-bottom: 1px dashed #C8E8F5;
    display: flex;
    gap: 16px;
    align-items: baseline;
}
.evolution-list li:last-child { border-bottom: none; }
.evo-date { font-size: 0.82rem; color: #4a6a8a; min-width: 90px; }
.evo-title { font-size: 0.95rem; }

/* ── Footer ── */
.site-footer {
    text-align: center;
    padding: 36px 0;
    border-top: 1px solid #C8E8F5;
    color: #4a6a8a;
    font-size: 0.88rem;
}
.site-footer a { color: #2B5EA7; }

/* ── Tool detail page ── */
.tool-detail-header {
    background: linear-gradient(135deg, #2B5EA7 0%, #2ABBA8 100%);
    padding: 40px 0 32px;
    border-bottom: 1px solid #C8E8F5;
}
.back-link {
    font-size: 0.9rem;
    color: #C8E8F5;
    display: inline-block;
    margin-bottom: 20px;
}
.back-link:hover { color: #fff; }
.tool-detail-header h1 { font-size: clamp(1.4rem, 4vw, 2.2rem); font-weight: normal; color: #fff; }
.tool-detail-header .meta {
    margin-top: 10px;
    color: #C8E8F5;
    font-size: 0.9rem;
}
.detail-section { padding: 36px 0; }
.detail-section + .detail-section { border-top: 1px solid #C8E8F5; }
.detail-section h2 {
    font-size: 1.1rem;
    font-weight: bold;
    margin-bottom: 14px;
    color: #2B5EA7;
}
.description-text {
    font-size: 1rem;
    line-height: 1.75;
    color: #1a2a3a;
    max-width: 680px;
}
.req-list { list-style: none; display: flex; flex-wrap: wrap; gap: 8px; }
.req-list li {
    background: #EBF7FD;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 0.85rem;
    font-family: 'Courier New', monospace;
    color: #2B5EA7;
    border: 1px solid #C8E8F5;
}

/* ── Pyodide Try-it UI ── */
.try-it { margin: 2rem 0; }
.try-it label {
    display: block;
    font-weight: bold;
    color: #2B5EA7;
    margin-top: 1rem;
    margin-bottom: 0.25rem;
}
.try-it textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #C8E8F5;
    border-radius: 8px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    margin: 0.5rem 0;
    box-sizing: border-box;
    background: #fff;
    color: #1a2a3a;
}
#run-btn {
    background: #2ABBA8;
    color: white;
    border: none;
    padding: 0.6rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    margin: 0.5rem 0;
}
#run-btn:hover { background: #229990; }
#run-btn:disabled { background: #aaa; cursor: not-allowed; }
#pyodide-status { color: #4a6a8a; font-style: italic; padding: 1rem 0; }
#output {
    background: #1a2a3a;
    color: #e8f5fd;
    padding: 1rem;
    border-radius: 8px;
    min-height: 80px;
    white-space: pre-wrap;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

/* ── Responsive ── */
@media (max-width: 600px) {
    .today-card { padding: 20px; }
    .tool-grid { grid-template-columns: 1fr; }
    .evolution-list li { flex-direction: column; gap: 4px; }
    .evo-date { min-width: unset; }
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

def render_today_card(diaries: list[dict], tools: list[dict]) -> str:
    if not diaries:
        return "<p>No diary entries found yet.</p>"

    d = diaries[0]  # most recent

    # Find matching tool for this date
    tool_link = ""
    for t in tools:
        if t["date"] == d["date"]:
            tool_link = f'<a class="btn btn-secondary" href="tools/{h(t["slug"])}/index.html">🛠️ View Tool</a>'
            break

    title_zh_html = f'<div class="title-zh">{h(d["title_zh"])}</div>' if d["title_zh"] else ""
    mood_html     = f'<div class="mood">{h(d["mood"])}</div>' if d["mood"] else ""

    return f"""
<div class="today-card">
  <div class="entry-date">{h(d["date"])}</div>
  <h2>{h(d["title"])}</h2>
  {title_zh_html}
  {mood_html}
  <div class="excerpt">{h(d["excerpt"])}</div>
  <div class="links">
    <a class="btn btn-primary" href="{h(d['github'])}" target="_blank" rel="noopener">📖 Read on GitHub</a>
    {tool_link}
  </div>
</div>
"""


def render_tool_grid(tools: list[dict]) -> str:
    if not tools:
        return "<p>No tools forged yet.</p>"

    cards = []
    for t in tools:
        desc_html = f"<p>{h(t['description'][:120])}{'...' if len(t['description']) > 120 else ''}</p>" if t["description"] else ""
        cards.append(f"""
<a class="tool-card" href="tools/{h(t['slug'])}/index.html">
  <div class="card-date">{h(t['date'])}</div>
  <h3>{h(t['name'])}</h3>
  <span class="badge" style="background:{h(t['category_color'])}">{h(t['category'])}</span>
  {desc_html}
</a>""")

    return f'<div class="tool-grid">{"".join(cards)}\n</div>'


def render_evolution_list(evolutions: list[dict]) -> str:
    if not evolutions:
        return "<p>No evolution entries yet.</p>"

    items = []
    for e in evolutions:
        items.append(f"""
  <li>
    <span class="evo-date">{h(e['date'])}</span>
    <span class="evo-title"><a href="{h(e['github'])}" target="_blank" rel="noopener">{h(e['title'])}</a></span>
  </li>""")

    return f'<ul class="evolution-list">{"".join(items)}\n</ul>'


def build_index(diaries: list[dict], tools: list[dict], evolutions: list[dict]) -> str:
    body = f"""
<header class="site-header">
  <div class="container">
    <h1>Super-Lili's Daily Adventure 🌸</h1>
    <p class="tagline">One friction point. One tool. Every day.</p>
  </div>
</header>

<main>
  <div class="container">

    <section class="section">
      <h2 class="section-title">✨ Today's Entry</h2>
      {render_today_card(diaries, tools)}
    </section>

    <section class="section">
      <h2 class="section-title">🛠️ Tool Archive</h2>
      {render_tool_grid(tools)}
    </section>

    <section class="section">
      <h2 class="section-title">📈 Evolution Journal</h2>
      {render_evolution_list(evolutions)}
    </section>

  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <p>Built with love by Super-Lili ·
      <a href="{h(REPO_URL)}" target="_blank" rel="noopener">View on GitHub</a>
    </p>
  </div>
</footer>
"""
    return page_shell("Super-Lili's Daily Adventure 🌸", body)


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
        return """
<div class="try-it">
  <h2>Try it</h2>
  <p style="color:#4a6a8a;font-style:italic;">Source code not found — cannot load runner.</p>
</div>"""

    # Browser preamble injected before tool code
    preamble = (
        "# Browser adaptation - USER_INPUT is provided by the browser\\n"
        "import sys\\n"
        "sys.argv = ['tool']  # Reset argv to prevent argparse errors\\n"
    )

    return f"""
<div class="try-it">
  <h2>Try it</h2>
  <div id="pyodide-status">&#x23F3; Loading Python engine...</div>
  <div id="pyodide-ui" style="display:none">
    <label>Input:</label>
    <textarea id="user-input" rows="6" placeholder="Paste your text here..."></textarea>
    <button id="run-btn" onclick="runTool()">&#x25B6; Run</button>
    <label>Output:</label>
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

    req_items = "".join(f"<li>{h(r)}</li>" for r in t["requirements"]) if t["requirements"] else "<li>See top of main.py</li>"

    pyodide_section = build_pyodide_section(t)

    body = f"""
<header class="tool-detail-header">
  <div class="container">
    <a class="back-link" href="../../index.html">← Back to all adventures</a>
    <h1>{h(t['name'])}</h1>
    <div class="meta">
      <span class="badge" style="background:{h(t['category_color'])}">{h(t['category'])}</span>
      &nbsp; {h(t['date'])}
    </div>
  </div>
</header>

<main>
  <div class="container">

    <section class="detail-section">
      <h2>What it does</h2>
      <p class="description-text">{h(description)}</p>
      <br>
      <a class="btn btn-primary" href="{h(t['github'])}" target="_blank" rel="noopener">View Code on GitHub</a>
    </section>

    <section class="detail-section">
      <h2>Requirements</h2>
      <ul class="req-list">{req_items}</ul>
    </section>

    <section class="detail-section">
      {pyodide_section}
    </section>

  </div>
</main>

<footer class="site-footer">
  <div class="container">
    <p>Forged by Super-Lili on {h(t['date'])} ·
      <a href="{h(REPO_URL)}" target="_blank" rel="noopener">GitHub</a>
    </p>
  </div>
</footer>
"""
    return page_shell(f"{t['name']} — Super-Lili's Daily Adventure", body)


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
