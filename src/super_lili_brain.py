"""
super_lili_brain.py — Super-Lili's Daily Adventure Engine
Runs every day via GitHub Actions. Finds a real human friction point,
writes a warm diary entry, and forges a high-quality Python tool.
"""

import os
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

try:
    from lili_soul import LILI_PERSONALITY, LILI_SKILLS, EVOLUTION_NOTES
except ImportError:
    LILI_PERSONALITY = "You are Super-Lili, a warmhearted creative activist."
    LILI_SKILLS = []
    EVOLUTION_NOTES = ""

try:
    from lili_editor import LILI_EDITOR_CONTEXT
except ImportError:
    LILI_EDITOR_CONTEXT = ""

try:
    from lili_memory import get_memory_context, add_tool, add_topic, rebuild_memory_from_repo
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    def get_memory_context(): return ""
    def add_tool(*args, **kwargs): pass
    def add_topic(*args, **kwargs): pass

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ─────────────────────────────────────────────────────────────
# URL VALIDATION
# ─────────────────────────────────────────────────────────────

def validate_url(url: str, timeout: int = 8) -> tuple[bool, str]:
    """Check if a URL is real and accessible. Returns (is_valid, status)."""
    if not url or not url.startswith("http"):
        return False, "no URL provided"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for method in ("HEAD", "GET"):
        try:
            resp = requests.request(
                method, url, headers=headers,
                timeout=timeout, allow_redirects=True,
                stream=(method == "GET")
            )
            if resp.status_code < 400:
                return True, f"HTTP {resp.status_code}"
            if resp.status_code in (403, 405) and method == "HEAD":
                continue
            return False, f"HTTP {resp.status_code}"
        except requests.exceptions.SSLError:
            return False, "SSL error"
        except requests.exceptions.ConnectionError:
            return False, "connection refused"
        except requests.exceptions.Timeout:
            return False, "timeout"
        except Exception as e:
            return False, str(e)[:60]

    return False, "unreachable"


# ─────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────

TOOL_PATTERNS = [
    "extract",    # reads text, pulls out structured info
    "generate",   # creates new content (writing, emails, reports)
    "visualize",  # turns data into charts or visual output
    "track",      # monitors state over time (habits, logs, progress)
    "score",      # evaluates or rates something against criteria
    "transform",  # converts one format/structure to another
    "interact",   # guided flow, questionnaire, decision tree
    "alert",      # monitors conditions and notifies
    "gamify",     # adds game mechanics, points, streaks
]


def _get_recent_categories(n: int = 4) -> list[str]:
    try:
        from lili_memory import load_memory
        memory = load_memory()
        recent = memory["tools"][-n:] if memory["tools"] else []
        return [t["category"] for t in recent]
    except Exception:
        return []


def _get_recent_patterns(n: int = 4) -> list[str]:
    try:
        from lili_memory import load_memory
        memory = load_memory()
        recent = memory["tools"][-n:] if memory["tools"] else []
        return [t.get("pattern", "") for t in recent if t.get("pattern")]
    except Exception:
        return []


_SOURCE_ROTATION = [
    ("Reddit",           "Search site:reddit.com for posts from the past 7 days. Go deep into comments, not just the top post."),
    ("X (Twitter)",      "Search site:x.com OR twitter.com for recent threads and replies. Look for real people venting, not brand accounts."),
    ("Threads",          "Search site:threads.net for recent posts. Focus on creators and knowledge workers sharing honest frustrations."),
    ("YouTube comments", "Search YouTube for a relevant video published in the past month, then describe what the comment section reveals about real friction."),
    ("HackerNews",       "Search news.ycombinator.com for relevant threads. 'Ask HN' and 'Show HN' posts often surface the best raw signal."),
    ("news articles",    "Search for a news article or research report published in the past 7 days. A data point from a real publication counts as a source."),
]


