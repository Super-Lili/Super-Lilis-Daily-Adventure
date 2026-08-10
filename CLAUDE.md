# CLAUDE.md — Super-Lili Project Memory

> Written for the Claude agent picking up this project. Read this first.
> Last updated: 2026-08-09 · Updated weekly (scheduled task refreshes this file and docs/FINDINGS.md every Sunday evening after weekly evolution).

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

**PostToolUse syntax check hook**: configured in `.claude/settings.local.json` — runs `ast.parse()` on every Edit/Write to any `src/*.py`, surfaces `SYNTAX ERROR` immediately before push

### Phase 9 — Model Sovereignty & Ground Truth (2026-07-03 to 2026-07-06)

The biggest overhaul since ReAct. Full details in `docs/ARCHITECTURE.md`; evidence-backed lessons in `docs/FINDINGS.md` (F-001 ~ F-010).

**Gemini fully removed** (quota exhaustion + paid upgrade never completed). New model roles:
| Phase | Model | Notes |
|-------|-------|-------|
| SCOUT | `qwen-plus` (DashScope web search via `extra_body={"enable_search": True}`, never `tools=[]`) | DeepSeek fallback |
| SPEC | `deepseek-reasoner` (R1) | falls back to v4-pro |
| BUILD | `deepseek-v4-pro` | `deepseek-chat` alias actually resolves to v4-flash (billing-confirmed) |
| Critic | `qwen3.7-max` | independent of BUILD model — breaks self-grading echo chamber |
| Weekly evolution / Issues | `deepseek-v4-pro` | |

Cross-provider fallback chain (R1 → v4-pro → qwen3.7-max); empty responses are retried (DeepSeek empties are transient, unlike Gemini where empty = quota gone).

**Module split**: `super_lili_brain.py` (2700 lines) → `lili_llm.py` / `lili_prompts.py` / `lili_validators.py` / `lili_pipeline.py` + 49-line entry shim. Actions entry unchanged.

**Validation stack (the core theme: every gate needs ground truth)**:
- Reliability routing: analysis tools ("paste text, get insights") → Mode 1/2 (executed for real); Mode 3 only for genuinely interactive/ambient concepts
- Mode 3 ground truth: Playwright headless browser fills input, clicks controls, asserts DOM changed. Fail-open (browser flake never causes false rest day). First live catch: 2026-07-06
- validate_spec new gates: self-containment (no corpus/database/pretrained promises), concrete algorithm (named mechanical steps, not aspirations)
- BUILD anti-hallucination rules: no external facts, no invented entries to complete a shape, graceful degradation mandatory (marker absent → paragraphs → sentences → chunks, never refuse)
- Critique-patch loop: retries repair previous code (PATCH MODE) instead of re-rolling from scratch; truncation failures clear prev_code

**Test suite**: `tests/` (53 unittest tests as of 2026-07-17, openai mocked, zero network) + `lili_tests.yml` CI on every push. Feedback loop: hours → seconds.

**FINDINGS.md**: evidence-backed record of AI capability boundaries (docs/FINDINGS.md). Every entry must name the specific models — reconstruct attribution from commit/billing history, never from memory of the current stack.

### Phase 10 — Self-Modification Guardrail & Statistical Ledger (2026-07-16 to 2026-07-17)

