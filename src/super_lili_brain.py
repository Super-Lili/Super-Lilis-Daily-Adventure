"""
super_lili_brain.py — Super-Lili's Daily Adventure Engine
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
        LILI_EDITORIAL_CRITERIA,
    )
    _EDITOR_DOMAINS: dict[str, str] = {
        "work":     LILI_DOMAIN_WORK,
        "learning": LILI_DOMAIN_LEARNING,
        "healing":  LILI_DOMAIN_HEALING,
        "design":   "",   # Design Alchemy: core lenses already in prompt template
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
    from lili_engineering import LILI_ENGINEERING_LESSONS
except ImportError:
    LILI_ENGINEERING_LESSONS = ""

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
            lines.append(f"  • {tool_name}" + (f" — {desc}" if desc else ""))
    return "\n".join(lines) if lines else "  (none yet)"


_SOURCE_ROTATION = [
    # ── KNOWLEDGE WORKERS & PRODUCTIVITY ──
    ("Reddit (knowledge workers)",
     "Search r/productivity, r/gtd, r/remotework for posts from the past 7 days. "
     "Focus on people drowning in tools, notifications, or the performance of busyness. "
     "Go deep into comments — the real signal is in the replies, not the post."),

    # ── PARENTS & FAMILY LIFE ──
    ("Reddit (parents)",
     "Search r/Parenting, r/beyondthebump, r/SingleParents for posts from the past 7 days. "
     "Look for friction around maintaining identity, attention, and personal time "
     "while caring for others. What do parents wish existed that nobody has built for them?"),

    # ── STUDENTS & LEARNING ──
    ("YouTube comments (students)",
     "Search YouTube for a study, exam prep, or 'how I actually learned X' video from the past month. "
     "Read the comment section carefully — students are brutally honest about what fails them. "
     "Look for patterns around memory, motivation collapse, and tutorial hell."),

    # ── OLDER ADULTS & CAREGIVERS ──
    ("Reddit (older adults & caregivers)",
     "Search r/eldertech, r/AgingParents, r/Caregiver for posts from the past 7 days. "
     "Look for friction where digital life fails older people, or where adult children "
     "struggle to bridge the gap between their parents and technology."),

    # ── TEACHERS & EDUCATORS ──
    ("Reddit (teachers)",
     "Search r/Teachers, r/teaching, r/OnlinEducators for posts from the past 7 days. "
     "Look for burnout signals, the gap between what teachers wish they could do "
     "and what their actual constraints allow. What invisible labor do they carry?"),

    # ── CREATIVE PROFESSIONALS ──
    ("Threads & X (creative workers)",
     "Search threads.net and x.com for designers, illustrators, writers, and musicians "
     "posting about creative blocks, platform anxiety, algorithm fatigue, or the pressure "
     "to produce content instead of art. Look for the grief underneath the productivity language."),

    # ── MENTAL HEALTH & NEURODIVERGENCE ──
    ("Reddit (ADHD & mental health)",
     "Search r/ADHD, r/anxiety, r/depression for posts from the past 7 days. "
     "Focus on daily friction — not clinical discussions, but real moments where "
     "ordinary tasks feel impossible. What small environmental changes help people function?"),

    # ── FINANCIAL STRESS ──
    ("Reddit (money & financial anxiety)",
     "Search r/personalfinance, r/povertyfinance, r/financialindependence for recent posts. "
     "Look for the emotional and cognitive friction of financial uncertainty — "
     "not investment advice needs, but the mental load of scarcity and decision fatigue."),

    # ── SMALL BUSINESS & FREELANCERS ──
    ("HackerNews & Reddit (freelancers)",
     "Search news.ycombinator.com and r/freelance, r/smallbusiness for posts from the past week. "
     "Look for friction where solo workers and small teams fall through the gaps — "
     "tools built for enterprises that crush individuals, invisible admin overhead, "
     "the loneliness of working without a team."),

    # ── BODY, HEALTH & PHYSICAL EXPERIENCE ──
    ("Reddit (chronic illness & body)",
     "Search r/ChronicIllness, r/ChronicPain, r/disability for posts from the past 7 days. "
     "Look for friction where digital tools ignore the reality of living in a body "
     "that doesn't behave predictably. What does the world assume about people "
     "that chronic illness patients know is false?"),

    # ── COMMUTERS & URBAN LIFE ──
    ("X & Threads (urban daily life)",
     "Search x.com and threads.net for people posting about commuting, urban friction, "
     "the texture of daily city life — transit delays, noise, crowds, the small indignities "
     "of shared space. What moment in an ordinary day quietly costs people something?"),

    # ── INTROVERTS & SOCIAL ENERGY ──
    ("Reddit (introverts & social exhaustion)",
     "Search r/introvert, r/socialskills, r/hsp for posts from the past 7 days. "
     "Look for friction around social energy management, the cost of performing "
     "extroversion, and the absence of tools designed for people who need recovery time."),

    # ── LIFE TRANSITIONS ──
    ("Reddit (major life changes)",
     "Search r/divorce, r/GriefSupport, r/NewToCollege, r/retirement for recent posts. "
     "Look for people navigating identity ruptures — the friction of becoming someone "
     "different than you were, without any map for the new territory."),

    # ── NIGHT SHIFT & IRREGULAR SCHEDULES ──
    ("Reddit (shift workers & irregular hours)",
     "Search r/nightshift, r/ShiftWork, r/nursing for posts from the past 7 days. "
     "Look for friction where the entire world is designed for 9-to-5 rhythms "
     "and people with different schedules constantly fall outside the default."),

    # ── RESEARCH & NEWS SIGNAL ──
    ("news & research reports",
     "Search for a research report, academic study, or long-form journalism piece "
     "published in the past 14 days about human behavior, social friction, wellbeing, "
     "or work/learning/health. A surprising data point from a credible source "
     "is more valuable than a trending tweet. Look for the finding that changes how you see something."),
]


# ─────────────────────────────────────────────────────────────
# AUDIENCE ROTATION — cycles independently of source rotation
# ─────────────────────────────────────────────────────────────

_AUDIENCE_ROTATION = [
    "general",    # 0 — everyday people, mixed backgrounds
    "media",      # 1 — journalists, editors, writers
    "tech",       # 2 — PMs, engineers, founders
    "creative",   # 3 — designers, CDs, brand/luxury professionals
    "research",   # 4 — researchers, analysts, academics
]

_AUDIENCE_CONTEXT = {
    "general": {
        "label": "General Users",
        "who": "Everyday people across all backgrounds — parents, students, workers, caregivers.",
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
            "Look for craft-level friction — not tech problems, but editorial and professional ones."
        ),
        "quality_bar": (
            "Output must meet the standard of a senior editor — no filler phrases, "
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
            "Design tools must RENDER actual visual output — not describe it. "
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
# Matches the order of _SOURCE_ROTATION above (15 entries).
_SOURCE_DOMAIN_HINT = [
    "work",      # 0  — knowledge workers & productivity
    "healing",   # 1  — parents & family life
    "learning",  # 2  — students & learning
    "healing",   # 3  — older adults & caregivers
    "learning",  # 4  — teachers & educators
    "design",    # 5  — creative professionals (Design Alchemy)
    "healing",   # 6  — ADHD & mental health
    "healing",   # 7  — financial stress
    "work",      # 8  — freelancers & small business
    "healing",   # 9  — chronic illness & body
    "healing",   # 10 — commuters & urban life
    "healing",   # 11 — introverts & social exhaustion
    "healing",   # 12 — life transitions
    "work",      # 13 — shift workers & irregular hours
    "work",      # 14 — news & research (default to work)
]


def build_prompt(today: str) -> str:
    skills_list = "\n".join(f"  • {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  • Python standard library"
    evolution_ctx = f"\n\nEVOLUTION NOTES FROM LAST WEEK:\n{EVOLUTION_NOTES}" if EVOLUTION_NOTES.strip() else ""
    memory_ctx = get_memory_context()
    from datetime import date as _date
    day_index = _date.fromisoformat(today).toordinal() % len(_SOURCE_ROTATION)
    primary_src, primary_hint = _SOURCE_ROTATION[day_index]

    # Audience rotation — cycles independently (5 audiences vs 15 sources)
    audience_index = _date.fromisoformat(today).toordinal() % len(_AUDIENCE_ROTATION)
    audience_key = _AUDIENCE_ROTATION[audience_index]
    aud = _AUDIENCE_CONTEXT[audience_key]
    audience_block = (
        f"\n═══════════════════════════════════════════════════════\n"
        f"TODAY'S AUDIENCE — {aud['label'].upper()}\n"
        f"═══════════════════════════════════════════════════════\n"
        f"Who they are: {aud['who']}\n\n"
        + (f"Extra search targets: {aud['search_add']}\n\n" if aud['search_add'] else "")
        + f"Quality bar for this audience:\n  {aud['quality_bar']}\n\n"
        f"Preferred tool formats:\n  {aud['format_pref']}\n\n"
        f"→ Apply Rule 12 ({aud['label']}) from the Engineering Rules injected above.\n"
        f"  Build to THEIR standard, not a generic one.\n"
        f"  If today's audience is professional (not general), the tool must meet professional craft standards.\n"
    )

    # Targeted domain injection: only the block matching today's source category.
    # Reduces injection from 578 lines (all domains) → ~150 lines (one domain + criteria).
    # Positioned right before SOLUTION PATTERNS so domain knowledge is fresh in context.
    domain_key = _SOURCE_DOMAIN_HINT[day_index]
    domain_block = _EDITOR_DOMAINS.get(domain_key, "")
    if domain_block or _EDITOR_CRITERIA:
        _domain_label = {
            "work":     "FUTURE OF WORK",
            "learning": "FUTURE OF LEARNING",
            "healing":  "HEALING INVENTIONS",
            "design":   "DESIGN ALCHEMY",
        }.get(domain_key, domain_key.upper())
        editor_ctx = (
            f"\n\n═══════════════════════════════════════════════════════\n"
            f"DOMAIN INTELLIGENCE — {_domain_label}\n"
            f"(matched to today's source: {primary_src})\n"
            f"Apply this knowledge when reading friction signals and designing the tool.\n"
            f"═══════════════════════════════════════════════════════\n"
            + (domain_block + "\n\n" if domain_block else "")
            + _EDITOR_CRITERIA
        )
    else:
        editor_ctx = ""

    # ③ Category rotation: ban any category used in the last 2 days
    recent_cats = _get_recent_categories(2)
    banned_cats = list(set(recent_cats))
    avoid_cats = f"\nBANNED CATEGORIES TODAY (used in the last 2 days — choose something different):\n  {', '.join(banned_cats)}" if banned_cats else ""

    # Blindspot antidote from last Sunday's self-analysis
    blindspot_nudge = (
        f"\nBLINDSPOT ANTIDOTE FROM LAST WEEK'S SELF-REVIEW:\n"
        f"  {LILI_BLINDSPOT_ANTIDOTE}\n"
        f"  Read this before choosing today's topic. Then choose."
    ) if LILI_BLINDSPOT_ANTIDOTE.strip() else ""

    # Engineering lessons from last Sunday's code quality review
    engineering_nudge = (
        f"\n═══════════════════════════════════════════════════════\n"
        f"ENGINEERING RULES FROM LAST WEEK'S CODE REVIEW\n"
        f"(These rules came from real failures in your own tools — follow them.)\n"
        f"═══════════════════════════════════════════════════════\n"
        f"{LILI_ENGINEERING_LESSONS}\n"
    ) if LILI_ENGINEERING_LESSONS.strip() else ""

    # ② Similarity check: inject all existing tools into prompt
    existing_tools_block = _get_existing_tools()

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
EXISTING TOOLS — STRICT DUPLICATION BAN
═══════════════════════════════════════════════════════
You have already built these tools. Study this list carefully.
DO NOT build anything conceptually similar to any of them.
If your proposed tool could be described with the same verb + noun as one below, reject it and find a different problem.

{existing_tools_block}

═══════════════════════════════════════════════════════
YOUR MEMORY — WHAT YOU'VE ALREADY DONE
═══════════════════════════════════════════════════════
{memory_ctx}

IMPORTANT: Do NOT repeat a topic or tool you've already done.
Find a genuinely fresh friction point in a genuinely different area.

═══════════════════════════════════════════════════════
YOUR 4 MISSION AREAS — PICK ONE FOR TODAY
═══════════════════════════════════════════════════════
{avoid_cats}{blindspot_nudge}

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
{audience_block}
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

SOURCE EVIDENCE — MANDATORY, COMES FIRST:
Before writing anything else, you MUST quote 2-3 sentences VERBATIM from the actual post,
comment, or article you found. These must be the real words of a real human — not your
paraphrase, not a summary, not a reconstruction.

Format:
  SOURCE: [Reddit r/subreddit | X @username | HackerNews | Article name]
  QUOTE: "[exact words copied from the source]"

Rules:
  ✗ You MAY NOT proceed if you cannot produce a real verbatim quote.
  ✗ Do NOT paraphrase and call it a quote.
  ✗ Do NOT invent a quote that "sounds like" what someone might say.
  ✓ If you searched and found nothing quotable — keep searching a different community.
  ✓ A short real quote ("i've rewritten this function 6 times and it still doesn't work lol")
    is worth more than a polished invented scenario.

This quote is the FOUNDATION of everything that follows. If it's fake, everything built on it is fake.

PAIN PORTRAIT — BUILT FROM THE QUOTE ABOVE:
Using the real words you just found, construct a Pain Portrait with 3 elements:

  1. WHO (derive from the source — who wrote this? what's their situation?):
     ✗ WEAK: "people who struggle with learning"
     ✓ STRONG: "a 34-year-old nurse working night shifts who bought a Python course
       6 months ago but can't finish it because she's always too tired after her shift"

  2. THE MOMENT OF FAILURE (what exact moment does the quote describe?):
     ✗ WEAK: "they can't stay focused"
     ✓ STRONG: "she opens the course at 7am after her shift, gets through 4 minutes,
       then falls asleep — and when she wakes up she has no idea where she was or
       what she half-learned. The progress bar shows 23% but she feels like she knows nothing."

  3. WHY EXISTING TOOLS FAIL THEM (what has this person already tried?):
     ✗ WEAK: "current tools aren't good enough"
     ✓ STRONG: "Anki is designed for dedicated study sessions, not 4-minute fragments.
       YouTube doesn't remember where she stopped. Her notes are scattered across
       3 apps. Nothing connects the fragments into cumulative understanding."

If you cannot write a convincing Pain Portrait GROUNDED IN THE REAL QUOTE, the friction is too vague.
Keep searching — do not build a tool for a fuzzy problem.

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

TOOL-TO-PORTRAIT FIT CHECK (run this before writing a single line of code):
Ask yourself these 3 questions. If you can't answer all 3 with a YES, redesign:

  Q1: Does this tool directly address THE SPECIFIC MOMENT OF FAILURE from my Pain Portrait?
      Not a generic version of the problem — the exact moment I described.
      ✗ FAIL: "the nurse struggles with learning" → tool = generic note-taker
      ✓ PASS: "the nurse wakes up not knowing what she half-learned" → tool = micro-session
              recap generator that produces a 5-bullet summary of any video/text fragment

  Q2: Would THE SPECIFIC PERSON from my Pain Portrait recognize this tool as built for them?
      If the nurse saw this tool, would she say "this is exactly what I needed"?
      Or would she say "this is for students, not for someone like me"?

  Q3: Does the tool's OUTPUT directly give the user something they can ACT ON?
      ✗ FAIL: shows analysis, insights, a score — user still doesn't know what to do
      ✓ PASS: produces a specific next action, a formatted output they can use immediately

If any answer is NO — go back. The tool is solving a fantasy version of the problem.

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

TOOL FORMAT SELECTION (mandatory — decide this before writing any code):

A tool is not always a text box. Choose the format that best serves the Pain Portrait and Audience.
Declare your choice in ---SPEC--- as: FORMAT: [letter] — [one sentence why]

  FORMAT A — Single text input → output
    Use when: user has one document, email, or text blob to process
    Modes: 1 (text) or 2 (SVG)
    Examples: email rewriter, meeting notes → decisions, pitch sharpener

  FORMAT B — Multi-field structured form (HTML)
    Use when: the tool needs several specific pieces of information to do its job
    Mode: 3 (HTML with multiple labeled input fields + submit)
    Examples: interview guide (subject + angle + publication + word count),
              project budget (description + team size + timeline + budget range),
              commission brief (contributor name + story concept + deadline + format),
              creative brief (client + project + adjectives + audience + constraints)

  FORMAT C — Wizard / progressive steps (HTML)
    Use when: each answer shapes the next question; the output emerges through a conversation
    Mode: 3 (HTML, step-by-step reveal)
    Examples: brand archive builder (section by section),
              thesis outline (research question → methodology → chapter structure),
              pitch deck narrative (audience → goal → key message → slide flow)

  FORMAT D — Live canvas / real-time transformer (HTML)
    Use when: the user needs to SEE output transform as they type or adjust
    Mode: 3 (HTML with live input → Canvas/DOM update)
    Examples: typography lab (type text, sliders for size/weight/leading),
              color palette generator (type brand name, see palettes update live),
              poster maker (type a quote, see it rendered as a designed artifact)

  FORMAT E — Ambient / environment (no input, just open) (HTML)
    Use when: the tool IS the experience — no text processing needed
    Mode: 3 (HTML, self-starting on load)
    Examples: focus timer with ambient sound, breathing exercise,
              minimum viable day planner (opens with today's inputs)

  FORMAT F — Generator + inline editor (HTML)
    Use when: generate a first draft the user then refines directly in the tool
    Mode: 3 (HTML with generated content in editable fields + copy-to-clipboard)
    Examples: brand archive document (generated framework → user fills/edits sections),
              slide narrative (generated outline → user edits each slide inline),
              interview guide (generated questions → user adds/removes/reorders)

IMPORTANT:
  ✗ Do NOT default to Format A just because it's easiest to implement.
  ✓ Professional audience tools (media, tech, creative, research) almost always
    benefit from Format B, C, or F — they have structured, multi-part inputs.
  ✓ Design tools (Design Alchemy) almost always benefit from Format D.
  ✓ Healing Inventions almost always benefit from Format E or D.


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

BROWSER COMPATIBILITY (mandatory — all new tools must support this):
  Every tool MUST support both local CLI use AND browser execution via Pyodide.

  ══════════════════════════════════════════════════════
  TOOL OUTPUT MODES — choose the right one for this tool
  ══════════════════════════════════════════════════════

  MODE 1 — PLAIN TEXT  (text-processing tools)
    process(text) returns a plain string.
    Best for: summarizers, rewriters, extractors, converters.

  MODE 2 — SVG IMAGE
    process(text) returns a string starting with <svg.
    Best for: charts, diagrams, visual outputs.

  MODE 3 — INTERACTIVE HTML APP  ← USE THIS for Healing Inventions & interactive tools
    process(text) returns a complete HTML page string starting with <!DOCTYPE html>.
    The returned HTML runs inside a sandboxed iframe in the browser.
    It can use ANY browser API: Web Audio, Canvas, CSS animations, keyboard events,
    localStorage, requestAnimationFrame — full JavaScript freedom.
    Best for: ambient tools, mini-games, interactive experiences, virtual companions,
    sound tools, animated visualizations, anything that stays open and responds to user.

    HTML tool pattern:
    ```python
    def process(text: str) -> str:
        theme = text.strip() or "forest"
        html = f\"\"\"<!DOCTYPE html>
    <html lang="en"><head><meta charset="UTF-8">
    <style>
      /* all CSS inline */
    </style></head>
    <body>
      <!-- interactive content here -->
      <script>
        // all JavaScript inline — Web Audio, Canvas, events, etc.
        const theme = {repr(theme)};
        // ... full interactive app ...
      </script>
    </body></html>\"\"\"
        return html

    _browser_input = globals().get('USER_INPUT', None)
    if _browser_input is not None:
        print(process(_browser_input))
    elif __name__ == "__main__":
        import sys
        print(process(sys.argv[1] if len(sys.argv) > 1 else ""))
    ```
    For HTML tools: empty input is fine — just return the default app.
    No argparse needed. No "Output" label needed — the app IS the output.

  ══════════════════════════════════════════════════════

  For MODE 1 & 2 only — Pyodide library rules:
  ✓ ALLOWED: numpy, pandas, matplotlib, scipy, Pillow, regex, dateutil, standard library
  ✗ FORBIDDEN: svgwrite, rich, click, requests, openpyxl, ics, pytz
  For MODE 3: no Pyodide restrictions — all JS runs natively in the iframe.

  For MODE 1 & 2 — dual-mode pattern:
  ```python
  def process(text: str) -> str:
      \"\"\"Core logic — takes plain text input, returns plain text result.\"\"\"
      return result_string

  def _cli_main():
      import argparse
      p = argparse.ArgumentParser()
      p.add_argument("--input", required=True)
      args = p.parse_args()
      text = open(args.input).read() if os.path.exists(args.input) else args.input
      print(process(text))

  _browser_input = globals().get('USER_INPUT', None)
  if _browser_input is not None:
      print(process(_browser_input))
  elif __name__ == "__main__":
      _cli_main()
  ```

  Rules:
  ✓ `globals().get('USER_INPUT', None)` is the ONLY way to detect browser mode
  ✓ argparse goes inside `_cli_main()`, NOT at module level
  ✗ NEVER use sys.argv directly at module level — breaks browser

CODE QUALITY:
  - Minimum 4 well-named functions with type hints, each doing ONE thing
  - Requirements comment block at top
  - process() MUST handle empty/very-short input gracefully
  - MODE 1/2: Output MUST have labeled sections — never a raw text blob
  - MODE 3: HTML must be self-contained, beautiful, and immediately usable
  - Include at least one concrete example in the docstring
{engineering_nudge}
QUALITY BAR: Would a non-technical person be able to run this and feel like their problem
is actually solved? If no — go deeper. The sophistication should be invisible to the user
and obvious in the result.

USABILITY CONSTRAINTS (mandatory — no exceptions):
  ✗ NO external API keys required — the tool must work out of the box, zero setup
  ✗ Mode 1/2: NO more than 3 CLI arguments — if it needs more, redesign it
  ✓ Mode 3 (HTML): multi-field forms are encouraged for professional tools —
    5–8 labeled fields is fine when each field genuinely shapes the output
  ✗ NO tools that only print text to the terminal — the output must be a file or visual
  ✓ A stranger with no technical background can use it in under 5 minutes
  ✓ The tool solves ONE specific problem, not a family of vague problems
  ✓ Mode 1/2: aim for under 200 lines — complexity is the enemy of usability
  ✓ Mode 3 (HTML): no line limit — but every line must earn its place.
    A rich interactive tool naturally runs longer. That is fine.

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
---SPEC---
Answer ALL items before writing any code. Be specific — generic answers fail.

FORMAT: [A / B / C / D / E / F] — [one sentence: why this format serves the Pain Portrait]

Q1-PASS: [In one sentence: which EXACT moment of failure from the Pain Portrait does this tool address?
  ✗ FAIL: "helps people with learning"
  ✓ PASS: "addresses the moment the nurse opens a course at 7am after her shift and can't remember where she stopped"]

Q2-PASS: [In one sentence: why would the specific person from the Pain Portrait immediately recognize this tool?
  ✗ FAIL: "any user will find it helpful"
  ✓ PASS: "she sees her own fragmented progress bar pattern described exactly in the --help text"]

Q3-PASS: [In one sentence: what SPECIFIC thing does the user receive as output? What can they do with it in the next 5 minutes?
  ✗ FAIL: "the tool shows insights"
  ✓ PASS: "a 5-bullet session recap saved to recap.txt she can re-read before her next fragment"]

TEST_INPUT: [Write 3-6 sentences of REALISTIC sample input a real user of this tool would paste in.
  This must match the tool's actual domain — study notes, meeting transcript, task list, diary entry, etc.
  NOT generic filler text. This will be used to validate the tool actually works.]
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
                    print(f"  ✓ {model_name} succeeded.")
                    return response.text
                break  # empty response — no point retrying this model
            except Exception as e:
                wait = 15 * (2 ** attempt)  # 15s, 30s, 60s
                print(f"  ✗ {model_name} attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print(f"  ⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)

    return None


def call_gemini_simple(prompt: str) -> str | None:
    """Call Gemini without search tool — for quick scoring/review tasks."""
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    for model_name in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response.text:
                    return response.text
                break
            except Exception as e:
                wait = 15 * (2 ** attempt)
                if attempt < 2:
                    time.sleep(wait)
    return None


def extract_format(spec: str) -> str:
    """Pull the FORMAT letter (A–F) out of the spec section."""
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
    # URL-encode the skill_dir path for the curl command (spaces → %20)
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
                           audience: str = "") -> None:
    """Persist quality scores to tool_quality_ledger.jsonl for weekly evolution to read."""
    ledger_path = Path("tool_quality_ledger.jsonl")
    entry = {
        "date":      datetime.utcnow().strftime("%Y-%m-%d"),
        "tool":      tool_name,
        "category":  category,
        "format":    format_type,   # A–F tool format
        "audience":  audience,      # general / media / tech / creative / research
        "engineering": eng_score,
        "warmth":    warm_score,
        "combined":  round((eng_score + warm_score) / 2, 1),
        "reason":    reason,
        "passed":    passed,
    }
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def validate_tool(skill_dir: str, test_input: str = "", description: str = "",
                  format_type: str = "", audience: str = "") -> tuple[bool, str]:
    """Validate the tool: syntax, browser compatibility, output quality."""
    import subprocess, sys
    main_py = f"{skill_dir}/main.py"
    test_py = f"{skill_dir}/test_main.py"

    # 1. Syntax check
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open('{main_py}').read())"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, f"Syntax error: {result.stderr[:200]}"
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
                    "All argparse arguments have defaults — tool runs on internal fake data. "
                    "At least one argument must require real user input (no default)."
                )
    except Exception:
        pass

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
    if os.path.exists(test_py):
        try:
            result = subprocess.run(
                [sys.executable, test_py],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return False, f"Tests failed: {result.stderr[:300]}"
            print(f"  ✓ Tests passed.")
        except subprocess.TimeoutExpired:
            return False, "Tests timed out (60s)"
        except Exception as e:
            return False, f"Test error: {e}"

    # 6. Output quality check — use domain-specific test_input from spec
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

        if not output or len(output) < 80 or len(output_lines) < 2:
            return False, (
                f"Output too weak: {len(output)} chars, {len(output_lines)} lines. "
                f"Got: {repr(output[:200])}. "
                f"Must produce structured, substantive output (80+ chars, 2+ lines)."
            )
        print(f"  ✓ Output check passed ({len(output)} chars, {len(output_lines)} lines).")

        # 7. Two-dimension quality score:
        #    ENGINEERING — structured, substantive, actionable output
        #    WARMTH      — specific to a real person, not generic, not robotic
        quality_prompt = (
            f"Rate this tool output on TWO dimensions (each 1–5).\n\n"
            f"DIMENSION 1 — ENGINEERING\n"
            f"  5 = clearly structured, specific sections, immediately actionable\n"
            f"  3 = readable but could be more organised or concrete\n"
            f"  1 = vague, too short, or generic filler\n\n"
            f"DIMENSION 2 — HUMAN WARMTH\n"
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
            print(f"  ✓ Quality — Engineering: {eng_score}/5  Warmth: {warm_score}/5  ({combined} avg) — {reason_line}")
            # Persist to ledger regardless of pass/fail
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
                    f"Quality too low — Engineering {eng_score}/5, Warmth {warm_score}/5. "
                    f"{reason_line}. Output was: {repr(output[:200])}"
                )

    except subprocess.TimeoutExpired:
        return False, "Output check timed out — tool may be hanging on input"
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

    # Extract domain-specific test input and format from spec
    test_input = extract_test_input(parsed.get("spec", ""))
    tool_format = extract_format(parsed.get("spec", ""))
    if test_input:
        print(f"  ✓ Spec test input extracted ({len(test_input)} chars)")
    else:
        print(f"  ⚠ No TEST_INPUT in spec — using fallback test data")
    if tool_format:
        print(f"  ✓ Tool format: {tool_format}")

    # Resolve today's audience key (mirrors build_prompt logic)
    from datetime import date as _date_evolve
    _aud_index = _date_evolve.fromisoformat(today).toordinal() % len(_AUDIENCE_ROTATION)
    today_audience = _AUDIENCE_ROTATION[_aud_index]

    # Save tool + validate, retry up to 3 times if validation fails
    skill_dir = None
    for attempt in range(1, 4):
        print(f"💾 Saving tool (attempt {attempt}/3)...")
        skill_dir = save_tool(today, parsed, source_badge)
        parsed["_skill_dir"] = skill_dir
        print(f"  ✓ Tool saved: {skill_dir}/main.py")

        print("🔬 Validating tool...")
        ok, reason = validate_tool(
            skill_dir,
            test_input=test_input,
            description=parsed.get("description", ""),
            format_type=tool_format,
            audience=today_audience,
        )
        if ok:
            print("  ✓ Validation passed.")
            break
        else:
            print(f"  ✗ Validation failed: {reason}")
            if attempt < 3:
                print("  ↻ Asking Gemini to fix the tool...")
                fix_prompt = (
                    f"The Python tool you wrote failed validation.\n\n"
                    f"TOOL PURPOSE: {parsed.get('description', '')}\n\n"
                    f"TOOL SPEC:\n{parsed.get('spec', 'Not provided')}\n\n"
                    f"VALIDATION ERROR:\n{reason}\n\n"
                    f"TEST INPUT USED:\n{test_input or '(fallback generic input)'}\n\n"
                    f"BROKEN CODE:\n```python\n{parsed['code']}\n```\n\n"
                    f"Fix requirements:\n"
                    f"1. Process the TEST INPUT above and produce substantive output (80+ chars, 2+ lines)\n"
                    f"2. Use USER_INPUT dual-mode: _browser_input = globals().get('USER_INPUT', None)\n"
                    f"3. Pass --help without crashing\n"
                    f"4. Output must be specific and actionable, not generic filler\n\n"
                    f"Return ONLY the fixed Python code, no explanation."
                )
                fixed = call_gemini_simple(fix_prompt)
                if fixed:
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

    # Regenerate GitHub Pages site
    import subprocess, sys as _sys
    subprocess.run([_sys.executable, "docs/generate_site.py"], check=False)


if __name__ == "__main__":
    evolve()
