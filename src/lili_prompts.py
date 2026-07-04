"""
lili_prompts.py - All prompt construction: context data, rotations,
episodic memory, and the SCOUT / SPEC / BUILD prompt builders.
"""

import os
import json
from datetime import datetime
from pathlib import Path

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
  Pick the format the tool's CORE VALUE actually needs - do not force everything into one mode.
  [OK] Pick A (Mode 1/2) when the value is the computed RESULT and text/SVG delivers it fully.
  [OK] Pick B/C/D/E/F (Mode 3 HTML) when the value genuinely needs live interaction:
       dragging, real-time preview, canvas drawing, progressive input, in-place editing.
  CRITICAL for Mode 3: the JavaScript must do REAL work with the user's input - parse it,
  compute from it, build the DOM from it at runtime. Any of these = automatic rejection:
    [NO] CSS-only toggles pretending to be logic   [NO] hardcoded lookup tables / preset answers
    [NO] pre-filled data-* attributes in the HTML  [NO] output identical regardless of input
  If you cannot make the JS genuinely compute from input, fall back to Mode A instead of faking it.

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

DIFFERENTIATION RULE (critical - Critic will reject for this):
  If the tool analyses multiple items from input (words, phrases, sentences, ideas),
  EACH item's output MUST be visibly different from every other item's output.
  [NO] Do NOT reuse the same sentence structure for different items.
  [NO] Do NOT copy-paste interpretations with only the subject noun swapped.
  [OK] Each item must surface a UNIQUE insight derived from that specific item's content.
  Test yourself: if you swapped two items' outputs, would a reader notice? If no - rewrite.

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
2b. SELF-CONTAINMENT (critical): the tool is ONE file with NO database, NO corpus, NO
   pretrained model, NO internet. The depth MUST compute from the user's own input -
   measuring structure, patterns, ratios, positions, consistency, or relationships WITHIN
   the text they provide. NEVER promise "comparison against a curated corpus / database of
   exemplars / industry benchmark / trained model" - the tool cannot contain that, so it
   would be faked and rejected. Ask: can this run with ZERO external data? If no, redesign.
3. For Mode 3 HTML: define all 3 UI states (Rule 19)
4. Q1/Q2/Q3 must be specific and verifiable - not vague

FORMAT OPTIONS:
  A - Single text input -> computed output (Mode 1/2 - Python text or SVG)
  B - Multi-field form (Mode 3 HTML)
  C - Wizard / progressive steps (Mode 3 HTML)
  D - Live canvas / real-time transformer (Mode 3 HTML)
  E - Ambient / environment, no input needed (Mode 3 HTML)
  F - Generator + inline editor (Mode 3 HTML)

FORMAT ROUTING - choose by what can be reliably BUILT and VALIDATED, not by what looks fancy:
  >> If the tool's core value is COMPUTING something FROM text the user provides
     (analyze, score, extract, rank, diff, restructure, summarise, detect, compare
     parts of the input against each other) -> ALWAYS Format A (Mode 1/2).
     Reason: Mode 1/2 tools are executed for real and judged on their ACTUAL output.
     The same tool wrapped in HTML renders a static-looking preview and gets rejected
     as "fake / does nothing with input" - because the analysis is exactly what Mode 1/2
     already does honestly. Do NOT wrap analysis in a UI.
  >> Choose Mode 3 (B-F) ONLY when the value is genuinely interactive or ambient and
     literally cannot exist as computed text/SVG:
       D - real-time visual manipulation (dragging, drawing, live canvas)
       E - ambient/generative artifact with NO input analysis (a clock, a soundscape,
           a generative visual that just runs)
       F - generator where in-place editing IS the point
       B/C - only if the multi-step interaction itself is the core value, not decoration
  >> Litmus test: "does the user paste text and get insights back?" -> that is Format A.
     When unsure, choose A. A real computed result beats a pretty shell that fakes it.

