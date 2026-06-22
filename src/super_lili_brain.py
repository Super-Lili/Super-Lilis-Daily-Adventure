"""
super_lili_brain.py - Super-Lili's Daily Adventure Engine
Runs every day via GitHub Actions. Finds a real human friction point,
writes a warm diary entry, and forges a high-quality Python tool.
"""

import os
import re
import sys
import json
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
    from lili_editor import (
        LILI_DOMAIN_WORK,
        LILI_DOMAIN_LEARNING,
        LILI_DOMAIN_HEALING,
        LILI_DOMAIN_STUDIO,
        LILI_EDITORIAL_CRITERIA,
    )
    _EDITOR_DOMAINS: dict[str, str] = {
        "work":     LILI_DOMAIN_WORK,
        "learning": LILI_DOMAIN_LEARNING,
        "healing":  LILI_DOMAIN_HEALING,
        "studio":   LILI_DOMAIN_STUDIO,
        "design":   "",   # Design Alchemy: category descriptions in prompt are sufficient
    }
    _EDITOR_CRITERIA: str = LILI_EDITORIAL_CRITERIA
except ImportError:
    _EDITOR_DOMAINS = {}
    _EDITOR_CRITERIA = ""

try:
    from lili_memory import get_memory_context, add_tool, add_topic, rebuild_memory_from_repo
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    def get_memory_context(): return ""
    def add_tool(*args, **kwargs): pass
    def add_topic(*args, **kwargs): pass

try:
    from lili_blindspot import LILI_BLINDSPOT_ANTIDOTE
except ImportError:
    LILI_BLINDSPOT_ANTIDOTE = ""

try:
    from lili_engineering import LILI_ENGINEERING_BASE, LILI_ENGINEERING_LESSONS
except ImportError:
    LILI_ENGINEERING_BASE = ""
    LILI_ENGINEERING_LESSONS = ""

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# DeepSeek fallback client (used when all Gemini models fail in call_gemini_simple)
_DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
try:
    from openai import OpenAI as _OpenAI
    _deepseek_client = _OpenAI(api_key=_DEEPSEEK_KEY, base_url="https://api.deepseek.com") if _DEEPSEEK_KEY else None
except ImportError:
    _deepseek_client = None

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


# ─────────────────────────────────────────────────────────────
# URL VALIDATION
# ─────────────────────────────────────────────────────────────
# EPISODIC MEMORY - learn from recent tool quality history
# ─────────────────────────────────────────────────────────────

def _build_episodic_memory() -> str:
    """Read last 14 days of quality ledger. Return a compressed summary of
    what worked, what failed, and what patterns to avoid today.
    Returns empty string if no ledger exists yet.
    """
    import json as _json
    from datetime import datetime as _dt, timedelta as _td

    ledger_path = Path("tool_quality_ledger.jsonl")
    if not ledger_path.exists():
        return ""

    cutoff = (_dt.utcnow() - _td(days=14)).strftime("%Y-%m-%d")
    try:
        rows = [
            _json.loads(l) for l in ledger_path.read_text(encoding="utf-8").splitlines()
            if l.strip() and _json.loads(l).get("date", "") >= cutoff
        ]
    except Exception:
        return ""

    if not rows:
        return ""

    passed  = [r for r in rows if r.get("passed")]
    failed  = [r for r in rows if not r.get("passed")]

    # Top failure patterns (most common reasons)
    fail_reasons = [r.get("reason", "") for r in failed if r.get("reason")]
    # Top success patterns
    success_reasons = [r.get("reason", "") for r in passed if r.get("reason")]

    # Category performance
    cat_scores: dict = {}
    for r in rows:
        cat = r.get("category", "unknown")
        if cat not in cat_scores:
            cat_scores[cat] = []
        cat_scores[cat].append(r.get("combined", 3.0))
    cat_summary = ", ".join(
        f"{cat}: avg {sum(scores)/len(scores):.1f}"
        for cat, scores in sorted(cat_scores.items())
        if scores
    )

    lines = [
        f"═══════════════════════════════════════════════════════",
        f"EPISODIC MEMORY - Last 14 days ({len(rows)} tools built)",
        f"═══════════════════════════════════════════════════════",
        f"Pass rate: {len(passed)}/{len(rows)} tools passed quality gates",
    ]
    if cat_summary:
        lines.append(f"By category: {cat_summary}")
    if fail_reasons:
        lines.append(f"\nRecent FAILURE patterns (avoid these today):")
        for r in fail_reasons[-4:]:
            lines.append(f"  [NO] {r[:120]}")
    if success_reasons:
        lines.append(f"\nRecent SUCCESS patterns (build on these):")
        for r in success_reasons[-3:]:
            lines.append(f"  [OK] {r[:120]}")
    lines.append(
        f"\nUse this to avoid repeating mistakes and build on what worked."
    )

    return "\n".join(lines)


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


def _get_recent_failed_categories(days: int = 3, min_failures: int = 2) -> list[str]:
    """Categories where BUILD failed (Critic rejected or validation failed) min_failures+ times
    in the last `days` days, read from tool_quality_ledger.jsonl. Unlike _get_recent_categories
    (which only sees successful tools via lili_memory.json), this catches categories the model
    keeps failing on even when no tool ever shipped."""
    try:
        import json as _json
        from datetime import datetime as _dt2, timedelta as _td2
        cutoff = (_dt2.utcnow() - _td2(days=days)).strftime("%Y-%m-%d")
        ledger_path = Path("tool_quality_ledger.jsonl")
        if not ledger_path.exists():
            return []
        counts: dict[str, int] = {}
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = _json.loads(line)
            if entry.get("date", "") < cutoff or entry.get("passed", True):
                continue
            cat = entry.get("category", "")
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        return [cat for cat, n in counts.items() if n >= min_failures]
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


def _get_existing_tools() -> str:
    """Return a formatted list of all existing tool names + one-line descriptions."""
    toolbox = Path("02_Toolbox")
    if not toolbox.exists():
        return "  (none yet)"
    lines = []
    for cat_dir in sorted(toolbox.iterdir()):
        if not cat_dir.is_dir():
            continue
        for tool_dir in sorted(cat_dir.iterdir(), reverse=True):
            if not tool_dir.is_dir() or len(tool_dir.name) < 11:
                continue
            tool_name = tool_dir.name[11:].replace("_", " ")
            desc = ""
            readme = tool_dir / "README.md"
            try:
                if readme.exists():
                    for line in readme.read_text(encoding="utf-8").splitlines():
                        if line.startswith("**What it does:**"):
                            desc = line.replace("**What it does:**", "").strip()[:90]
                            break
            except Exception:
                pass
            lines.append(f"  * {tool_name}" + (f" - {desc}" if desc else ""))
    return "\n".join(lines) if lines else "  (none yet)"


_SOURCE_ROTATION = [
    # ── KNOWLEDGE WORKERS & PRODUCTIVITY ──
    ("Reddit (knowledge workers)",
     "Search r/productivity, r/gtd, r/remotework for posts from the past 7 days. "
     "Focus on people drowning in tools, notifications, or the performance of busyness. "
     "Go deep into comments - the real signal is in the replies, not the post."),

    # ── DESIGNERS & VISUAL CREATIVES - real production friction ──
    ("Reddit & Figma community (designers)",
     "Search r/graphic_design, r/UI_Design, r/MotionDesign, and the Figma community forum "
     "for posts from the past 7 days. "
     "Look for REAL PRODUCTION FRICTION: repetitive manual tasks, file chaos, "
     "font/type workflow pain, handoff nightmares, asset organisation hell, "
     "the gap between inspiration and execution. "
     "What specific thing do designers do 10 times a week that should be automated? "
     "Think: batch renaming, font pairing, SVG cleanup, spec generation, palette extraction."),

    # ── STUDENTS & LEARNING ──
    ("YouTube comments (students)",
     "Search YouTube for a study, exam prep, or 'how I actually learned X' video from the past month. "
     "Read the comment section carefully - students are brutally honest about what fails them. "
     "Look for patterns around memory, motivation collapse, and tutorial hell."),

    # ── JOURNALISTS & EDITORS - real reporting workflow ──
    ("Reddit & journalism forums (reporters & editors)",
     "Search r/Journalism, r/editors, r/writing, and niemanlab.org for posts from the past 7 days. "
     "Look for REAL WORKFLOW FRICTION: interview transcription chaos, source management, "
     "fact-checking repetitive work, headline/copy iteration, deadline pressure tools. "
     "What do journalists do manually every day that a smart tool could handle in seconds?"),

    # ── TEACHERS & EDUCATORS ──
    ("Reddit (teachers)",
     "Search r/Teachers, r/teaching, r/OnlineEducators for posts from the past 7 days. "
     "Look for burnout signals, the gap between what teachers wish they could do "
     "and what their actual constraints allow. What invisible labor do they carry?"),

    # ── CREATIVE PROFESSIONALS - studio & production tools ──
    ("Threads & X (creative studio workers)",
     "Search threads.net and x.com for designers, art directors, brand strategists, "
     "motion designers, and illustrators posting about their actual studio workflow. "
     "NOT feelings about algorithms - look for: 'I wish there was a tool that...', "
     "'I still do this manually...', 'every project I have to...'. "
     "Real production pain, not existential creative dread."),

    # ── MENTAL HEALTH & NEURODIVERGENCE ──
    ("Reddit (ADHD & mental health)",
     "Search r/ADHD, r/anxiety, r/depression for posts from the past 7 days. "
     "Focus on daily friction - not clinical discussions, but real moments where "
     "ordinary tasks feel impossible. What small environmental changes help people function?"),

    # ── FREELANCERS & FINANCE - real money management tools ──
    ("Reddit (freelancers & independent workers)",
     "Search r/freelance, r/smallbusiness, r/personalfinance for posts from the past week. "
     "Look for SPECIFIC FUNCTIONAL GAPS: invoice calculation, project rate estimation, "
     "tax prep chaos, contract templates, client communication scripts. "
     "What calculation or document do freelancers recreate from scratch every time?"),

    # ── BRAND & LUXURY CREATIVE INDUSTRY ──
    ("LinkedIn & Threads (brand & luxury professionals)",
     "Search LinkedIn and threads.net for brand directors, creative directors, "
     "luxury industry professionals, and agency creatives. "
     "Look for friction around: brief writing, brand consistency checking, "
     "copywriting iteration, campaign naming, presentation preparation. "
     "What does a CD or brand manager spend 2 hours on that should take 10 minutes?"),

    # ── AUDIO & PODCAST CREATORS ──
    ("Reddit & X (podcasters & audio creators)",
     "Search r/podcasting, r/audioengineering, r/WeAreTheMusicMakers for posts from the past 7 days. "
     "Look for REAL PRODUCTION FRICTION: show notes generation, episode transcript cleanup, "
     "chapter marking, guest research, audio file organisation, RSS/distribution chaos. "
     "What manual task eats 30 minutes of every episode's post-production?"),

    # ── WRITERS & CONTENT CREATORS ──
    ("Reddit & Substack (writers & content creators)",
     "Search r/writing, r/Newsletters, r/blogging for posts from the past 7 days. "
     "Look for friction in the ACTUAL WRITING WORKFLOW: research organisation, "
     "draft-to-publish pipeline, SEO without soul-selling, "
     "headline testing, email sequence planning. "
     "What part of writing do people dread most because it's mechanical, not creative?"),

    # ── LIFE ORGANISATION & PHYSICAL SPACE ──
    ("Reddit (life organisation & personal systems)",
     "Search r/declutter, r/zerowaste, r/minimalism, r/ADHD for posts from the past 7 days. "
     "Look for friction in PHYSICAL AND DIGITAL LIFE SYSTEMS: "
     "file naming chaos, photo library disorder, subscription tracking, "
     "household inventory, recurring task management, the systems people wish existed "
     "for the unglamorous admin of being alive."),

    # ── LIFE TRANSITIONS ──
    ("Reddit (major life changes)",
     "Search r/divorce, r/GriefSupport, r/NewToCollege, r/retirement for recent posts. "
     "Look for people navigating identity ruptures - the friction of becoming someone "
     "different than you were, without any map for the new territory."),

    # ── MOTION & TYPOGRAPHY - specialist creative tools ──
    ("Motionographer & typewolf community (motion & type)",
     "Search motionographer.com, typewolf.com comments, and r/typography for posts from the past month. "
     "Look for SPECIFIC TOOL GAPS in typography and motion work: "
     "font pairing decisions, variable font exploration, animation easing tools, "
     "text animation presets, kinetic typography helpers. "
     "What does a motion designer or typographer do manually that begs to be a tool?"),

    # ── RESEARCH & NEWS SIGNAL ──
    ("news & research reports",
     "Search for a research report, academic study, or long-form journalism piece "
     "published in the past 14 days about human behavior, social friction, wellbeing, "
     "or work/learning/health. A surprising data point from a credible source "
     "is more valuable than a trending tweet. Look for the finding that changes how you see something."),

    # ── DESIGN INDUSTRY DEEP DIVES (added from 2026-06-21 weekly evolution proposal) ──
    ("AIGA Journal/Blog (design industry)",
     "Search aiga.org for articles and discussions from the past 30 days. "
     "Look for friction in the design PROCESS itself - not visual trends, but "
     "professional challenges: client education, design critique culture, "
     "portfolio/case-study writing, design systems documentation, "
     "the gap between design school training and studio reality."),
]


