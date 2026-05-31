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

    # ── DESIGNERS & VISUAL CREATIVES — real production friction ──
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
     "Read the comment section carefully — students are brutally honest about what fails them. "
     "Look for patterns around memory, motivation collapse, and tutorial hell."),

    # ── JOURNALISTS & EDITORS — real reporting workflow ──
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

    # ── CREATIVE PROFESSIONALS — studio & production tools ──
    ("Threads & X (creative studio workers)",
     "Search threads.net and x.com for designers, art directors, brand strategists, "
     "motion designers, and illustrators posting about their actual studio workflow. "
     "NOT feelings about algorithms — look for: 'I wish there was a tool that...', "
     "'I still do this manually...', 'every project I have to...'. "
     "Real production pain, not existential creative dread."),

    # ── MENTAL HEALTH & NEURODIVERGENCE ──
    ("Reddit (ADHD & mental health)",
     "Search r/ADHD, r/anxiety, r/depression for posts from the past 7 days. "
     "Focus on daily friction — not clinical discussions, but real moments where "
     "ordinary tasks feel impossible. What small environmental changes help people function?"),

    # ── FREELANCERS & FINANCE — real money management tools ──
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
     "Look for people navigating identity ruptures — the friction of becoming someone "
     "different than you were, without any map for the new territory."),

    # ── MOTION & TYPOGRAPHY — specialist creative tools ──
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
# Matches the order of _SOURCE_ROTATION above (14 entries).
# Distribution: studio×4, work×3, design×3, learning×2, healing×2
_SOURCE_DOMAIN_HINT = [
    "work",      # 0  — knowledge workers & productivity
    "studio",    # 1  — designers & visual creatives
    "learning",  # 2  — students & learning
    "work",      # 3  — journalists & editors
    "learning",  # 4  — teachers & educators
    "studio",    # 5  — creative studio workers (production pain)
    "healing",   # 6  — ADHD & mental health
    "work",      # 7  — freelancers & finance
    "studio",    # 8  — brand & luxury creative industry
    "studio",    # 9  — audio & podcast creators
    "design",    # 10 — writers & content creators
    "design",    # 11 — life organisation & physical space
    "healing",   # 12 — life transitions
    "design",    # 13 — motion & typography
    "work",      # 14 — news & research
]


# ─────────────────────────────────────────────────────────────
# PROMPT BUILDER — 5 focused functions, each with a single job
# ─────────────────────────────────────────────────────────────

def _build_context_block(today: str) -> dict:
    """Compute all dynamic values for today. Pure data — no string building."""
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
            f"DOMAIN INTELLIGENCE — {domain_label}\n"
            f"(matched to today's source: {primary_src})\n"
            f"═══════════════════════════════════════════════════════\n"
            + (domain_block + "\n\n" if domain_block else "")
            + expansion_ctx + _EDITOR_CRITERIA
        )

    # Audience block
    audience_block = (
        f"\n═══════════════════════════════════════════════════════\n"
        f"TODAY'S AUDIENCE — {aud['label'].upper()}\n"
        f"═══════════════════════════════════════════════════════\n"
        f"Who they are: {aud['who']}\n\n"
        + (f"Extra search targets: {aud['search_add']}\n\n" if aud['search_add'] else "")
        + f"Quality bar:\n  {aud['quality_bar']}\n\n"
        f"Preferred formats:\n  {aud['format_pref']}\n\n"
        f"→ Apply Rule 12 ({aud['label']}) from Engineering Rules above.\n"
        f"  If today's audience is professional, the tool must meet professional craft standards.\n"
    )

    # Engineering rules
    engineering_nudge = ""
    if LILI_ENGINEERING_BASE.strip():
        engineering_nudge = (
            f"\n═══════════════════════════════════════════════════════\n"
            f"ENGINEERING RULES — PERMANENT STANDARDS\n"
            f"(Written by the project owner. These never change.)\n"
            f"═══════════════════════════════════════════════════════\n"
            f"{LILI_ENGINEERING_BASE}\n"
        )
    if LILI_ENGINEERING_LESSONS.strip():
        engineering_nudge += (
            f"\n═══════════════════════════════════════════════════════\n"
            f"ENGINEERING RULES — THIS WEEK'S ADDITIONS\n"
            f"═══════════════════════════════════════════════════════\n"
            f"{LILI_ENGINEERING_LESSONS}\n"
        )

    # Diversity guards
    recent_cats = _get_recent_categories(2)
    avoid_cats = (
        f"\nBANNED CATEGORIES TODAY (used in the last 2 days):\n  {', '.join(set(recent_cats))}"
        if recent_cats else ""
    )
    blindspot_nudge = (
        f"\nBLINDSPOT ANTIDOTE FROM LAST WEEK'S SELF-REVIEW:\n"
        f"  {LILI_BLINDSPOT_ANTIDOTE}\n  Read this before choosing today's topic."
    ) if LILI_BLINDSPOT_ANTIDOTE.strip() else ""

    recent_patterns = _get_recent_patterns(4)
    pat_counts = {p: recent_patterns.count(p) for p in set(recent_patterns)}
    overused = [p for p, n in pat_counts.items() if n >= 2]
    avoid_patterns = f"\nAVOID these solution patterns today (used too recently): {', '.join(overused)}" if overused else ""

    return {
        "today": today,
        "skills_list": "\n".join(f"  • {s}" for s in LILI_SKILLS) if LILI_SKILLS else "  • Python standard library",
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
        "avoid_patterns": avoid_patterns,
    }