- `5d0091e` **Impossible-commission circuit breaker**: commissions previously retried daily forever, so an out-of-scope Issue could consume the whole week. Issue #5 (screenshot organization — needs vision AI + OCR a single-file sandboxed tool cannot have) ate 07-14~16. Fix: `mark_commission_attempt_failed()` in `lili_pipeline.py` — 1st failure posts an honest progress comment, 2nd adds a new `lili-blocked` label and posts a capability-boundary explanation; `fetch_tool_requests` skips blocked issues so the pipeline returns to free scouting the next day. Issue stays open (paused, not forgotten). See FINDINGS F-014.
- `0955e35` **Self-write guardrail** (closes the 2026-07-12 pitfall below): weekly evolution writes model-authored text directly into `.py` carrier files (`lili_soul.py`, `lili_blindspot.py`, `lili_engineering.py`) as triple-quoted string literals — the same failure class as embedding HTML/JS in Python (F-007), but for its own reflection text. `_sanitize_embedded()` escapes triple-quotes and trailing backslashes before embedding; `_guarded_write()` runs `ast.parse()` + `exec()` + a required-names check *before* persisting, and on any failure keeps last week's file untouched instead of committing broken code. Verified end-to-end against the exact 2026-07-12 killer input. See FINDINGS F-013.
- `0955e35` **`lili_ledger_report.py`**: aggregates `tool_quality_ledger.jsonl` over a 28-day window — pass rate by ISO week, keyword-bucketed failure modes (taxonomy synced with retry branches), per-category performance, repeat-offender concepts (3+ fails). Injected into the weekly evolution prompt so reflection cites counted facts instead of impressions of the last few days. Implements the "Error frequency quantification" item from Future Backlog (now removed from backlog as done).
- Test suite grew 43 → 53 (sanitizer on the incident payload, guarded-write refusal/acceptance matrix, bucket classification, report from sample ledger).

### Phase 11 — Retry-Routing Fix, Ground-Truth Probe Blind Spot, Format B/F Retired (2026-07-24 to 2026-07-25)

- `fc79d91` **Retry-feedback keyword routing self-shadowing fixed**: the padding-specific retry branch (added 07-04 for F-009) sat *after* a broader generic/static branch in the elif chain. Critic rejections often contained both "generic" and "hallucinat" wording, so they were always caught by the earlier, less specific branch — the padding-specific feedback was dead code for 20 days without any error being visible in logs. Fixed by moving the more specific branch first; added `tests/test_retry_routing.py` as a standing regression test over real historical rejection strings instead of one-off manual verification. See FINDINGS F-015.
- `9f53675` **Ground-truth probe blind spot fixed**: `_browser_interactivity_check` only drove `textarea`/`input[type=text]`/contenteditable elements — a tool whose real interaction model is selection (`<select>`, radio/checkbox, `[role=option]`/`.chip`/`.option`) could never pass regardless of whether its JS worked. Added selection-driving to the probe, plus `_is_environment_noise()` to stop misreporting headless-sandbox artifacts (e.g. Clipboard API permission denial) as code bugs. See FINDINGS F-016.
- `1327dfe` **F-002 partially overturned, formats B/F retired**: `lili_ledger_report.py` broken down by output format over 311 attempts (28 days) showed the real reliability boundary isn't Mode 1/2 vs Mode 3 — it's whether the tool's value depends on deep semantic/algorithmic analysis of user text. Format B (multi-field form) and F (generator+inline edit) had a 0% pass rate (0/25, 0/18) and are now disabled in SPEC generation, with `validate_spec` deterministically remapping B→A and F→D as a hard fallback (model has a track record of ignoring format instructions). See FINDINGS F-017.
- Test suite grew 53 → 66 (60 after the routing fix, 63 after the ground-truth probe fix, 66 after the format B/F retirement).

### Phase 12 — Ghost workflow_dispatch Trigger & Throttle (2026-07-29)

