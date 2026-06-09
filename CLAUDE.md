# CLAUDE.md — Super-Lili Project Memory

> Written for the Claude agent picking up this project. Read this first.
> Last updated: 2026-06-05 · Updated monthly.

---

## What This Project Is

**Super-Lili's Daily Adventure** is a self-evolving AI toolbox project.

Core mechanism:
- Lili (Gemini) runs automatically every day, finds a real human friction point, writes a bilingual diary entry, and builds a browser-native tool
- Every Sunday: self-evolution — reviews the week's tools, updates her own engineering rules and soul config
- Users can commission specific tools via GitHub Issues

### Ultimate Goal (do not paraphrase)

```
Super-Lili's ultimate purpose is to become a self-evolving personal super toolbox —
and over time, a PKM (Personal Knowledge Management) system designed specifically
for creative professionals.
```

**Three stages:**
- Stage 1 (now): Daily tools solving specific creative friction points
- Stage 2 (soon): Curated toolkit — 50-100 quality tools covering media/editorial/design/brand/tech/research
- Stage 3 (later): Tools that know YOU — your projects, your voice, your clients — a living creative workspace that grows with you

**Quality standard:**
The project owner (xiaojiahaina) is a senior media editor and editorial director with 15+ years in top-tier media, with deep networks in global design, tech, creative, and luxury industries. Tools must meet the standard of this circle: no amateur output, no generic templates, nothing that would embarrass a professional in front of colleagues.
The test: would a senior journalist, creative director, or brand strategist use this tool twice?

**Future display strategy:** Do not show every generated tool. Curate 100 genuinely high-value tools for the website. The rest lives in GitHub but stays off the homepage.

---

## Project Evolution History

### Phase 1 — Origin (2026-04-29)
- Started as "Clarity Compass", a simple Python script generator
- Renamed to Super-Lili's Daily Adventure
- Basic structure: GitHub Actions runs daily, tools saved to `02_Skills/`
- Tools were Python scripts only — no browser experience

### Phase 2 — Soul Added (early May 2026)
- `5a5cd67` Super-Lili v2: warm personality, URL validation, weekly evolution, diary README
- `d4c6bc5` Memory system: Lili remembers all past tools and topics, never repeats
- `c0d732f` Bilingual support: EN + Chinese diary — Chinese is re-expressed, not translated
- Tool directory renamed from `02_Skills/` to `02_Toolbox/`

### Phase 3 — Engineering Quality (mid May 2026)
- `e7f08c9` Created `lili_engineering.py` — engineering standards extracted from prompts, permanently stored
- `8ce7e7e` Unlocked Mode 3: tools can return full HTML pages, run in sandboxed browser iframe
- `cbabb03` Raised quality ceiling: per-category benchmarks, richness standard
- `c0b43f0` Audience rotation: each day targets a different professional group (media, design, PM, research)
- `1a0d4c9` Two-dimension quality scoring: Engineering + Warmth scores written to ledger, read by weekly evolution

### Phase 4 — Website (mid-late May 2026)
- Migrated from README-driven to GitHub Pages website
- `6a8fa0e` Emoji reactions on all 28 tool pages (localStorage)
- `09a8baf` System architecture page (dark visual flow diagram)
- `1d83301` Instant tool experience: Mode 3 pre-render + Mode 1/2 auto-run on load

### Phase 5 — Design Philosophy (late May 2026)
- `8e28d6b` Injected industrial design philosophy: Dieter Rams, Jasper Morrison, Naoto Fukasawa, Jonathan Ive
- `054d6a7` Tried dark design (aged paper black + film grain + terracotta accent)
- `3639164` Dark design rolled back — owner felt it was wrong, restored white design
- `55e808f` Injected north star: Lili builds a coherent toolkit, not random daily tools
- `cd66547` Refactored `build_prompt()`: split 628-line monolith into 5 focused functions

### Phase 6 — Voice Purification (2026-05-31)
- `094fb2f` Banned performative writing in diary: no "This struck me so deeply!" type sentences
- `36170dc` Same rule extended to weekly evolution reports

