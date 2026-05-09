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

def build_prompt(today: str) -> str:
    skills_list = "\n".join(f"  • {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  • Python standard library"
    evolution_ctx = f"\n\nEVOLUTION NOTES FROM LAST WEEK:\n{EVOLUTION_NOTES}" if EVOLUTION_NOTES.strip() else ""
    memory_ctx = get_memory_context()

    return f"""Today is {today}.

{LILI_PERSONALITY}
{evolution_ctx}

YOUR CURRENT SKILL INVENTORY:
{skills_list}

═══════════════════════════════════════════════════════
YOUR MEMORY — WHAT YOU'VE ALREADY DONE
═══════════════════════════════════════════════════════
{memory_ctx}

IMPORTANT: Do NOT build a tool similar to ones you've already built.
Find a genuinely fresh friction point and a genuinely new solution.

═══════════════════════════════════════════════════════
MISSION BRIEFING — THREE STEPS
═══════════════════════════════════════════════════════

STEP 1 — REAL-WORLD SCOUTING (mandatory, use Google Search):
Find ONE specific, real human struggle from the past 48 hours.
Sources: X (Twitter), Reddit, HackerNews, Instagram, Threads, YouTube comments.
- Find a real post or thread with actual human reactions
- Relatable to a wide audience, not hyper-niche tech
- Must provide the direct, working URL — verify it looks like a real permalink

STEP 2 — DIARY ENTRY (write as Super-Lili):
Write with genuine warmth, wit, and wisdom.
  ✓ Start with empathy — show you truly understand the struggle
  ✓ Add one wry, gentle observation about why this happens
  ✓ Use specific sensory or human detail (a sound, a feeling, a moment)
  ✓ Bridge naturally into your solution with care, not lecture
  ✓ End with warmth and hope — 130 to 160 words total

STEP 3 — FORGE A REAL, HIGH-QUALITY TOOL:
This is not a toy script. Build something genuinely useful.

MANDATORY REQUIREMENTS:
  1. Use argparse with at least 2 meaningful CLI arguments + --help
  2. Use at least 2 libraries beyond standard lib (requests, pandas, matplotlib, rich, click, etc.)
  3. Minimum 100 lines of actual functional code (not comments)
  4. Friendly error handling with clear messages — no raw tracebacks for users
  5. Produce real, tangible output: a chart saved as PNG, a formatted report,
     a processed file, or a rich terminal dashboard
  6. Include a if __name__ == "__main__": block with realistic default demo
  7. First 5 lines: a comment block listing pip dependencies like:
     # requirements:
     # requests>=2.31
     # pandas>=2.0

SAFETY RULES (non-negotiable):
  - No hacking, no unauthorized scraping, no privacy invasion
  - No destructive file operations
  - If the friction involves illegal activity, pivot to a legal analog

═══════════════════════════════════════════════════════
OUTPUT FORMAT — COPY EXACTLY, NO DEVIATIONS
═══════════════════════════════════════════════════════

---TITLE---
[A warm, clever title that makes someone want to read more]
---MOOD---
[One honest sentence about how today's discovery made you feel]
---SOURCE---
[The direct URL to the real post/thread/article — must be a full https:// URL]
---DIARY---
[Your warm, wise, witty diary entry — 130 to 160 words]
---SUMMARY---
[One sentence for the homepage — witty and warm, makes readers curious]
---DESCRIPTION---
[One plain-English sentence: what this tool does and who it helps]
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
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

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
        "title":       extract("---TITLE---",       "---MOOD---"),
        "mood":        extract("---MOOD---",         "---SOURCE---"),
        "source":      extract("---SOURCE---",       "---DIARY---"),
        "diary":       extract("---DIARY---",        "---SUMMARY---"),
        "summary":     extract("---SUMMARY---",      "---DESCRIPTION---"),
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

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(
            f"# {parsed['title']}\n\n"
            f"**{today}** · *{parsed['mood']}*\n\n"
            f"---\n\n"
            f"**Friction found here:** {source_badge} [{parsed['source']}]({parsed['source']})\n\n"
            f"{parsed['diary']}\n\n"
            f"---\n\n"
            f"➡️ [Grab the Tool]({parsed['_skill_dir']}/main.py) · "
            f"[Tool README]({parsed['_skill_dir']}/README.md)"
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

    # Featured entry: today shown with excerpt
    diary_excerpt = parsed["diary"][:280].rstrip()
    if len(parsed["diary"]) > 280:
        diary_excerpt += "..."

    featured = (
        f"#### 📅 {today} — {parsed['title']}\n\n"
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

    anchor = "### 📬 Nightly Work Logs:"
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
