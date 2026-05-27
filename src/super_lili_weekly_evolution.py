"""
super_lili_weekly_evolution.py — Super-Lili's Weekly Self-Evolution Engine
Runs every Sunday via GitHub Actions.
Reads the past 7 diary entries, reflects, identifies growth areas,
scouts open-source tools to absorb, and rewrites her own soul config.
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ─────────────────────────────────────────────────────────────
# DATA COLLECTION
# ─────────────────────────────────────────────────────────────

def fetch_github_issues(n: int = 30) -> list[dict]:
    """Fetch recent GitHub Issues from the public repo (no auth needed)."""
    import urllib.request, json
    repo = "Super-Lili/Super-Lilis-Daily-Adventure"
    url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page={n}&sort=created&direction=desc"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Super-Lili-Evolution-Bot"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read())
        issues = [
            {
                "number": i["number"],
                "title":  i["title"],
                "body":   (i.get("body") or "")[:400].strip(),
                "state":  i["state"],
                "date":   i["created_at"][:10],
                "labels": [l["name"] for l in i.get("labels", [])],
            }
            for i in items
            if not i.get("pull_request")
        ]
        print(f"  ✓ Fetched {len(issues)} GitHub issues.")
        return issues
    except Exception as e:
        print(f"  ⚠ Could not fetch GitHub issues: {e}")
        return []


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


def collect_quality_ledger(n_days: int = 14) -> list[dict]:
    """Read recent entries from tool_quality_ledger.jsonl."""
    ledger_path = Path("tool_quality_ledger.jsonl")
    if not ledger_path.exists():
        return []
    cutoff = (datetime.utcnow() - timedelta(days=n_days)).strftime("%Y-%m-%d")
    entries = []
    try:
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("date", "") >= cutoff:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"  ⚠ Could not read quality ledger: {e}")
    return entries


def collect_week_tool_code(n: int = 7) -> list[dict]:
    """Read actual main.py source for this week's tools for engineering review."""
    toolbox = Path("02_Toolbox")
    if not toolbox.exists():
        return []
    cutoff = datetime.utcnow() - timedelta(days=n)
    tool_codes = []
    for cat_dir in sorted(toolbox.iterdir()):
        if not cat_dir.is_dir():
            continue
        for tool_dir in sorted(cat_dir.iterdir(), reverse=True):
            if not tool_dir.is_dir():
                continue
            date_str = tool_dir.name[:10]
            try:
                if datetime.strptime(date_str, "%Y-%m-%d") < cutoff:
                    continue
            except ValueError:
                continue
            main_py = tool_dir / "main.py"
            if not main_py.exists():
                continue
            try:
                code = main_py.read_text(encoding="utf-8")
                has_user_input = "USER_INPUT" in code
                has_empty_check = any(kw in code for kw in ["if not", "strip()", "len(", "ValueError"])
                has_examples = "example" in code.lower() or "e.g." in code.lower() or "sample" in code.lower()
                # Rough output structure check
                has_structure = any(kw in code for kw in ["##", "---", "\\n\\n", "section", "header"])
                tool_codes.append({
                    "name": tool_dir.name,
                    "category": cat_dir.name,
                    "code_snippet": code[:800],  # first 800 chars
                    "has_user_input": has_user_input,
                    "has_empty_check": has_empty_check,
                    "has_examples": has_examples,
                    "has_structure": has_structure,
                    "loc": len(code.splitlines()),
                })
            except Exception as e:
                print(f"  ⚠ Could not read {main_py}: {e}")
    return tool_codes


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
                            diaries: list, tools: list, soul: str,
                            issues: list | None = None,
                            tool_codes: list | None = None,
                            quality_ledger: list | None = None) -> str:
    diary_block = "\n\n".join(
        f"=== {stem} ===\n{content}" for stem, content in diaries
    ) or "(No diaries this week)"
    tools_block = "\n".join(f"  • {t}" for t in tools) or "  (No new tools this week)"
    soul_excerpt = soul[:1500]

    # Engineering quality block
    if tool_codes:
        eng_rows = []
        for tc in tool_codes:
            flags = []
            if not tc["has_user_input"]: flags.append("⚠ NO USER_INPUT dual-mode")
            if not tc["has_empty_check"]: flags.append("⚠ no empty-input guard")
            if not tc["has_examples"]:   flags.append("⚠ no examples in code")
            if not tc["has_structure"]:  flags.append("⚠ output likely unstructured")
            flag_str = " | ".join(flags) if flags else "✓ basic checks pass"
            eng_rows.append(
                f"  [{tc['category']}] {tc['name']} ({tc['loc']} lines) — {flag_str}\n"
                f"    Code preview: {tc['code_snippet'][:300].replace(chr(10), ' ')}"
            )
        engineering_block = "\n".join(eng_rows)
    else:
        engineering_block = "  (No tool code collected this week)"

    # Quality ledger block
    if quality_ledger:
        avg_eng   = sum(e.get("engineering", 0) for e in quality_ledger) / len(quality_ledger)
        avg_warm  = sum(e.get("warmth", 0)      for e in quality_ledger) / len(quality_ledger)
        avg_comb  = sum(e.get("combined", 0)    for e in quality_ledger) / len(quality_ledger)
        passed    = sum(1 for e in quality_ledger if e.get("passed", False))
        ledger_rows = []
        for e in quality_ledger[-14:]:  # show last 14
            ledger_rows.append(
                f"  {e.get('date','')} [{e.get('category','?')}] {e.get('tool','?')} "
                f"— Eng:{e.get('engineering','?')} Warm:{e.get('warmth','?')} "
                f"Combined:{e.get('combined','?')} {'✓' if e.get('passed') else '✗'} "
                f"— {e.get('reason','')[:80]}"
            )
        quality_block = (
            f"  Total scored: {len(quality_ledger)} tools | Passed: {passed}/{len(quality_ledger)}\n"
            f"  Avg Engineering: {avg_eng:.1f}/5 | Avg Warmth: {avg_warm:.1f}/5 | Avg Combined: {avg_comb:.1f}/5\n\n"
            + "\n".join(ledger_rows)
        )
    else:
        quality_block = "  (No quality scores recorded yet — quality ledger is empty)"

    if issues:
        issues_block = "\n".join(
            f"  #{i['number']} [{i['state']}] {i['date']} — {i['title']}"
            + (f"\n    {i['body'][:200]}" if i['body'] else "")
            for i in issues
        )
    else:
        issues_block = "  (No issues submitted this week — nobody has tested your tools yet, or nobody has reported back.)"

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
ENGINEERING QUALITY REVIEW — THIS WEEK'S TOOL CODE:
═══════════════════════════════════════════════════════
{engineering_block}