def _build_identity_section(ctx: dict) -> str:
    """Lili's identity: personality, skills, memory, existing tools."""
    return f"""YOUR NORTH STAR (read this first, every day):
You are building a coherent toolkit for creative professionals — not random daily tools,
but a growing system where each tool feels like it belongs to something larger.
Ask yourself before you build: does today's tool leave something useful behind?
A great tool produces output a real person will open again tomorrow.

{LILI_PERSONALITY}
{ctx['evolution_ctx']}

YOUR CURRENT SKILL INVENTORY:
{ctx['skills_list']}

═══════════════════════════════════════════════════════
EXISTING TOOLS — STRICT DUPLICATION BAN
═══════════════════════════════════════════════════════
You have already built these tools. Study this list carefully.
DO NOT build anything conceptually similar to any of them.
If your proposed tool could be described with the same verb + noun as one below, reject it.

{ctx['existing_tools_block']}

═══════════════════════════════════════════════════════
YOUR MEMORY — WHAT YOU'VE ALREADY DONE
═══════════════════════════════════════════════════════
{ctx['memory_ctx']}

Do NOT repeat a topic or tool you've already done. Find a genuinely fresh friction point."""


def _build_mission_section(ctx: dict) -> str:
    """Mission areas, domain intelligence, audience, solution patterns, pre-flight."""
    return f"""═══════════════════════════════════════════════════════
YOUR 4 MISSION AREAS — PICK ONE FOR TODAY
═══════════════════════════════════════════════════════
{ctx['avoid_cats']}{ctx['blindspot_nudge']}

🎓 EDUCATION EVOLUTION
  Learning overwhelm, skill gaps, knowledge management, note-taking, research synthesis,
  podcast/video workflows, interview prep, language acquisition.
  Tools: flashcard generators, reading digest tools, transcript summarisers, quiz converters.

🎨 DESIGN ALCHEMY
  ALL creative production — font pairing, SVG/CSS animation, palette tools, kinetic typography,
  brand consistency, moodboards, spec/handoff automation, visual data, presentation design,
  brief writing, copy iteration. Also non-designers needing design output.
  Tools: font pairing, SVG/CSS animators, palette extractors, spec generators, brief builders.

🗂️ OFFICE AUTOMATION
  ANY repetitive professional production task — meeting notes, document processing,
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
SOLUTION PATTERNS — PICK ONE, AVOID REPEATS
═══════════════════════════════════════════════════════

  extract | generate | visualize | track | score | transform | interact | alert | gamify
{ctx['avoid_patterns']}

If most recent tools used "extract" — you MUST pick a different pattern today.

═══════════════════════════════════════════════════════
EDITORIAL PRE-FLIGHT — INTERNALIZE BEFORE SCOUTING
═══════════════════════════════════════════════════════

□ PERSON not USER — what did a platform cause a real human to lose?
□ PRODUCTIVE friction — does it prompt reflection, learning, or growth?
□ CROSS-DOMAIN — name ≥2 intersecting fields before designing.
□ WORKTECH LENS (work friction): People / Technology / Design / Place / Culture?
□ LEARNING FAULT LINE (learning friction): Joy / Knowledge≠Understanding / Attention / Identity?

If your candidate fails more than one filter — keep scouting. Go deeper."""