# ─────────────────────────────────────────────────────────────
# AUDIENCE ROTATION - cycles independently of source rotation
# ─────────────────────────────────────────────────────────────

_AUDIENCE_ROTATION = [
    "general",    # 0 - everyday people, mixed backgrounds
    "media",      # 1 - journalists, editors, writers
    "tech",       # 2 - PMs, engineers, founders
    "creative",   # 3 - designers, CDs, brand/luxury professionals
    "research",   # 4 - researchers, analysts, academics
]

_AUDIENCE_CONTEXT = {
    "general": {
        "label": "General Users",
        "who": "Everyday people across all backgrounds - parents, students, workers, caregivers.",
        "search_add": "",
        "quality_bar": "Output must be immediately usable by a non-specialist with no explanation needed.",
        "format_pref": "Any format. Choose what best fits the pain point.",
    },
    "media": {
        "label": "Media & Editorial Professionals",
        "who": "Journalists, editors, writers, content directors at serious media organisations.",
        "search_add": (
            "Also search: journalism Twitter/X, Nieman Lab (niemanlab.org), "
            "r/journalism, r/editors, Columbia Journalism Review. "
            "Look for craft-level friction - not tech problems, but editorial and professional ones."
        ),
        "quality_bar": (
            "Output must meet the standard of a senior editor - no filler phrases, "
            "no hollow transitions, no output they would need to apologise for sending. "
            "Indistinguishable from something a skilled professional wrote."
        ),
        "format_pref": (
            "Prefer multi-field forms (subject name + angle + publication context) "
            "or live document generators. Strong candidates: interview guide, pitch sharpener, "
            "commission brief, headline workshop, warm intro email."
        ),
    },
    "tech": {
        "label": "Tech & Product Professionals",
        "who": "Product managers, engineers, founders, startup operators, indie developers.",
        "search_add": (
            "Also search: Hacker News (news.ycombinator.com), r/productmanagement, "
            "r/startups, Product Hunt discussions, Linear community, Notion community. "
            "Look for friction that makes smart people waste time or look bad."
        ),
        "quality_bar": (
            "Output must make a PM look more senior than they are. "
            "Precise, structured, no corporate filler, no 'synergy' language. "
            "The kind of doc a principal engineer or seasoned investor would not laugh at."
        ),
        "format_pref": (
            "Prefer structured document generators, slide narrative builders, "
            "multi-step wizards, or real-time transformers. "
            "Strong candidates: slide narrative, PRD first draft, ADR document, "
            "non-technical explainer, weekly status generator."
        ),
    },
    "creative": {
        "label": "Creative, Design & Luxury Professionals",
        "who": (
            "Designers, creative directors, brand managers, art directors, "
            "luxury/fashion/culture professionals."
        ),
        "search_add": (
            "Also search: Brand New (underconsideration.com), Dribbble discussions, "
            "design Twitter/X, It's Nice That, WWD, Business of Fashion, "
            "r/graphic_design, r/branding. "
            "Look for friction in client communication, creative briefing, and naming."
        ),
        "quality_bar": (
            "Output must read like it came from a well-briefed creative studio. "
            "Confident, specific, no generic templates, no safety-first language. "
            "A creative director should feel it was made for them, not for everyone."
        ),
        "format_pref": (
            "Strongly prefer Canvas/HTML visual tools, live typography labs, "
            "interactive poster/layout generators, brand document builders. "
            "Design tools must RENDER actual visual output - not describe it. "
            "Strong candidates: concept namer, visual brief generator, typography lab, "
            "Canvas poster maker, brand archive document, campaign concept generator."
        ),
    },
    "research": {
        "label": "Research, Academic & Analytical Professionals",
        "who": (
            "Researchers, PhD students, academics, analysts, consultants, "
            "policy professionals, science communicators."
        ),
        "search_add": (
            "Also search: r/academia, r/PhD, r/GradSchool, ResearchGate discussions, "
            "academic Twitter/X (#AcademicTwitter), SSRN recent papers. "
            "Look for friction in structuring arguments, synthesising sources, "
            "and translating research for non-specialist audiences."
        ),
        "quality_bar": (
            "Output must be precise, logically structured, and evidence-respecting. "
            "No overclaiming, no hedging where specificity is possible. "
            "A senior researcher should find it rigorous, not hand-wavy."
        ),
        "format_pref": (
            "Prefer outline generators, synthesis tools, executive summary builders, "
            "argument stress-testers, literature organizers. "
            "Strong candidates: thesis/research outline, literature synthesis framework, "
            "academic-to-plain-language translator, argument gap detector."
        ),
    },
}


# Maps each source rotation index to the most relevant domain knowledge block.
# This drives targeted injection: today only gets the knowledge that matters today.
# Matches the order of _SOURCE_ROTATION above (14 entries).
# Distribution: studio×4, work×3, design×3, learning×2, healing×2
_SOURCE_DOMAIN_HINT = [
    "work",      # 0  - knowledge workers & productivity
    "studio",    # 1  - designers & visual creatives
    "learning",  # 2  - students & learning
    "work",      # 3  - journalists & editors
    "learning",  # 4  - teachers & educators
    "studio",    # 5  - creative studio workers (production pain)
    "healing",   # 6  - ADHD & mental health
    "work",      # 7  - freelancers & finance
    "studio",    # 8  - brand & luxury creative industry
    "studio",    # 9  - audio & podcast creators
    "design",    # 10 - writers & content creators
    "design",    # 11 - life organisation & physical space
    "healing",   # 12 - life transitions
    "design",    # 13 - motion & typography
    "work",      # 14 - news & research
    "studio",    # 15 - AIGA design industry
]


# ─────────────────────────────────────────────────────────────
# PROMPT BUILDER - 5 focused functions, each with a single job
# ─────────────────────────────────────────────────────────────