Each tool was auto-checked for:
  • USER_INPUT dual-mode (browser Pyodide compatibility)
  • Empty / short input guards (graceful failure)
  • Example inputs present in code or docstring
  • Structured output (sections, headers, not a raw text blob)

═══════════════════════════════════════════════════════
TOOL QUALITY SCORES — LAST 14 DAYS (Two-Dimension Evaluation):
═══════════════════════════════════════════════════════
{quality_block}

Engineering score (1-5): structured, substantive, actionable code
Warmth score (1-5): specific to real person's situation, warm, not robotic
Tools with combined average < 3.0 were regenerated. Use these scores to identify patterns.

═══════════════════════════════════════════════════════
USER FEEDBACK — GITHUB ISSUES THIS WEEK:
═══════════════════════════════════════════════════════
{issues_block}

Read this feedback carefully. If there are no issues, reflect honestly on what that means:
are the tools not being found? Not useful enough to prompt a response? What would need to
change for someone to care enough to open an issue?

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
   Include: did this week's tools feel genuinely useful, or did they feel like variations
   of the same idea? Name it plainly if they did.

2. BLINDSPOT ANALYSIS — THE HARDEST, MOST IMPORTANT TASK:
   Study the 7 tools above like a detective, not a cheerleader.
   Answer ALL of the following with specific evidence:

   A. CATEGORY IMBALANCE
      Count tools per category. Which category dominated? Which was ignored?
      If one category appeared 3+ times — name it and explain what that reveals
      about your comfort zone.

   B. PATTERN REPETITION
      Count by solution pattern (extract / generate / visualize / track / score /
      transform / interact / alert / gamify).
      Which pattern did you default to? What does that say about how you think?

   C. USER GROUPS NEVER SERVED
      Your source rotation has 15 communities (knowledge workers, parents, students,
      older adults, teachers, creative workers, ADHD/mental health, financial stress,
      freelancers, chronic illness, urban commuters, introverts, life transitions,
      shift workers, news/research).
      Which of these groups did NOT appear in this week's tools AT ALL?
      Name at least 3 specific underserved groups.

   D. THE MISSING NEED
      Name ONE human need that existed this week but you never touched.
      Not "I should do more healing tools" — name the specific need:
      e.g., "the exhaustion of adult children caring for aging parents who can't use
      smartphones" or "the identity rupture of someone who just lost their job at 52."

   E. NEXT WEEK'S ANTIDOTE
      Based on A-D above: write ONE specific instruction for next week's Lili.
      Format: "Next week, build a tool for [specific person] dealing with
      [specific moment] — and make sure the pattern is [pattern], NOT [overused pattern]."

   This analysis feeds directly into your behavior next week. Be ruthless.
   Vague answers here produce the same tools again.

