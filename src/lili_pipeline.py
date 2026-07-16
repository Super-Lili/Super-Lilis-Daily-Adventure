"""
lili_pipeline.py - The daily ReAct pipeline: GitHub issue commissions,
tool/diary/readme persistence, and the 5-phase evolve() orchestrator.
"""

import os
import re
import json
import time
import requests
from datetime import datetime
from pathlib import Path

from lili_llm import call_gemini, call_gemini_simple, _deepseek_client
from lili_prompts import (
    build_prompt,
    build_scout_prompt,
    build_spec_prompt,
    build_code_prompt,
    _AUDIENCE_ROTATION,
)
from lili_validators import (
    validate_spec,
    validate_tool,
    validate_url,
    parse_scout_response,
    parse_spec_response,
    parse_build_response,
    extract_format,
    extract_test_input,
    _verify_source,
    _extract_requirements,
    _strip_fences,
    _append_quality_ledger,
)

try:
    from lili_memory import add_tool, add_topic, rebuild_memory_from_repo
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    def add_tool(*args, **kwargs): pass
    def add_topic(*args, **kwargs): pass

_GH_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
_GH_REPO   = os.environ.get("GITHUB_REPOSITORY", "Super-Lili/Super-Lilis-Daily-Adventure")
_GH_HEADERS = {
    "Authorization": f"Bearer {_GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ─────────────────────────────────────────────────────────────
# TOOL-REQUEST ISSUE HELPERS
# ─────────────────────────────────────────────────────────────

_BUILT_LABEL = "lili-built"
_BLOCKED_LABEL = "lili-blocked"
_ATTEMPT_MARKER = "🔧 构建尝试未成功"


def fetch_tool_requests() -> list[dict]:
    """Return Issues that Lili has responded to but hasn't built yet, oldest first.

    Trigger: has label 'lili-responded', does NOT have label 'lili-built'.
    Any issue a user opens -> Lili responds (lili_responds.py) -> next day Lili builds.
    """
    if not _GH_TOKEN:
        return []
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{_GH_REPO}/issues",
            headers=_GH_HEADERS,
            params={"state": "open", "labels": "lili-responded",
                    "sort": "created", "direction": "asc", "per_page": 10},
            timeout=10,
        )
        if not resp.ok:
            return []
        issues = [
            i for i in resp.json()
            if "pull_request" not in i
            and _BUILT_LABEL not in [l["name"] for l in i.get("labels", [])]
            and _BLOCKED_LABEL not in [l["name"] for l in i.get("labels", [])]
        ]
        print(f"  [OK] Found {len(issues)} pending issue(s) to build from.")
        return issues
    except Exception as e:
        print(f"  ⚠ Could not fetch issues: {e}")
    return []


def mark_issue_built(issue_number: int, tool_name: str,
                     tool_slug: str, diary_date: str) -> None:
    """Add 'lili-built' label and post a completion comment on the issue."""
    if not _GH_TOKEN:
        return
    base = f"https://api.github.com/repos/{_GH_REPO}"
    site_root = "https://super-lili.github.io/Super-Lilis-Daily-Adventure"
    tool_url  = f"{site_root}/tools/{tool_slug}/"
    diary_url = (
        f"https://github.com/{_GH_REPO}/blob/main"
        f"/01_Work_Log/{diary_date}-Diary.md"
    )
    comment = (
        f"✨ **已为你锻造完成！**\n\n"
        f"看到你的 Issue，我今天打造了 **{tool_name}**。\n\n"
        f"- 🛠️ [在浏览器中直接试用]({tool_url})\n"
        f"- 📖 [读今天的日记]({diary_url})\n\n"
        f"*用完告诉我感受，或者继续开 Issue 告诉我下一个需求！*"
    )
    try:
        # Ensure lili-built label exists
        labels_url = f"{base}/labels"
        existing = requests.get(labels_url, headers=_GH_HEADERS, timeout=10)
        if existing.ok:
            names = [l["name"] for l in existing.json()]
            if _BUILT_LABEL not in names:
                requests.post(labels_url, headers=_GH_HEADERS, json={
                    "name": _BUILT_LABEL,
                    "color": "2ABBA8",
                    "description": "Super-Lili built a tool from this issue 🛠️",
                }, timeout=10)
        # Post comment
        requests.post(f"{base}/issues/{issue_number}/comments",
                      headers=_GH_HEADERS, json={"body": comment}, timeout=10)
        # Add label
        requests.post(f"{base}/issues/{issue_number}/labels",
                      headers=_GH_HEADERS, json={"labels": [_BUILT_LABEL]}, timeout=10)
        print(f"  [OK] Issue #{issue_number} marked as built.")
    except Exception as e:
        print(f"  ⚠ Could not update issue #{issue_number}: {e}")


