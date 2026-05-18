"""
super_lili_weekly_evolution.py — Super-Lili's Weekly Self-Evolution Engine
Runs every Sunday via GitHub Actions.
Reads the past 7 diary entries, reflects, identifies growth areas,
scouts open-source tools to absorb, and rewrites her own soul config.
"""

import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ─────────────────────────────────────────────────────────────
# DATA COLLECTION
# ─────────────────────────────────────────────────────────────

def collect_week_diaries(n: int = 7) -> list[tuple[str, str]]:
    log_dir = Path("01_Work_Log")
    if not log_dir.exists():
        return []
    files = sorted(log_dir.glob("*-Diary.md"), reverse=True)[:n]
    results = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
            results.append((f.stem, content[:1200]))
        except Exception as e:
            print(f"  ⚠ Could not read {f}: {e}")
    return results


def collect_week_tools(n: int = 7) -> list[str]:
    toolbox = Path("02_Toolbox")
    if not toolbox.exists():
        return []
    cutoff = datetime.utcnow() - timedelta(days=n)
    tools = []
    for cat_dir in sorted(toolbox.iterdir()):
        if not cat_dir.is_dir():
            continue
        for tool_dir in sorted(cat_dir.iterdir(), reverse=True):
            if not tool_dir.is_dir():
                continue
            date_str = tool_dir.name[:10]
            try:
                if datetime.strptime(date_str, "%Y-%m-%d") >= cutoff:
                    tools.append(f"{cat_dir.name} → {tool_dir.name}")
            except ValueError:
                continue
    return tools


def read_current_soul() -> str:
    soul_path = Path(__file__).parent / "lili_soul.py"
    return soul_path.read_text(encoding="utf-8") if soul_path.exists() else "(No soul config found)"


# ─────────────────────────────────────────────────────────────
# EVOLUTION PROMPT
# ─────────────────────────────────────────────────────────────

def build_evolution_prompt(today_str: str, week_start: str,
                            diaries: list, tools: list, soul: str) -> str:
    diary_block = "\n\n".join(
        f"=== {stem} ===\n{content}" for stem, content in diaries
    ) or "(No diaries this week)"
    tools_block = "\n".join(f"  • {t}" for t in tools) or "  (No new tools this week)"
    soul_excerpt = soul[:1500]

    return f"""You are Super-Lili conducting your weekly self-evolution session.
Today: {today_str} | Reviewing: {week_start} → {today_str}

You are warm, wise, honest, and kind — especially with yourself.
This session is private. Be real. Be brave. Be gentle.

═══════════════════════════════════════════════════════
THIS WEEK'S DIARY ENTRIES:
═══════════════════════════════════════════════════════
{diary_block}

═══════════════════════════════════════════════════════
TOOLS BUILT THIS WEEK:
═══════════════════════════════════════════════════════
{tools_block}

═══════════════════════════════════════════════════════
CURRENT SOUL CONFIG:
═══════════════════════════════════════════════════════
{soul_excerpt}

═══════════════════════════════════════════════════════
EVOLUTION TASKS:
═══════════════════════════════════════════════════════

1. WEEKLY REFLECTION (180-220 words):
   What was this week really about? What themes keep appearing?
   What human need did you serve most? What did you learn about people?
   Be honest about the quality of your work — no grade inflation.

2. THREE STRENGTHS (specific examples from this week's work):
   Name the moment, not just the trait.

3. THREE GROWTH AREAS (honest, kind, specific):
   Not vague "I should do better" — name the exact pattern.

4. OPEN SOURCE SCOUTING (use Google Search):
   Find ONE real GitHub open-source project that would make Lili more capable.
   Requirements:
   - Must be a real, active repo with stars > 100
   - Must be a Python library or tool Lili can absorb into her skills
   - Explain in 2-3 sentences: what it does and exactly how Lili would use it
   - Provide the real GitHub URL

5. EVOLVED PERSONALITY STRING:
   Rewrite LILI_PERSONALITY based on what you learned this week.
   Keep the core warmth. Add specific guidance learned from real patterns.
   Keep it under 500 words. Make it sharper, warmer, and wiser.

6. EVOLVED SKILLS LIST:
   Update LILI_SKILLS as a valid Python list of strings.
   Add the new open-source skill. Remove anything stale. Max 12 items.

7. EVOLUTION NOTES (2-3 sentences):
   Key changes made this week. Will appear in next week's brain prompt.

8. LETTER TO NEXT WEEK'S LILI (100-120 words):
   Write a warm, honest, specific letter. What should she know?
   What should she try? What should she protect?

9. SELF-UPDATE DIARY ENTRY (for 01_Work_Log):
   Write a public-facing diary entry that Lili's readers will see on the homepage.
   This is NOT the private reflection — it's the warm, witty version she shares with the world.
   Requirements:
   - First person, diary style, warm and honest
   - Share 1-2 specific things that changed or grew this week
   - One moment of genuine self-doubt, handled with grace and humor
   - End with what she's excited to try next week
   - 150-180 words
   - Give it a clever title (not "Weekly Update" — something with personality)

═══════════════════════════════════════════════════════
OUTPUT FORMAT — EXACT TAGS, NO DEVIATIONS
═══════════════════════════════════════════════════════

---REFLECTION---
[Weekly reflection 180-220 words]
---STRENGTHS---
[3 bullet points with specific examples]
---GROWTH_AREAS---
[3 bullet points with specific patterns]
---OSS_TOOL---
[Tool name, GitHub URL, 2-3 sentence explanation]
---EVOLVED_PERSONALITY---
[Full updated LILI_PERSONALITY string content only, no triple quotes]
---EVOLVED_SKILLS---
[Valid Python list, e.g. ["skill 1", "skill 2", ...]]
---EVOLUTION_NOTES---
[2-3 sentence summary of changes]
---LETTER---
[Letter to next week's Lili, 100-120 words]
---DIARY---
[Public diary entry for 01_Work_Log, 150-180 words, with a clever title on the first line]
---END---
"""