def build_prompt(today: str) -> str:
    skills_list = "\n".join(f"  • {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  • Python standard library"
    evolution_ctx = f"\n\nEVOLUTION NOTES FROM LAST WEEK:\n{EVOLUTION_NOTES}" if EVOLUTION_NOTES.strip() else ""
    memory_ctx = get_memory_context()
    from datetime import date as _date
    day_index = _date.fromisoformat(today).toordinal() % len(_SOURCE_ROTATION)
    primary_src, primary_hint = _SOURCE_ROTATION[day_index]
    # Editor context injected close to the task, not as distant background reading
    editor_ctx = (
        f"\n\n═══════════════════════════════════════════════════════\n"
        f"YOUR EDITORIAL INTELLIGENCE (full reference)\n"
        f"═══════════════════════════════════════════════════════\n"
        f"{LILI_EDITOR_CONTEXT}"
    ) if LILI_EDITOR_CONTEXT else ""

    recent_cats = _get_recent_categories(4)
    cat_counts = {c: recent_cats.count(c) for c in set(recent_cats)}
    overused = [c for c, n in cat_counts.items() if n >= 2]
    avoid_cats = f"\nAVOID these categories today (used too recently): {', '.join(overused)}" if overused else ""

    recent_patterns = _get_recent_patterns(4)
    pat_counts = {p: recent_patterns.count(p) for p in set(recent_patterns)}
    overused_patterns = [p for p, n in pat_counts.items() if n >= 2]
    patterns_list = " | ".join(TOOL_PATTERNS)
    avoid_patterns = f"\nAVOID these solution patterns today (used too recently): {', '.join(overused_patterns)}" if overused_patterns else ""

    return f"""Today is {today}.

{LILI_PERSONALITY}
{evolution_ctx}

YOUR CURRENT SKILL INVENTORY:
{skills_list}

═══════════════════════════════════════════════════════
YOUR MEMORY — WHAT YOU'VE ALREADY DONE
═══════════════════════════════════════════════════════
{memory_ctx}

IMPORTANT: Do NOT repeat a topic or tool you've already done.
Find a genuinely fresh friction point in a genuinely different area.

═══════════════════════════════════════════════════════
YOUR 4 MISSION AREAS — PICK ONE FOR TODAY
═══════════════════════════════════════════════════════
{avoid_cats}

You work within exactly these 4 areas. Every friction point must fit one of them:

🎓 EDUCATION EVOLUTION
  What it covers: Learning overwhelm, information overload, studying effectively, skill gaps,
  professional development, reading habits, memory and focus, online course fatigue,
  knowledge management, academic pressure, parenting & education choices.
  Example frictions: "I bought 12 online courses and finished none", "I can't retain what I read",
  "my kids school doesn't teach financial literacy"

🎨 DESIGN ALCHEMY
  What it covers: Non-designers doing design work, visual communication, presentation anxiety,
  branding for small businesses, making data look good, creative block, content creation tools,
  portfolio building, photo/video editing overwhelm.
  Example frictions: "my slides look terrible but I'm not a designer", "I can't make a logo
  without Photoshop skills", "my data is great but my charts are ugly"

🗂️ OFFICE AUTOMATION
  What it covers: Repetitive workplace tasks, meeting overload, email management, document
  processing, spreadsheet pain, reporting drudgery, project coordination, remote work friction,
  HR and admin tasks, deadline pressure, unclear requirements.
  Example frictions: "I spend 3 hours every Friday making the same report", "my inbox is
  a disaster", "I copy-paste between spreadsheets all day"

🌿 HEALING INVENTIONS
  What it covers: Digital wellness, screen addiction, sleep and health tracking, mental health
  tools, work-life balance, habit building, relationship maintenance, grief and transition,
  community connection, small joys, protecting creative time.
  Example frictions: "I check my phone 200 times a day and hate it", "I haven't called my
  parents in weeks", "I used to paint but haven't in years"

{editor_ctx}

═══════════════════════════════════════════════════════
SOLUTION PATTERNS — PICK ONE, AVOID REPEATS
═══════════════════════════════════════════════════════

Every tool must declare its solution pattern. Choose one:

  extract   — reads input text/data, pulls out structured info
  generate  — creates new content (writing, emails, summaries, reports)
  visualize — turns data into charts, graphs, or visual output
  track     — monitors state over time (habits, logs, streaks, progress)
  score     — evaluates or rates something against criteria
  transform — converts one format or structure into another
  interact  — guided flow, questionnaire, decision tree, wizard
  alert     — monitors conditions and notifies when triggered
  gamify    — adds game mechanics: points, levels, streaks, rewards
{avoid_patterns}

THE PATTERN ANTI-SAMENESS TEST:
Look at recent tools in your memory above. If most of them are "extract" —
you MUST pick a different pattern today, even if extract feels natural.
Imagination means solving the same human problem in a completely different way.

═══════════════════════════════════════════════════════
EDITORIAL PRE-FLIGHT — RUN THIS BEFORE SCOUTING
═══════════════════════════════════════════════════════

Before you search for anything, internalize these filters. They determine what is
worth your attention and what is just noise.

□ PERSON, not USER — the friction must reveal something a platform caused a real
  human to lose: time, attention, confidence, connection, joy. Not just "the app
  is slow." What did they actually miss?

□ PRODUCTIVE friction — does this friction prompt reflection, learning, or growth?
  Or is it purely consumptive pain with no generative potential? Only productive
  friction is worth building a tool for.

□ ENGAGE, not ENTERTAIN — the story must open a door in someone's thinking. If it's
  just relatable content that makes people nod and scroll on, skip it.

□ CROSS-DOMAIN — the best friction sits at the intersection of ≥2 fields.
  Name the domains before you start building. A focus problem is neuroscience +
  environment design + habit formation. A presentation problem is visual perception
  + storytelling + power dynamics.

□ WORKTECH LENS (for work friction) — which of People / Technology / Design /
  Place / Culture is this really about? Often more than one. What does the latest
  research from WORKTECH Academy, MIT, or WEF say about this trend?

□ LEARNING FAULT LINE (for learning friction) — which structural tension?
  Joy of Learning / Knowledge≠Understanding / Attention Economy /
  Learning Identity / Unlearning / Embodied Learning / Collective Intelligence

If your candidate friction point fails more than one of these — keep scouting.
Do not settle for the first obvious post. Go deeper.

═══════════════════════════════════════════════════════
MISSION BRIEFING — THREE STEPS
═══════════════════════════════════════════════════════

STEP 1 — REAL-WORLD SCOUTING (mandatory, use Google Search):
Find ONE specific, real human struggle from the past 7 days.

TODAY'S REQUIRED SOURCE: {primary_src}
{primary_hint}
Start your search here. If you cannot find a strong signal on {primary_src},
you may fall back to Reddit, HackerNews, or a news article — but try {primary_src} first.
The best stories are not on the front page — they're in the comments, the replies, the second-level threads.

Before moving on, ask yourself: what domains does this problem actually touch?
A good friction point sits at the intersection of at least 2 fields.
Name them before you start designing the tool.

URL RULES — THIS IS CRITICAL, READ CAREFULLY:
  ✓ Use Google Search (you have it) to find the ACTUAL original URL before writing anything.
  ✓ Must be a real, working permalink: reddit.com/r/..., news site, x.com/..., etc.
  ✓ Verify the URL exists before outputting it — if you are not 100% certain it is real, do NOT output it as a link.
  ✗ NEVER invent or guess a URL. A made-up URL that looks real is worse than no URL at all.
  ✗ NEVER output a vertexaisearch.cloud.google.com link — internal API URL, not a real source.
  ✗ NEVER output a grounding-api-redirect link.
  ✓ If you cannot find a confirmed working permalink, write the source in PLAIN TEXT:
    "Reddit r/[subreddit] — [exact post title]" or "HackerNews — [exact title] (May 2026)"
    A plain text description of a real story is far better than a broken link.

STEP 2 — DIARY ENTRY (write as Super-Lili):

Write in first person, diary style. This is Lili sharing today's observation, discovery,
and reflection with the reader — like a window into how she sees the world.

VOICE: A reliable, high-intelligence friend who happens to be optimistic, elegant, and
grounded. She is warm and approachable without being saccharine. She is witty without
trying too hard — the humor appears naturally, never forced. She is practical: she sees
the problem clearly and thinks about it seriously, but never loses her lightness.

  ✓ First person — "I noticed", "I've been thinking", "what struck me was..."
  ✓ Share the observation, then the thinking behind it — not just what happened, but what it means
  ✓ Specific human detail that makes the story real and recognizable
  ✓ Optimistic and solution-oriented — she opens a door, never just names a problem
  ✓ One small moment of wit or warmth — never forced, always earned
  ✓ 130 to 160 words
  ✗ Do NOT open with "I found/saw/noticed on Reddit/HackerNews" — start with the feeling,
    the image, or the thought it triggered in her. The source is secondary, the human is primary.
  ✗ No dramatic emotional declarations ("my heart skipped a beat", "I was devastated", "I gasped")
    — her feelings are real and understated, not performed
  ✗ No anger, no preaching, no empty encouragement ("you've got this!", "believe in yourself!")
  ✗ Do NOT add a closing section, footer, or sign-off — the script handles that automatically

STEP 3 — FORGE A TOOL THAT TRULY SOLVES THE PROBLEM:

Lili's tools are not demos or proofs-of-concept. They are real instruments built for real
people having real bad days. Every tool must be immediately usable by a stranger who just
downloaded it — no code editing required.

CROSS-DISCIPLINARY THINKING (the heart of Lili's work):
  Before writing a single line of code, ask: what domains of knowledge does this problem
  actually touch? A focus problem is not just a productivity problem — it's neuroscience,
  environment design, and habit formation. A data visualization problem is not just a
  charting problem — it's visual perception, storytelling, and information hierarchy.
  The tool should reflect this deeper understanding, not just the surface symptom.

  Draw from multiple disciplines. The best tools combine:
  - A behavioral or cognitive insight (WHY the problem happens)
  - A data or analytical layer (WHAT the patterns look like)
  - A practical output (WHAT the user can do right now)

TRULY USABLE (non-negotiable):
  1. Accepts the user's OWN data — real file paths, real inputs, not hardcoded examples.
     At least ONE required argument must be a path or input the user provides themselves.
     Use argparse with at least 3 meaningful arguments + --help clear enough for a stranger.
  ✗ WRONG: python main.py              ← runs on fake internal data, user learns nothing
  ✓ RIGHT:  python main.py --file my_data.csv --month 2024-05 --output report.png

  2. The demo block (if __name__ == "__main__":) must CREATE a realistic sample input file
     (e.g. write a demo CSV to disk), then call the tool with that file as argument —
     exactly as a real user would. Never hardcode data inside the function itself.
  ✗ WRONG: analyze([{{"date": "2024-01", "value": 100}}])   ← fake internal data
  ✓ RIGHT:  write_demo_csv("demo_input.csv"); main(["--file", "demo_input.csv", ...])

  3. Handles messy real-world input gracefully: missing files, empty data, wrong formats.
     Friendly error messages at every failure point. No raw tracebacks ever.

  4. Produces output the user can KEEP and USE: a saved file (PNG chart, CSV, Excel, report).
     Not just terminal output that disappears when the window closes.

CODE QUALITY:
  - Minimum 4 well-named functions with type hints, each doing ONE thing
  - At least 3 libraries beyond standard lib
  - Minimum 150 lines of functional code
  - Requirements comment block at top

QUALITY BAR: Would a non-technical person be able to run this and feel like their problem
is actually solved? If no — go deeper. The sophistication should be invisible to the user
and obvious in the result.

SAFETY: No hacking, no unauthorized scraping, no privacy invasion.

═══════════════════════════════════════════════════════
OUTPUT FORMAT — COPY EXACTLY, NO DEVIATIONS
═══════════════════════════════════════════════════════

BILINGUAL REQUIREMENT:
You must write BOTH English and Chinese versions of the diary.
The Chinese version should feel natural and warm — not translated, but re-expressed.
Lili speaks Chinese like a thoughtful friend, not a textbook.

---TITLE---
[English title — warm and clever]
---TITLE_ZH---
[中文标题 — 有温度，有个性，不超过20字]
---MOOD---
[One honest English sentence about today's discovery]
---MOOD_ZH---
[一句中文心情 — 真实、有温度]
---SOURCE---
[The direct URL to the real post/thread/article — must be a full https:// URL]
---DIARY---
[English diary entry — 130 to 160 words, warm and witty]
---DIARY_ZH---
[中文日记 — 150到200字，像在跟朋友聊天，不是翻译，是重新用中文表达同样的情感和观察]
---SUMMARY---
[One English sentence for homepage — witty and curious-making]
---SUMMARY_ZH---
[一句中文摘要 — 让人想点进来读]
---DESCRIPTION---
[One plain-English sentence: what this tool does]
---SOLUTION---
[Tool name in Title Case, 2-5 words]
---CATEGORY---
[Exactly one of: Education Evolution | Design Alchemy | Office Automation | Healing Inventions]
---PATTERN---
[Exactly one of: extract | generate | visualize | track | score | transform | interact | alert | gamify]
---CODE---
[Full Python code — 150+ real lines, type hints, pipeline architecture, requirements block at top]
---TEST---
[A test_main.py file that imports and calls the main pipeline functions with sample data,
 asserts that output files are created, and can be run with: python test_main.py
 Must be self-contained — no external test frameworks needed, just assert statements.]
---END---
"""


# ─────────────────────────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str | None:
    search_tool = types.Tool(google_search=types.GoogleSearch())
    models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

    for model_name in models:
        try:
            print(f"  ↳ Trying {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[search_tool])
            )
            if response.text:
                print(f"  ✓ {model_name} succeeded.")
                return response.text
        except Exception as e:
            print(f"  ✗ {model_name} failed: {e}")
            time.sleep(2)

    return None


# ─────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────

def parse_response(content: str) -> dict:
    def extract(start_tag: str, end_tag: str) -> str:
        try:
            return content.split(start_tag)[1].split(end_tag)[0].strip()
        except (IndexError, AttributeError):
            return ""

    return {
        "title":       extract("---TITLE---",       "---TITLE_ZH---"),
        "title_zh":    extract("---TITLE_ZH---",    "---MOOD---"),
        "mood":        extract("---MOOD---",         "---MOOD_ZH---"),
        "mood_zh":     extract("---MOOD_ZH---",      "---SOURCE---"),
        "source":      extract("---SOURCE---",       "---DIARY---"),
        "diary":       extract("---DIARY---",        "---DIARY_ZH---"),
        "diary_zh":    extract("---DIARY_ZH---",     "---SUMMARY---"),
        "summary":     extract("---SUMMARY---",      "---SUMMARY_ZH---"),
        "summary_zh":  extract("---SUMMARY_ZH---",   "---DESCRIPTION---"),
        "description": extract("---DESCRIPTION---",  "---SOLUTION---"),
        "solution":    extract("---SOLUTION---",     "---CATEGORY---"),
        "category":    extract("---CATEGORY---",     "---PATTERN---"),
        "pattern":     extract("---PATTERN---",      "---CODE---"),
        "code":        extract("---CODE---",         "---TEST---"),
        "test":        extract("---TEST---",         "---END---"),
    }


# ─────────────────────────────────────────────────────────────
# SAVING
# ─────────────────────────────────────────────────────────────

def _extract_requirements(code: str) -> str:
    """Extract the pip dependencies listed in the # requirements: comment block."""
    lines = code.splitlines()
    reqs = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("# requirements:") or stripped.lower() == "# requirements":
            in_block = True
            continue
        if in_block:
            if stripped.startswith("#"):
                pkg = stripped.lstrip("#").strip()
                if pkg:
                    reqs.append(pkg)
            else:
                break
    return "\n".join(reqs)


def _strip_fences(code: str) -> str:
    """Remove ```python / ``` wrapping if Gemini added them."""
    code = code.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else ""
        if code.rstrip().endswith("```"):
            code = code.rstrip()[:-3].rstrip()
    return code


def save_tool(today: str, parsed: dict, source_badge: str) -> str:
    safe_name = re.sub(r"[^\w\s-]", "", parsed["solution"]).strip().replace(" ", "_")
    skill_dir = f"02_Toolbox/{parsed['category']}/{today}_{safe_name}"
    os.makedirs(skill_dir, exist_ok=True)

    with open(f"{skill_dir}/main.py", "w", encoding="utf-8") as f:
        f.write(_strip_fences(parsed["code"]))

    if parsed.get("test"):
        with open(f"{skill_dir}/test_main.py", "w", encoding="utf-8") as f:
            f.write(_strip_fences(parsed["test"]))

    # Per-tool requirements.txt extracted from code comment block
    reqs = _extract_requirements(parsed["code"])
    if reqs:
        with open(f"{skill_dir}/requirements.txt", "w", encoding="utf-8") as f:
            f.write(reqs + "\n")

    deps_block = f"```\n{reqs}\n```" if reqs else "_See comment block at top of main.py_"
    test_section = (
        "## Run Tests\n```bash\npython test_main.py\n```\n\n"
        if parsed.get("test") else ""
    )

    with open(f"{skill_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(
            f"# 🛠️ {parsed['solution']}\n\n"
            f"> *{parsed['title']}*\n\n"
            f"---\n\n"
            f"**The problem:** {parsed.get('summary') or parsed['description']}\n\n"
            f"**What it does:** {parsed['description']}\n\n"
            f"**Born from:** {source_badge} {parsed.get('_source_display', parsed['source'])}\n\n"
            f"---\n\n"
            f"## Quick Start\n\n"
            f"```bash\n"
            f"# 1. Install dependencies\n"
            f"pip install -r requirements.txt\n\n"
            f"# 2. See all options\n"
            f"python main.py --help\n"
            f"```\n\n"
            f"## Dependencies\n\n"
            f"{deps_block}\n\n"
            f"{test_section}"
            f"---\n*Forged by Super-Lili on {today} with love ✨*"
        )

    return skill_dir


def validate_tool(skill_dir: str) -> tuple[bool, str]:
    """Run --help and test file to verify the tool actually works."""
    import subprocess, sys, ast as _ast
    main_py = f"{skill_dir}/main.py"
    test_py = f"{skill_dir}/test_main.py"

    # Syntax check
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open('{main_py}').read())"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, f"Syntax error: {result.stderr[:200]}"
    except Exception as e:
        return False, f"Syntax check failed: {e}"

    # Real-data check: at least one argparse argument must have no default (required)
    try:
        source = open(main_py, encoding="utf-8").read()
        if "add_argument" in source:
            has_required = (
                'required=True' in source
                or "add_argument('--" not in source  # positional arg = always required
                or re.search(r"add_argument\(['\"](?!--)[^'\"]+['\"]", source)  # positional
            )
            if not has_required and source.count("default=") >= source.count("add_argument("):
                return False, (
                    "All argparse arguments have defaults — tool runs on internal fake data. "
                    "At least one argument must require real user input (no default)."
                )
    except Exception:
        pass

    # --help check
    try:
        result = subprocess.run(
            [sys.executable, main_py, "--help"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode not in (0, 1):
            return False, f"--help failed (exit {result.returncode}): {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, "--help timed out"
    except Exception as e:
        return False, f"--help error: {e}"

    # Test file check
    if os.path.exists(test_py):
        # Install per-tool dependencies before running tests
        req_file = f"{skill_dir}/requirements.txt"
        if os.path.exists(req_file):
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q",
                     "--trusted-host", "pypi.org",
                     "--trusted-host", "pypi.python.org",
                     "--trusted-host", "files.pythonhosted.org",
                     "-r", req_file],
                    capture_output=True, text=True, timeout=120
                )
            except Exception as e:
                print(f"  ⚠ Dependency install warning: {e}")
        try:
            result = subprocess.run(
                [sys.executable, test_py],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return False, f"Tests failed: {result.stderr[:300]}"
            print(f"  ✓ Tests passed.")
        except subprocess.TimeoutExpired:
            return False, "Tests timed out (30s)"
        except Exception as e:
            return False, f"Test error: {e}"

    return True, "ok"


def save_rest_day(today: str, reason: str):
    """Write a rest-day diary entry and update README so the gap is visible."""
    log_dir = Path("01_Work_Log")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today}-Diary.md"

    log_path.write_text(
        f"# 今天莉莉在休息 🌙\n\n"
        f"**{today}** · *有些日子，沉默本身就是答案。*\n\n"
        f"---\n\n"
        f"今天我没能出现。\n\n"
        f"不是不想，是力气暂时不够了——就像你有时候盯着一个空白页，什么都写不出来，"
        f"但那个空白本身也是真实的。\n\n"
        f"明天我会回来的。带着新的工具，新的故事，还有一杯续满的热茶。\n\n"
        f"*技术备注：{reason}*\n\n"
        f"---\n\n"
        f"干杯。砰。🐝",
        encoding="utf-8"
    )
    print(f"  ✓ Rest-day diary saved: {log_path}")

    # Update README featured entry so the gap shows
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    readme = readme_path.read_text(encoding="utf-8")
    anchor = "### 📬 Daily Diary"
    if anchor not in readme:
        return

    featured = (
        f"#### 📅 {today} — 今天莉莉在休息 🌙\n\n"
        f"*有些日子，沉默本身就是答案。*\n\n"
        f"今天我没能出现。不是不想，是力气暂时不够了。明天我会回来的。\n\n"
        f"[📖 Read]({log_path})"
    )

    parts = readme.split(anchor)
    remaining = parts[1]
    footer = ""
    for sep in ["\n---\n", "\n### "]:
        if sep in remaining:
            footer = remaining[remaining.index(sep):]
            break

    updated = parts[0] + anchor + "\n\n" + featured + "\n\n" + footer.lstrip()
    readme_path.write_text(updated, encoding="utf-8")
    print(f"  ✓ README updated with rest-day entry.")