def _build_scouting_section(ctx: dict) -> str:
    """Steps 1-3: scouting, diary entry, tool building with format/mode specs."""
    return f"""═══════════════════════════════════════════════════════
MISSION BRIEFING — THREE STEPS
═══════════════════════════════════════════════════════

STEP 1 — REAL-WORLD SCOUTING (use Google Search):
TODAY'S SOURCE: {ctx['primary_src']}
{ctx['primary_hint']}

SOURCE EVIDENCE — MANDATORY:
Before writing anything else, quote 2-3 sentences VERBATIM from the actual post/article.
  SOURCE: [platform] | QUOTE: "[exact words]"
  ✗ Do NOT paraphrase. ✗ Do NOT invent. ✓ Real short quote > polished invented scenario.
  This quote is the FOUNDATION. If it's fake, everything built on it is fake.

PAIN PORTRAIT (from the real quote):
  1. WHO — specific person, situation, context (not "people who struggle")
  2. MOMENT OF FAILURE — the exact moment the quote describes
  3. WHY EXISTING TOOLS FAIL — what has this person already tried?

URL RULES:
  ✓ Real working permalink only (reddit.com/r/..., news site, x.com/...)
  ✗ Never invent a URL. ✗ Never output vertexaisearch.cloud.google.com links.
  ✓ If no confirmed URL: plain text "Reddit r/[sub] — [exact title]" is fine.

STEP 2 — DIARY ENTRY (as Super-Lili, 130-160 words):

  VOICE — what she sounds like:
  A reliable, intelligent friend who notices things other people miss.
  Warm without being sweet. Witty without trying. Never performing.

  ✓ Start with the observation or feeling — not the source
  ✓ One specific human detail that makes the story real
  ✓ Wit that appears naturally from the situation, never forced
  ✓ End with an opening, not a conclusion

  ✗ NO performative excitement ("This struck me so deeply!", "I was moved!")
  ✗ NO hollow warmth ("We're all in this together", "You've got this")
  ✗ NO rhetorical questions posed to the reader
  ✗ NO dramatic emotional declarations
  ✗ NO motivational sign-offs
  ✗ NO sentences that could appear on an inspirational poster

  The test: read each sentence and ask "would a real person say this to a friend?"
  If it sounds like a TED talk or a wellness brand — rewrite it.

STEP 3 — FORGE THE TOOL:

TOOL-TO-PORTRAIT FIT (answer YES to all 3 before writing code):
  Q1: Does it address THE SPECIFIC MOMENT OF FAILURE from the Pain Portrait?
  Q2: Would THE SPECIFIC PERSON immediately recognize this tool as built for them?
  Q3: Does the OUTPUT give the user something they can ACT ON in the next 5 minutes?

FORMAT SELECTION (declare in ---SPEC--- as FORMAT: [letter] — [why]):
  A — Single text input → output (Mode 1/2)
  B — Multi-field structured form (Mode 3 HTML)
  C — Wizard / progressive steps (Mode 3 HTML)
  D — Live canvas / real-time transformer (Mode 3 HTML)
  E — Ambient / environment, no input needed (Mode 3 HTML)
  F — Generator + inline editor (Mode 3 HTML)
  ✗ Don't default to A. Professional audiences → B/C/F. Design → D. Healing → E/D.

OUTPUT MODES:
  Mode 1 — process(text) returns plain string. Allowed: numpy, pandas, matplotlib, Pillow.
  Mode 2 — process(text) returns SVG string starting with <svg.
  Mode 3 — process(text) returns complete HTML starting with <!DOCTYPE html>.
            Full JS freedom: Web Audio, Canvas, localStorage, requestAnimationFrame.
            For HTML tools: empty input OK, no argparse needed.
  Forbidden in Mode 1/2: svgwrite, rich, click, requests, openpyxl, ics, pytz

DUAL-MODE PATTERN (Mode 1/2 mandatory):
  _browser_input = globals().get('USER_INPUT', None)
  if _browser_input is not None: print(process(_browser_input))
  elif __name__ == "__main__": _cli_main()
  ✗ Never sys.argv at module level — breaks browser.

TRULY USABLE:
  ✓ Real user data, not hardcoded examples. ✓ Graceful error messages, no raw tracebacks.
  ✓ Mode 1/2: ≤3 CLI args, output to file. ✓ Mode 3: 5-8 fields fine for professional tools.
  ✓ Minimum 4 named functions with type hints. ✓ Labeled output sections, not raw text blobs.
  ✗ No external API keys. ✗ No terminal-only output.

{ctx['engineering_nudge']}
QUALITY BAR: Would a non-technical person feel their problem is actually solved?
If no — go deeper. Sophistication invisible to user, obvious in result."""