### Phase 8 — ReAct Architecture & Stability (2026-06-03 to 2026-06-05)
- **Fix**: stale source proposals entry in evolution journal (merged into weekly report)
- **Fix**: teal tool button disappeared on evolution days (falls back to latest tool)
- **Engineering rules upgrade** (`lili_engineering.py` LILI_ENGINEERING_LESSONS):
  - Transform-first architecture: input structure != output structure = real transformation
  - Algorithmic depth floor: must do one thing the user can't do themselves in 10 seconds
  - HTML three-state machine: entry state -> active state -> result state
  - Output density test: every sentence must fail the input-replacement test or get cut
- **Issue commission system**: user opens Issue -> Lili responds (lili_responds.py adds lili-responded label) -> next day Lili prioritises building from that Issue -> marks lili-built label on completion
- **Manually built Sun Light Color Clock** (Issue #1 — API quota exhausted, Lili couldn't run herself)
- **Clock redesigned**: from cold digital digits to analog face with hands and smooth second hand
- **Rule 16**: physical world as emotional foundation — Lili's tools are digital, their emotional register must be physical
- **Design lineage expanded**: added Inga Sempé, Ilse Crawford, Hella Jongerius (alongside Rams, Morrison, Fukasawa, Ive)
- **Pyodide fix**: detects `rich`/`requests` and other incompatible libraries, switches to "run locally" instructions
- **Loading UX**: shows "~15 seconds" warning, auto-demo adds a note guiding users to try their own input

### Phase 8 details

**ReAct 5-phase architecture** — `super_lili_brain.py` refactored from single-pass prompt to staged pipeline:
```
Phase 1 SCOUT  — Gemini searches web, finds friction point, writes diary (call_gemini with search tool)
Phase 2 SPEC   — Designs tool architecture, validated BEFORE any code is written (call_gemini_simple)
Phase 3 BUILD  — Writes code from approved spec only (call_gemini_simple, 3 attempts, 15s retry delay)
Phase 4 EVALUATE — validate_tool() runs inside BUILD loop: syntax, browser-compat, output quality, Critic check, Win Rate
Phase 5 REFLECT — save_diary(), update_readme(), add_tool() to memory, mark_issue_built() if commission
```

**validate_spec() mechanical gate** — spec must pass before BUILD phase is allowed:
- `INPUT_MODEL` and `OUTPUT_MODEL` must differ structurally
- `ALGORITHMIC_DEPTH` >= 10 chars (non-trivial computation description)
- `Q1_PASS`, `Q2_PASS`, `Q3_PASS` each >= 10 chars
- `TEST_INPUT` >= 15 chars
- On failure: precise error message fed back to Gemini as `spec_feedback` for retry (max 2 attempts)

**parse_spec_response() multi-line fallback**:
- Primary: extract between `---SPEC_START---` and `---SPEC_END---`
- Fallback: if tags missing, search entire response
- Field parser collects continuation lines (up to 4 lines) until next `ALL_CAPS:` key

**BUILD retry with 15s delay**: `continue` (not `break`) on empty response, 15s sleep before each retry

**Python source file Unicode restriction** — CRITICAL:
- `super_lili_brain.py` must NOT contain em-dash (U+2014), en-dash (U+2013), checkmarks (U+2713 U+2717), or other non-ASCII Unicode in string literals or f-strings
- GitHub Actions Python 3.11 raises `SyntaxError: invalid character` for these
- Use ASCII equivalents: `-` for dashes, `[OK]`/`[NO]` for checkmarks, `->` for arrows
- PostToolUse hook auto-checks syntax after every edit (see `.claude/settings.local.json`)

**PostToolUse syntax check hook**: configured in `.claude/settings.local.json` — runs `ast.parse()` on every Edit/Write to `super_lili_brain.py`, surfaces `SYNTAX ERROR` immediately before push

---

## Key Architecture Decisions

### Three Tool Modes
- **Mode 1**: `process(text)` returns plain text
- **Mode 2**: `process(text)` returns SVG string
- **Mode 3**: `process(text)` returns full HTML page (runs in sandboxed iframe — Web Audio, Canvas, localStorage all available)
- **Direction**: all new tools default to Mode 3. Healing Inventions must be Mode 3.

### Category System
- 🎨 Design Alchemy
- 🎓 Education Evolution
- 🗂️ Office Automation
- 🌿 Healing Inventions — capped at ~20% of tools

### Issue Commission Flow
```
User opens Issue
  → lili_responds.py replies same day, adds lili-responded label
  → Next day: evolve() detects lili-responded without lili-built
  → Skips random topic selection, builds from Issue content
  → Adds lili-built label, posts tool link in Issue comment
```

### Website Generation
- `docs/generate_site.py` reads all tools and diaries, generates static HTML
- Tool pages auto-detect: Mode 3 → pre-rendered iframe; Mode 1/2 → Pyodide runner (auto-demo); incompatible libraries → local run instructions
- `generate_site.py` is called automatically after every `evolve()` run

---

## Owner Aesthetic Preferences

This is the most important section. Lili's tools must meet these standards.

**Physical world warmth** (Rule 16)
> Before designing any tool, ask: in a world without screens, what object would do this job?
> Clocks need hands, not digits. Progress needs arcs, not bars. If a shape can carry the meaning, don't use a number.

**Design lineage** (Rule 15)
- Dieter Rams: less, but better
- Jasper Morrison: quiet, undemanding, rewards daily use
- Naoto Fukasawa: fits the body and the rhythm of daily life
- Jonathan Ive: surface simplicity concealing deep craft
- Inga Sempé: poetic tension between handmade and manufactured
- Ilse Crawford: the senses are design material — warmth, texture, weight
- Hella Jongerius: colour has memory, material has depth

**Target users**
Creative professionals: journalists, editors, designers, brand directors, creative directors.
Not general users. Not engineers. They have high standards and will immediately feel whether a tool was truly made for them.

---

## lili_editor.py — Critical Context

`lili_editor.py` is Lili's **internal operating system** — how she sees the world before she acts. It does not appear in her diary, but it determines what Lili looks for, how she judges, and what she builds.

Written by project owner xiaojiahaina, based on the neo-slow media framework (2021–present).

**Three core editorial lenses:**

1. **Users vs People** — Platforms see humans as users (predictable, quantifiable, monetizable). Lili reads through that frame to the person underneath. User complaints produce utility. People complaints produce meaning. Lili builds tools that aim for the second.

2. **Entertain vs Engage** — Entertainment ends when the screen closes. Engagement leaves a change behind after the tool is closed. Lili's tools aim to engage, not entertain. The test: after using this tool, is the person in a different relationship with their work, learning, or attention?

3. **Consumptive vs Productive Friction** — Core insight from neo-slow media thinking. Not all friction is the enemy. Consumptive friction (bureaucratic loops, platform complexity) drains without return. Productive friction (questions that make you stop and think, necessary difficulty of learning) demands something and returns more. Lili's tools introduce productive friction and eliminate consumptive friction.

**Also contains:** deep domain knowledge across 4 creative work areas (work/learning/healing/design), audience rotation mechanism (media/design/PM/research), domain expansion system (weekly evolution adds new domain knowledge).

---

## Unfinished / Future Direction

- **Open to public**: once Issues are open to real users, authentic needs become the best evolution fuel
- **Quality ceiling**: current tools are uneven — 34 tools, maybe 2-3 reach "creative professional uses it weekly" standard. Direction is right, needs time

---

## Future Backlog — Good Ideas, Wrong Timing

Ideas discussed and consciously deferred. Revisit when conditions are right.

**Curation**
- Curation mechanism: build a "top 100" display system. Owner marks tools they've actually used; website shows only curated selection. Wait until 50+ tools accumulated and quality stabilizes.

**Visual**
- Radiooooo-style design: warm retro color palette, colorful icons, map/timeline navigation. Wait until 50+ tools accumulated — the visual language needs content density to work.

**Architecture**
- Deep SCOUT: read industry reports and long-form forum discussions, not just Reddit post titles. Owner can inject observations via GitHub Issues in the meantime. Requires more API calls — defer until Gemini quota is stable.
- Agentic RAG for SCOUT: inspired by Google's Agentic RAG (6-agent framework, 34% accuracy gain). Two specific upgrades worth adding: (1) Query Rewriter — rewrite vague search terms into precise ones before searching; (2) Sufficient Context Agent — after SCOUT, validate "is this friction point real and specific enough?" before proceeding to SPEC. If not sufficient, search again from a different angle. Small change to pipeline, meaningful quality improvement. Defer until 2-week stability check passes.
- Parallel agent architecture: SCOUT and SPEC running simultaneously. Currently serial pipeline is sufficient; revisit when run time becomes a bottleneck.
- Lili modifies her own core code (super_lili_brain.py): via PR review flow — Lili proposes, owner approves. Revisit after 2 weeks of stable quality runs (from 2026-06-08).

**Quality & Memory**
- Error frequency quantification: track how many times each error pattern repeats across weeks. Currently errors are logged as text but not counted. Would make weekly evolution more precise.
- Structured memory system: upgrade lili_memory.json to include failure_patterns, deepseek_verdict, was_shell fields per tool. Enables evolution reports to say "js_in_fstring error occurred 3 times this week" instead of vague "improve code quality". Build after 2 weeks of stable runs when real failure patterns emerge.
- Real selection pressure: self-evolution is only meaningful with real user feedback. Tools need actual users who return (or don't). Without this, evolution is self-referential.
- /schedule daily quality check: Claude checks today's tool at 10:00 Beijing time. Blocked by claude.ai remote connection issue as of 2026-06-08. Retry periodically.

**Alternative Direction**
- Lili as Curator, not Creator: instead of building tools from scratch, Lili discovers the best existing tools for creative professionals, evaluates them, writes usage guides, and embeds them directly into the static site. Core value shifts from "original tool maker" to "trusted creative toolkit curator" — closer to the owner's editorial strengths and neo-slow media philosophy. Revisit if tool quality remains unstable after the first two weeks of stable runs.

**Inspiration**
- auto_research system (github.com/zartbot/blog/tree/main/auto_research): generates deep technical research reports automatically. Not directly applicable to Lili's creative-professional focus, but the deep synthesis approach is worth studying.
- Owner can submit GitHub Issues with real-world phenomena and articles as tool inspiration — higher quality than random Reddit SCOUT.

---

## Pitfalls Logged

- **Dark design experiment**: tried aged paper black + terracotta, owner felt it was wrong, rolled back
- **Performative writing**: early diary entries full of hollow phrases ("This moved me so deeply"), banned via rules
- **Source proposals file**: weekly evolution generated a standalone source-proposals.md, site rendered it as a journal entry. Fixed: merged into weekly report
- **git add . pulled in .claude/**: caused embedded git repository warning. Added to .gitignore
- **Healing category overload**: at one point 53% of tools were Healing Inventions, capped to 20% via rotation mechanism
- **Pyodide doesn't support rich**: Content_Current_Catalyst used rich library, broke in browser. Fixed: auto-detects and shows local run instructions instead
- **Unicode in Python source causes SyntaxError on GitHub Actions**: em-dash, en-dash, checkmarks in f-strings/docstrings break Python 3.11. Fixed: replaced all with ASCII equivalents. Local Python 3.13 is stricter and catches these too.
- **Missing closing triple-quote after f-string edit**: adding lines inside an f-string without preserving the closing `"""` silently breaks the entire function and the one after it. Always verify `ast.parse()` passes after edits.
- **validate_spec thresholds were too strict**: fields with multi-line values got truncated to <20 chars by single-line parser, causing false rejections. Fixed: relaxed thresholds + multi-line field parser.
- **API quota exhausted from repeated manual triggers**: each run consumes 6-8 Gemini calls. Triggering 5+ times in a day depletes the free tier daily quota. Wait for quota reset (midnight UTC) before retrying.
- **Rest day diary blocks rerun**: if `save_rest_day()` runs and pushes a diary file, subsequent triggers skip because diary exists. Must delete the file from GitHub before retriggering.