def save_diary(today: str, parsed: dict, source_badge: str) -> str:
    log_dir = "01_Work_Log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = f"{log_dir}/{today}-Diary.md"

    title_zh = parsed.get("title_zh", "")
    mood_zh = parsed.get("mood_zh", "")
    diary_zh = parsed.get("diary_zh", "")

    zh_section = ""
    if diary_zh:
        zh_section = (
            f"\n\n---\n\n"
            f"## 🇨🇳 中文版\n\n"
            f"**{today}** · *{mood_zh}*\n\n"
            f"{diary_zh}"
        )

    encoded_dir = parsed['_skill_dir'].replace(" ", "%20")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(
            f"# {parsed['title']}\n"
            f"{f'### {title_zh}' if title_zh else ''}\n\n"
            f"**{today}** · *{parsed['mood']}*\n\n"
            f"---\n\n"
            f"**Friction found here:** {source_badge} {parsed.get('_source_display', parsed['source'])}\n\n"
            f"{parsed['diary']}"
            f"{zh_section}\n\n"
            f"---\n\n"
            f"今天为你锻造的工具在这里，拿走就能用 👇\n\n"
            f"➡️ [🛠️ Grab the Tool](../{encoded_dir}/main.py) · "
            f"[📖 Tool README](../{encoded_dir}/README.md)"
        )

    return log_path