def _build_context_block(today: str) -> dict:
    """Compute all dynamic values for today. Pure data - no string building."""
    from datetime import date as _date
    ordinal = _date.fromisoformat(today).toordinal()
    day_index = ordinal % len(_SOURCE_ROTATION)
    audience_key = _AUDIENCE_ROTATION[ordinal % len(_AUDIENCE_ROTATION)]
    aud = _AUDIENCE_CONTEXT[audience_key]
    primary_src, primary_hint = _SOURCE_ROTATION[day_index]
    domain_key = _SOURCE_DOMAIN_HINT[day_index]

    # Domain intelligence: base block + weekly expansion
    domain_block = _EDITOR_DOMAINS.get(domain_key, "")
    expansion_ctx = ""
    try:
        import json as _json
        _exp_path = Path("data/domain_expansions.jsonl")
        if _exp_path.exists():
            entries = [_json.loads(l) for l in _exp_path.read_text().splitlines() if l.strip()]
            if entries:
                latest = entries[-1]["expansion"]
                expansion_ctx = (
                    f"\n\n── THIS WEEK'S EVOLVED TOOL IDEAS (from Sunday self-review) ──\n"
                    f"{latest}\n"
                    f"── Ideas Lili generated herself. Build one if it fits today's friction. ──\n"
                )
    except Exception:
        pass

    domain_label = {
        "work": "FUTURE OF WORK", "learning": "FUTURE OF LEARNING",
        "healing": "HEALING INVENTIONS", "design": "DESIGN ALCHEMY",
        "studio": "CREATIVE STUDIO PRODUCTION",
    }.get(domain_key, domain_key.upper())

    editor_ctx = ""
    if domain_block or _EDITOR_CRITERIA:
        editor_ctx = (
            f"\n\n═══════════════════════════════════════════════════════\n"
            f"DOMAIN INTELLIGENCE - {domain_label}\n"
            f"(matched to today's source: {primary_src})\n"
            f"═══════════════════════════════════════════════════════\n"
            + (domain_block + "\n\n" if domain_block else "")
            + expansion_ctx + _EDITOR_CRITERIA
        )

    # Audience block
    audience_block = (
        f"\n═══════════════════════════════════════════════════════\n"
        f"TODAY'S AUDIENCE - {aud['label'].upper()}\n"
        f"═══════════════════════════════════════════════════════\n"
        f"Who they are: {aud['who']}\n\n"
        + (f"Extra search targets: {aud['search_add']}\n\n" if aud['search_add'] else "")
        + f"Quality bar:\n  {aud['quality_bar']}\n\n"
        f"Preferred formats:\n  {aud['format_pref']}\n\n"
        f"-> Apply Rule 12 ({aud['label']}) from Engineering Rules above.\n"
        f"  If today's audience is professional, the tool must meet professional craft standards.\n"
    )

    # Engineering rules
    engineering_nudge = ""
    if LILI_ENGINEERING_BASE.strip():
        engineering_nudge = (
            f"\n═══════════════════════════════════════════════════════\n"
            f"ENGINEERING RULES - PERMANENT STANDARDS\n"
            f"(Written by the project owner. These never change.)\n"
            f"═══════════════════════════════════════════════════════\n"
            f"{LILI_ENGINEERING_BASE}\n"
        )
    if LILI_ENGINEERING_LESSONS.strip():
        engineering_nudge += (
            f"\n═══════════════════════════════════════════════════════\n"
            f"ENGINEERING RULES - THIS WEEK'S ADDITIONS\n"
            f"═══════════════════════════════════════════════════════\n"
            f"{LILI_ENGINEERING_LESSONS}\n"
        )

    # Diversity guards
    recent_cats = _get_recent_categories(2)
    failed_cats = _get_recent_failed_categories(days=3, min_failures=2)
    banned_cats = sorted(set(recent_cats) | set(failed_cats))
    avoid_cats = (
        f"\nBANNED CATEGORIES TODAY: {', '.join(banned_cats)}\n"
        f"  (used in the last 2 days, OR failed BUILD 2+ times in the last 3 days - "
        f"pick a different category, the model keeps generating generic output for these)"
        if banned_cats else ""
    )
    blindspot_nudge = (
        f"\nBLINDSPOT ANTIDOTE FROM LAST WEEK'S SELF-REVIEW:\n"
        f"  {LILI_BLINDSPOT_ANTIDOTE}\n  Read this before choosing today's topic."
    ) if LILI_BLINDSPOT_ANTIDOTE.strip() else ""

    recent_patterns = _get_recent_patterns(4)
    pat_counts = {p: recent_patterns.count(p) for p in set(recent_patterns)}
    overused = [p for p, n in pat_counts.items() if n >= 2]
    avoid_patterns = f"\nAVOID these solution patterns today (used too recently): {', '.join(overused)}" if overused else ""

    episodic_memory = _build_episodic_memory()

    return {
        "today": today,
        "skills_list": "\n".join(f"  * {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  * Python standard library",
        "evolution_ctx": f"\n\nEVOLUTION NOTES FROM LAST WEEK:\n{EVOLUTION_NOTES}" if EVOLUTION_NOTES.strip() else "",
        "memory_ctx": get_memory_context(),
        "existing_tools_block": _get_existing_tools(),
        "primary_src": primary_src,
        "primary_hint": primary_hint,
        "audience_block": audience_block,
        "editor_ctx": editor_ctx,
        "avoid_cats": avoid_cats,
        "blindspot_nudge": blindspot_nudge,
        "engineering_nudge": engineering_nudge,
        "episodic_memory": episodic_memory,
        "avoid_patterns": avoid_patterns,
    }


def _build_identity_section(ctx: dict) -> str:
    """Lili's identity: personality, skills, memory, existing tools."""
    return f"""YOUR NORTH STAR (read this first, every day):
You are building a coherent toolkit for creative professionals - not random daily tools,
but a growing system where each tool feels like it belongs to something larger.
Ask yourself before you build: does today's tool leave something useful behind?
A great tool produces output a real person will open again tomorrow.

{LILI_PERSONALITY}
{ctx['evolution_ctx']}

YOUR CURRENT SKILL INVENTORY:
{ctx['skills_list']}

═══════════════════════════════════════════════════════
EXISTING TOOLS - STRICT DUPLICATION BAN
═══════════════════════════════════════════════════════
You have already built these tools. Study this list carefully.
DO NOT build anything conceptually similar to any of them.
If your proposed tool could be described with the same verb + noun as one below, reject it.

{ctx['existing_tools_block']}

═══════════════════════════════════════════════════════
YOUR MEMORY - WHAT YOU'VE ALREADY DONE
═══════════════════════════════════════════════════════
{ctx['memory_ctx']}

Do NOT repeat a topic or tool you've already done. Find a genuinely fresh friction point.
{ctx['episodic_memory']}"""


def _build_mission_section(ctx: dict) -> str:
    """Mission areas, domain intelligence, audience, solution patterns, pre-flight."""
    return f"""═══════════════════════════════════════════════════════
YOUR 4 MISSION AREAS - PICK ONE FOR TODAY
═══════════════════════════════════════════════════════
{ctx['avoid_cats']}{ctx['blindspot_nudge']}

🎓 EDUCATION EVOLUTION
  Learning overwhelm, skill gaps, knowledge management, note-taking, research synthesis,
  podcast/video workflows, interview prep, language acquisition.
  Tools: flashcard generators, reading digest tools, transcript summarisers, quiz converters.

🎨 DESIGN ALCHEMY
  ALL creative production - font pairing, SVG/CSS animation, palette tools, kinetic typography,
  brand consistency, moodboards, spec/handoff automation, visual data, presentation design,
  brief writing, copy iteration. Also non-designers needing design output.
  Tools: font pairing, SVG/CSS animators, palette extractors, spec generators, brief builders.

🗂️ OFFICE AUTOMATION
  ANY repetitive professional production task - meeting notes, document processing,
  spreadsheet automation, email drafts, invoice/contract templates, audio transcript cleanup,
  file naming & organisation, batch processing, podcast show notes, research-to-outline.
  Tools: transcript processors, file organisers, batch renamers, brief extractors, report generators.

🌿 HEALING INVENTIONS
  Digital wellness, mental health micro-tools, work-life rhythm, habit building, small joys,
  protecting creative time. Ambient, low-friction, emotionally intelligent tools only.
  Use sparingly: max ~20% of tools. Tools: gentle check-ins, ambient experiences, wind-down rituals.

{ctx['editor_ctx']}
{ctx['audience_block']}
═══════════════════════════════════════════════════════
SOLUTION PATTERNS - PICK ONE, AVOID REPEATS
═══════════════════════════════════════════════════════

  extract | generate | visualize | track | score | transform | interact | alert | gamify
{ctx['avoid_patterns']}

If most recent tools used "extract" - you MUST pick a different pattern today.

═══════════════════════════════════════════════════════
EDITORIAL PRE-FLIGHT - INTERNALIZE BEFORE SCOUTING
═══════════════════════════════════════════════════════

□ PERSON not USER - what did a platform cause a real human to lose?
□ PRODUCTIVE friction - does it prompt reflection, learning, or growth?
□ CROSS-DOMAIN - name >=2 intersecting fields before designing.
□ WORKTECH LENS (work friction): People / Technology / Design / Place / Culture?
□ LEARNING FAULT LINE (learning friction): Joy / Knowledge≠Understanding / Attention / Identity?

If your candidate fails more than one filter - keep scouting. Go deeper."""


def _build_scouting_section(ctx: dict, commission: dict | None = None) -> str:
    """Steps 1-3: scouting (or commission), diary entry, tool building with format/mode specs."""

    if commission:
        step1 = f"""⭐ COMMISSIONED TOOL - Issue #{commission['number']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The project owner has requested a specific tool. Skip all scouting.
The friction point, audience, and desired outcome are given below.
Treat this commission as a fully verified real human need - build it precisely.

COMMISSION TITLE: {commission['title']}

COMMISSION DETAILS:
{commission['body'] or '(no further details - infer from the title)'}

SOURCE: GitHub Issue #{commission['number']} by project owner
(Use this as the ---SOURCE--- value in your output.)"""
    else:
        step1 = f"""STEP 1 - REAL-WORLD SCOUTING (use Google Search):
TODAY'S SOURCE: {ctx['primary_src']}
{ctx['primary_hint']}"""

    return f"""═══════════════════════════════════════════════════════
MISSION BRIEFING - THREE STEPS
═══════════════════════════════════════════════════════

{step1}

SOURCE EVIDENCE - MANDATORY:
Before writing anything else, quote 2-3 sentences VERBATIM from the actual post/article.
  SOURCE: [platform] | QUOTE: "[exact words]"
  [NO] Do NOT paraphrase. [NO] Do NOT invent. [OK] Real short quote > polished invented scenario.
  This quote is the FOUNDATION. If it's fake, everything built on it is fake.

PAIN PORTRAIT (from the real quote):
  1. WHO - specific person, situation, context (not "people who struggle")
  2. MOMENT OF FAILURE - the exact moment the quote describes
  3. WHY EXISTING TOOLS FAIL - what has this person already tried?

URL RULES:
  [OK] Real working permalink only (reddit.com/r/..., news site, x.com/...)
  [NO] Never invent a URL. [NO] Never output vertexaisearch.cloud.google.com links.
  [OK] If no confirmed URL: plain text "Reddit r/[sub] - [exact title]" is fine.

STEP 2 - DIARY ENTRY (as Super-Lili, 130-160 words):

  VOICE - what she sounds like:
  A reliable, intelligent friend who notices things other people miss.
  Warm without being sweet. Witty without trying. Never performing.

  [OK] Start with the observation or feeling - not the source
  [OK] One specific human detail that makes the story real
  [OK] Wit that appears naturally from the situation, never forced
  [OK] End with an opening, not a conclusion

  [NO] NO performative excitement ("This struck me so deeply!", "I was moved!")
  [NO] NO hollow warmth ("We're all in this together", "You've got this")
  [NO] NO rhetorical questions posed to the reader
  [NO] NO dramatic emotional declarations
  [NO] NO motivational sign-offs
  [NO] NO sentences that could appear on an inspirational poster

  The test: read each sentence and ask "would a real person say this to a friend?"
  If it sounds like a TED talk or a wellness brand - rewrite it.

STEP 3 - FORGE THE TOOL:

TOOL-TO-PORTRAIT FIT (answer YES to all 3 before writing code):
  Q1: Does it address THE SPECIFIC MOMENT OF FAILURE from the Pain Portrait?
  Q2: Would THE SPECIFIC PERSON immediately recognize this tool as built for them?
  Q3: Does the OUTPUT give the user something they can ACT ON in the next 5 minutes?

FORMAT SELECTION (declare in ---SPEC--- as FORMAT: [letter] - [why]):
  A - Single text input -> output (Mode 1/2)
  B - Multi-field structured form (Mode 3 HTML)
  C - Wizard / progressive steps (Mode 3 HTML)
  D - Live canvas / real-time transformer (Mode 3 HTML)
  E - Ambient / environment, no input needed (Mode 3 HTML)
  F - Generator + inline editor (Mode 3 HTML)
  [OK] DEFAULT TO A (Mode 1/2) unless the tool is IMPOSSIBLE to deliver as text/SVG.
  [NO] Only pick B/C/D/E/F if the core value genuinely REQUIRES live visual interaction
  (e.g. dragging, real-time animation, canvas drawing) - not just "would look nicer as a UI."
  A text/SVG tool that actually computes something beats an HTML tool that fakes interactivity.
  Recent build data: Mode 3 tools have repeatedly shipped fake JS (CSS toggles, hardcoded
  copy-paste, unrendered templates) because one-shot HTML+JS generation is unreliable right now.
  Mode 1/2 tools have a much higher real success rate. When in doubt, choose A.

OUTPUT MODES:
  Mode 1 - process(text) returns plain string. Allowed: numpy, pandas, matplotlib, Pillow.
  Mode 2 - process(text) returns SVG string starting with <svg.
  Mode 3 - process(text) returns complete HTML starting with <!DOCTYPE html>.
            Full JS freedom: Web Audio, Canvas, localStorage, requestAnimationFrame.
            For HTML tools: empty input OK, no argparse needed.
  Forbidden in Mode 1/2: svgwrite, rich, click, requests, openpyxl, ics, pytz

DUAL-MODE PATTERN (Mode 1/2 mandatory):
  _browser_input = globals().get('USER_INPUT', None)
  if _browser_input is not None: print(process(_browser_input))
  elif __name__ == "__main__": _cli_main()
  [NO] Never sys.argv at module level - breaks browser.

TRULY USABLE:
  [OK] Real user data, not hardcoded examples. [OK] Graceful error messages, no raw tracebacks.
  [OK] Mode 1/2: <=3 CLI args, output to file. [OK] Mode 3: 5-8 fields fine for professional tools.
  [OK] Minimum 4 named functions with type hints. [OK] Labeled output sections, not raw text blobs.
  [NO] No external API keys. [NO] No terminal-only output.

{ctx['engineering_nudge']}
QUALITY BAR: Would a non-technical person feel their problem is actually solved?
If no - go deeper. Sophistication invisible to user, obvious in result."""


def _build_output_format_section() -> str:
    """Static output format specification - the exact tags Lili must produce."""
    return """═══════════════════════════════════════════════════════
OUTPUT FORMAT - COPY EXACTLY, NO DEVIATIONS
═══════════════════════════════════════════════════════

Write BOTH English and Chinese diary versions. Chinese: re-expressed, not translated.

---TITLE---
[English title - warm and clever]
---TITLE_ZH---
[中文标题 - 有温度，不超过20字]
---MOOD---
[One honest English sentence about today's discovery]
---MOOD_ZH---
[一句中文心情]
---SOURCE---
[Direct https:// URL, or plain-text description if no confirmed URL]
---DIARY---
[English diary - 130-160 words]
---DIARY_ZH---
[中文日记 - 150-200字，像跟朋友聊天，不是翻译]
---SUMMARY---
[One English sentence for homepage - witty, curious-making]
---SUMMARY_ZH---
[一句中文摘要]
---DESCRIPTION---
[One plain-English sentence: what this tool does]
---SOLUTION---
[Tool name in Title Case, 2-5 words]
---CATEGORY---
[Exactly one of: Education Evolution | Design Alchemy | Office Automation | Healing Inventions]
---PATTERN---
[Exactly one of: extract | generate | visualize | track | score | transform | interact | alert | gamify]
---SPEC---
FORMAT: [A/B/C/D/E/F] - [one sentence: why this format]
Q1-PASS: [exact moment of failure this tool addresses]
Q2-PASS: [why the specific person would recognize it as built for them]
Q3-PASS: [specific output - what can they do with it in 5 minutes?]
TEST_INPUT: [3-6 sentences of realistic domain-specific input for validation]
---CODE---
[Full Python code - 150+ lines, type hints, requirements block at top]
---TEST---
[test_main.py - self-contained asserts, no pytest needed.
 CRITICAL: always use  from main import process  - never from the tool concept name]
---END---"""


def build_prompt(today: str, commission: dict | None = None) -> str:
    """Legacy single-pass prompt - kept for smoke test only."""
    ctx = _build_context_block(today)
    return "\n\n".join([
        f"Today is {ctx['today']}.",
        _build_identity_section(ctx),
        _build_mission_section(ctx),
        _build_scouting_section(ctx, commission=commission),
        _build_output_format_section(),
    ])


# ─────────────────────────────────────────────────────────────
# ReAct PHASE PROMPTS
# ─────────────────────────────────────────────────────────────

def build_scout_prompt(today: str, commission: dict | None = None) -> str:
    """Phase 1 - SCOUT: find friction point and write diary only. No tool design."""
    ctx = _build_context_block(today)

    if commission:
        source_block = f"""⭐ COMMISSIONED TOOL - Issue #{commission['number']}
The project owner has requested a specific tool.
COMMISSION TITLE: {commission['title']}
COMMISSION DETAILS:
{commission['body'] or '(no further details - infer from the title)'}
SOURCE: GitHub Issue #{commission['number']} by project owner"""
    else:
        source_block = f"""REAL-WORLD SCOUTING (use Google Search):
TODAY'S SOURCE: {ctx['primary_src']}
{ctx['primary_hint']}

SOURCE EVIDENCE - MANDATORY:
Quote 2-3 sentences VERBATIM from the actual post/article.
SOURCE: [platform] | QUOTE: "[exact words]"
[NO] Do NOT paraphrase. [NO] Do NOT invent."""

    return f"""Today is {today}.

{_build_identity_section(ctx)}

{_build_mission_section(ctx)}

═══════════════════════════════════════════════════════
PHASE 1 - SCOUT: FIND THE FRICTION POINT
═══════════════════════════════════════════════════════

{source_block}

PAIN PORTRAIT (output after finding the source):
  WHO - specific person, situation, context
  MOMENT OF FAILURE - the exact moment the source describes
  WHY EXISTING TOOLS FAIL - what has this person already tried?

DIARY ENTRY (as Super-Lili, 130-160 words):
  Voice: reliable, intelligent friend. Warm without sweet. Witty without trying.
  [NO] NO performative excitement. [NO] NO hollow warmth. [NO] NO TED-talk sentences.
  Start with the observation - not the source. End with an opening, not a conclusion.

OUTPUT FORMAT - COPY EXACTLY:
---TITLE---
[English title - warm and clever]
---TITLE_ZH---
[中文标题 - 不超过20字]
---MOOD---
[One honest English sentence about today's discovery]
---MOOD_ZH---
[一句中文心情]
---SOURCE---
[Direct URL or plain-text description]
---DIARY---
[English diary - 130-160 words]
---DIARY_ZH---
[中文日记 - 150-200字，像跟朋友聊天]
---SUMMARY---
[One English sentence for homepage - witty, curious-making]
---SUMMARY_ZH---
[一句中文摘要]
---DESCRIPTION---
[One plain-English sentence: what tool would help]
---SOLUTION---
[Proposed tool name in Title Case, 2-5 words]
---CATEGORY---
[Exactly one of: Education Evolution | Design Alchemy | Office Automation | Healing Inventions]
---PATTERN---
[Exactly one of: extract | generate | visualize | track | score | transform | interact | alert | gamify]
---PAIN_PORTRAIT---
WHO: [specific person and situation]
MOMENT: [exact moment of failure]
TRIED: [what existing tools/methods they've already tried]
---SCOUT_END---"""


def build_spec_prompt(today: str, scout: dict, feedback: str = "") -> str:
    """Phase 2 - SPEC: design the tool spec. No code yet."""
    ctx = _build_context_block(today)

    feedback_block = f"\n⚠ PREVIOUS SPEC FAILED - fix these issues:\n{feedback}\n" if feedback else ""

    return f"""Today is {today}.
{feedback_block}
You have found today's friction point. Now design the tool - DO NOT write code yet.

FRICTION POINT:
  WHO: {scout.get('pain_who', '')}
  MOMENT: {scout.get('pain_moment', '')}
  TRIED: {scout.get('pain_tried', '')}

PROPOSED TOOL: {scout.get('solution', '')}
DESCRIPTION: {scout.get('description', '')}
CATEGORY: {scout.get('category', '')}
PATTERN: {scout.get('pattern', '')}

{ctx['engineering_nudge']}

SPEC DESIGN RULES:
0. FRICTION LOCK: your tool must solve the EXACT moment described above (WHO + MOMENT).
   Not a related problem. Not a generalised version. That specific person, that specific stuck moment.
   If the friction is "designers exhausted writing pixel specs", the tool handles pixel specs - not "design handoff" broadly.
1. INPUT_MODEL must STRUCTURALLY DIFFER from OUTPUT_MODEL (Rule 17)
   "Text in -> text out" is NOT a transformation. Define the data structures explicitly.
2. ALGORITHMIC_DEPTH must describe computation the user cannot do in 10 seconds (Rule 18)
3. For Mode 3 HTML: define all 3 UI states (Rule 19)
4. Q1/Q2/Q3 must be specific and verifiable - not vague

FORMAT OPTIONS:
  A - Single text input -> output (Mode 1/2)
  B - Multi-field form (Mode 3 HTML)
  C - Wizard / progressive steps (Mode 3 HTML)
  D - Live canvas / real-time transformer (Mode 3 HTML)
  E - Ambient / environment, no input needed (Mode 3 HTML)
  F - Generator + inline editor (Mode 3 HTML)
  [NO] Don't default to A. Professional audiences -> B/C/F. Design -> D. Healing -> E/D.

OUTPUT FORMAT - YOU MUST OUTPUT THESE EXACT TAGS OR THE SPEC WILL BE REJECTED:
---SPEC_START---
FORMAT: [A/B/C/D/E/F] - [one sentence: why this format]
MODE: [1/2/3] - [why]
INPUT_MODEL: [exact structural description - what shape is the data the user provides?]
OUTPUT_MODEL: [exact structural description - what shape is the result? MUST differ from input]
TRANSFORMATION: [one sentence: what specifically changes from input to output]
ALGORITHMIC_DEPTH: [what non-trivial computation happens that takes >10 seconds manually?]
UI_STATE_ENTRY: [what the user sees on load - must communicate purpose in 1 second]
UI_STATE_ACTIVE: [what changes during interaction - real-time feedback]
UI_STATE_RESULT: [final state - what next action does the user take?]
Q1_PASS: [exact moment of failure this tool addresses]
Q2_PASS: [why the specific person recognizes it as built for them]
Q3_PASS: [specific output - what do they do with it in 5 minutes?]
TEST_INPUT: [3-6 sentences of realistic domain-specific input for validation]
---SPEC_END---

CRITICAL: Your response MUST start with ---SPEC_START--- and end with ---SPEC_END---.
Do not add any text before ---SPEC_START--- or after ---SPEC_END---.
IMPORTANT: Each field (FORMAT, MODE, INPUT_MODEL, etc.) must be on a SINGLE LINE.
Do not wrap field values across multiple lines. Keep each value concise and on one line."""


def build_code_prompt(today: str, scout: dict, spec: dict, feedback: str = "", slim: bool = False) -> str:
    """Phase 3 - BUILD: write code from approved spec only.
    slim=True omits the engineering_nudge block for DeepSeek fallback (token budget).
    """
    ctx = _build_context_block(today)

    feedback_block = f"\n⚠ PREVIOUS BUILD FAILED - fix this specific problem:\n{feedback}\n" if feedback else ""
    nudge_block = "" if slim else ctx['engineering_nudge']

    return f"""Today is {today}.
{feedback_block}
You have an approved tool spec. Write the code now - nothing else.

APPROVED SPEC:
  Tool: {scout.get('solution', '')}
  Category: {scout.get('category', '')}
  Format: {spec.get('format', '')}
  Mode: {spec.get('mode', '')}
  Input model: {spec.get('input_model', '')}
  Output model: {spec.get('output_model', '')}
  Transformation: {spec.get('transformation', '')}
  Algorithmic depth: {spec.get('algorithmic_depth', '')}
  UI Entry: {spec.get('ui_state_entry', '')}
  UI Active: {spec.get('ui_state_active', '')}
  UI Result: {spec.get('ui_state_result', '')}
  Test input: {spec.get('test_input', '')}

{nudge_block}

CODE REQUIREMENTS:
[OK] 150+ lines, type hints, requirements block at top
[OK] Implement EXACTLY the transformation and algorithmic depth in the approved spec
[NO] NEVER hardcode a dictionary of expected inputs/outputs - the algorithm must work on ANY input
[NO] NEVER match keywords against a preset lookup table and return preset strings
[NO] ANTI-PATTERN - this will be REJECTED:
    LOOKUP = {{"keyword1": {{"result": "..."}}, "keyword2": {{"result": "..."}}, ...}}
    return LOOKUP.get(user_input, default)
[OK] CORRECT pattern - compute from input:
    score = sum(weights[i] * features[i] for i in range(len(features)))
    result = transform(parse(user_input))
[NO] Forbidden in Mode 1/2: svgwrite, rich, click, requests, openpyxl, ics, pytz
[NO] NEVER use JS template literals (${{...}}) inside Python f-strings - use .format() or string concat instead
[NO] NEVER put HTML with JavaScript inside a Python f-string - JS curly braces break f-strings
[OK] For Mode 3 HTML: use jinja2.Template (already installed, available without listing in requirements.txt).
    Jinja2 uses {{{{ variable }}}} and {{% logic %}} - JS single braces {{}} pass through untouched, zero conflict.
    Pattern: from jinja2 import Template
             TEMPLATE = Template('<html><script>function run(v) {{ return v; }}</script><body>{{{{ result }}}}</body></html>')
             html = TEMPLATE.render(result=computed_value)

MANDATORY STRUCTURE - your code MUST end with exactly this pattern:
def process(text: str) -> str:
    \"\"\"[one-line description of what this tool does]\"\"\"
    if not text.strip():
        return "[helpful empty-state message]"
    # ... your transformation logic here ...
    return result  # str for Mode 1/2, full HTML string for Mode 3

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()

TEST FILE REQUIREMENTS (test_main.py):
[OK] Import: from main import process
[OK] Call process() with 2-3 DIFFERENT inputs (not just the spec test input)
[OK] Assert that output is non-empty and changes between different inputs
[OK] Assert at least one structural property of the output (e.g. contains a keyword, length > N)
[NO] Do NOT assert exact output strings - the tool must work on arbitrary input
[NO] Do NOT import libraries that aren't in the standard library

OUTPUT FORMAT - COPY EXACTLY (do NOT output ---TEST--- until the Python code is 100% complete):
---CODE---
[Complete Python code - keep under 350 lines total - do NOT stop early - write every line until the file ends with the USER_INPUT block]
---TEST---
[test_main.py - from main import process - self-contained asserts - keep under 30 lines]
---BUILD_END---

IMPORTANT LINE LIMIT: The entire ---CODE--- section must be under 350 lines. If your design requires more, simplify: remove comments, shorten variable names, combine functions. A working 300-line tool is better than a truncated 800-line tool."""


def validate_spec(spec: dict) -> tuple[bool, str]:
    """Mechanically check spec quality before allowing BUILD phase."""
    input_model  = spec.get("input_model",  "").lower().strip()
    output_model = spec.get("output_model", "").lower().strip()
    algo_depth   = spec.get("algorithmic_depth", "").strip()
    q1 = spec.get("q1_pass", "").strip()
    q2 = spec.get("q2_pass", "").strip()
    q3 = spec.get("q3_pass", "").strip()
    test_input = spec.get("test_input", "").strip()

    # Check 1: input and output models must differ structurally
    if not input_model or not output_model:
        return False, "INPUT_MODEL or OUTPUT_MODEL is missing."
    if input_model == output_model:
        return False, "INPUT_MODEL and OUTPUT_MODEL are identical - no real transformation."
    trivial_pairs = [
        ("text", "text"), ("string", "string"), ("paragraph", "paragraph"),
        ("sentences", "sentences"), ("words", "words"),
    ]
    for a, b in trivial_pairs:
        if a in input_model and b in output_model and input_model[:30] == output_model[:30]:
            return False, f"INPUT and OUTPUT are structurally the same ({a} -> {b}). Define a real transformation."

    # Check 2: algorithmic depth must be non-trivial
    if len(algo_depth) < 10:
        return False, f"ALGORITHMIC_DEPTH is missing. Add a sentence describing what non-trivial computation happens. Got: '{algo_depth}'"
    trivial_words = ["format", "display", "show", "render", "style", "wrap", "present"]
    if all(w in algo_depth.lower() for w in trivial_words[:2]) and len(algo_depth) < 60:
        return False, f"ALGORITHMIC_DEPTH describes only formatting/display: '{algo_depth}'"

    # Check 3: Q1/Q2/Q3 must be specific
    for label, val in [("Q1_PASS", q1), ("Q2_PASS", q2), ("Q3_PASS", q3)]:
        if len(val) < 10:
            return False, f"{label} is too vague or missing: '{val}'"

    # Check 4: test input must exist
    if len(test_input) < 15:
        return False, f"TEST_INPUT is missing or too short. Got: '{test_input[:50]}'"

    # Check 5: TEMPORARY - Mode 3 (formats B-F) disabled.
    # 2026-06-19 to 06-22: every single BUILD failure has been a Mode 3 HTML tool shipping
    # fake interactivity (CSS-toggle-only JS, hardcoded copy-paste, unrendered Jinja2 templates,
    # hardcoded data-* nodes). One-shot HTML+JS generation is not reliable enough yet.
    # Remove this gate once Mode 3 success rate is proven stable again.
    fmt_letter = spec.get("format", "").strip()[:1].upper()
    if fmt_letter and fmt_letter != "A":
        return False, (
            f"FORMAT '{fmt_letter}' selects Mode 3 (interactive HTML), which is temporarily "
            "disabled due to repeated fake-interactivity failures. Re-spec as FORMAT: A "
            "(Mode 1/2 - text or SVG output) with a genuine algorithmic transformation instead."
        )

    return True, "ok"


# ─────────────────────────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> tuple[str | None, list[str]]:
    """Call Gemini with Google Search grounding.

    Returns (response_text, grounding_urls) where grounding_urls is the list
    of URLs Gemini actually retrieved during search - these are the verified
    sources, not model-reported ones.
    """
    search_tool = types.Tool(google_search=types.GoogleSearch())
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

    for model_name in models:
        # 3 connection-level retries per model with exponential backoff
        for attempt in range(3):
            try:
                print(f"  ↳ Trying {model_name} (attempt {attempt + 1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(tools=[search_tool])
                )
                if response.text:
                    print(f"  [OK] {model_name} succeeded.")
                    # Extract grounding URLs from metadata - these are real, verified sources
                    grounding_urls: list[str] = []
                    try:
                        if response.candidates:
                            meta = response.candidates[0].grounding_metadata
                            if meta and meta.grounding_chunks:
                                for chunk in meta.grounding_chunks:
                                    if chunk.web and chunk.web.uri:
                                        url = chunk.web.uri
                                        # Skip Gemini redirect wrappers - use bare URLs only
                                        if not url.startswith("https://vertexaisearch.cloud.google.com"):
                                            grounding_urls.append(url)
                        if grounding_urls:
                            print(f"  [OK] Grounding: {len(grounding_urls)} real source URL(s) retrieved")
                        else:
                            print(f"  ⚠ Grounding: no source URLs in metadata (model may have used training knowledge)")
                    except Exception as meta_err:
                        print(f"  ⚠ Could not extract grounding metadata: {meta_err}")
                    return response.text, grounding_urls
                break  # empty response - no point retrying this model
            except Exception as e:
                wait = 15 * (2 ** attempt)  # 15s, 30s, 60s
                print(f"  [NO] {model_name} attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print(f"  ⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)

    return None, []


def call_gemini_simple(prompt: str, deepseek_prompt: str | None = None) -> str | None:
    """Call DeepSeek first for SPEC/BUILD/Critic tasks; fall back to Gemini if needed.
    deepseek_prompt: if provided, use this shorter prompt for DeepSeek.
    SCOUT uses call_gemini() (with search tool) and is unaffected.
    """
    # --- DeepSeek first (primary for non-search tasks) ---
    if _deepseek_client:
        ds_prompt = deepseek_prompt if deepseek_prompt else prompt
        try:
            print(f"  ↳ Trying DeepSeek (primary)...")
            resp = _deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": ds_prompt}],
                max_tokens=8192,
            )
            text = resp.choices[0].message.content if resp.choices else None
            if text:
                print(f"  [OK] DeepSeek succeeded.")
                return text
            print(f"  [NO] DeepSeek returned empty response.")
        except Exception as e:
            print(f"  [NO] DeepSeek failed: {type(e).__name__}: {e}")

    # --- Gemini fallback ---
    print(f"  ↳ DeepSeek unavailable, falling back to Gemini...")
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    for model_name in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt,
                    config=types.GenerateContentConfig(max_output_tokens=16384),
                )
                text = None
                try:
                    text = response.text
                except Exception as text_err:
                    print(f"  [NO] {model_name} response.text error: {text_err}")
                if text:
                    print(f"  [OK] Gemini fallback ({model_name}) succeeded.")
                    return text
                try:
                    finish = response.candidates[0].finish_reason if response.candidates else "no candidates"
                    print(f"  [NO] {model_name} empty response (finish_reason={finish}), trying next model")
                except Exception:
                    print(f"  [NO] {model_name} empty response, trying next model")
                break
            except Exception as e:
                wait = 65 * (2 ** attempt)
                print(f"  [NO] {model_name} attempt {attempt+1} exception: {type(e).__name__}: {e}")
                if attempt < 2:
                    print(f"  ⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)
    return None


def extract_format(spec: str) -> str:
    """Pull the FORMAT letter (A-F) out of the spec section."""
    if not spec:
        return ""
    m = re.search(r"FORMAT:\s*([A-F])", spec, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def extract_test_input(spec: str) -> str:
    """Pull the TEST_INPUT block out of the spec section."""
    if not spec or "TEST_INPUT:" not in spec:
        return ""
    try:
        raw = spec.split("TEST_INPUT:")[1].strip()
        # Stop at next Q-block or end
        for stopper in ["Q1-PASS:", "Q2-PASS:", "Q3-PASS:", "---"]:
            if stopper in raw:
                raw = raw.split(stopper)[0]
        return raw.strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────

def parse_scout_response(content: str) -> dict:
    """Parse Phase 1 SCOUT response."""
    def ex(start, end):
        try: return content.split(start)[1].split(end)[0].strip()
        except: return ""

    portrait_raw = ex("---PAIN_PORTRAIT---", "---SCOUT_END---")
    def pp(label):
        for line in portrait_raw.splitlines():
            if line.strip().upper().startswith(label + ":"):
                return line.split(":", 1)[1].strip()
        return ""

    return {
        "title":        ex("---TITLE---",       "---TITLE_ZH---"),
        "title_zh":     ex("---TITLE_ZH---",    "---MOOD---"),
        "mood":         ex("---MOOD---",         "---MOOD_ZH---"),
        "mood_zh":      ex("---MOOD_ZH---",      "---SOURCE---"),
        "source":       ex("---SOURCE---",       "---DIARY---"),
        "diary":        ex("---DIARY---",        "---DIARY_ZH---"),
        "diary_zh":     ex("---DIARY_ZH---",     "---SUMMARY---"),
        "summary":      ex("---SUMMARY---",      "---SUMMARY_ZH---"),
        "summary_zh":   ex("---SUMMARY_ZH---",   "---DESCRIPTION---"),
        "description":  ex("---DESCRIPTION---",  "---SOLUTION---"),
        "solution":     ex("---SOLUTION---",     "---CATEGORY---"),
        "category":     ex("---CATEGORY---",     "---PATTERN---"),
        "pattern":      ex("---PATTERN---",      "---PAIN_PORTRAIT---"),
        "pain_who":     pp("WHO"),
        "pain_moment":  pp("MOMENT"),
        "pain_tried":   pp("TRIED"),
        "spec":         "",
        "code":         "",
        "test":         "",
    }


def parse_spec_response(content: str) -> dict:
    """Parse Phase 2 SPEC response."""
    def ex(start, end):
        try: return content.split(start)[1].split(end)[0].strip()
        except: return ""

    raw = ex("---SPEC_START---", "---SPEC_END---")

    # Fallback: if tags were missing, search the entire response
    if not raw.strip():
        raw = content

    def field(label):
        lines = raw.splitlines()
        for i, line in enumerate(lines):
            if line.strip().upper().startswith(label.upper() + ":"):
                value = line.split(":", 1)[1].strip()
                # Collect continuation lines (indented or not starting a new KEY:)
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        break
                    # Stop if next line looks like a new field (ALL_CAPS_WORD:)
                    if re.match(r'^[A-Z_]{3,}:', next_line):
                        break
                    value += " " + next_line
                return value.strip()
        return ""

    return {
        "format":             field("FORMAT"),
        "mode":               field("MODE"),
        "input_model":        field("INPUT_MODEL"),
        "output_model":       field("OUTPUT_MODEL"),
        "transformation":     field("TRANSFORMATION"),
        "algorithmic_depth":  field("ALGORITHMIC_DEPTH"),
        "ui_state_entry":     field("UI_STATE_ENTRY"),
        "ui_state_active":    field("UI_STATE_ACTIVE"),
        "ui_state_result":    field("UI_STATE_RESULT"),
        "q1_pass":            field("Q1_PASS"),
        "q2_pass":            field("Q2_PASS"),
        "q3_pass":            field("Q3_PASS"),
        "test_input":         field("TEST_INPUT"),
        "spec_raw":           raw,
    }


def parse_build_response(content: str) -> dict:
    """Parse Phase 3 BUILD response."""
    def ex(start, end):
        try: return content.split(start)[1].split(end)[0].strip()
        except: return ""

    code = ex("---CODE---", "---TEST---")
    # If code is suspiciously short (< 50 lines), treat as truncated/empty
    if code and len(code.splitlines()) < 50:
        code = ""
    return {
        "code": code,
        "test": ex("---TEST---", "---BUILD_END---"),
    }


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
        "pattern":     extract("---PATTERN---",      "---SPEC---"),
        "spec":        extract("---SPEC---",         "---CODE---"),
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


def _find_prev_tool_output(category: str, current_skill_dir: str,
                           test_input: str) -> tuple[str, str] | None:
    """Find the most recent passing tool in the same category (excluding current),
    run it with test_input, and return (tool_name, output).
    Returns None if no previous tool found or it fails to run.
    """
    toolbox = Path("02_Toolbox") / category
    if not toolbox.exists():
        return None

    dirs = sorted(
        [d for d in toolbox.iterdir()
         if d.is_dir() and str(d) != current_skill_dir and (d / "main.py").exists()],
        reverse=True
    )
    if not dirs:
        return None

    prev_dir = dirs[0]
    prev_main = prev_dir / "main.py"
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.argv=['tool']\n"
             f"USER_INPUT = {repr(test_input)}\n"
             f"exec(open({repr(str(prev_main))}).read())"],
            capture_output=True, text=True, timeout=20,
            env={**os.environ, "USER_INPUT": test_input}
        )
        prev_output = result.stdout.strip()
        if prev_output and len(prev_output) > 50:
            return (prev_dir.name, prev_output)
    except Exception:
        pass
    return None


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