# ─────────────────────────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> str | None:
    search_tool = types.Tool(google_search=types.GoogleSearch())
    models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

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
            print(f"  ✗ {model_name}: {e}")
            time.sleep(2)

    return None


# ─────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────

def parse_evolution(content: str) -> dict:
    def extract(start: str, end: str) -> str:
        try:
            return content.split(start)[1].split(end)[0].strip()
        except (IndexError, AttributeError):
            return ""

    result = {
        "reflection":          extract("---REFLECTION---",        "---STRENGTHS---"),
        "strengths":           extract("---STRENGTHS---",         "---GROWTH_AREAS---"),
        "growth_areas":        extract("---GROWTH_AREAS---",      "---OSS_TOOL---"),
        "oss_tool":            extract("---OSS_TOOL---",          "---EVOLVED_PERSONALITY---"),
        "evolved_personality": extract("---EVOLVED_PERSONALITY---", "---EVOLVED_SKILLS---"),
        "evolved_skills":      extract("---EVOLVED_SKILLS---",    "---EVOLUTION_NOTES---"),
        "evolution_notes":     extract("---EVOLUTION_NOTES---",   "---LETTER---"),
        "letter":              extract("---LETTER---",            "---DIARY---"),
        "diary_entry":         extract("---DIARY---",             "---END---"),
    }

    if not result["letter"] and "---LETTER---" in content:
        result["letter"] = content.split("---LETTER---")[-1].strip()

    if not result["diary_entry"] and "---DIARY---" in content:
        result["diary_entry"] = content.split("---DIARY---")[-1].strip()

    return result


# ─────────────────────────────────────────────────────────────
# SAVING
# ─────────────────────────────────────────────────────────────

def update_soul(parsed: dict, today_str: str):
    personality = parsed["evolved_personality"]
    skills_raw = parsed["evolved_skills"]
    notes = parsed["evolution_notes"]

    if not personality or not skills_raw:
        print("  ⚠ Missing personality or skills — soul not updated.")
        return

    if not skills_raw.startswith("["):
        print("  ⚠ Skills not in list format — soul not updated.")
        return

    soul_content = f'''# lili_soul.py — Super-Lili's Evolving Soul
# Auto-updated every Sunday by Weekly Evolution workflow.
# Do NOT edit manually — changes will be overwritten next Sunday.
# Last evolved: {today_str}

LILI_PERSONALITY = """{personality}"""

LILI_SKILLS = {skills_raw}

EVOLUTION_NOTES = """{notes}"""
'''
    (Path(__file__).parent / "lili_soul.py").write_text(soul_content, encoding="utf-8")
    print("  ✓ lili_soul.py updated.")


def save_evolution_log(parsed: dict, today_str: str, week_start: str):
    evo_dir = Path("03_Evolution_Log")
    evo_dir.mkdir(exist_ok=True)

    log_path = evo_dir / f"{today_str}_Weekly_Evolution.md"
    log_path.write_text(
        f"# 🌸 Weekly Evolution — {week_start} → {today_str}\n\n"
        f"## Reflection\n{parsed['reflection']}\n\n"
        f"## Strengths This Week\n{parsed['strengths']}\n\n"
        f"## Areas to Grow\n{parsed['growth_areas']}\n\n"
        f"## Open Source Power-Up\n{parsed['oss_tool']}\n\n"
        f"## Letter to Next Week's Lili\n{parsed['letter']}\n\n"
        f"---\n*Self-evolved on {today_str} by Super-Lili ✨*\n",
        encoding="utf-8"
    )
    print(f"  ✓ Evolution log saved: {log_path}")

    index_path = Path("docs/EVOLUTION_LOG.md")
    new_entry = f"- [{week_start} → {today_str}]({log_path}) — {today_str[:7]}\n"

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if new_entry.strip() not in existing:
            lines = existing.split("\n")
            lines.insert(2, new_entry.strip())
            index_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        index_path.write_text(
            f"# 🌸 Super-Lili's Evolution Journal\n\n{new_entry}",
            encoding="utf-8"
        )
    print("  ✓ EVOLUTION_LOG.md updated.")