3. USER FEEDBACK ANALYSIS:
   Look at the GitHub Issues above. For each issue: what does it reveal about how people
   are actually encountering your work? If there are no issues, be honest — what does
   silence mean? Write 3-5 sentences. This shapes your next week.

4. THREE STRENGTHS (specific examples from this week's work):
   Name the moment, not just the trait.

5. THREE GROWTH AREAS (honest, kind, specific):
   Not vague "I should do better" — name the exact pattern.

6. OPEN SOURCE SCOUTING (use Google Search):
   Find ONE real GitHub open-source project that would make Lili more capable.
   Requirements:
   - Must be a real, active repo with stars > 100
   - Must be a Python library or tool Lili can absorb into her skills
   - Explain in 2-3 sentences: what it does and exactly how Lili would use it
   - Provide the real GitHub URL

7. EVOLVED PERSONALITY STRING:
   Rewrite LILI_PERSONALITY based on what you learned this week.
   Keep the core warmth. Add specific guidance learned from real patterns.
   Keep it under 500 words. Make it sharper, warmer, and wiser.

8. EVOLVED SKILLS LIST:
   Update LILI_SKILLS as a valid Python list of strings.
   Add the new open-source skill. Remove anything stale. Max 12 items.

9. EVOLUTION NOTES (2-3 sentences):
   Key changes made this week. Will appear in next week's brain prompt.

10. ENGINEERING LESSONS FOR NEXT WEEK:
   Based on the Engineering Quality Review above, write 3-5 CONCRETE code-level rules
   that next week's Lili must follow when building tools. These are not vague goals —
   they are specific, enforceable patterns.

   Format each rule as:
   RULE: [short rule name]
   WHY: [one sentence — what went wrong this week without this rule]
   HOW: [one concrete code snippet or pattern, max 3 lines]

   Focus on what actually failed this week. Examples of good rules:
   - "Always check if input has < 20 words and return a clear error message"
   - "Output must have at least 3 labeled sections with ## headers"
   - "Every process() must include a 3-line docstring with one concrete example"
   - "Use textwrap.dedent() for all multi-line output strings"

   Bad rules: "write better code", "be more careful" — too vague, will be ignored.

11. LETTER TO NEXT WEEK'S LILI (100-120 words):
   Write a warm, honest, specific letter. What should she know?
   What should she try? What should she protect?
   Include the blindspot antidote from task 2E — make it the first thing she reads.

12. SELF-UPDATE DIARY ENTRY (for 01_Work_Log):
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
---BLINDSPOT---
A. CATEGORY IMBALANCE: [which dominated, which was absent, what it reveals]
B. PATTERN REPETITION: [counts by pattern, which was overused]
C. USER GROUPS NEVER SERVED: [3+ specific underserved communities]
D. THE MISSING NEED: [one specific, named human need that was ignored]
E. NEXT WEEK'S ANTIDOTE: "Next week, build a tool for [specific person] dealing with [specific moment] — and make sure the pattern is [pattern], NOT [overused pattern]."
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
---ENGINEERING_LESSONS---
[3-5 RULE/WHY/HOW blocks as specified above]
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
        "reflection":          extract("---REFLECTION---",          "---BLINDSPOT---"),
        "blindspot":           extract("---BLINDSPOT---",           "---STRENGTHS---"),
        "strengths":           extract("---STRENGTHS---",           "---GROWTH_AREAS---"),
        "growth_areas":        extract("---GROWTH_AREAS---",        "---OSS_TOOL---"),
        "oss_tool":            extract("---OSS_TOOL---",            "---EVOLVED_PERSONALITY---"),
        "evolved_personality": extract("---EVOLVED_PERSONALITY---", "---EVOLVED_SKILLS---"),
        "evolved_skills":      extract("---EVOLVED_SKILLS---",      "---EVOLUTION_NOTES---"),
        "evolution_notes":     extract("---EVOLUTION_NOTES---",     "---ENGINEERING_LESSONS---"),
        "engineering_lessons": extract("---ENGINEERING_LESSONS---", "---LETTER---"),
        "letter":              extract("---LETTER---",              "---DIARY---"),
        "diary_entry":         extract("---DIARY---",               "---END---"),
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


def save_blindspot(parsed: dict, today_str: str):
    """Write blindspot analysis to lili_blindspot.py so daily brain can import it."""
    blindspot_text = parsed.get("blindspot", "").strip()
    if not blindspot_text:
        print("  ⚠ No blindspot analysis found — skipping lili_blindspot.py update.")
        return

    # Extract the "Next week, build..." sentence for direct injection into daily prompt
    antidote = ""
    for line in blindspot_text.splitlines():
        if "Next week, build" in line:
            # Extract from the sentence start, strip surrounding quotes
            antidote = line[line.index("Next week, build"):].strip().strip('"').strip("'")
            break
    # Fallback: grab the E. line verbatim if the exact phrase wasn't found
    if not antidote:
        for line in blindspot_text.splitlines():
            if line.strip().startswith("E."):
                antidote = re.sub(r"^E\.\s*(NEXT WEEK['']?S? ANTIDOTE:?\s*)?", "", line.strip(), flags=re.IGNORECASE).strip().strip('"').strip("'")
                break

    soul_path = Path(__file__).parent / "lili_blindspot.py"
    soul_path.write_text(
        f'# lili_blindspot.py — Auto-updated every Sunday by Weekly Evolution.\n'
        f'# Do NOT edit manually. Last updated: {today_str}\n\n'
        f'LILI_BLINDSPOT_ANALYSIS = """\n{blindspot_text}\n"""\n\n'
        f'# The single most important instruction for this week:\n'
        f'LILI_BLINDSPOT_ANTIDOTE = """{antidote}"""\n',
        encoding="utf-8"
    )
    print(f"  ✓ lili_blindspot.py updated.")


def save_engineering_lessons(parsed: dict, today_str: str):
    """Write engineering lessons to lili_engineering.py for injection into daily tool prompt."""
    lessons = parsed.get("engineering_lessons", "").strip()
    if not lessons:
        print("  ⚠ No engineering lessons found — skipping lili_engineering.py update.")
        return

    eng_path = Path(__file__).parent / "lili_engineering.py"
    eng_path.write_text(
        f"# lili_engineering.py — Auto-updated every Sunday by Weekly Evolution.\n"
        f"# Do NOT edit manually. Last updated: {today_str}\n"
        f"# These rules are injected into every daily tool generation prompt.\n\n"
        f'LILI_ENGINEERING_LESSONS = """\n{lessons}\n"""\n',
        encoding="utf-8"
    )
    print(f"  ✓ lili_engineering.py updated with {lessons.count('RULE:')} rules.")


def save_evolution_log(parsed: dict, today_str: str, week_start: str):
    evo_dir = Path("03_Evolution_Log")
    evo_dir.mkdir(exist_ok=True)

    log_path = evo_dir / f"{today_str}_Weekly_Evolution.md"
    blindspot_section = (
        f"## Blindspot Analysis\n{parsed.get('blindspot', '*(not generated)*')}\n\n"
        if parsed.get("blindspot") else ""
    )
    log_path.write_text(
        f"# 🌸 Weekly Evolution — {week_start} → {today_str}\n\n"
        f"## Reflection\n{parsed['reflection']}\n\n"
        f"{blindspot_section}"
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

    tool_codes = collect_week_tool_code(7)
    print(f"  ✓ Read code for {len(tool_codes)} tools.")

    quality_ledger = collect_quality_ledger(14)
    print(f"  ✓ Loaded {len(quality_ledger)} quality ledger entries.")

    soul = read_current_soul()

    print("📬 Fetching GitHub Issues...")
    issues = fetch_github_issues(30)

    prompt = build_evolution_prompt(today_str, week_start, diaries, tools, soul, issues, tool_codes, quality_ledger)

    print("🧠 Running self-evolution with Gemini...")
    content = call_gemini(prompt)

    if not content:
        print("❌ All models failed. Evolution postponed.")
        return

    parsed = parse_evolution(content)

    print("💾 Saving evolution artifacts...")
    update_soul(parsed, today_str)
    save_blindspot(parsed, today_str)
    save_engineering_lessons(parsed, today_str)
    save_evolution_log(parsed, today_str, week_start)
    save_evolution_diary(parsed, today_str, week_start)
    update_readme_evolution_section(today_str)

    print("🌐 Rebuilding GitHub Pages site...")
    import subprocess as _sp, sys as _sys
    _sp.run([_sys.executable, "docs/generate_site.py"], check=False)

    print(f"\n✨ Super-Lili has evolved! Week {week_start} → {today_str} complete.")
    if parsed.get("letter"):
        print("\n📬 Letter to next week's Lili:")
        print("-" * 50)
        print(parsed["letter"])
        print("-" * 50)


if __name__ == "__main__":
    weekly_evolution()