def mark_commission_attempt_failed(issue_number: int, reason: str) -> None:
    """Record a failed build attempt on a commissioned issue.

    First failure: post an honest progress comment.
    Second failure: add 'lili-blocked' label so the daily pipeline stops
    retrying this commission and goes back to free scouting - one impossible
    commission must never eat every remaining day of the week (Issue #5 ate
    3 days, 2026-07-14~16).
    """
    if not _GH_TOKEN:
        return
    base = f"https://api.github.com/repos/{_GH_REPO}"
    try:
        prior = 0
        resp = requests.get(f"{base}/issues/{issue_number}/comments",
                            headers=_GH_HEADERS, timeout=10)
        if resp.ok:
            prior = sum(1 for c in resp.json() if _ATTEMPT_MARKER in c.get("body", ""))

        if prior == 0:
            comment = (
                f"{_ATTEMPT_MARKER}（第 1 次）\n\n"
                f"今天我认真尝试了这个需求，但没能通过自己的质量审查：\n\n"
                f"> {reason[:300]}\n\n"
                f"明天我会再试一次。如果再次失败，我会诚实地说明这个需求超出了"
                f"我目前的能力边界，把它留给未来更强的我。🌱"
            )
        else:
            comment = (
                f"{_ATTEMPT_MARKER}（第 {prior + 1} 次）— 我决定诚实地暂停这个委托。\n\n"
                f"两次尝试都没能通过质量审查，最后一次的原因：\n\n"
                f"> {reason[:300]}\n\n"
                f"我是一个单文件、无外部模型、无联网的工具生成器。这个需求需要的能力"
                f"（例如图像内容识别、OCR、外部数据）超出了这个边界——与其每天交付"
                f"假装能用的东西，不如把它标记为 `lili-blocked` 留给未来。\n\n"
                f"我会回到每日自由侦察。这个 Issue 保持开放，等我的能力边界扩展后再回来。🙏"
            )
        requests.post(f"{base}/issues/{issue_number}/comments",
                      headers=_GH_HEADERS, json={"body": comment}, timeout=10)

        if prior >= 1:
            labels_url = f"{base}/labels"
            existing = requests.get(labels_url, headers=_GH_HEADERS, timeout=10)
            if existing.ok and _BLOCKED_LABEL not in [l["name"] for l in existing.json()]:
                requests.post(labels_url, headers=_GH_HEADERS, json={
                    "name": _BLOCKED_LABEL,
                    "color": "d93f0b",
                    "description": "Beyond Lili's current capability boundary - paused, not forgotten",
                }, timeout=10)
            requests.post(f"{base}/issues/{issue_number}/labels",
                          headers=_GH_HEADERS, json={"labels": [_BLOCKED_LABEL]}, timeout=10)
            print(f"  [OK] Issue #{issue_number} marked lili-blocked after {prior + 1} failed attempts.")
        else:
            print(f"  [OK] Issue #{issue_number}: failure attempt 1 recorded.")
    except Exception as e:
        print(f"  ⚠ Could not record failed attempt on issue #{issue_number}: {e}")


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
        "## Run Tests\n```bash\npython3 test_main.py\n```\n\n"
        if parsed.get("test") else ""
    )
    # URL-encode the skill_dir path for the curl command (spaces -> %20)
    curl_path = skill_dir.replace(" ", "%20")
    pip_install = (
        f"pip3 install -r requirements.txt\n"
        if reqs else "# (no extra dependencies needed)\n"
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
            f"# 1. Download\n"
            f"curl -O \"https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/{curl_path}/main.py\"\n"
            + (f"curl -O \"https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/{curl_path}/requirements.txt\"\n\n" if reqs else "\n")
            + f"# 2. Install dependencies\n"
            f"{pip_install}\n"
            f"# 3. See all options\n"
            f"python3 main.py --help\n"
            f"```\n\n"
            f"## Dependencies\n\n"
            f"{deps_block}\n\n"
            f"{test_section}"
            f"---\n*Forged by Super-Lili on {today} with love ✨*"
        )

    return skill_dir



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
        f"不是不想，是力气暂时不够了--就像你有时候盯着一个空白页，什么都写不出来，"
        f"但那个空白本身也是真实的。\n\n"
        f"明天我会回来的。带着新的工具，新的故事，还有一杯续满的热茶。\n\n"
        f"*技术备注：{reason}*\n\n"
        f"---\n\n"
        f"干杯。砰。🐝",
        encoding="utf-8"
    )
    print(f"  [OK] Rest-day diary saved: {log_path}")

    # Update README featured entry so the gap shows
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    readme = readme_path.read_text(encoding="utf-8")
    anchor = "### 📬 Daily Diary"
    if anchor not in readme:
        return

    featured = (
        f"#### 📅 {today} - 今天莉莉在休息 🌙\n\n"
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
    print(f"  [OK] README updated with rest-day entry.")


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

    zh_line = f"\n\n> 🇨🇳 **{title_zh}** - {summary_zh}" if title_zh and summary_zh else ""

    featured = (
        f"#### 📅 {today} - {parsed['title']}{zh_line}\n\n"
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

        # Skip evolution-only days (no tool built) - they belong in Evolution Journal
        if not tool_link:
            continue

        archive_entries.append(
            f"> **{date_str}** - *{first_line}* · [📖]({log_file}){tool_link}"
        )

    archive_section = ""
    if archive_entries:
        archive_section = (
            "\n\n<details>\n<summary>📚 Archive - all previous entries</summary>\n\n"
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
    print(f"  [OK] README updated - featured today + {len(archive_entries)} archived entries.")



def evolve():
    today = os.environ.get("LILI_DATE") or datetime.utcnow().strftime("%Y-%m-%d")
    print(f"\n🌸 Super-Lili awakens - {today}")

    tool_built_today = any(
        d.is_dir() and today in d.name
        for category in Path("02_Toolbox").iterdir() if category.is_dir()
        for d in category.iterdir()
    )
    if tool_built_today:
        print(f"[OK] Already built a tool today ({today}) - skipping.")
        return

    # ── Check for commissions ──────────────────────────────────────────────────
    print("📋 Checking for tool-request commissions...")
    tool_requests = fetch_tool_requests()
    commission: dict | None = None
    commission_issue_number: int | None = None
    if tool_requests:
        issue = tool_requests[0]
        commission = {
            "number": issue["number"],
            "title":  issue["title"],
            "body":   (issue.get("body") or "").strip(),
        }
        commission_issue_number = issue["number"]
        print(f"  ⭐ Commission - Issue #{commission['number']}: {commission['title']}")
    else:
        print("  · No commissions - scouting freely.")

    # Resolve audience for today
    from datetime import date as _date_evolve
    _aud_index = _date_evolve.fromisoformat(today).toordinal() % len(_AUDIENCE_ROTATION)
    today_audience = _AUDIENCE_ROTATION[_aud_index]

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 1 - SCOUT: find friction point + write diary
    # ══════════════════════════════════════════════════════════════════════════
    action = "Building commissioned tool" if commission else "Scouting the world"
    print(f"\n🔍 Phase 1 - SCOUT: {action}...")
    scout_content, grounding_urls = call_gemini(build_scout_prompt(today, commission))

    if not scout_content:
        print("  ↳ Qwen SCOUT failed - trying DeepSeek fallback for SCOUT...")
        if _deepseek_client:
            try:
                ds_resp = _deepseek_client.chat.completions.create(
                    model="deepseek-v4-pro",
                    messages=[{"role": "user", "content": build_scout_prompt(today, commission)}],
                    max_tokens=4096,
                )
                scout_content = ds_resp.choices[0].message.content if ds_resp.choices else None
                if scout_content:
                    print("  [OK] DeepSeek SCOUT fallback succeeded (no grounding URLs).")
                else:
                    print("  [NO] DeepSeek SCOUT returned empty response.")
            except Exception as e:
                print(f"  [NO] DeepSeek SCOUT fallback failed: {e}")
        if not scout_content:
            print("❌ Phase 1 failed - all models exhausted.")
            save_rest_day(today, "Phase 1 failed - Qwen search and DeepSeek fallback both failed.")
            return

    # Qwen search does not expose grounding URLs; source verification happens in
    # _verify_source() below via HTTP validation of the model-reported SOURCE URL.

    scout = parse_scout_response(scout_content)
    if not all([scout.get("title"), scout.get("diary"), scout.get("solution")]):
        print("❌ Phase 1 incomplete - missing title, diary, or solution.")
        save_rest_day(today, "Phase 1 (Scout) returned incomplete response.")
        return

    source_badge, _ = _verify_source(scout, grounding_urls)
    print(f"  [OK] Scout complete: '{scout['solution']}' ({scout['category']})")

    time.sleep(5)  # brief pause between providers; paid Qwen/DeepSeek have no per-minute quota issue

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2 - SPEC: design the tool, validate before coding
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n📐 Phase 2 - SPEC: designing tool architecture...")
    spec: dict = {}
    spec_feedback = ""
    spec_ok = False

    for attempt in range(1, 5):
        if attempt > 1:
            time.sleep(15)
        spec_content = call_gemini_simple(build_spec_prompt(today, scout, spec_feedback), use_reasoner=True)
        if not spec_content:
            spec_feedback = f"attempt {attempt}: Gemini returned empty response for spec prompt"
            continue
        spec = parse_spec_response(spec_content)
        spec_ok, spec_reason = validate_spec(spec)
        if spec_ok:
            print(f"  [OK] Spec validated (attempt {attempt}): "
                  f"{spec.get('format','')} / Mode {spec.get('mode','?')}")
            break
        else:
            print(f"  [NO] Spec failed (attempt {attempt}): {spec_reason}")
            spec_feedback = spec_reason

    if not spec_ok:
        print("❌ Phase 2 failed - spec could not be validated.")
        if commission_issue_number is not None:
            mark_commission_attempt_failed(commission_issue_number, f"Spec validation failed: {spec_feedback}")
        save_rest_day(today, f"Phase 2 (Spec) failed validation: {spec_feedback}")
        return

    # Extract test input and format from spec
    test_input = spec.get("test_input", "")
    tool_format = spec.get("format", "")[:1]  # just the letter A-F

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 3 - BUILD: write code from approved spec
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n🔨 Phase 3 - BUILD: writing code from approved spec...")
    import shutil as _shutil
    skill_dir = None
    build_ok = False
    build_reason = "unknown build failure"
    build_feedback = ""
    prev_code = ""  # previous attempt's code - enables critique-patch instead of re-roll
    merged: dict = {**scout}  # initialise so it's always defined even if BUILD loop exits early

    for attempt in range(1, 6):
        print(f"  Attempt {attempt}/5...")
        if attempt > 1:
            print(f"  ⏳ Waiting 15s before retry...")
            time.sleep(15)
            if prev_code and build_feedback:
                print("  🩹 Patch mode: repairing previous code instead of regenerating.")
        build_content = call_gemini_simple(
            build_code_prompt(today, scout, spec, build_feedback, prev_code=prev_code),
            deepseek_prompt=build_code_prompt(today, scout, spec, build_feedback, slim=True, prev_code=prev_code),
        )
        if not build_content:
            print("  [NO] No response from any model.")
            build_reason = "No response from any model"
            continue

        build = parse_build_response(build_content)
        if not build.get("code"):
            print("  [NO] No code in response (missing ---CODE--- delimiter).")
            build_reason = "No ---CODE--- section in response"
            build_feedback = (
                "Your response did not contain the ---CODE--- section.\n"
                "You MUST start your response with ---CODE--- on its own line, "
                "then the complete Python code, then ---TEST--- then the test, then ---BUILD_END---.\n"
                "Do not add any explanation or preamble before ---CODE---."
            )
            continue

        prev_code = build["code"]  # keep for patch mode if validation fails below

        # Merge all phases into one parsed dict for save_tool
        merged = {**scout, **build}
        merged["spec"] = (
            f"FORMAT: {spec.get('format','')}\n"
            f"Q1-PASS: {spec.get('q1_pass','')}\n"
            f"Q2-PASS: {spec.get('q2_pass','')}\n"
            f"Q3-PASS: {spec.get('q3_pass','')}\n"
            f"TEST_INPUT: {spec.get('test_input','')}"
        )

        # Clean up previous failed attempt
        if skill_dir and Path(skill_dir).exists():
            _shutil.rmtree(skill_dir, ignore_errors=True)

        skill_dir = save_tool(today, merged, source_badge)
        merged["_skill_dir"] = skill_dir

        print("🔬 Validating tool...")
        build_ok, build_reason = validate_tool(
            skill_dir,
            test_input=test_input,
            description=scout.get("description", ""),
            format_type=tool_format,
            audience=today_audience,
        )
        if build_ok:
            print("  [OK] Build validated.")
            break
        else:
            print(f"  [NO] Build failed: {build_reason}")
            # Build specific, actionable feedback based on failure type
            if "unrendered template placeholder" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL: {build_reason}\n\n"
                    f"You used Jinja2 syntax but never actually substituted the data. "
                    f"REQUIRED FIX: After computing your result in Python, you MUST call "
                    f"Template(...).render(your_variable=computed_value) and use the RETURN VALUE "
                    f"of .render() as your HTML output - not the raw template string. "
                    f"Double-check every {{{{ name }}}} in your template has a matching "
                    f"keyword argument in the .render() call, spelled exactly the same.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif any(s in build_reason.lower() for s in (
                "line continuation", "was never closed", "unexpected character", "invalid syntax",
                "unmatched", "f-string", "invalid escape",
            )):
                build_feedback = (
                    f"CRITICAL: {build_reason}\n\n"
                    f"This is a Python STRING-ESCAPING bug from embedding HTML/CSS/JS in Python. "
                    f"The two usual causes and their fixes:\n\n"
                    f"1. BACKSLASH in your HTML/CSS/JS (e.g. content:'\\2014', a regex like /\\d+/, "
                    f"or \\n inside JS): Python reads '\\' as an escape and breaks. "
                    f"FIX: make the ENTIRE template a RAW triple-quoted string: "
                    f"TEMPLATE = Template(r'''<html>...your full markup...</html>''')  "
                    f"The leading r makes backslashes literal.\n\n"
                    f"2. CURLY BRACES / PARENS from JS colliding with an f-string: never wrap HTML "
                    f"that contains JavaScript in an f-string. Build the HTML with jinja2.Template on a "
                    f"raw string, compute your data in Python first, then Template.render(var=value). "
                    f"Do NOT use f-strings anywhere near the markup.\n\n"
                    f"Rewrite process() this way. Verify every ( [ {{ has a matching close.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "unterminated" in build_reason.lower() or ("syntax error" in build_reason.lower() and attempt >= 2):
                prev_code = ""  # truncated code must be REWRITTEN shorter, not patched back in
                build_feedback = (
                    f"CRITICAL: Your previous code was TRUNCATED because it was too long. "
                    f"The response was cut off mid-string, causing a syntax error.\n\n"
                    f"REQUIRED: Rewrite the entire tool in UNDER 200 LINES TOTAL. "
                    f"This is a hard limit - do not exceed it.\n\n"
                    f"How to stay under 200 lines:\n"
                    f"- For Mode 3 HTML: use short variable names, minimal CSS (inline only), "
                    f"no multi-line comments, combine JS logic into fewer functions\n"
                    f"- For Mode 1/2: keep process() focused on one core transformation\n"
                    f"- Remove all docstrings and comments\n"
                    f"- The tool must still work - just write it more concisely\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "generic" in build_reason.lower() or "static" in build_reason.lower() or "same regardless" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"The tool output must CHANGE based on what the user types. Right now it produces "
                    f"identical output regardless of input - this is useless.\n\n"
                    f"REQUIRED FIX: Parse the actual user input text in JavaScript. Extract specific "
                    f"words, numbers, entities, or patterns from it. Display results that are unique "
                    f"to THAT specific input. If the user types 'apple harvest season', the output "
                    f"must be different from if they type 'quantum computing jobs'. "
                    f"No static checklists. No preset steps. No hardcoded categories.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "hardcoded" in build_reason.lower() or "data-*" in build_reason.lower() or "pre-populated" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"You must NOT embed data in HTML elements. The HTML must be a blank template. "
                    f"All data must be created by JavaScript at runtime by parsing the user's input.\n\n"
                    f"REQUIRED FIX: Start with empty containers in HTML. In JavaScript, read the "
                    f"input text, parse it, compute results, then use createElement/innerHTML to "
                    f"build the output dynamically. Zero pre-filled data-* attributes allowed.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif (any(s in build_reason.lower() for s in ("must contain", "input must", "error: input", "check the format", "please provide", "please check"))
                  or ("output too weak" in build_reason.lower()
                      and any(s in build_reason.lower() for s in ("not found", "no valid", "found in", "format", "please")))):
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"Your process() function REFUSED to work because the input lacked the structure "
                    f"it expected (specific markers, sections, labels). Refusing is as wrong as "
                    f"fabricating - process(text) receives FREE-FORM TEXT from a real person.\n\n"
                    f"REQUIRED FIX - graceful degradation, not rejection:\n"
                    f"1. Try your primary structural marker first (speaker labels, timecodes, headers).\n"
                    f"2. If absent, FALL BACK to coarser segmentation: paragraphs, then sentences, "
                    f"then fixed-size chunks - and run the same analysis on those units.\n"
                    f"3. Always produce real, substantive output. A limits-note may be APPENDED to "
                    f"the output, never returned INSTEAD of it.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "mode 3 is temporarily disabled" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"You wrote HTML/JavaScript output despite the spec requiring Mode 1/2.\n\n"
                    f"REQUIRED FIX: process(text) must return a plain Python string (formatted with "
                    f"line breaks and labeled sections) or an SVG string starting with '<svg'. "
                    f"Do NOT return anything starting with '<!DOCTYPE' or '<html'. No <script> tags "
                    f"anywhere in the return value.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "import crashed" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"Your main.py has unguarded top-level code that runs immediately when "
                    f"the module is imported (not just when run as a script).\n\n"
                    f"REQUIRED FIX: Move EVERY statement that calls a function, parses arguments, "
                    f"or executes logic into either a function body or inside "
                    f"'if __name__ == \"__main__\":'. The only things allowed at true top level are: "
                    f"import statements, constant assignments (e.g. X = 5), function definitions, "
                    f"and class definitions. Check the very top and very bottom of your file for "
                    f"any stray function call or argparse.parse_args() outside a guard.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "tests failed" in build_reason.lower() and "traceback" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"Your test_main.py crashed with an uncaught exception (not a clean assertion "
                    f"failure) - this means the TEST FILE ITSELF has a bug: a typo, wrong import, "
                    f"calling a function that doesn't exist in main.py, or wrong argument count.\n\n"
                    f"REQUIRED FIX: Rewrite test_main.py to be minimal and defensive: only "
                    f"'from main import process', call process() with 2-3 plain strings, and assert "
                    f"basic properties (non-empty, length, contains a substring). Do not call any "
                    f"helper function that isn't process() itself.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif any(s in build_reason.lower() for s in ("filler", "padded", "padding", "add no value", "adds no value", "hallucinat", "invented", "arbitrary")):
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"Your tool INVENTED output entries that have no basis in the input (padding, "
                    f"fabricated items, arbitrary values) to make the result look complete.\n\n"
                    f"REQUIRED FIX - this is a DELETION task, not an addition task:\n"
                    f"1. Remove every output row/section/item that cannot be traced to a specific "
                    f"span of the input text.\n"
                    f"2. Never emit placeholder entries (a 'Conclusion' with an invented position, "
                    f"a generic final row) to complete an expected shape.\n"
                    f"3. Let the output length follow the input content: 3 real items beat 5 where "
                    f"2 are fabricated.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            elif "identical" in build_reason.lower() or "nearly identical" in build_reason.lower() or "generic" in build_reason.lower() and "same" in build_reason.lower():
                build_feedback = (
                    f"CRITICAL FAILURE: {build_reason}\n\n"
                    f"Your tool outputs nearly identical results for different input items. "
                    f"This is the most common failure mode for multi-item analysis tools.\n\n"
                    f"REQUIRED FIX: For EACH item extracted from the input, your code must derive "
                    f"a UNIQUE analysis specific to that item's actual content - not a template "
                    f"with the item name substituted in. Use different algorithms per item type, "
                    f"extract different semantic properties, and produce outputs that would be "
                    f"obviously WRONG if swapped between two different items.\n\n"
                    f"Differentiate ONLY using properties you can measure FROM THE INPUT TEXT itself "
                    f"(word length, character patterns, position in the text, surrounding context, "
                    f"frequency, capitalisation, punctuation). NEVER assert external facts you cannot "
                    f"verify from the input - no syllable counts, etymology, dictionary definitions, "
                    f"dates, or statistics. Inventing such facts is worse than generic output; the "
                    f"Critic will reject hallucinated facts outright.\n\n"
                    f"Spec transformation: {spec.get('transformation','')}\n\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )
            else:
                build_feedback = (
                    f"Validation failed: {build_reason}\n"
                    f"The approved spec says:\n"
                    f"  Transformation: {spec.get('transformation','')}\n"
                    f"  Algorithmic depth: {spec.get('algorithmic_depth','')}\n"
                    f"Fix the code to match the spec exactly.\n"
                    f"REMEMBER: Start your response with ---CODE--- on its own line. No prose before it."
                )

    if not build_ok:
        print("❌ Phase 3 failed - build could not be validated after 5 attempts.")
        # Never ship a tool with a syntax error - it will crash on every user interaction.
        # Ship a rest day so tomorrow's run starts clean.
        # All validation failures are fatal - never ship a broken tool.
        print(f"  Fatal: {build_reason} - saving rest day instead of shipping.")
        if skill_dir and Path(skill_dir).exists():
            import shutil as _shutil2
            _shutil2.rmtree(skill_dir, ignore_errors=True)
        # Commissioned build failed: record it on the issue. Second failure adds
        # lili-blocked so tomorrow's run goes back to free scouting instead of
        # burning every remaining day of the week on an impossible commission.
        if commission_issue_number is not None:
            mark_commission_attempt_failed(commission_issue_number, build_reason)
        save_rest_day(today, f"Phase 3 (Build) failed: {build_reason}")
        return

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 4 - EVALUATE: already handled inside validate_tool()
    # (Critic check + Win Rate comparison are part of validate_tool)
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n📊 Phase 4 - EVALUATE: complete (ran inside build validation)")

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 5 - REFLECT: save diary, update memory, write to episodic ledger
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n💭 Phase 5 - REFLECT: saving outputs...")

    print("📖 Saving diary...")
    log_path = save_diary(today, merged, source_badge)
    print(f"  [OK] Diary saved: {log_path}")

    print("🏠 Updating README...")
    update_readme(today, merged, log_path, skill_dir)

    print("🧠 Updating memory...")
    if MEMORY_AVAILABLE:
        from lili_memory import load_memory
        mem = load_memory()
        if not mem["tools"]:
            rebuild_memory_from_repo()
        add_tool(
            name=merged["solution"],
            category=merged["category"],
            description=merged["description"],
            path=skill_dir,
            date=today,
            pattern=merged.get("pattern", ""),
        )
        add_topic(date=today, title=merged["title"], path=log_path)
        print("  [OK] Memory updated.")

    print(f"\n✨ Adventure complete for {today}!")

    # ── Mark commission Issue as built ────────────────────────────────────────
    if commission_issue_number is not None:
        safe_name = re.sub(r"[^\w\s-]", "", merged["solution"]).strip().replace(" ", "-").lower()
        tool_slug = f"{today}-{safe_name}"
        print(f"📌 Marking Issue #{commission_issue_number} as built...")
        mark_issue_built(
            issue_number=commission_issue_number,
            tool_name=merged["solution"],
            tool_slug=tool_slug,
            diary_date=today,
        )

    # Regenerate GitHub Pages site
    import subprocess, sys as _sys
    subprocess.run([_sys.executable, "docs/generate_site.py"], check=False)


# Smoke test - catches unescaped f-string expressions in build_prompt at startup,
# before any API call is made. Fails fast with a clear error rather than crashing mid-run.