OUTPUT FORMAT - YOU MUST OUTPUT THESE EXACT TAGS OR THE SPEC WILL BE REJECTED:
---SPEC_START---
FORMAT: [A/B/C/D/E/F] - [one sentence: why this format]
MODE: [1/2/3] - [why]
INPUT_MODEL: [exact structural description - what shape is the data the user provides?]
OUTPUT_MODEL: [exact structural description - what shape is the result? MUST differ from input]
TRANSFORMATION: [one sentence: what specifically changes from input to output]
ALGORITHMIC_DEPTH: [a CONCRETE step-by-step mechanical procedure a programmer could implement verbatim - name the actual operations. NOT an aspiration. BAD: "structure the debate into insightful chapters". GOOD: "1. split on speaker-turn markers (regex for 'Name:' or blank-line breaks); 2. group consecutive same-speaker turns; 3. label each group by its 3 highest term-frequency content words; 4. mark a topic shift wherever lexical overlap between adjacent turns drops below 0.2". Every step must run on the input alone with stdlib/numpy - no semantic 'understanding', no LLM, no external data.]
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


def build_code_prompt(today: str, scout: dict, spec: dict, feedback: str = "", slim: bool = False,
                      prev_code: str = "") -> str:
    """Phase 3 - BUILD: write code from approved spec only.
    slim=True omits the engineering_nudge block for DeepSeek fallback (token budget).
    prev_code: the previous attempt's code. When provided together with feedback,
    the prompt switches to PATCH MODE: repair the named problem instead of
    regenerating from scratch (a rejected tool is usually 90% good code).
    """
    ctx = _build_context_block(today)

    if feedback and prev_code:
        feedback_block = (
            f"\n⚠ PATCH MODE - your previous code failed validation for this SPECIFIC reason:\n"
            f"{feedback}\n\n"
            f"YOUR PREVIOUS CODE (mostly good - do NOT start over):\n"
            f"```python\n{prev_code}\n```\n\n"
            f"Fix ONLY what the failure reason requires. Keep everything that already works: "
            f"same structure, same function names, same working logic. Output the COMPLETE "
            f"corrected file in the required ---CODE--- format (not a diff).\n"
        )
    elif feedback:
        feedback_block = f"\n⚠ PREVIOUS BUILD FAILED - fix this specific problem:\n{feedback}\n"
    else:
        feedback_block = ""
    nudge_block = "" if slim else ctx['engineering_nudge']

    # Mode 3 (HTML) needs room for HTML+CSS+JS; Mode 1/2 stays tight to avoid truncation.
    _is_mode3 = spec.get("mode", "").strip().startswith("3") or spec.get("format", "").strip()[:1].upper() in ("B", "C", "D", "E", "F")
    _line_cap = 320 if _is_mode3 else 200
    _line_floor = "220" if _is_mode3 else "150"

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
[OK] {_line_floor}+ lines, type hints, requirements block at top
[OK] Implement EVERY step of the spec's Algorithmic depth literally - it is a procedure, not a
    suggestion. If it says "split on X, group by Y, rank by Z", write code that splits, groups,
    AND ranks. Do NOT shortcut to grabbing the first sentence or a random word.
[NO] REJECTED: processing only the start of the input, ignoring later parts (e.g. a second
    speaker, later paragraphs). Every distinct part of the input must affect the output.
[NO] NEVER hardcode a dictionary of expected inputs/outputs - the algorithm must work on ANY input
[NO] NEVER match keywords against a preset lookup table and return preset strings
[NO] NEVER assert external facts you cannot derive from the input text: syllable counts, word
    etymology, dictionary definitions, historical dates, population/statistics, "this word means X".
    The model does not know these reliably and WILL hallucinate them (e.g. wrong syllable counts) -
    the Critic rejects hallucinated facts outright. Only compute from what is measurable in the
    input itself: length, patterns, position, frequency, structure, user-provided context.