- `6461cab` **Unexplained daily trigger investigated, throttle added as defense-in-depth**: a `workflow_dispatch` event fired every day at ~00:05 UTC with second-level precision, actor `Super-Lili` — not traced to this Mac's crontab/launchd, any local Claude scheduled task, or the repo's own workflows (which reference only `GITHUB_TOKEN`/`DEEPSEEK_API_KEY`/`QWEN_API_KEY`, none of which is the legacy PAT `lili-deploy` found in the account's token settings). Root cause is **not yet confirmed** — owner is testing whether deleting that PAT stops it. Regardless of cause, `lili_daily.yml` now refuses `workflow_dispatch` once 3+ real attempts (success or rest-day) already ran that day; native `schedule` triggers are never throttled (07-24 alone had 7 legitimate schedule + manual attempts during active debugging, which a blanket cap would have blocked).
- This is an infrastructure/security finding, not a model-capability one — logged here rather than in FINDINGS.md, which is scoped to AI capability boundaries with model attribution.

### Phase 13 — Promise-vs-Actual Gate, Billing-Outage Visibility, Retrospective Evolution Loop (2026-08-03 to 2026-08-09)

The densest single week of harness work to date: ten FINDINGS entries (F-018 finalized, F-019 through F-030), all still awaiting a full week of production data before any get upgraded from "observed" to "confirmed." Owner's explicit instruction after F-030: pause new mechanisms, watch real ledger data for at least a week before adding more.

- `97c424c` **Promise-vs-actual gate** (closes F-018, root-caused by `06241cc`'s SVG Path Purifier namespace bug — a shipped tool whose deletion logic silently no-op'd for 7 days because every prior quality gate checked "does this look clean" and none checked "did it do what it claimed"): SPEC now requires `MUST_CONTAIN`/`MUST_NOT_CONTAIN` fields — a mechanically checkable claim about `process(TEST_INPUT)`'s actual output; `validate_tool()` executes it for real and reports the specific broken promise instead of a generic quality complaint.
- `55b658d` + `730af3b` **Harness plan A+F**: execution-feedback inner loop and differential testing (F-019); sealed test-set + patch gate for weekly self-evolution so evolution proposals are backtested against held-out data before being applied (F-020).
- `da5f250` + `4c074e0` + `de5b4b3` **Three ledger-diagnosed structural gaps closed**: category floor had no ceiling, self-correction inner loop skipped Mode 3, concept-level ban list reacted too slowly (F-021); `COMMON_ROLES` universality gate added to SPEC after 190+ days of "never repeat a topic" pushed scouting toward niche long-tail friction points (F-022); Office Automation's SPEC description used "ANY repetitive professional production task" — the only unbounded catch-all phrasing among the four categories — and was structurally absorbing ambiguous topics regardless of the category-floor fix; narrowed to a bounded definition with explicit exclusions (F-023).
- `953cac8` **Billing outages made visually distinct from creative rest days** (F-024): 2026-08-06/07, Qwen (DashScope) arrears + DeepSeek balance exhaustion simultaneously failed SCOUT's first call, so none of F-019~F-023's downstream logic ever ran — but the diary rendered the same poetic "quiet day" copy used for an ordinary rest day, and the real cause went unnoticed until someone read raw Action logs by hand. `is_billing_error()` + `classify_scout_failure()` now render a distinct "infrastructure outage" banner in both the diary and README.
- `dc11d11` **Pre-flight provider health check** (F-025, the following step after F-024 — fixes visibility, this fixes waste): `check_provider_health()` probes Qwen/DeepSeek with near-zero token cost before spending any real tokens; only skips the day if *both* providers show billing-specific failures (a single healthy provider is enough, per the 08-07 precedent where DeepSeek alone shipped a real tool). Self-correction round cap raised 2 → 4.
- `39a5cde` **Edge-case input check + on-demand retrieval of historical successful examples** injected into BUILD (F-026).
- `af8a023` **BUILD replaced fixed-round text patching with a real tool-calling debug loop** — the model now writes code, executes it, reads real output, and decides its own next step, instead of a hardcoded 2-4 round patch cycle (F-027).
- `c9fe207` **Portable-takeaway gate on `Q3_PASS`** (F-028): validated (passes every mechanical gate) and valuable (worth opening twice) are orthogonal — `Q3_PASS` previously only checked length (≥10 chars), so "gains insight" sailed through. Now requires a concrete take-away-able artifact (copy/download/export/file/script/paragraph/table…); deliberately trades against F-017's Format E preference (ambient/no-input tools have the highest historical pass rate but structurally can't produce a takeaway) — an intentional value trade-off, not a regression.
- `27b82bf` **Retrospective review closes the evolution loop** (F-029): F-020's backtest gate was a one-way valve — it validated a proposal before applying it, but nothing ever checked whether an applied knob actually helped once real data came in, so ineffective knobs accumulated and were never revoked. `retrospective_check_knobs()` compares 7-day windows before/after each active knob and drops ones that show no measurable effect, logged every week before the next proposal overwrites the previous one.
- `dc14908` **Mechanical-fit selection filter added to SCOUT** (F-030): the risk isn't "mechanical-depth solutions are inherently mediocre" (Hemingway App is a counterexample) — it's applying a mechanical/statistical algorithm to a friction point that actually requires semantic judgment. SCOUT now screens candidate friction points for objective measurability *before* committing to a topic, rather than discovering the mismatch downstream in SPEC.
- Test suite grew from 141 (F-024) to 180 (F-030) over the week, all verified under both local Python 3.13 and a real 3.11 venv per the Phase 11 CI-parity lesson.