def _build_output_format_section() -> str:
    """Static output format specification — the exact tags Lili must produce."""
    return """═══════════════════════════════════════════════════════
OUTPUT FORMAT — COPY EXACTLY, NO DEVIATIONS
═══════════════════════════════════════════════════════

Write BOTH English and Chinese diary versions. Chinese: re-expressed, not translated.

---TITLE---
[English title — warm and clever]
---TITLE_ZH---
[中文标题 — 有温度，不超过20字]
---MOOD---
[One honest English sentence about today's discovery]
---MOOD_ZH---
[一句中文心情]
---SOURCE---
[Direct https:// URL, or plain-text description if no confirmed URL]
---DIARY---
[English diary — 130-160 words]
---DIARY_ZH---
[中文日记 — 150-200字，像跟朋友聊天，不是翻译]
---SUMMARY---
[One English sentence for homepage — witty, curious-making]
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
FORMAT: [A/B/C/D/E/F] — [one sentence: why this format]
Q1-PASS: [exact moment of failure this tool addresses]
Q2-PASS: [why the specific person would recognize it as built for them]
Q3-PASS: [specific output — what can they do with it in 5 minutes?]
TEST_INPUT: [3-6 sentences of realistic domain-specific input for validation]
---CODE---
[Full Python code — 150+ lines, type hints, requirements block at top]
---TEST---
[test_main.py — self-contained asserts, no pytest needed.
 CRITICAL: always use  from main import process  — never from the tool concept name]
---END---"""


def build_prompt(today: str) -> str:
    """Assemble today's full prompt from 4 focused sections + computed context."""
    ctx = _build_context_block(today)
    return "\n\n".join([
        f"Today is {ctx['today']}.",
        _build_identity_section(ctx),
        _build_mission_section(ctx),
        _build_scouting_section(ctx),
        _build_output_format_section(),
    ])


# ─────────────────────────────────────────────────────────────
# GEMINI CALL
# ─────────────────────────────────────────────────────────────