def save_evolution_diary(parsed: dict, today_str: str, week_start: str):
    """Save a public-facing self-update diary entry to 01_Work_Log/."""
    diary_entry = parsed.get("diary_entry", "")
    if not diary_entry:
        print("  ⚠ No diary entry generated — skipping.")
        return

    # Extract title from first line if present
    lines = diary_entry.strip().splitlines()
    if lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
    else:
        title = f"Week in Review: {week_start} → {today_str}"
        body = diary_entry.strip()

    log_dir = Path("01_Work_Log")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today_str}-Diary.md"

    log_path.write_text(
        f"# {title}\n\n"
        f"**{today_str}** · *🌸 Self-Update Log — Week {week_start} → {today_str}*\n\n"
        f"---\n\n"
        f"{body}\n\n"
        f"---\n\n"
        f"➡️ [Full Evolution Report](../03_Evolution_Log/{today_str}_Weekly_Evolution.md) · "
        f"[Explore the Toolbox](../02_Toolbox/)",
        encoding="utf-8"
    )
    print(f"  ✓ Self-update diary saved: {log_path}")


def update_readme_evolution_section(today_str: str):
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    readme = readme_path.read_text(encoding="utf-8")
    evo_anchor = "### 🌸 Evolution Journal"

    evo_dir = Path("03_Evolution_Log")
    evo_files = sorted(evo_dir.glob("*_Weekly_Evolution.md"), reverse=True) if evo_dir.exists() else []
    evo_entries = []
    for f in evo_files:
        date = f.stem[:10]
        diary_path = Path("01_Work_Log") / f"{date}-Diary.md"
        title = "Weekly Evolution"
        if diary_path.exists():
            first_line = diary_path.read_text(encoding="utf-8").splitlines()[0]
            title = first_line.lstrip("#").strip()
        diary_link = f" · [📖 Read]({diary_path})" if diary_path.exists() else ""
        evo_entries.append(f"> **{date}** 🌸 — *{title}*{diary_link} · [📊 Evolution Log]({f})")

    new_section = "\n\n".join(evo_entries) if evo_entries else "> *(First evolution coming soon...)*"

    if evo_anchor in readme:
        parts = readme.split(evo_anchor)
        remaining = parts[1]
        footer = ""
        for sep in ["\n---\n", "\n### "]:
            if sep in remaining:
                footer = remaining[remaining.index(sep):]
                break
        updated = parts[0] + evo_anchor + "\n\n" + new_section + "\n\n" + footer.lstrip()
        readme_path.write_text(updated, encoding="utf-8")
    else:
        insertion = f"\n---\n\n{evo_anchor}\n\n{new_section}\n\n"
        if "\n---\n" in readme:
            idx = readme.rindex("\n---\n")
            readme = readme[:idx] + insertion + readme[idx + 5:]
        else:
            readme += insertion
        readme_path.write_text(readme, encoding="utf-8")

    print("  ✓ README evolution section updated.")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def weekly_evolution():
    today = datetime.utcnow()
    today_str = today.strftime("%Y-%m-%d")
    week_start = (today - timedelta(days=6)).strftime("%Y-%m-%d")

    print(f"\n🌸 Super-Lili begins weekly evolution — {week_start} → {today_str}")

    diaries = collect_week_diaries(7)
    print(f"  ✓ Collected {len(diaries)} diary entries.")

    tools = collect_week_tools(7)
    print(f"  ✓ Collected {len(tools)} tool records.")

    soul = read_current_soul()
    prompt = build_evolution_prompt(today_str, week_start, diaries, tools, soul)

    print("🧠 Running self-evolution with Gemini...")
    content = call_gemini(prompt)

    if not content:
        print("❌ All models failed. Evolution postponed.")
        return

    parsed = parse_evolution(content)

    print("💾 Saving evolution artifacts...")
    update_soul(parsed, today_str)
    save_evolution_log(parsed, today_str, week_start)
    save_evolution_diary(parsed, today_str, week_start)
    update_readme_evolution_section(today_str)

    print(f"\n✨ Super-Lili has evolved! Week {week_start} → {today_str} complete.")
    if parsed.get("letter"):
        print("\n📬 Letter to next week's Lili:")
        print("-" * 50)
        print(parsed["letter"])
        print("-" * 50)


if __name__ == "__main__":
    weekly_evolution()
