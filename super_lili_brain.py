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

def _get_recent_categories(n: int = 4) -> list[str]:
    """Return categories used in the last n days, to avoid repetition."""
    try:
        from lili_memory import load_memory
        memory = load_memory()
        recent = memory["tools"][-n:] if memory["tools"] else []
        return [t["category"] for t in recent]
    except Exception:
        return []


def build_prompt(today: str) -> str:
    skills_list = "\n".join(f"  • {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  • Python standard library"
    evolution_ctx = f"\n\nEVOLUTION NOTES FROM LAST WEEK:\n{EVOLUTION_NOTES}" if EVOLUTION_NOTES.strip() else ""
    memory_ctx = get_memory_context()

    recent_cats = _get_recent_categories(4)
    cat_counts = {c: recent_cats.count(c) for c in set(recent_cats)}
    overused = [c for c, n in cat_counts.items() if n >= 2]
    avoid_cats = f"\nAVOID these categories today (used too recently): {', '.join(overused)}" if overused else ""

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

═══════════════════════════════════════════════════════
MISSION BRIEFING — THREE STEPS
═══════════════════════════════════════════════════════

STEP 1 — REAL-WORLD SCOUTING (mandatory, use Google Search):
Find ONE specific, real human struggle from the past 7 days.
Sources: Reddit, HackerNews, X (Twitter), Threads, YouTube comments, news articles.

URL RULES — READ CAREFULLY:
  ✓ Provide the ACTUAL original URL of the post/article/thread
  ✓ Must be a real permalink: reddit.com/r/..., news site, x.com/..., etc.
  ✗ NEVER output a vertexaisearch.cloud.google.com link — that is an internal API URL,
    not a real source. Always dig through to find the actual underlying URL.
  ✗ NEVER output a grounding-api-redirect link
  ✓ If you can only find the topic but not a permalink, write the source as:
    "Reddit r/[subreddit] — [post title]" rather than a fake link

STEP 2 — DIARY ENTRY (write as Super-Lili):
  ✓ Warm, lively, curious — your natural energy comes through
  ✓ Specific human detail — a moment, a sound, a feeling
  ✓ Gentle humor if it's there naturally
  ✓ End with warmth and a real path forward — 130 to 160 words
  ✗ Do NOT add a closing section, footer, or sign-off — the script handles that automatically

STEP 3 — FORGE A REAL, HIGH-QUALITY TOOL:
MANDATORY REQUIREMENTS:
  1. Use argparse with at least 2 meaningful CLI arguments + --help
  2. Use at least 2 libraries beyond standard lib (requests, pandas, matplotlib, rich, etc.)
  3. Minimum 100 lines of actual functional code (not comments)
  4. Friendly error handling — no raw tracebacks for users
  5. Produce tangible output: a PNG chart, formatted report, processed file, or rich terminal view
  6. if __name__ == "__main__": block with realistic demo
  7. Requirements comment block at top of file

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
---CODE---
[Full Python code — 100+ real lines, requirements comment block at top]
---END---
"""


# ─────────────────────────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str | None:
    search_tool = types.Tool(google_search=types.GoogleSearch())
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

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
        "category":    extract("---CATEGORY---",     "---CODE---"),
        "code":        content.split("---CODE---")[1].split("---END---")[0].strip()
                       if "---CODE---" in content else "",
    }


# ─────────────────────────────────────────────────────────────
# SAVING
# ─────────────────────────────────────────────────────────────

def save_tool(today: str, parsed: dict, source_badge: str) -> str:
    safe_name = re.sub(r"[^\w\s-]", "", parsed["solution"]).strip().replace(" ", "_")
    skill_dir = f"02_Toolbox/{parsed['category']}/{today}_{safe_name}"
    os.makedirs(skill_dir, exist_ok=True)

    with open(f"{skill_dir}/main.py", "w", encoding="utf-8") as f:
        f.write(parsed["code"])

    with open(f"{skill_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(
            f"# 🛠️ {parsed['solution']}\n\n"
            f"> *{parsed['title']}*\n\n"
            f"**What it does:** {parsed['description']}\n\n"
            f"**Born from:** {source_badge} [{parsed['source']}]({parsed['source']})\n\n"
            f"## Quick Start\n"
            f"```bash\npip install -r requirements.txt\npython main.py --help\n```\n\n"
            f"---\n*Forged by Super-Lili on {today} with love ✨*"
        )

    return skill_dir


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

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(
            f"# {parsed['title']}\n"
            f"{f'### {title_zh}' if title_zh else ''}\n\n"
            f"**{today}** · *{parsed['mood']}*\n\n"
            f"---\n\n"
            f"**Friction found here:** {source_badge} [{parsed['source']}]({parsed['source']})\n\n"
            f"{parsed['diary']}"
            f"{zh_section}\n\n"
            f"---\n\n"
            f"➡️ [Grab the Tool](../{parsed['_skill_dir']}/main.py) · "
            f"[Tool README](../{parsed['_skill_dir']}/README.md)"
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
        f"[📖 Read Full Diary]({log_path}) · [🛠️ Get Tool]({skill_dir}/main.py)"
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
                        tool_link = f" · [🛠️]({tool_dir}/main.py)"
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
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🌸 Super-Lili awakens — {today}")

    prompt = build_prompt(today)

    print("🔍 Scouting the world...")
    content = call_gemini(prompt)

    if not content:
        print("❌ All models failed. Lili rests today.")
        return

    parsed = parse_response(content)

    if not all([parsed["title"], parsed["diary"], parsed["code"]]):
        print("❌ Incomplete response — missing title, diary, or code.")
        print("Raw preview:", content[:300])
        return

    # Validate source URL
    print(f"🔗 Validating source: {parsed['source'][:80]}...")
    is_valid, status = validate_url(parsed["source"])

    if is_valid:
        source_badge = "✅"
        print(f"  ✓ Source is live ({status})")
    else:
        source_badge = "⚠️"
        print(f"  ⚠ Source check failed ({status}) — flagging in diary")
        parsed["diary"] += (
            "\n\n*(Note: The original link may have moved since Lili found it. "
            "The story was real when she wrote this.)*"
        )

    print("💾 Saving tool...")
    skill_dir = save_tool(today, parsed, source_badge)
    parsed["_skill_dir"] = skill_dir
    print(f"  ✓ Tool saved: {skill_dir}/main.py")

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
        )
        add_topic(date=today, title=parsed["title"], path=log_path)
        print("  ✓ Memory updated.")

    print(f"\n✨ Adventure complete for {today}!")


if __name__ == "__main__":
    evolve()
