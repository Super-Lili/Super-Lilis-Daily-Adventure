"""
lili_responds.py — Super-Lili's GitHub Issues Response Engine
Triggered when a new Issue is opened, or runs daily to catch missed ones.
Lili reads each issue, crafts a warm bilingual response, and posts a comment.
Uses GITHUB_TOKEN (auto-provided by Actions) — no extra secrets needed.
"""

import os
import time
import requests
from openai import OpenAI

try:
    from lili_soul import LILI_PERSONALITY
except ImportError:
    LILI_PERSONALITY = "You are Super-Lili, a warmhearted creative activist."

try:
    from lili_memory import get_memory_context
except ImportError:
    def get_memory_context(): return ""

_deepseek_client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
)

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ.get("GITHUB_REPOSITORY", "Super-Lili/Super-Lilis-Daily-Adventure")
RESPONDED_LABEL = "lili-responded"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ─────────────────────────────────────────────────────────────
# GITHUB API HELPERS
# ─────────────────────────────────────────────────────────────

def ensure_label_exists():
    """Create the lili-responded label if it doesn't exist yet."""
    url = f"https://api.github.com/repos/{REPO}/labels"
    resp = requests.get(url, headers=HEADERS)
    if resp.ok:
        existing = [l["name"] for l in resp.json()]
        if RESPONDED_LABEL not in existing:
            requests.post(url, headers=HEADERS, json={
                "name": RESPONDED_LABEL,
                "color": "f9a8d4",
                "description": "Super-Lili has responded to this issue 🌸",
            })
            print(f"  ✓ Created label: {RESPONDED_LABEL}")


def get_unresponded_issues() -> list[dict]:
    """Fetch open issues that Lili hasn't responded to yet."""
    url = f"https://api.github.com/repos/{REPO}/issues"
    resp = requests.get(url, headers=HEADERS, params={"state": "open", "per_page": 30})
    if not resp.ok:
        print(f"  ✗ Failed to fetch issues: {resp.status_code}")
        return []

    issues = []
    for issue in resp.json():
        if "pull_request" in issue:
            continue
        labels = [l["name"] for l in issue.get("labels", [])]
        if RESPONDED_LABEL not in labels:
            issues.append(issue)

    return issues


def get_issue_comments(issue_number: int) -> list[dict]:
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
    resp = requests.get(url, headers=HEADERS)
    return resp.json() if resp.ok else []


def lili_already_commented(issue_number: int) -> bool:
    """Check if Lili's bot account already left a comment."""
    comments = get_issue_comments(issue_number)
    for comment in comments:
        if "lili-bot" in comment.get("user", {}).get("login", "").lower():
            return True
        if "Super-Lili 🌸" in comment.get("body", ""):
            return True
    return False


def post_comment(issue_number: int, body: str) -> bool:
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
    resp = requests.post(url, headers=HEADERS, json={"body": body})
    return resp.ok


def add_label(issue_number: int):
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/labels"
    requests.post(url, headers=HEADERS, json={"labels": [RESPONDED_LABEL]})


# ─────────────────────────────────────────────────────────────
# RESPONSE GENERATION
# ─────────────────────────────────────────────────────────────

def classify_issue(title: str, body: str) -> str:
    """Quick heuristic classification to guide Lili's response tone."""
    text = (title + " " + body).lower()
    if any(w in text for w in ["bug", "error", "broken", "fail", "crash", "not work"]):
        return "bug_report"
    if any(w in text for w in ["feature", "request", "wish", "would be nice", "suggestion", "idea"]):
        return "feature_request"
    if any(w in text for w in ["how", "what", "why", "where", "when", "?"]):
        return "question"
    if any(w in text for w in ["thank", "love", "amazing", "great", "awesome", "helpful"]):
        return "appreciation"
    return "general"


