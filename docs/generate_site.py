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
    box-shadow: 0 3px 0 0 #fff, 0 4px 0 0 #e0e0e0;
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
    display: flex;
    align-items: center;
    gap: 10px;
}
.nav-logo .dot { color: #111; }
.nav-avatar {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 2px solid #111;
    object-fit: cover;
    object-position: center top;
    filter: grayscale(100%) contrast(1.05);
    flex-shrink: 0;
}
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
    border-bottom: 3px solid #111;
    position: relative;
    overflow: hidden;
}
/* Manga screen-tone: halftone dot texture over hero */
.site-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(17,17,17,0.07) 1.3px, transparent 1.3px);
    background-size: 14px 14px;
    pointer-events: none;
    z-index: 0;
}
.site-hero .container { position: relative; z-index: 1; }
.hero-bar {
    border-top: 3px solid #111;
    border-bottom: 1px solid #ddd;
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
    color: #111;
}
.hero-bar-date {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #999;
}
.hero-bar-rule {
    flex: 1;
    height: 1px;
    background: #ddd;
}
.hero-bar-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #bbb;
}
.hero-inner {
    display: flex;
    align-items: flex-start;
    gap: 56px;
}
.hero-text { flex: 1; min-width: 0; }
.hero-avatar-wrap {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding-top: 8px;
}
.hero-avatar {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    border: 3px solid #111;
    object-fit: cover;
    object-position: center top;
    display: block;
    filter: grayscale(100%) contrast(1.05);
}
.hero-avatar-name {
    font-size: 0.62rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 700;
    color: #111;
}
.hero-title {
    font-size: clamp(1.8rem, 4.5vw, 3.2rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.05;
    color: #111;
    margin-bottom: 24px;
}
.hero-excerpt {
    font-size: 0.95rem;
    color: #555;
    line-height: 1.85;
    max-width: 520px;
    margin-bottom: 36px;
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
    transition: box-shadow 0.12s, transform 0.12s, background 0.12s, border-color 0.12s;
    text-decoration: none;
    transform: skewX(-2deg);
}
.btn:hover { text-decoration: none; }
.btn-dark {
    background: #1a1a1a;
    color: #fff;
    border-color: #1a1a1a;
    box-shadow: 3px 3px 0 0 #555;
}
.btn-dark:hover {
    background: #1a1a1a;
    box-shadow: 5px 5px 0 0 #555;
    transform: skewX(-2deg) translate(-1px, -1px);
}
.btn-ghost { background: transparent; color: #999; border-color: #d0d0d0; }
.btn-ghost:hover { color: #1a1a1a; border-color: #1a1a1a; }
.btn-teal {
    background: #2ABBA8;
    color: #fff;
    border-color: #2ABBA8;
    box-shadow: 3px 3px 0 0 #1a8a7a;
}
.btn-teal:hover {
    background: #229990;
    border-color: #229990;
    box-shadow: 5px 5px 0 0 #1a8a7a;
    transform: skewX(-2deg) translate(-1px, -1px);
}

/* ── Category filter tabs ── */
.cat-filters {
    display: flex;
    gap: 0;
    margin-bottom: 0;
    border: 2px solid #111;
    border-bottom: 2px solid #111;
    overflow: hidden;
}
.cat-filter {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 18px 8px 14px;
    background: #fff;
    border: none;
    border-right: 1.5px solid #111;
    cursor: pointer;
    transition: background 0.15s;
    font-family: inherit;
    position: relative;
}
.cat-filter:last-child { border-right: none; }
.cat-filter:hover { background: #f7f7f5; }
.cat-filter.active { background: #111; }
.cf-icon {
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.cf-icon svg { width: 52px; height: 52px; }
.cat-filter .cf-icon { color: #111; }
.cat-filter.active .cf-icon { color: #fff; }
.cf-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #555;
    transition: color 0.15s;
}
.cat-filter.active .cf-label { color: #fff; }
.cf-count {
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: #bbb;
    transition: color 0.15s;
}
.cat-filter.active .cf-count { color: rgba(255,255,255,0.55); }

/* "All" button — no icon, larger label */
.cat-filter[data-filter="all"] {
    flex: 0 0 auto;
    min-width: 72px;
    padding: 0 16px;
    justify-content: center;
}
.cat-filter[data-filter="all"] .cf-label {
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    color: #111;
}
.cat-filter[data-filter="all"].active .cf-label { color: #fff; }
.cat-filter[data-filter="all"] .cf-count { font-size: 0.65rem; color: #999; }
.cat-filter[data-filter="all"].active .cf-count { color: rgba(255,255,255,0.6); }

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
    border-left: 4px solid #111;
    padding-left: 14px;
}
.section-num {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #111;
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
    gap: 2px;
    background: #111;      /* inner lines + empty cells: black */
    border: 2.5px solid #111; /* outer manga panel frame */
    border-top: none;      /* connects flush with cat-filters */
}
.tool-card {
    background: #fff;
    display: flex;
    flex-direction: column;
    padding: 28px 24px 24px;
    text-decoration: none;
    color: inherit;
    transition: background 0.12s, box-shadow 0.12s, transform 0.12s;
    position: relative;
}
/* Manga panel depth: offset shadow on hover */
.tool-card:hover {
    background: #fafafa;
    box-shadow: 4px 4px 0 0 #111;
    transform: translate(-2px, -2px);
    z-index: 2;
}
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
    position: relative;
    overflow: hidden;
}
.site-footer::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(17,17,17,0.05) 1px, transparent 1px);
    background-size: 12px 12px;
    pointer-events: none;
    z-index: 0;
}
.site-footer .container { position: relative; z-index: 1; }
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
    .hero-avatar { width: 120px; height: 120px; }
    .cf-icon { width: 40px; height: 40px; }
    .cf-icon svg { width: 40px; height: 40px; }
}
@media (max-width: 580px) {
    .container { padding: 0 24px; }
    .card-grid { grid-template-columns: 1fr; }
    .cat-filters { flex-wrap: wrap; }
    .cat-filter { flex: 1 1 40%; }
    .nav-links { display: none; }
    .footer-inner { flex-direction: column; gap: 16px; align-items: flex-start; }
    .footer-tagline { font-size: 0.88rem; }
    .evo-item { grid-template-columns: 80px 1fr; }
    .evo-arrow { display: none; }
    .hero-inner { flex-direction: column-reverse; align-items: center; gap: 32px; }
    .hero-avatar { width: 100px; height: 100px; }
    .hero-title { font-size: 1.8rem; }
    .hero-bar { flex-wrap: wrap; }
}

/* ── Emoji Reactions ────────────────────────────── */
.reactions-section { border-top: 1px solid #f0f0f0; padding-top: 28px; }
.reactions-label { font-size: 0.78rem; font-weight: 600; letter-spacing: .06em;
  text-transform: uppercase; color: #aaa; margin-bottom: 16px; }
.reaction-bar { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.reaction-btn {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  background: #f9f9f9; border: 1.5px solid #ebebeb; border-radius: 12px;
  padding: 10px 16px; cursor: pointer; transition: all .15s ease;
  font-family: inherit; min-width: 72px;
}
.reaction-btn:hover { background: #f0f0f0; border-color: #ddd; transform: translateY(-1px); }
.reaction-btn.selected { background: #fff8f0; border-color: #f59e0b; }
.reaction-emoji { font-size: 1.4rem; line-height: 1; }
.reaction-label { font-size: 0.7rem; color: #888; font-weight: 500; white-space: nowrap; }
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
    if not tool_btn and tools:
        t = tools[0]
        tool_btn = f'<a class="btn btn-teal" href="tools/{h(t["slug"])}/index.html">Latest Tool &rarr;</a>'

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

    # Count tools per category label
    counts = {}
    for t in tools:
        lbl = CATEGORY_LABELS.get(t["category"], t["category"])
        counts[lbl] = counts.get(lbl, 0) + 1

    SVG_OFFICE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 152"><defs><filter id="f1"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.4" xChannelSelector="R" yChannelSelector="G"/></filter></defs><g filter="url(#f1)"><path fill="white" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round" d="M75,12 L85,12 L89,25 Q98,27 106,33 L119,26 L129,36 L122,49 Q128,57 130,66 L143,69 L143,81 L130,84 Q128,93 122,101 L129,114 L119,124 L106,117 Q98,123 89,125 L85,138 L75,138 L71,125 Q62,123 54,117 L41,124 L31,114 L38,101 Q32,93 30,84 L17,81 L17,69 L30,66 Q32,57 38,49 L31,36 L41,26 L54,33 Q62,27 71,25 Z"/><circle fill="white" stroke="currentColor" stroke-width="2.5" cx="80" cy="75" r="30"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="52" y1="46" x2="46" y2="60"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="59" y1="43" x2="52" y2="58"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="105" y1="46" x2="99" y2="60"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="112" y1="52" x2="105" y2="66"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="112" y1="88" x2="105" y2="102"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="105" y1="96" x2="97" y2="108"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="55" y1="95" x2="47" y2="107"/><line stroke="currentColor" stroke-width="1.2" stroke-linecap="round" x1="48" y1="87" x2="41" y2="100"/><circle fill="currentColor" cx="80" cy="75" r="14"/><line stroke="white" stroke-width="3" stroke-linecap="round" x1="80" y1="66" x2="80" y2="84"/><line stroke="white" stroke-width="3" stroke-linecap="round" x1="71" y1="75" x2="89" y2="75"/><circle fill="currentColor" cx="80" cy="47" r="4.5"/><circle fill="currentColor" cx="80" cy="103" r="4.5"/><circle fill="currentColor" cx="52" cy="75" r="4.5"/><circle fill="currentColor" cx="108" cy="75" r="4.5"/></g></svg>'
    SVG_EDUCATION = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><defs><filter id="f2"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.4" xChannelSelector="R" yChannelSelector="G"/></filter></defs><g filter="url(#f2)"><line stroke="currentColor" stroke-width="3.5" stroke-linecap="round" x1="80" y1="114" x2="40" y2="152"/><line stroke="currentColor" stroke-width="3.5" stroke-linecap="round" x1="80" y1="114" x2="120" y2="152"/><line stroke="currentColor" stroke-width="2.5" stroke-linecap="round" x1="49" y1="142" x2="111" y2="142"/><g transform="rotate(-30, 80, 80)"><rect fill="currentColor" x="30" y="67" width="100" height="26" rx="3"/><line stroke="white" stroke-width="3" x1="72" y1="67" x2="72" y2="93"/><line stroke="white" stroke-width="3" x1="98" y1="67" x2="98" y2="93"/><line stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.4" x1="34" y1="70" x2="126" y2="70"/><ellipse fill="currentColor" cx="30" cy="80" rx="9" ry="20"/><ellipse fill="white" cx="30" cy="80" rx="5" ry="12"/><rect fill="currentColor" x="130" y="69" width="18" height="22" rx="2"/><line stroke="white" stroke-width="1.5" stroke-linecap="round" x1="134" y1="73" x2="144" y2="73"/><rect fill="currentColor" stroke="white" stroke-width="1" x="78" y="59" width="12" height="12" rx="2"/></g><polygon fill="currentColor" points="118,22 121,30 130,30 123,35 126,43 118,38 110,43 113,35 106,30 115,30"/><circle fill="currentColor" cx="140" cy="50" r="4.5"/></g></svg>'
    SVG_HEALING = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 162"><defs><filter id="f3"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.4" xChannelSelector="R" yChannelSelector="G"/></filter></defs><g filter="url(#f3)"><path fill="white" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round" d="M46,78 Q42,84 42,96 L42,132 Q42,146 58,146 L102,146 Q118,146 118,132 L118,96 Q118,84 114,78 Z"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="47" y1="84" x2="44" y2="100"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="52" y1="82" x2="48" y2="100"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="113" y1="84" x2="116" y2="100"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="108" y1="82" x2="112" y2="100"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="46" y1="124" x2="44" y2="140"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="52" y1="124" x2="49" y2="142"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="114" y1="124" x2="116" y2="140"/><line stroke="currentColor" stroke-width="1.1" stroke-linecap="round" x1="108" y1="124" x2="111" y2="142"/><path fill="white" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round" d="M62,62 L62,78 L98,78 L98,62 Z"/><rect fill="white" stroke="currentColor" stroke-width="2.5" x="66" y="40" width="28" height="24" rx="2"/><path fill="currentColor" d="M64,28 Q64,20 80,20 Q96,20 96,28 L96,44 L64,44 Z"/><line stroke="white" stroke-width="2" stroke-linecap="round" x1="72" y1="22" x2="72" y2="43"/><line stroke="white" stroke-width="2" stroke-linecap="round" x1="80" y1="21" x2="80" y2="43"/><line stroke="white" stroke-width="2" stroke-linecap="round" x1="88" y1="22" x2="88" y2="43"/><rect fill="white" stroke="currentColor" stroke-width="2.5" x="54" y="88" width="52" height="36" rx="2"/><line stroke="currentColor" stroke-width="5.5" stroke-linecap="round" x1="80" y1="95" x2="80" y2="118"/><line stroke="currentColor" stroke-width="5.5" stroke-linecap="round" x1="68" y1="106" x2="92" y2="106"/></g></svg>'
    SVG_DESIGN = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><defs><filter id="f4"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="1.4" xChannelSelector="R" yChannelSelector="G"/></filter></defs><g filter="url(#f4)"><rect fill="currentColor" x="73" y="68" width="14" height="72" rx="5" transform="rotate(-38, 80, 104)"/><line stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.55" x1="96" y1="103" x2="107" y2="115" transform="rotate(-38, 101, 109)"/><line stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.55" x1="96" y1="113" x2="107" y2="125" transform="rotate(-38, 101, 119)"/><line stroke="white" stroke-width="2" stroke-linecap="round" opacity="0.55" x1="96" y1="123" x2="107" y2="135" transform="rotate(-38, 101, 129)"/><polygon fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" points="55,14 61,32 80,32 65,43 71,61 55,50 39,61 45,43 30,32 49,32"/><polygon fill="white" opacity="0.25" points="55,23 59,34 69,34 61,40 64,51 55,45 46,51 49,40 41,34 51,34"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="55" y1="0" x2="55" y2="9"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="88" y1="6" x2="82" y2="16"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="96" y1="36" x2="85" y2="36"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="86" y1="66" x2="78" y2="58"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="22" y1="6" x2="28" y2="16"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="14" y1="36" x2="25" y2="36"/><line stroke="currentColor" stroke-width="4" stroke-linecap="round" x1="24" y1="66" x2="32" y2="58"/><circle fill="currentColor" cx="112" cy="20" r="5"/><circle fill="currentColor" cx="128" cy="46" r="3.5"/><circle fill="currentColor" cx="18" cy="82" r="3"/></g></svg>'

    filters = f"""<div class="cat-filters">
  <button class="cat-filter active" data-filter="all">
    <span class="cf-label">All</span>
    <span class="cf-count">{len(tools)}</span>
  </button>
  <button class="cat-filter" data-filter="Office">
    <span class="cf-icon">{SVG_OFFICE}</span>
    <span class="cf-label">Office</span>
    <span class="cf-count">{counts.get('Office', 0)}</span>
  </button>
  <button class="cat-filter" data-filter="Education">
    <span class="cf-icon">{SVG_EDUCATION}</span>
    <span class="cf-label">Education</span>
    <span class="cf-count">{counts.get('Education', 0)}</span>
  </button>
  <button class="cat-filter" data-filter="Healing">
    <span class="cf-icon">{SVG_HEALING}</span>
    <span class="cf-label">Healing</span>
    <span class="cf-count">{counts.get('Healing', 0)}</span>
  </button>
  <button class="cat-filter" data-filter="Design">
    <span class="cf-icon">{SVG_DESIGN}</span>
    <span class="cf-label">Design</span>
    <span class="cf-count">{counts.get('Design', 0)}</span>
  </button>
</div>"""

    cards = []
    for i, t in enumerate(tools):
        cat_label = CATEGORY_LABELS.get(t["category"], t["category"])
        idx = str(len(tools) - i).zfill(2)
        desc_html = f'<div class="tc-desc">{h(t["description"][:110])}{"…" if len(t["description"]) > 110 else ""}</div>' if t["description"] else ""
        cards.append(f"""<a class="tool-card" data-cat="{h(cat_label)}" href="tools/{h(t['slug'])}/index.html">
  <div class="tc-top">
    <span class="tc-index">{idx}</span>
    <span class="tc-cat">{h(cat_label)}</span>
  </div>
  <div class="tc-name">{h(t['name'])}</div>
  {desc_html}
  <div class="tc-date">{h(t['date'])}</div>
</a>""")

    js = """<script>
(function(){
  var btns = document.querySelectorAll('.cat-filter');
  btns.forEach(function(btn){
    btn.addEventListener('click', function(){
      btns.forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      var f = btn.dataset.filter;
      document.querySelectorAll('.tool-card').forEach(function(c){
        c.style.display = (f === 'all' || c.dataset.cat === f) ? '' : 'none';
      });
    });
  });
})();
</script>"""

    return f'{filters}<div class="card-grid">{"".join(cards)}</div>{js}'


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
      <div class="nav-logo">
        <img class="nav-avatar" src="assets/lili-avatar.png" alt="Super-Lili" onerror="this.style.display='none'">
        Super-Lili's Daily Adventure<span class="dot">.</span>
      </div>
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
        f"/main/02_Toolbox/{t['category'].replace(' ', '%20')}/{t['dir_name'].replace(' ', '%20')}/main.py"
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


def _prerender_mode3(main_py: Path) -> str | None:
    """Run the tool at site-build time and return its HTML output, or None if it's not Mode 3."""
    import subprocess as _sp, sys as _sys
    try:
        abs_path = str(main_py.resolve())
        result = _sp.run(
            [_sys.executable, "-c",
             f"import sys; sys.argv=['tool']\nUSER_INPUT=''\nexec(open({repr(abs_path)}).read())"],
            capture_output=True, text=True, timeout=30,
            cwd=str(main_py.parent),
        )
        out = result.stdout.strip()
        if out.lstrip().startswith(("<!DOCTYPE", "<html", "<!doctype")):
            return out
    except Exception:
        pass
    return None


def _extract_demo_input(t: dict) -> str:
    """Extract a meaningful demo input from the tool's test file, or return a category default."""
    # Try to find a real sample string from test_main.py
    test_py = TOOLBOX / t["category"] / t["dir_name"] / "test_main.py"
    if test_py.exists():
        try:
            src = test_py.read_text(encoding="utf-8")
            # Look for process("...substantial string...") calls
            for m in re.finditer(r'process\(["\'](.{40,}?)["\']\)', src, re.DOTALL):
                candidate = m.group(1).strip()
                if len(candidate) > 40 and "\n" not in candidate[:20]:
                    return candidate
        except Exception:
            pass
    # Category defaults — real enough to show genuine output
    cat = t.get("category", "")
    defaults = {
        "Education Evolution": (
            "I've been studying machine learning for 3 weeks. "
            "I understand basic concepts but struggle with backpropagation and "
            "keep forgetting the math behind gradient descent. "
            "I have an exam in 5 days and need a structured review plan."
        ),
        "Design Alchemy": (
            "Brand: Momi, a slow-living Japanese skincare line. "
            "Audience: women 28-45 who value ritual and simplicity. "
            "Tone: quiet luxury, minimal, honest. "
            "Deliverable: Instagram caption series for a new serum launch."
        ),
        "Office Automation": (
            "Meeting notes 14:00 Mon: Q3 review. Revenue down 8% vs plan. "
            "Sarah: push launch to Oct. Tom: disagree, delay costs more. "
            "Action items: Sarah sends revised forecast by Wed, "
            "Tom prepares risk analysis, sync again Friday 10am."
        ),
        "Healing Inventions": "",  # Mode 3 tools — use pre-render instead
    }
    return defaults.get(cat, (
        "I have a list of tasks I need to prioritize: "
        "finish the quarterly report, reply to 12 emails, "
        "prepare slides for tomorrow's presentation, "
        "and review two contracts. I only have 3 hours."
    ))


def build_pyodide_section(t: dict) -> str:
    """Return the tool runner HTML — instant iframe for Mode 3, Pyodide+auto-run for Mode 1/2."""
    import json as _json

    tool_code = read_tool_code(t)
    if not tool_code:
        return '<p style="color:#999;font-size:0.85rem;font-style:italic;">Source code not found — cannot load runner.</p>'

    if "USER_INPUT" not in tool_code:
        return build_local_run_section(t)

    # ── Mode 3: pre-render HTML at build time — zero Pyodide wait ──────────────
    main_py = TOOLBOX / t["category"] / t["dir_name"] / "main.py"
    if main_py.exists():
        prerendered = _prerender_mode3(main_py)
        if prerendered:
            html_json = _json.dumps(prerendered).replace("</script>", "<\\/script>")
            return f"""
<div class="prerendered-app" style="margin-top:8px">
  <iframe id="app-frame"
          sandbox="allow-scripts allow-same-origin"
          style="width:100%;min-height:540px;border:1px solid #e8e8e8;border-radius:8px;background:#fff;display:block"
          title="Interactive tool"></iframe>
  <p style="margin-top:10px;font-size:0.8rem;color:#aaa;text-align:center">
    ✨ Interactive app — runs entirely in your browser
  </p>
</div>
<script>
  (function() {{
    const frame = document.getElementById('app-frame');
    frame.srcdoc = {html_json};
    frame.addEventListener('load', function() {{
      try {{
        const h = frame.contentDocument.body.scrollHeight;
        if (h > 200) frame.style.minHeight = (h + 24) + 'px';
      }} catch(e) {{}}
    }});
  }})();
</script>"""

    # ── Mode 1/2: Pyodide runner with auto-run on demo input ───────────────────
    preamble = (
        "import sys\n"
        "sys.argv = ['tool']  # browser mode: reset argv so argparse never fires\n"
    )
    full_code = preamble + "\n" + tool_code
    code_json = _json.dumps(full_code).replace("</script>", "<\\/script>")

    demo_input = _extract_demo_input(t)
    demo_json  = _json.dumps(demo_input)

    cat = t.get("category", "")
    placeholder_hints = {
        "Education Evolution": "Paste your study notes, article, or learning material here…",
        "Design Alchemy":      "Paste your brief, content, or design description here…",
        "Office Automation":   "Paste your meeting notes, task list, or work text here…",
        "Healing Inventions":  "Paste a few sentences about how you're feeling or what's on your mind…",
    }
    placeholder = placeholder_hints.get(cat, "Paste your text here…")

    return f"""
<div id="pyodide-status">&#x23F3; Loading&hellip;</div>
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
const DEMO_INPUT = {demo_json};

async function loadPyodide_() {{
  try {{
    pyodide = await loadPyodide();
    try {{ await pyodide.loadPackagesFromImports(TOOL_CODE); }} catch(e) {{}}
    document.getElementById('pyodide-status').style.display = 'none';
    document.getElementById('pyodide-ui').style.display = 'block';
    // Auto-run with demo input so user sees real output immediately
    if (DEMO_INPUT) {{
      document.getElementById('user-input').value = DEMO_INPUT;
      await runTool(true);
    }}
  }} catch(e) {{
    document.getElementById('pyodide-status').textContent = '❌ Failed to load Python engine. Please refresh.';
  }}
}}

async function runTool(isDemo) {{
  if (!pyodide) return;
  const userInput = document.getElementById('user-input').value.trim();
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Running...';

  try {{
    pyodide.runPython('import sys; from io import StringIO; sys.stdout = StringIO()');
    pyodide.globals.set('USER_INPUT', userInput);
    pyodide.runPython(TOOL_CODE);
    const output = pyodide.runPython('sys.stdout.getvalue()').trim();
    const outEl = document.getElementById('output');
    if (output.startsWith('<!DOCTYPE') || output.startsWith('<html') || output.startsWith('<!-- APP -->')) {{
      outEl.textContent = '';
      outEl.style.cssText = 'background:transparent;padding:0;border:none;white-space:normal';
      const iframe = document.createElement('iframe');
      iframe.sandbox = 'allow-scripts allow-same-origin';
      iframe.style.cssText = 'width:100%;min-height:520px;border:1px solid #e8e8e8;border-radius:8px;background:#fff;display:block';
      iframe.srcdoc = output;
      outEl.appendChild(iframe);
      iframe.addEventListener('load', () => {{
        try {{
          const h = iframe.contentDocument.body.scrollHeight;
          if (h > 200) iframe.style.minHeight = (h + 24) + 'px';
        }} catch(e) {{}}
      }});
    }} else if (output.startsWith('<svg') || output.startsWith('<?xml')) {{
      outEl.textContent = '';
      outEl.style.background = '#f8f8f8';
      const wrapper = document.createElement('div');
      wrapper.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:12px;padding:8px 0';
      const img = document.createElement('div');
      img.innerHTML = output;
      img.style.cssText = 'width:100%;max-width:400px;border-radius:8px;overflow:hidden';
      wrapper.appendChild(img);
      const hint = document.createElement('small');
      hint.textContent = '⬇ Right-click the image to save as SVG';
      hint.style.color = '#aaa';
      wrapper.appendChild(hint);
      outEl.appendChild(wrapper);
    }} else {{
      outEl.textContent = output || '(no output — tool may write to a file instead)';
    }}
    // If this was an auto-run, add a subtle hint
    if (isDemo && output) {{
      const hint = document.createElement('p');
      hint.style.cssText = 'font-size:0.75rem;color:#aaa;margin:6px 0 0;text-align:right';
      hint.textContent = '↑ Demo output — replace the input above with your own text and hit Run';
      document.getElementById('output').after(hint);
    }}
  }} catch(e) {{
    document.getElementById('output').textContent = '❌ Error:\\n' + e.message;
  }}

  btn.disabled = false;
  btn.textContent = '▶ Run';
}}

loadPyodide_();
</script>"""


def build_reaction_section(tool_slug: str) -> str:
    """Discord-style emoji reaction bar. Purely client-side via localStorage."""
    reactions = [
        ("🔥", "fire",      "Used it!"),
        ("👍", "useful",    "Useful"),
        ("🚀", "rocket",    "Inspiring"),
        ("❤️", "heart",     "Love it"),
        ("😕", "confused",  "Not quite"),
    ]
    buttons = "".join(
        f'<button class="reaction-btn" data-key="{key}" title="{label}">'
        f'<span class="reaction-emoji">{emoji}</span>'
        f'<span class="reaction-label">{label}</span>'
        f'</button>'
        for emoji, key, label in reactions
    )
    slug_js = h(tool_slug)
    return f"""
<section class="detail-section reactions-section">
  <div class="reactions-label">Was this useful?</div>
  <div class="reaction-bar" id="reaction-bar-{slug_js}">
    {buttons}
  </div>
</section>
<script>
(function() {{
  var bar = document.getElementById('reaction-bar-{slug_js}');
  if (!bar) return;
  var storageKey = 'lili-rx-{slug_js}';
  var selected = {{}};
  try {{ selected = JSON.parse(localStorage.getItem(storageKey) || '{{}}'); }} catch(e) {{}}
  bar.querySelectorAll('.reaction-btn').forEach(function(btn) {{
    if (selected[btn.dataset.key]) btn.classList.add('selected');
    btn.addEventListener('click', function() {{
      var k = btn.dataset.key;
      selected[k] = !selected[k];
      btn.classList.toggle('selected', !!selected[k]);
      try {{ localStorage.setItem(storageKey, JSON.stringify(selected)); }} catch(e) {{}}
    }});
  }});
}})();
</script>"""


def build_tool_page(t: dict) -> str:
    description = read_readme_description(t["readme_path"]) or t["description"] or "A tool forged by Super-Lili."
    cat_label   = CATEGORY_LABELS.get(t["category"], t["category"])
    reaction_html = build_reaction_section(t.get("slug", ""))

    req_items = "".join(f"<li>{h(r)}</li>" for r in t["requirements"]) if t["requirements"] else "<li style='color:#aaa;font-style:italic;list-style:none;'>None — runs entirely in browser</li>"

    tool_code = read_tool_code(t)
    is_browser = bool(tool_code) and "USER_INPUT" in tool_code
    run_label = "Try in Browser" if is_browser else "Run Locally"

    pyodide_section = build_pyodide_section(t)

    body = f"""
<nav class="site-nav">
  <div class="container">
    <div class="nav-inner">
      <div class="nav-logo">
        <img class="nav-avatar" src="../../assets/lili-avatar.png" alt="Super-Lili" onerror="this.style.display='none'">
        Super-Lili's Daily Adventure<span class="dot">.</span>
      </div>
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

    {reaction_html}

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