---

## Key Architecture Decisions

### Three Tool Modes
- **Mode 1**: `process(text)` returns plain text
- **Mode 2**: `process(text)` returns SVG string
- **Mode 3**: `process(text)` returns full HTML page (runs in sandboxed iframe — Web Audio, Canvas, localStorage all available)
- **Direction (2026-07)**: route by validation reliability — analysis tools go Mode 1/2 (executed for real); Mode 3 reserved for genuinely interactive/ambient concepts (browser-verified via Playwright). See FINDINGS F-001/F-002.
- **Refined 2026-07-25**: the real reliability boundary is not the output format but whether the tool's value depends on deep semantic/algorithmic analysis of user text (~3% pass, 28-day) vs. craft/ambient tools (8-11% pass). Formats B (multi-field form) and F (generator+inline edit) had 0% pass rate over 25 attempts combined and are now disabled in SPEC generation. See FINDINGS F-017 (partially overturns F-002).

### Category System
- 🎨 Design Alchemy
- 🎓 Education Evolution
- 🗂️ Office Automation
- 🌿 Healing Inventions — capped at ~20% of tools

### Issue Commission Flow
```
User opens Issue
  → lili_responds.py replies same day, adds lili-responded label
  → Next day: evolve() detects lili-responded without lili-built or lili-blocked
  → Skips random topic selection, builds from Issue content
  → Success: adds lili-built label, posts tool link in Issue comment
  → Failure: mark_commission_attempt_failed() posts a progress comment (1st)
    or a capability-boundary explanation + lili-blocked label (2nd) —
    blocked issues are skipped so the pipeline returns to free scouting
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
- **Quality ceiling**: current tools are uneven — 58 tools as of 2026-08-02 (28-day ledger: 4.8% pass rate per build attempt, 14/294), maybe 2-3 reach "creative professional uses it weekly" standard. Direction is right, needs time

---

## Future Backlog — Good Ideas, Wrong Timing

Ideas discussed and consciously deferred. Revisit when conditions are right.

**Curation**
- Curation mechanism: build a "top 100" display system. Owner marks tools they've actually used; website shows only curated selection. **Threshold revised 2026-08-10**: not "50+ tools accumulated" (that count was hit at 61 tools) — the real gate is **at least 10 tools clearing a strict "would I actually use this myself" bar**. Checked 2026-08-10 by cross-referencing `tool_quality_ledger.jsonl` "passed" entries against actual tool folders (combined score ≥4.5 AND no Critic-flagged caveat like "no real algorithmic depth" in the same passing record): only 3 qualified — Variable_Font_Warm-Up_Wheel (07-08), Thought-to-Type_Threshold (07-13), Name_Fold_Animator (07-23). Re-run this same check before starting the curation build; don't use total tool count as the readiness signal.

**Visual**
- Radiooooo-style design: warm retro color palette, colorful icons, map/timeline navigation. Wait until 50+ tools accumulated — the visual language needs content density to work.

**Architecture**
- Deep SCOUT: read industry reports and long-form forum discussions, not just Reddit post titles. Owner can inject observations via GitHub Issues in the meantime. Requires more API calls — defer until Gemini quota is stable.
- Agentic RAG for SCOUT: inspired by Google's Agentic RAG (6-agent framework, 34% accuracy gain). Two specific upgrades worth adding: (1) Query Rewriter — rewrite vague search terms into precise ones before searching; (2) Sufficient Context Agent — after SCOUT, validate "is this friction point real and specific enough?" before proceeding to SPEC. If not sufficient, search again from a different angle. Small change to pipeline, meaningful quality improvement. Defer until 2-week stability check passes.
- Parallel agent architecture: SCOUT and SPEC running simultaneously. Currently serial pipeline is sufficient; revisit when run time becomes a bottleneck.
- Lili modifies her own core code (super_lili_brain.py): via PR review flow — Lili proposes, owner approves. Revisit after 2 weeks of stable quality runs (from 2026-06-08).

**Quality & Memory**
- ~~Error frequency quantification~~ — **done 2026-07-17** (`0955e35`): `lili_ledger_report.py` aggregates the 28-day ledger into pass rate by week, keyword-bucketed failure modes, per-category performance, and repeat-offender concepts (3+ fails), injected into the weekly evolution prompt.
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
- **API quota exhausted from repeated manual triggers** (Gemini era, historical): each run consumed 6-8 Gemini calls; 5+ triggers/day depleted the free tier. Root cause of the 2026-06-19 switch away from Gemini.
- **Rest day diary blocks rerun** (fixed): the daily workflow skip check now reads the tool directory (`find 02_Toolbox`), not the diary — a rest-day diary no longer blocks later same-day triggers, and a successful run overwrites it.
- **One empty DeepSeek response treated as model-dead**: Gemini-era `break` logic caused two avoidable rest days on 2026-07-03. DeepSeek empties are transient — retry with backoff. See FINDINGS F-003.
- **Prompt examples become executable specs**: suggesting "syllable count, etymology" as differentiation examples made the model fabricate wrong syllable counts. Every example in feedback must be safe to execute literally. See F-004.
- **One-sided prohibitions create pendulums**: banning fabrication (14:30) produced polite refusal to work (20:30 same day). Every "never X" must name the correct middle state (graceful degradation). See F-010.
- **Browser-check rejections were invisible to evolution**: they returned before the scoring step, so never reached the quality ledger. Fixed 2026-07-06 — now logged with probe detail.
- **Findings must name models from commit/billing history, not memory**: attribution written from the current stack fabricated history (claimed Qwen was the June Critic; it arrived 2026-07-03). Owner caught it.
- **Weekly evolution's auto-generated content can break its own carrier files, and nothing catches it**: the 2026-07-12 weekly evolution run wrote an engineering-lesson example containing a literal `"""..."""` docstring into `LILI_ENGINEERING_LESSONS` (`src/lili_engineering.py`) and the duplicate copy in `LILI_BLINDSPOT_ANALYSIS` (`src/lili_blindspot.py`) — the embedded triple-quotes closed the outer triple-quoted string early, leaving a `SyntaxError` in both files from that commit onward. The PostToolUse hook that catches this for Claude-driven edits does not run when Lili's own pipeline writes these files. Found 2026-07-13 because it broke `tests/test_prompts.py` (import chain: `lili_prompts` → `lili_blindspot`). Fixed by escaping the embedded quotes (`\"\"\"`) in both files. The self-evolution write path (whatever code renders `ENGINEERING_LESSONS`/`BLINDSPOT_ANALYSIS` into these `.py` files) should `ast.parse()` its own output before committing, the same way the Claude-side hook does. **Closed 2026-07-17** (`0955e35`): `_sanitize_embedded()` + `_guarded_write()` in `super_lili_weekly_evolution.py` now escape triple-quotes/trailing backslashes and `ast.parse()`+`exec()`-verify every generated carrier file before writing, refusing (and keeping last week's file) on any failure. Verified against the exact 07-12 killer input. See FINDINGS F-013.
- **Commissions with no valid completion path can eat the whole week**: Issue #5 (organize phone screenshots — needs vision AI + OCR that a single-file sandboxed browser tool cannot provide) was retried once per day for 3 consecutive days (2026-07-14~16) because the commission loop had no termination condition — it simply retried until `lili-built` was set, which for an impossible task is never. Root cause: retry-until-success logic assumed every commission was eventually buildable. Fixed 2026-07-16 (`5d0091e`): `mark_commission_attempt_failed()` posts an honest progress comment on the 1st failure and a capability-boundary explanation + `lili-blocked` label on the 2nd, after which `fetch_tool_requests` skips the issue and the pipeline returns to free scouting. See FINDINGS F-014.
- **Ground-truth prober had its own blind spot**: `_browser_interactivity_check` only filled text inputs/clicked buttons — a tool whose real interaction model is selection (`<select>`, radio/checkbox, option chips) could never pass, regardless of whether its JS was correct. A validator's own coverage needs the same scrutiny as the code it validates. Fixed 2026-07-24: probe now also drives `<select>`, radio/checkbox, and `[role=option]/.chip/.option` elements; added `_is_environment_noise()` to stop surfacing headless-sandbox artifacts (e.g. Clipboard API denial) as if they were code bugs. See FINDINGS F-016.
- **CI-only SyntaxError from f-string backslash restriction**: Python 3.11 (CI's version) forbids a backslash inside an f-string's `{}` expression; Python 3.12+ (and the dev machine, 3.13) lifted this restriction, so a test written and passing locally can still be a syntax error on push. Two consecutive pushes (2026-07-24) showed green locally, red on GitHub Actions. Fix confirmed for real by running the full suite under an actual Python 3.11 venv with `requirements.txt` installed — not just `py_compile` or trusting the local interpreter. When editing test files, verify against CI's Python version, not just the dev machine's.
- **A shipped tool can be a complete no-op for 7 days and pass every existing quality gate**: SVG Path Purifier's deletion logic used `root.iter('g')`, which silently matches zero elements once ElementTree qualifies tags with the SVG namespace (`{http://www.w3.org/2000/svg}g`) — the normal case for any SVG with an `xmlns` declaration. Zero attributes were ever removed despite the README claiming otherwise; serialization was also unregistered, polluting output with `ns0:` prefixes that break re-import into design tools. Root cause: no gate in the validation stack (browser ground-truth, Critic, `test_main.py`) checked whether the tool's *specific stated promise* actually happened — all three checked "does this look/behave reasonably," not "did X get removed like it said." Fixed 2026-08-03 (`06241cc`): register the namespace unprefixed before parsing, match on local tag name when iterating. Generalized the same week into a standing mechanism — see F-018 (`MUST_CONTAIN`/`MUST_NOT_CONTAIN` promise-vs-actual gate in SPEC + `validate_tool()`).
- **Two weekly-evolution runs fired on back-to-back days** (2026-08-08 and 2026-08-09, commits `2168aa8` and `6fb0e58`) covering overlapping windows (07/27→08/08 in one report body vs. 08/03→08/09 in the other, despite both being dated 08-08/08-09 in the file). Not yet root-caused — plausibly connected to the still-unresolved ghost `workflow_dispatch` trigger from Phase 12 (2026-07-29), but that was never confirmed to recur here. Flagging for owner attention rather than guessing at a fix.