[NO] NEVER invent entries to make the output LOOK complete. Every row/section/item in the output
    must be traceable to a specific span of the input. If the input has no conclusion, do NOT
    emit a "Conclusion" entry with an invented timecode/position; if only 3 real items exist,
    output 3, not a padded 5. An honest short output beats a complete-looking fabricated one -
    the Critic rejects padding and invented entries as hallucination.
[NO] ANTI-PATTERN - this will be REJECTED:
    LOOKUP = {{"keyword1": {{"result": "..."}}, "keyword2": {{"result": "..."}}, ...}}
    return LOOKUP.get(user_input, default)
[OK] CORRECT pattern - compute from input:
    score = sum(weights[i] * features[i] for i in range(len(features)))
    result = transform(parse(user_input))
[NO] Forbidden in Mode 1/2: svgwrite, rich, click, requests, openpyxl, ics, pytz
[NO] NEVER require the input to follow a specific structure (exact section count, blank-line
    delimiters, specific headers, fixed field order). process(text) gets FREE-FORM TEXT from a
    real person typing naturally - it must parse loosely (regex, keyword search, sentence
    splitting) and produce a best-effort result. Never return an error like "Input must contain
    3 sections separated by blank lines" - that rejects every real user.
[OK] GRACEFUL DEGRADATION is mandatory: when your primary structural marker is absent
    (no speaker labels, no timecodes, no headers), FALL BACK to a coarser segmentation
    (paragraphs -> sentences -> fixed-size chunks) and still produce the best analysis the
    input allows. Returning a one-line "not found, please check the format" error is an
    automatic validation failure - honesty about limits belongs in a note appended to real
    output, never in place of output.
[NO] test_main.py must ONLY call process() (never any other function from main.py) with 2-3
    plain string inputs and assert simple properties (non-empty, length, substring present).
    A test that crashes with a Traceback (not a clean assert) means the test itself is buggy -
    keep it minimal and defensive.
[NO] NEVER write a bare top-level statement that calls a function or parses arguments outside
    a function body or outside `if __name__ == "__main__":`. test_main.py does
    `from main import process`, which sets __name__ to "main" (NOT "__main__"), so ANY unguarded
    top-level code still executes during that import and will crash the test before it even runs.
    Only function defs, class defs, constants, and imports are allowed at true top level.
[NO] NEVER use JS template literals (${{...}}) inside Python f-strings - use .format() or string concat instead
[NO] NEVER put HTML with JavaScript inside a Python f-string - JS curly braces break f-strings
[OK] For Mode 3 HTML: use jinja2.Template (already installed, available without listing in requirements.txt).
    Jinja2 uses {{{{ variable }}}} and {{% logic %}} - JS single braces {{}} pass through untouched, zero conflict.
[CRITICAL] The template string MUST be a RAW triple-quoted string: Template(r'''...''').
    The leading r is mandatory - it makes every backslash literal so CSS content:'\\2014',
    JS regex /\\d+/, and \\n inside scripts do NOT trigger a Python "line continuation" syntax error.
    Pattern: from jinja2 import Template
             TEMPLATE = Template(r'''<html><script>function run(v) {{ return v; }}</script><body>{{{{ result }}}}</body></html>''')
             html = TEMPLATE.render(result=computed_value)
    Never wrap HTML-with-JavaScript in an f-string - JS braces collide with f-string braces.

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
[Complete Python code - keep under {_line_cap} lines total - do NOT stop early - write every line until the file ends with the USER_INPUT block]
---TEST---
[test_main.py - from main import process - self-contained asserts - keep under 30 lines]
---BUILD_END---

IMPORTANT LINE LIMIT: The entire ---CODE--- section must be under {_line_cap} lines. If your design requires more, simplify: remove comments, shorten variable names, combine functions. A working tool within the limit is better than a truncated 800-line tool."""




# Smoke test - catches unescaped f-string expressions in build_prompt at import
# time, before any API call is made.
try:
    build_prompt("1970-01-01")
except Exception as _smoke_err:
    raise RuntimeError(
        f"build_prompt() smoke test failed - fix before running: {_smoke_err}"
    ) from _smoke_err