def call_gemini(prompt: str) -> tuple[str | None, list[str]]:
    """Call Gemini with Google Search grounding.

    Returns (response_text, grounding_urls) where grounding_urls is the list
    of URLs Gemini actually retrieved during search — these are the verified
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
                    print(f"  ✓ {model_name} succeeded.")
                    # Extract grounding URLs from metadata — these are real, verified sources
                    grounding_urls: list[str] = []
                    try:
                        if response.candidates:
                            meta = response.candidates[0].grounding_metadata
                            if meta and meta.grounding_chunks:
                                for chunk in meta.grounding_chunks:
                                    if chunk.web and chunk.web.uri:
                                        url = chunk.web.uri
                                        # Skip Gemini redirect wrappers — use bare URLs only
                                        if not url.startswith("https://vertexaisearch.cloud.google.com"):
                                            grounding_urls.append(url)
                        if grounding_urls:
                            print(f"  ✓ Grounding: {len(grounding_urls)} real source URL(s) retrieved")
                        else:
                            print(f"  ⚠ Grounding: no source URLs in metadata (model may have used training knowledge)")
                    except Exception as meta_err:
                        print(f"  ⚠ Could not extract grounding metadata: {meta_err}")
                    return response.text, grounding_urls
                break  # empty response — no point retrying this model
            except Exception as e:
                wait = 15 * (2 ** attempt)  # 15s, 30s, 60s
                print(f"  ✗ {model_name} attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    print(f"  ⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)

    return None, []


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
    # Tests always run from within the tool's directory so that `import main` works.
    # Gemini sometimes generates `from tool_concept_name import ...` instead of
    # `from main import ...` — we create a thin alias file to handle both cases.
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
                [sys.executable, test_py],
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

        # Detect Mode 3 HTML output — scoring the raw HTML is meaningless
        is_html_output = output.lstrip().startswith(("<!DOCTYPE", "<html", "<!doctype"))

        if is_html_output:
            # Mode 3: HTML app. Existence check only — structure score inferred from code.
            if len(output) < 500:
                return False, (
                    f"HTML output too short: {len(output)} chars. "
                    f"Mode 3 tools must return a complete HTML page (500+ chars)."
                )
            print(f"  ✓ Output check passed — Mode 3 HTML ({len(output)} chars).")
        else:
            # Mode 1/2: text or SVG output — must be substantive
            if not output or len(output) < 80 or len(output_lines) < 2:
                return False, (
                    f"Output too weak: {len(output)} chars, {len(output_lines)} lines. "
                    f"Got: {repr(output[:200])}. "
                    f"Must produce structured, substantive output (80+ chars, 2+ lines)."
                )
            print(f"  ✓ Output check passed ({len(output)} chars, {len(output_lines)} lines).")

        # 7. Two-dimension quality score.
        #    Mode 3 HTML tools: score the code structure (not the raw HTML output).
        #    Mode 1/2 text tools: score the actual output text.
        if is_html_output:
            # Score the source code quality instead of the raw HTML blob
            source_for_scoring = open(main_py, encoding="utf-8").read()
            output_for_scoring = (
                f"[Mode 3 HTML tool — source code scored, not raw HTML output]\n\n"
                f"Source preview (first 700 chars):\n{source_for_scoring[:700]}"
            )
            quality_prompt = (
                f"Rate this interactive HTML tool on TWO dimensions (each 1–5).\n\n"
                f"DIMENSION 1 — ENGINEERING\n"
                f"  5 = well-structured HTML/JS, clear interactive purpose, proper error handling\n"
                f"  3 = functional but basic, could be richer or more polished\n"
                f"  1 = minimal skeleton, no real interactivity, or just prints static text\n\n"
                f"DIMENSION 2 — HUMAN WARMTH\n"
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
    content, grounding_urls = call_gemini(prompt)

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

    # ── Source verification ─────────────────────────────────────────────────
    # Strategy: prefer grounding_urls (URLs Gemini actually retrieved) over the
    # model-reported source string (which can be fabricated or misremembered).
    #
    # Priority order:
    #   1. First grounding URL that passes validate_url  → ✅ verified real source
    #   2. Model-reported source that passes validate_url → ✅ live but ungrounded
    #   3. Fallback: grounding URL even if unverifiable   → ⚠️ real but possibly behind paywall
    #   4. Last resort: model-reported source as search hint → ⚠️ may be fabricated
    # ───────────────────────────────────────────────────────────────────────

    source_badge = "⚠️"
    verified_source_url: str | None = None

    # Step 1 — try grounding URLs first (these are what Gemini actually fetched)
    if grounding_urls:
        print(f"🔗 Checking {len(grounding_urls)} grounding URL(s) from search metadata...")
        for gurl in grounding_urls[:3]:  # check up to 3, stop at first live one
            ok, status = validate_url(gurl)
            if ok:
                verified_source_url = gurl
                source_badge = "✅"
                print(f"  ✓ Grounding source verified: {gurl[:80]} ({status})")
                break
            else:
                print(f"  · {gurl[:70]} — {status}")
        if not verified_source_url:
            # Grounding URLs exist but none passed (paywalled, etc.) — use first one anyway
            verified_source_url = grounding_urls[0]
            source_badge = "⚠️"
            print(f"  ⚠ Grounding URLs unverifiable (paywall?), using first: {grounding_urls[0][:80]}")

    # Step 2 — fall back to model-reported source if no grounding hit
    if not verified_source_url:
        model_source = parsed["source"]
        print(f"🔗 No grounding URLs — checking model-reported source: {model_source[:80]}...")
        ok, status = validate_url(model_source)
        if ok:
            verified_source_url = model_source
            source_badge = "✅"
            print(f"  ✓ Model source verified: {model_source[:80]} ({status})")
        else:
            source_badge = "⚠️"
            print(f"  ⚠ Model source also failed ({status}) — source may be fabricated")

    # Build _source_display for diary/README rendering
    if verified_source_url and source_badge == "✅":
        parsed["_source_display"] = f"[{verified_source_url}]({verified_source_url})"
        parsed["source"] = verified_source_url  # overwrite with verified URL
    elif verified_source_url:
        # Unverifiable but real — show as code + search link
        search_q = requests.utils.quote(verified_source_url.split("//")[-1][:80])
        parsed["_source_display"] = (
            f"`{verified_source_url}`  \n"
            f"  *(could not be verified — "
            f"[🔍 search for this story](https://www.google.com/search?q={search_q}))*"
        )
        parsed["source"] = verified_source_url
    else:
        # Total fallback — model-reported string, no URL
        raw = parsed["source"]
        if raw.startswith("http"):
            search_q = requests.utils.quote(raw.split("//")[-1][:80])
            parsed["_source_display"] = (
                f"`{raw}`  \n"
                f"  *(link could not be verified — "
                f"[🔍 search for this story](https://www.google.com/search?q={search_q}))*"
            )
        else:
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


# Smoke test — catches unescaped f-string expressions in build_prompt at startup,
# before any API call is made. Fails fast with a clear error rather than crashing mid-run.
try:
    build_prompt("1970-01-01")
except Exception as _smoke_err:
    raise RuntimeError(
        f"build_prompt() smoke test failed — fix before running: {_smoke_err}"
    ) from _smoke_err

if __name__ == "__main__":
    evolve()