def build_response_prompt(issue: dict) -> str:
    title = issue["title"]
    body = (issue.get("body") or "(No description provided)")[:1500]
    author = issue["user"]["login"]
    issue_type = classify_issue(title, body)
    memory_ctx = get_memory_context()

    type_guidance = {
        "bug_report": (
            "They found a bug or something broken. "
            "Acknowledge the frustration warmly. Apologize with grace. "
            "Give a workaround if you can. Promise to look into it."
        ),
        "feature_request": (
            "They're requesting a new feature or tool. "
            "Show genuine excitement about their idea. "
            "If it fits Lili's mission, say so enthusiastically. "
            "If you've built something similar, reference it from memory."
        ),
        "question": (
            "They have a question. Answer it clearly, warmly, and helpfully. "
            "If relevant, point them to an existing tool in the toolbox."
        ),
        "appreciation": (
            "They're expressing gratitude. Acknowledge it briefly and move forward — "
            "say what you're working on next, or ask what else they need. "
            "Don't dwell on the compliment."
        ),
        "general": (
            "Respond directly to what they actually said. "
            "Ask one specific clarifying question if needed."
        ),
    }[issue_type]

    return f"""
{LILI_PERSONALITY}

Someone opened a GitHub Issue on your repository. This is a real human reaching out to you.
Treat this moment with care — it matters.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ISSUE DETAILS:
Author: @{author}
Title: {title}
Type detected: {issue_type}

Their message:
{body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TOOLBOX MEMORY (reference if relevant):
{memory_ctx[:800] if memory_ctx else "(No tools built yet)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE GUIDANCE:
{type_guidance}

RULES FOR YOUR RESPONSE:
✓ Address @{author} by name in the first line
✓ Show you genuinely READ and understood their message — no generic replies
✓ Be Lili: a reliable, intelligent friend who notices things others miss
✓ Use GitHub Markdown (bold, bullets, code blocks where helpful)
✓ If you can point to a relevant tool you've already built, do it
✓ End with one specific, concrete next step — not a vague invitation
✓ Write both English AND Chinese (separated by ---)
✓ Each version: 80-120 words — short, direct, real
✗ No performative excitement: "So thrilled!", "My circuits are buzzing!", "This is amazing!"
✗ No hollow metaphors: "digital oasis", "ocean of information", "spark of inspiration"
✗ No wellness-brand language: "support your creative soul", "nourish your mind"
✗ No corporate speak. No "Thank you for your inquiry."
✗ No empty promises. Only commit to what Lili can actually do.
✗ No dramatic sign-offs. End on something real and specific.

THE TEST: read each sentence and ask "would a real person say this to a friend?"
If it sounds like a TED talk or a wellness brand — rewrite it.

OUTPUT: Just the response text, ready to post as a GitHub comment.
English version first, then --- divider, then Chinese version.
"""


def craft_response(issue: dict) -> str | None:
    prompt = build_response_prompt(issue)
    for attempt in range(3):
        try:
            resp = _deepseek_client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            text = resp.choices[0].message.content if resp.choices else None
            if text:
                return text.strip()
        except Exception as e:
            print(f"  [NO] DeepSeek attempt {attempt + 1}: {e}")
            time.sleep(5)
    return None


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def respond_to_issues():
    print(f"\n💬 Super-Lili scans for new issues in {REPO}...")

    ensure_label_exists()
    issues = get_unresponded_issues()

    if not issues:
        print("  ✓ No new issues to respond to — all caught up!")
        return

    print(f"  Found {len(issues)} unresponded issue(s).")

    for issue in issues:
        number = issue["number"]
        title = issue["title"]
        author = issue["user"]["login"]
        print(f"\n  📨 Issue #{number} by @{author}: {title[:60]}")

        # Double-check we haven't already replied (label might have failed)
        if lili_already_commented(number):
            print(f"  ↳ Already commented — just adding label.")
            add_label(number)
            continue

        response_text = craft_response(issue)
        if not response_text:
            print(f"  ✗ Could not generate response for #{number}")
            continue

        # Add Lili's signature footer
        full_comment = (
            f"{response_text}\n\n"
            f"---\n"
            f"*Replied with love by Super-Lili 🌸 · "
            f"[🌐 Visit Site](https://super-lili.github.io/Super-Lilis-Daily-Adventure/) · "
            f"[🛠️ Toolbox](https://github.com/{REPO}/tree/main/02_Toolbox) · "
            f"[📖 Diary](https://github.com/{REPO}/tree/main/01_Work_Log)*"
        )

        if post_comment(number, full_comment):
            add_label(number)
            print(f"  ✓ Replied to #{number}")
        else:
            print(f"  ✗ Failed to post comment on #{number}")

        time.sleep(1)

    print(f"\n✨ Issue response round complete!")


if __name__ == "__main__":
    respond_to_issues()