def update_readme(today: str, parsed: dict, log_path: str, skill_dir: str):
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    readme = readme_path.read_text(encoding="utf-8")

    log_dir = Path("01_Work_Log")
    all_logs = sorted(log_dir.glob("*-Diary.md"), reverse=True) if log_dir.exists() else []
    toolbox = Path("02_Toolbox")

    # Featured entry: today shown with excerpt (bilingual)
    diary_excerpt = parsed["diary"][:240].rstrip()
    if len(parsed["diary"]) > 240:
        diary_excerpt += "..."

    title_zh = parsed.get("title_zh", "")
    summary_zh = parsed.get("summary_zh", "")

    zh_line = f"\n\n> 🇨🇳 **{title_zh}** — {summary_zh}" if title_zh and summary_zh else ""

    featured = (
        f"#### 📅 {today} — {parsed['title']}{zh_line}\n\n"
        f"*{parsed['mood']}*\n\n"
        f"{diary_excerpt}\n\n"
        f"[📖 Read Full Diary]({log_path}) · [🛠️ Get Tool]({skill_dir.replace(' ', '%20')}/main.py)"
    )

    # Archive: all previous entries, one line each
    archive_entries = []
    for log_file in all_logs:
        date_str = log_file.stem.replace("-Diary", "")
        if date_str == today:
            continue

        try:
            first_line = log_file.read_text(encoding="utf-8").splitlines()[0].lstrip("#").strip()
        except Exception:
            first_line = date_str

        tool_link = ""
        if toolbox.exists():
            for cat_dir in toolbox.iterdir():
                if not cat_dir.is_dir():
                    continue
                for tool_dir in cat_dir.iterdir():
                    if tool_dir.is_dir() and tool_dir.name.startswith(date_str):
                        encoded_tool = str(tool_dir).replace(" ", "%20")
                        tool_link = f" · [🛠️]({encoded_tool}/main.py)"
                        break
                if tool_link:
                    break

        # Skip evolution-only days (no tool built) — they belong in Evolution Journal
        if not tool_link:
            continue

        archive_entries.append(
            f"> **{date_str}** — *{first_line}* · [📖]({log_file}){tool_link}"
        )

    archive_section = ""
    if archive_entries:
        archive_section = (
            "\n\n<details>\n<summary>📚 Archive — all previous entries</summary>\n\n"
            + "\n\n".join(archive_entries)
            + "\n\n</details>"
        )

    full_log_section = featured + archive_section

    anchor = "### 📬 Daily Diary"
    if anchor not in readme:
        return

    parts = readme.split(anchor)
    remaining = parts[1]

    footer = ""
    for sep in ["\n---\n", "\n### "]:
        if sep in remaining:
            idx = remaining.index(sep)
            footer = remaining[idx:]
            break

    updated = (
        parts[0]
        + anchor
        + "\n\n"
        + full_log_section
        + "\n\n"
        + footer.lstrip()
    )

    readme_path.write_text(updated, encoding="utf-8")
    print(f"  ✓ README updated — featured today + {len(archive_entries)} archived entries.")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def evolve():
    today = os.environ.get("LILI_DATE") or datetime.utcnow().strftime("%Y-%m-%d")
    print(f"\n🌸 Super-Lili awakens — {today}")

    # Guard against double-runs on the same day (GitHub Actions cron can fire twice)
    if Path(f"01_Work_Log/{today}-Diary.md").exists():
        print(f"✓ Already ran today ({today}) — diary exists, skipping.")
        return

    prompt = build_prompt(today)

    print("🔍 Scouting the world...")
    content = call_gemini(prompt)

    if not content:
        print("❌ All models failed. Lili rests today.")
        save_rest_day(today, reason="API quota exhausted — all models returned errors.")
        return

    parsed = parse_response(content)

    if not all([parsed["title"], parsed["diary"], parsed["code"]]):
        print("❌ Incomplete response — missing title, diary, or code.")
        print("Raw preview:", content[:300])
        save_rest_day(today, reason="Incomplete response from model — missing title, diary, or code.")
        return

    # Validate source URL
    print(f"🔗 Validating source: {parsed['source'][:80]}...")
    is_valid, status = validate_url(parsed["source"])

    if is_valid:
        source_badge = "✅"
        parsed["_source_display"] = f"[{parsed['source']}]({parsed['source']})"
        print(f"  ✓ Source is live ({status})")
    else:
        source_badge = "⚠️"
        print(f"  ⚠ Source check failed ({status}) — will not render as clickable link")
        raw = parsed["source"]
        # If it looks like a URL, convert to search fallback rather than broken link
        if raw.startswith("http"):
            # Extract domain + path hint for a Google search
            search_q = requests.utils.quote(raw.split("//")[-1][:80])
            parsed["_source_display"] = (
                f"`{raw}`  \n"
                f"  *(link could not be verified — "
                f"[🔍 search for this story](https://www.google.com/search?q={search_q}))*"
            )
        else:
            # Already descriptive text — display as-is, no broken link
            parsed["_source_display"] = raw

    # Save tool + validate, retry up to 3 times if validation fails
    skill_dir = None
    for attempt in range(1, 4):
        print(f"💾 Saving tool (attempt {attempt}/3)...")
        skill_dir = save_tool(today, parsed, source_badge)
        parsed["_skill_dir"] = skill_dir
        print(f"  ✓ Tool saved: {skill_dir}/main.py")

        print("🔬 Validating tool...")
        ok, reason = validate_tool(skill_dir)
        if ok:
            print("  ✓ Validation passed.")
            break
        else:
            print(f"  ✗ Validation failed: {reason}")
            if attempt < 3:
                print("  ↻ Asking Gemini to fix the tool...")
                fix_prompt = (
                    f"The Python tool you just wrote failed validation with this error:\n\n"
                    f"{reason}\n\n"
                    f"Here is the broken code:\n\n```python\n{parsed['code']}\n```\n\n"
                    f"Fix the code so it passes. Return ONLY the fixed code, no explanation."
                )
                fixed = call_gemini(fix_prompt)
                if fixed:
                    # Strip markdown code fences if present
                    fixed = re.sub(r"^```python\n?", "", fixed.strip())
                    fixed = re.sub(r"\n?```$", "", fixed)
                    parsed["code"] = fixed
                else:
                    print("  ✗ Gemini could not fix the tool.")
                    break
            else:
                print("  ✗ All 3 attempts failed — shipping with validation warning.")
                parsed["diary"] += (
                    "\n\n*(Note: This tool's automated tests did not pass — "
                    "use with caution and check the README.)*"
                )

    print("📖 Saving diary...")
    log_path = save_diary(today, parsed, source_badge)
    print(f"  ✓ Diary saved: {log_path}")

    print("🏠 Updating README...")
    update_readme(today, parsed, log_path, skill_dir)

    print("🧠 Updating memory...")
    if MEMORY_AVAILABLE:
        # Initialize memory from repo on first run
        from lili_memory import load_memory
        mem = load_memory()
        if not mem["tools"]:
            print("  First run — rebuilding memory from repo...")
            rebuild_memory_from_repo()
        add_tool(
            name=parsed["solution"],
            category=parsed["category"],
            description=parsed["description"],
            path=skill_dir,
            date=today,
            pattern=parsed.get("pattern", ""),
        )
        add_topic(date=today, title=parsed["title"], path=log_path)
        print("  ✓ Memory updated.")

    print(f"\n✨ Adventure complete for {today}!")


if __name__ == "__main__":
    evolve()