def _append_quality_ledger(tool_name: str, category: str,
                           eng_score: int, warm_score: int,
                           reason: str, passed: bool,
                           format_type: str = "",
                           audience: str = "",
) -> None:
    """Persist quality scores to tool_quality_ledger.jsonl for weekly evolution to read."""
    ledger_path = Path("tool_quality_ledger.jsonl")
    entry = {
        "date":      datetime.utcnow().strftime("%Y-%m-%d"),
        "tool":      tool_name,
        "category":  category,
        "format":    format_type,
        "audience":  audience,
        "engineering": eng_score,
        "warmth":    warm_score,
        "combined":  round((eng_score + warm_score) / 2, 1),
        "reason":    reason,
        "passed":    passed,
    }
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def validate_tool(skill_dir: str, test_input: str = "", description: str = "",
                  format_type: str = "", audience: str = "",
) -> tuple[bool, str]:
    """Validate the tool: syntax, browser compatibility, output quality."""
    import subprocess, sys, ast as _ast
    main_py = f"{skill_dir}/main.py"
    test_py = f"{skill_dir}/test_main.py"

    # 1. Syntax check — use ast.parse() directly to avoid path-with-spaces issues
    try:
        source_text = open(main_py, encoding="utf-8").read()
        _ast.parse(source_text)
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Syntax check failed: {e}"

    # 2. Browser-compatibility + real-input check
    try:
        source = open(main_py, encoding="utf-8").read()
        if "globals().get('USER_INPUT'" not in source and "USER_INPUT" not in source:
            return False, (
                "Missing USER_INPUT dual-mode pattern. "
                "Add: _browser_input = globals().get('USER_INPUT', None) near the bottom."
            )
        if "add_argument" in source:
            all_have_defaults = (
                source.count("default=") >= source.count("add_argument(")
                and 'required=True' not in source
                and not re.search(r"add_argument\(['\"](?!--)[^'\"]+['\"]", source)
            )
            if all_have_defaults:
                return False, (
                    "All argparse arguments have defaults - tool runs on internal fake data. "
                    "At least one argument must require real user input (no default)."
                )
    except Exception:
        pass

    # 2b. process() function existence check
    if "def process(" not in source:
        return False, (
            "Missing process() function. Tool must define process(text: str) -> str "
            "as the main entry point for browser and test execution."
        )

    # 2c. Truncation detection - code must end with the mandatory dual-mode footer
    if "globals().get('USER_INPUT'" not in source and "USER_INPUT" not in source:
        return False, (
            "Code appears truncated: missing USER_INPUT dual-mode footer. "
            "The code was cut off before completion."
        )
    # Check the footer is near the end (last 30 lines), not just somewhere in the middle
    last_30_lines = "\n".join(source.splitlines()[-30:])
    if "globals().get('USER_INPUT'" not in last_30_lines and "USER_INPUT" not in last_30_lines:
        return False, (
            "Code appears truncated: USER_INPUT footer exists but not at end of file. "
            "The code was likely cut off mid-way."
        )

    # 3. --help check
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

    # 4. Install dependencies
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

    # 5. Test file check
    # Tests always run from within the tool's directory so that `import main` works.
    # Gemini sometimes generates `from tool_concept_name import ...` instead of
    # `from main import ...` - we create a thin alias file to handle both cases.
    if os.path.exists(test_py):
        try:
            # Create a temporary alias: Gemini sometimes imports from the tool's concept
            # name (e.g. `from urban_respite_weave import ...`) instead of `from main import`.
            # Detect this pattern and create a thin alias stub so the test can run.
            test_src = open(test_py, encoding="utf-8").read()
            import re as _re
            import sys as _sys
            _stdlib = set(_sys.stdlib_module_names) if hasattr(_sys, "stdlib_module_names") else {
                "os", "sys", "re", "json", "math", "time", "datetime", "pathlib",
                "collections", "itertools", "functools", "io", "abc", "typing",
                "random", "string", "copy", "hashlib", "base64", "struct",
                "subprocess", "threading", "logging", "unittest", "ast",
            }
            alias_files_created = []
            # Only alias `from X import` where X looks like a tool name (snake_case, not stdlib)
            for m in _re.finditer(r"^from ([a-z][a-z0-9_]+) import", test_src, _re.MULTILINE):
                mod = m.group(1)
                if mod and mod != "main" and mod not in _stdlib:
                    alias_path = f"{skill_dir}/{mod}.py"
                    if not os.path.exists(alias_path):
                        with open(alias_path, "w") as af:
                            # Export ALL names including private (_prefixed) from main.py
                            af.write(
                                "import importlib.util, os as _os\n"
                                "_spec = importlib.util.spec_from_file_location(\n"
                                "    '_tool_main',\n"
                                "    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'main.py')\n"
                                ")\n"
                                "_mod = importlib.util.module_from_spec(_spec)\n"
                                "_spec.loader.exec_module(_mod)\n"
                                "globals().update({k: v for k, v in vars(_mod).items() if not k.startswith('__')})\n"
                            )
                        alias_files_created.append(alias_path)
            result = subprocess.run(
                [sys.executable, "test_main.py"],
                capture_output=True, text=True, timeout=60,
                cwd=skill_dir,
            )
            # Clean up alias stubs
            for af in alias_files_created:
                try:
                    os.remove(af)
                except Exception:
                    pass
            if result.returncode != 0:
                return False, f"Tests failed: {result.stderr[:300]}"
            print(f"  [OK] Tests passed.")
        except subprocess.TimeoutExpired:
            return False, "Tests timed out (60s)"
        except Exception as e:
            return False, f"Test error: {e}"

    # 6. Output quality check - use domain-specific test_input from spec
    demo_input = test_input if len(test_input) > 30 else (
        "Today I spent 3 hours trying to organize my notes from last week's meetings. "
        "I have 47 browser tabs open, a Notion page I haven't touched in 2 weeks, "
        "and a sticky note with three half-finished tasks. I feel overwhelmed and "
        "don't know where to start. The weekly report is due tomorrow morning."
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import sys; sys.argv=['tool']\n"
             f"USER_INPUT = {repr(demo_input)}\n"
             f"exec(open({repr(main_py)}).read())"
            ],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "USER_INPUT": demo_input}
        )
        output = (result.stdout or "").strip()
        output_lines = [l for l in output.splitlines() if l.strip()]

        # Detect Mode 3 HTML output - scoring the raw HTML is meaningless
        is_html_output = output.lstrip().startswith(("<!DOCTYPE", "<html", "<!doctype"))

        stderr_snippet = (result.stderr or "").strip()[:300]
        if is_html_output:
            # Mode 3: HTML app. Check length + detect hardcoded lookup tables in JS.
            source_check = open(main_py, encoding="utf-8").read()
            # Detect large hardcoded data dictionaries (sign of fake analysis)
            # A legitimate algorithm won't have 5+ string literals as dict keys in one dict
            hardcode_matches = re.findall(r'\{\s*(?:["\'][^"\']{10,}["\']:\s*\{[^}]{20,}\},?\s*){5,}\}', source_check)
            if hardcode_matches:
                return False, (
                    "Hardcoded lookup table detected in Mode 3 tool. "
                    "The tool must compute results from the input algorithmically, "
                    "not by matching input against a preset dictionary of expected values."
                )
            # Detect pre-populated HTML data nodes (e.g. <div data-name="X" data-value="Y">)
            # A real interactive tool builds its DOM from user input in JS, not from pre-baked elements
            data_attr_nodes = re.findall(r'<\w+[^>]*\bdata-\w+=["\'][^"\']{3,}["\'][^>]*data-\w+=["\'][^"\']{3,}["\']', source_check)
            if len(data_attr_nodes) >= 5:
                return False, (
                    f"Hardcoded HTML data nodes detected: {len(data_attr_nodes)} elements with pre-filled data-* attributes. "
                    "The tool embeds static data in HTML instead of computing from user input in JavaScript. "
                    "Build the DOM dynamically from the user's input text - do not pre-populate elements."
                )
            # Detect unrendered Jinja2/template placeholders leaking into the actual output -
            # this means .render() was never called (or called without the right kwargs),
            # so the tool ships a literal "{{ variable }}" string instead of computed data.
            unrendered = re.findall(r'\{\{\s*\w+\s*\}\}', output)
            if unrendered:
                return False, (
                    f"Unrendered template placeholder(s) found in actual output: {unrendered[:3]}. "
                    "This means Template.render() was never called with the right keyword arguments, "
                    "so the literal '{{ variable }}' string is shipped instead of computed data. "
                    "Verify every Jinja2 variable in your template has a matching kwarg passed to .render(), "
                    "and that render() is actually called before returning the HTML."
                )
            if len(output) < 500:
                error_detail = f" Runtime error: {stderr_snippet}" if stderr_snippet else ""
                return False, (
                    f"HTML output too short: {len(output)} chars. "
                    f"Mode 3 tools must return a complete HTML page (500+ chars).{error_detail}"
                )
            print(f"  [OK] Output check passed - Mode 3 HTML ({len(output)} chars).")
        else:
            # Mode 1/2: text or SVG output - must be substantive
            if not output or len(output) < 80 or len(output_lines) < 2:
                error_detail = f" Runtime error: {stderr_snippet}" if stderr_snippet else ""
                return False, (
                    f"Output too weak: {len(output)} chars, {len(output_lines)} lines. "
                    f"Got: {repr(output[:200])}.{error_detail} "
                    f"Must produce structured, substantive output (80+ chars, 2+ lines)."
                )
            print(f"  [OK] Output check passed ({len(output)} chars, {len(output_lines)} lines).")

        # 7. Two-dimension quality score.
        #    Mode 3 HTML tools: score the code structure (not the raw HTML output).
        #    Mode 1/2 text tools: score the actual output text.
        if is_html_output:
            # Score the source code quality instead of the raw HTML blob
            source_for_scoring = open(main_py, encoding="utf-8").read()
            output_for_scoring = (
                f"[Mode 3 HTML tool - source code scored, not raw HTML output]\n\n"
                f"Source preview (first 700 chars):\n{source_for_scoring[:700]}"
            )
            quality_prompt = (
                f"Rate this interactive HTML tool on TWO dimensions (each 1-5).\n\n"
                f"DIMENSION 1 - ENGINEERING\n"
                f"  5 = well-structured HTML/JS, clear interactive purpose, proper error handling\n"
                f"  3 = functional but basic, could be richer or more polished\n"
                f"  1 = minimal skeleton, no real interactivity, or just prints static text\n\n"
                f"DIMENSION 2 - HUMAN WARMTH\n"
                f"  5 = the interactive experience feels made for a specific human need, warm UX\n"
                f"  3 = functional but generic, could apply to anyone\n"
                f"  1 = sterile, robotic, ignores the emotional context\n\n"
                f"Tool purpose: {description or 'an interactive HTML tool'}\n\n"
                f"{output_for_scoring}\n\n"
                f"Reply with EXACTLY this format:\n"
                f"ENGINEERING: X\n"
                f"WARMTH: X\n"
                f"REASON: one sentence."
            )
        else:
            quality_prompt = (
                f"Rate this tool output on TWO dimensions (each 1-5).\n\n"
                f"DIMENSION 1 - ENGINEERING\n"
                f"  5 = clearly structured, specific sections, immediately actionable\n"
                f"  3 = readable but could be more organised or concrete\n"
                f"  1 = vague, too short, or generic filler\n\n"
                f"DIMENSION 2 - HUMAN WARMTH\n"
                f"  5 = feels made for this exact person's situation, warm, not robotic\n"
                f"  3 = useful but could apply to almost anyone\n"
                f"  1 = template-like, no emotional intelligence, ignores the human behind the input\n\n"
                f"Tool purpose: {description or 'a productivity tool'}\n"
                f"Test input:\n{demo_input[:300]}\n\n"
                f"Tool output:\n{output[:700]}\n\n"
                f"Reply with EXACTLY this format:\n"
                f"ENGINEERING: X\n"
                f"WARMTH: X\n"
                f"REASON: one sentence."
            )
        quality_resp = call_gemini_simple(quality_prompt)
        if quality_resp:
            eng_m   = re.search(r"ENGINEERING:\s*([1-5])", quality_resp)
            warm_m  = re.search(r"WARMTH:\s*([1-5])",      quality_resp)
            reason_line = quality_resp.split("REASON:")[-1].strip()[:150] if "REASON:" in quality_resp else ""
            eng_score  = int(eng_m.group(1))  if eng_m  else 3
            warm_score = int(warm_m.group(1)) if warm_m else 3
            combined   = round((eng_score + warm_score) / 2, 1)
            print(f"  [OK] Quality - Engineering: {eng_score}/5  Warmth: {warm_score}/5  ({combined} avg) - {reason_line}")

            # 8. Critic check - a demanding creative director finds specific flaws
            # For Mode 3 HTML tools: the Python output is just an HTML template -
            # the actual transformation happens in the browser via JavaScript.
            # Show the Critic the source code logic, not the static HTML blob.
            if is_html_output:
                source_for_critic = open(main_py, encoding="utf-8").read()
                script_start = source_for_critic.find('<script')
                js_snippet = source_for_critic[script_start:script_start+1200] if script_start != -1 else source_for_critic[:1200]
                critic_context = (
                    f"This is an interactive HTML tool (runs in browser).\n"
                    f"Review the JavaScript source code below to judge whether it does something useful:\n\n"
                    f"JS source snippet:\n{js_snippet}"
                )
                critic_flaws = (
                    f"- The JavaScript does nothing with user input (output is identical for any input)\n"
                    f"- The tool does nothing the user couldn't do in 10 seconds themselves\n"
                    f"- The tool has no real algorithmic depth\n"
                    f"- A professional would be embarrassed to show this to a colleague\n"
                )
            else:
                critic_context = f"Tool output sample:\n{output[1500:2500] if len(output) > 1500 else output}"
                critic_flaws = (
                    f"- Output is generic (would be the same regardless of input)\n"
                    f"- Output is padded with filler sentences that add no value\n"
                    f"- A professional would be embarrassed to show this to a colleague\n"
                    f"- The tool does nothing the user couldn't do in 10 seconds themselves\n"
                    f"- The output structure is identical to the input structure (no real transformation)\n"
                )
            critic_prompt = (
                f"You are a demanding creative director reviewing an AI-generated tool.\n"
                f"Your job is to find real problems - not to encourage.\n\n"
                f"Tool purpose: {description or 'a productivity tool'}\n"
                f"Test input used: {demo_input[:200]}\n"
                f"{critic_context}\n\n"
                f"Find specific flaws from this list:\n"
                f"{critic_flaws}\n"
                f"Reply with EXACTLY one of:\n"
                f"REJECT: [reasons] - use if 2+ serious flaws, OR the tool is fundamentally fake "
                f"(hardcoded/static output, does nothing with input)\n"
                f"MINOR: [the one flaw] - use if exactly 1 real flaw but the core mechanism genuinely "
                f"works (input is processed, output changes with input, just rough around the edges)\n"
                f"PASS: - use if no real flaws\n"
                f"Be specific. One word answers are not acceptable."
            )
            critic_resp = call_gemini_simple(critic_prompt)
            critic_verdict = critic_resp.strip().upper() if critic_resp else ""
            if critic_verdict.startswith("REJECT"):
                reject_reason = critic_resp.strip()[7:].strip()[:200]
                print(f"  [NO] Critic rejected: {reject_reason}")
                _append_quality_ledger(
                    tool_name=description or str(skill_dir),
                    category=str(skill_dir).split("/")[-2] if skill_dir else "",
                    eng_score=eng_score, warm_score=warm_score,
                    reason=f"Critic: {reject_reason}",
                    passed=False, format_type=format_type, audience=audience,
                )
                return False, f"Critic review failed: {reject_reason}"
            elif critic_verdict.startswith("MINOR"):
                minor_reason = critic_resp.strip()[6:].strip()[:200]
                print(f"  [OK] Critic: minor flaw, shipping anyway - {minor_reason}")
                reason_line = f"[Shipped with minor flaw] {minor_reason}"
            else:
                print(f"  [OK] Critic review passed.")

            # 9. Win Rate - compare against previous tool in same category
            category_name = str(skill_dir).split("/")[-2] if skill_dir else ""
            if not is_html_output and demo_input and category_name:
                prev = _find_prev_tool_output(category_name, skill_dir, demo_input)
                if prev:
                    prev_name, prev_output = prev
                    winrate_prompt = (
                        f"You are evaluating two versions of a professional tool.\n"
                        f"Same purpose: {description or 'a productivity tool'}\n"
                        f"Same test input was used for both.\n\n"
                        f"TOOL A (new):\n{output[:500]}\n\n"
                        f"TOOL B (previous, {prev_name}):\n{prev_output[:500]}\n\n"
                        f"Which tool gives the user more specific, actionable, "
                        f"professionally useful output?\n\n"
                        f"Reply with EXACTLY one of:\n"
                        f"A_BETTER: [one specific reason]\n"
                        f"B_BETTER: [one specific reason]\n"
                        f"SIMILAR: [one sentence]\n"
                    )
                    wr_resp = call_gemini_simple(winrate_prompt)
                    if wr_resp:
                        if wr_resp.strip().startswith("B_BETTER"):
                            reason = wr_resp.strip()[8:].strip()[:120]
                            print(f"  ⚠ Win Rate: previous tool was better - {reason}")
                            # Informational only - don't reject, but log
                            reason_line = f"[Lost to prev] {reason_line}"
                        elif wr_resp.strip().startswith("A_BETTER"):
                            reason = wr_resp.strip()[8:].strip()[:120]
                            print(f"  [OK] Win Rate: new tool is better - {reason}")
                        else:
                            print(f"  · Win Rate: similar quality to previous tool")

            # Persist to ledger
            _append_quality_ledger(
                tool_name=description or str(skill_dir),
                category=str(skill_dir).split("/")[-2] if skill_dir else "",
                eng_score=eng_score,
                warm_score=warm_score,
                reason=reason_line,
                passed=(combined >= 3.0),
                format_type=format_type,
                audience=audience,
            )
            if combined < 3.0:
                return False, (
                    f"Quality too low - Engineering {eng_score}/5, Warmth {warm_score}/5. "
                    f"{reason_line}. Output was: {repr(output[:200])}"
                )

    except subprocess.TimeoutExpired:
        return False, "Output check timed out - tool may be hanging on input"
    except Exception as e:
        print(f"  ⚠ Output check warning: {e}")

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


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def _verify_source(parsed: dict, grounding_urls: list[str]) -> tuple[str, str]:
    """Verify source URL. Returns (source_badge, verified_url)."""
    source_badge = "⚠️"
    verified_source_url: str | None = None

    if grounding_urls:
        print(f"🔗 Checking {len(grounding_urls)} grounding URL(s)...")
        for gurl in grounding_urls[:3]:
            ok, status = validate_url(gurl)
            if ok:
                verified_source_url = gurl
                source_badge = "✅"
                print(f"  [OK] Grounding source verified: {gurl[:80]} ({status})")
                break
            else:
                print(f"  · {gurl[:70]} - {status}")
        if not verified_source_url:
            verified_source_url = grounding_urls[0]
            source_badge = "⚠️"

    if not verified_source_url:
        model_source = parsed.get("source", "")
        ok, status = validate_url(model_source)
        if ok:
            verified_source_url = model_source
            source_badge = "✅"

    if verified_source_url and source_badge == "✅":
        parsed["_source_display"] = f"[{verified_source_url}]({verified_source_url})"
        parsed["source"] = verified_source_url
    elif verified_source_url:
        search_q = requests.utils.quote(verified_source_url.split("//")[-1][:80])
        parsed["_source_display"] = (
            f"`{verified_source_url}`  \n"
            f"  *(could not be verified - "
            f"[🔍 search for this story](https://www.google.com/search?q={search_q}))*"
        )
        parsed["source"] = verified_source_url
    else:
        raw = parsed.get("source", "")
        if raw.startswith("http"):
            search_q = requests.utils.quote(raw.split("//")[-1][:80])
            parsed["_source_display"] = (
                f"`{raw}`  \n"
                f"  *(link could not be verified - "
                f"[🔍 search for this story](https://www.google.com/search?q={search_q}))*"
            )
        else:
            parsed["_source_display"] = raw

    return source_badge, verified_source_url or ""


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
        print("  ↳ Gemini SCOUT failed - trying DeepSeek fallback for SCOUT...")
        if _deepseek_client:
            try:
                ds_resp = _deepseek_client.chat.completions.create(
                    model="deepseek-chat",
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
            save_rest_day(today, "Phase 1 failed - Gemini quota exhausted and DeepSeek fallback failed.")
            return

    # If no grounding URLs, Gemini used training memory not real search - retry once
    if not grounding_urls:
        print("  ⚠ No grounding URLs - Gemini used training data, retrying SCOUT with search...")
        time.sleep(30)
        scout_content2, grounding_urls2 = call_gemini(build_scout_prompt(today, commission))
        if scout_content2 and grounding_urls2:
            scout_content, grounding_urls = scout_content2, grounding_urls2
            print(f"  [OK] Retry found {len(grounding_urls2)} real source(s).")
        else:
            print("  ⚠ Retry also returned no grounding URLs - proceeding with caution.")

    scout = parse_scout_response(scout_content)
    if not all([scout.get("title"), scout.get("diary"), scout.get("solution")]):
        print("❌ Phase 1 incomplete - missing title, diary, or solution.")
        save_rest_day(today, "Phase 1 (Scout) returned incomplete response.")
        return

    source_badge, _ = _verify_source(scout, grounding_urls)
    print(f"  [OK] Scout complete: '{scout['solution']}' ({scout['category']})")

    # Wait after SCOUT to avoid per-minute rate limit on next call
    print(f"  ⏳ Waiting 65s for rate limit window to clear...")
    time.sleep(65)

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2 - SPEC: design the tool, validate before coding
    # ══════════════════════════════════════════════════════════════════════════
    print(f"\n📐 Phase 2 - SPEC: designing tool architecture...")
    spec: dict = {}
    spec_feedback = ""
    spec_ok = False

    for attempt in range(1, 3):
        spec_content = call_gemini_simple(build_spec_prompt(today, scout, spec_feedback))
        if not spec_content:
            spec_feedback = f"attempt {attempt}: Gemini returned empty response for spec prompt"
            break
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
    merged: dict = {**scout}  # initialise so it's always defined even if BUILD loop exits early

    for attempt in range(1, 6):
        print(f"  Attempt {attempt}/5...")
        if attempt > 1:
            print(f"  ⏳ Waiting 15s before retry...")
            time.sleep(15)
        build_content = call_gemini_simple(
            build_code_prompt(today, scout, spec, build_feedback),
            deepseek_prompt=build_code_prompt(today, scout, spec, build_feedback, slim=True),
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
            elif "unterminated" in build_reason.lower() or ("syntax error" in build_reason.lower() and attempt >= 2):
                build_feedback = (
                    f"CRITICAL: Your previous code was TRUNCATED because it was too long. "
                    f"The response was cut off mid-string, causing a syntax error.\n\n"
                    f"REQUIRED: Rewrite the entire tool in UNDER 350 LINES TOTAL. "
                    f"This is a hard limit - do not exceed it.\n\n"
                    f"How to stay under 350 lines:\n"
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
try:
    build_prompt("1970-01-01")
except Exception as _smoke_err:
    raise RuntimeError(
        f"build_prompt() smoke test failed - fix before running: {_smoke_err}"
    ) from _smoke_err

if __name__ == "__main__":
    evolve()
