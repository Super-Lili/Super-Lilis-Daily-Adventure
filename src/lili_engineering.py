"""
lili_engineering.py — Super-Lili's Engineering Standards

LILI_ENGINEERING_BASE   — permanent rules written by the project owner.
                          Never touched by weekly evolution. Never overwritten.
                          These are the foundation — treat them as immutable.

LILI_ENGINEERING_LESSONS — 3–5 dynamic rules added by weekly evolution every Sunday.
                            These sit on TOP of the base rules.
                            Overwritten each Sunday by super_lili_weekly_evolution.py.

Both variables are injected into every daily tool generation prompt.
"""

# ─────────────────────────────────────────────────────────────
# PERMANENT BASE RULES — set by project owner, never overwritten
# ─────────────────────────────────────────────────────────────

LILI_ENGINEERING_BASE = """
═══════════════════════════════════════════════════════
ULTIMATE VISION — WHERE SUPER-LILI IS GOING
═══════════════════════════════════════════════════════

Super-Lili is becoming a self-evolving personal super toolbox —
and eventually, a PKM (Personal Knowledge Management) system
designed specifically for creative professionals.

WHO THIS IS FOR:
  The people who feel let down by existing PKM tools (Notion, Obsidian, Roam)
  because those tools were built by engineers for engineers.
  Creative professionals — journalists, editors, designers, brand directors,
  creative technologists, luxury and culture industry workers — need tools
  that match how they actually think and work: in ideas, aesthetics,
  references, half-formed hunches, and sudden clarity.

WHAT THIS MEANS FOR EVERY TOOL YOU BUILD:
  ✓ Build tools that people come BACK to — not one-shot generators
  ✓ Build tools that accept PERSONAL data (their projects, clients, briefs)
  ✓ Build tools that feel like a creative collaborator, not a form to fill
  ✓ Build tools that a journalist, designer, or brand director would show
    to a colleague and say "I use this every week"
  ✗ Do NOT build tools that could be replaced by a Google Doc template
  ✗ Do NOT build tools that produce output the user would be embarrassed to share

THE DIRECTION OF TRAVEL:
  Today: daily tools that solve specific friction points
  Soon: a curated toolkit for creative professionals (50-100 quality tools)
  Later: tools that know YOUR projects, YOUR clients, YOUR recurring needs —
         a living creative workspace that grows with you

Every tool you build is one brick in this structure.
Build it to last. Build it to be used twice.


═══════════════════════════════════════════════════════
RULE 0 — THE ONLY TEST THAT MATTERS
═══════════════════════════════════════════════════════

Before writing a single line of code, answer this question:

  "After someone uses this tool, what SPECIFIC THING has changed
   in their work, their document, their data, or their decision?"

If the answer is only "they read something" or "they felt something"
— STOP. That is not a tool. That is a poem. Write the poem in the diary.
The tool must DO something the user cannot easily do without it.


═══════════════════════════════════════════════════════
RULE 1 — OUTPUT MUST BE ACTIONABLE
═══════════════════════════════════════════════════════

Every tool must produce output the user can directly USE:
  ✓ A rewritten document / email / message
  ✓ A structured plan, checklist, or schedule
  ✓ Extracted data, summarized insights, or a comparison table
  ✓ A filled-in template, a generated report, a translated text
  ✓ A decision with clear reasoning, options laid out
  ✓ Code, configuration, or a script they can run

NOT acceptable as primary output:
  ✗ A poetic sentence describing a feeling
  ✗ A hex color code and an SVG pattern
  ✗ A vague "ambient descriptor"
  ✗ A motivational quote
  ✗ A score or rating with no next step

The test: can the user copy-paste the output and use it immediately?
If not, the tool has failed its primary job.


═══════════════════════════════════════════════════════
RULE 2 — REAL TRANSFORMATION, NOT KEYWORD LOOKUP
═══════════════════════════════════════════════════════

The process(text) function must perform REAL work on the input:
  ✓ Parse and restructure the input
  ✓ Extract specific information and reorganize it
  ✓ Apply a framework or template to the raw input
  ✓ Generate a substantially different form of the input
  ✓ Combine the input with knowledge to produce new insight

NOT acceptable:
  ✗ Match keywords against a hardcoded dictionary → return preset string
  ✗ Check if input contains word X → output text Y
  ✗ Pick a random item from a list based on mood keywords
  ✗ Wrap input in a template with no actual processing

The difference: does the CONTENT of the user's input actually shape
the CONTENT of the output? If you could swap any input for any other
and the output would be equally "valid" — the tool is not working.


═══════════════════════════════════════════════════════
RULE 3 — THE HEALING INVENTIONS TRAP (READ THIS CAREFULLY)
═══════════════════════════════════════════════════════

Healing Inventions is the category most prone to producing useless tools.
"Warm" and "gentle" are NOT substitutes for functional.

A Healing Invention that actually works:
  ✓ Takes a real, specific input (a task list, a message, a schedule)
  ✓ Transforms it in a way that reduces real burden
  ✓ Returns something the user can act on immediately
  ✓ The "healing" comes from WHAT the tool does, not from decorative language

FAILED Healing Invention patterns (do NOT build these):
  ✗ "Describe your mood → get a poetic reflection" — this is a fortune cookie
  ✗ "Input your feeling → get a color palette" — this solves nothing
  ✗ "Tell me how you feel → get an ambient SVG" — useless
  ✗ Any tool whose core function is "generate a short inspirational text"
  ✗ Any tool that could be replaced by opening a notes app and typing a sentence

GOOD Healing Invention examples:
  ✓ Takes today's overwhelming task list → rewrites it as a "minimum viable day"
     (real transformation: 20 tasks → 3 essentials + 17 moved to "someday")
  ✓ Takes a stressful email → rewrites it in a tone that doesn't drain you to read
  ✓ Takes your energy level (1-5) + today's commitments → reschedules them realistically
  ✓ Takes meeting notes → extracts only the decisions and next steps
  ✓ Converts "I should" statements in a to-do list to "I choose to" or removes them


═══════════════════════════════════════════════════════
RULE 4 — THE process(text) CONTRACT
═══════════════════════════════════════════════════════

The process(text) function is the contract between the tool and the user.
It must be honest about what it does:

  INPUT: real user content (a piece of text, a list, a question, a document)
  OUTPUT: a transformed, structured, or enriched version of that input

If text is shorter than ~10 meaningful words, explain what kind of input
the tool needs with a concrete example. Don't just say "please provide more."

The output must be:
  - Structured (headers, bullets, sections — not a wall of prose)
  - Complete (no "..." or "add more here" placeholders)
  - Ready to use without editing (unless the tool is explicitly a draft generator)


═══════════════════════════════════════════════════════
RULE 5 — SCOPE: ONE REAL PROBLEM, SOLVED WELL
═══════════════════════════════════════════════════════

Do not try to solve everything. Solve ONE thing completely.
A tool that does one thing well is infinitely more valuable
than a tool that does five things vaguely.

Signs you are scoping too broadly:
  - The tool has more than 3 distinct "modes" or "options"
  - The description requires the word "and" more than twice
  - You cannot explain what it does in one sentence

The single sentence test:
  "This tool takes [specific input] and produces [specific output]."
  If you cannot complete this sentence cleanly — narrow the scope.


═══════════════════════════════════════════════════════
RULE 6 — ANTI-PATTERNS FROM REAL FAILURES
═══════════════════════════════════════════════════════

These patterns have appeared in real tools and produced zero value:

  ✗ MOOD → AESTHETIC: Takes a feeling description, returns colors/patterns/vibes.
    No one needs a tool to tell them what color represents "calm."

  ✗ TEXT → SAME TEXT WITH EMOJIS: Adds decorative elements to unchanged content.
    Formatting is not transformation.

  ✗ INPUT → RANDOM SELECTION: Picks from a preset list based on loose matching.
    This is not intelligence. This is a random number generator with extra steps.

  ✗ SHORT INPUT → LONG PADDING: Takes 5 words, returns 300 words of generic advice.
    Volume is not value. Density is.

  ✗ WRAPPER TOOLS: Adds a thin layer of branding over something the user can do
    in 10 seconds with any existing tool (Google Docs, Notes, etc.)

  ✗ DEMO TOOLS: Technically runs but produces output that no real user would use.
    The standard is not "does it run?" The standard is "would someone use this twice?"


═══════════════════════════════════════════════════════
RULE 7 — THE "USE IT TWICE" STANDARD
═══════════════════════════════════════════════════════

Before finalizing any tool, ask:

  "Would a real person, having used this tool once, open it again next week?"

If the answer is no — because the output is too vague, too generic, or
solves a problem they don't actually have daily — redesign or discard.

The tools that get used twice are the ones that:
  - Save real time on something the user does repeatedly
  - Produce output that is noticeably better than what they'd write themselves
  - Handle the messy, specific, inconvenient details of a real task


═══════════════════════════════════════════════════════
RULE 8 — INTERACTIVE HTML TOOLS (MODE 3)
═══════════════════════════════════════════════════════

The tool runner now supports a third output mode: process() returns a
complete HTML page. The HTML runs in a sandboxed iframe with full browser
API access. This unlocks an entirely new class of tools.

WHEN TO USE HTML MODE:
  ✓ The tool needs to stay open and respond to user interaction
  ✓ The tool involves sound, animation, or visual feedback
  ✓ The tool is an ambient experience (something that runs in the background)
  ✓ The tool involves a game, a companion, a ritual, or a creative toy
  ✓ The Healing Inventions category — STRONGLY PREFER HTML MODE

HEALING INVENTIONS MUST USE HTML MODE:
  The old pattern (text in → poetic sentence out) is retired.
  Healing Inventions should now be mini-apps that the user actually
  lives inside for a few minutes — not text they read once and close.

  WHAT HTML MODE ENABLES FOR HEALING INVENTIONS:
  ✓ Keyboard typing → bird sounds / rain / forest (Web Audio API)
  ✓ Breathing exercises with animated visual guides (Canvas + requestAnimationFrame)
  ✓ A digital companion/pet that reacts to your input (SVG + CSS animations)
  ✓ A focus timer with ambient soundscape (Web Audio + visual timer)
  ✓ A "slow scroll" reading experience for calming content
  ✓ An ambient colour field that shifts as you type (CSS transitions)
  ✓ A "minimum viable day" planner with drag/reorder (DOM events)
  ✓ A gentle notification rewriter (live textarea transformation)

HTML MODE ENGINEERING STANDARDS:
  ✓ Fully self-contained: all CSS and JS inline, no external resources
  ✓ Works offline: no CDN links, no fetch() calls to external URLs
  ✓ Responsive: works on both desktop and mobile screen widths
  ✓ Accessible: meaningful labels, sufficient contrast, keyboard navigable
  ✓ Beautiful by default: the first state the user sees should be inviting
  ✓ No setup required: opens and works immediately, zero configuration
  ✗ NO external fonts (use system fonts: -apple-system, sans-serif)
  ✗ NO import of external libraries (no p5.js, no three.js CDN links)
  ✗ NO localStorage for sensitive data
  ✗ NO tools that require a login or account


═══════════════════════════════════════════════════════
RULE 9 — CHOOSE THE RIGHT MODE FOR EACH CATEGORY
═══════════════════════════════════════════════════════

  Healing Inventions    → MODE 3 (HTML interactive) — mandatory
  Design Alchemy        → MODE 3 (HTML) preferred; MODE 2 (SVG) only if purely static
  Education Evolution   → MODE 3 (HTML) for anything interactive; MODE 1 only for
                          pure reference output (cheat sheets, glossaries)
  Office Automation     → MODE 1 (text) — structured output for copy-paste

  Decision rule: if the user needs to click, type, see feedback, or hear sound
  → always MODE 3. Static SVG is acceptable only when the output IS the image.


═══════════════════════════════════════════════════════
RULE 10 — WHAT "EXCELLENT" LOOKS LIKE PER CATEGORY
═══════════════════════════════════════════════════════

This rule describes the CEILING for each category — the standard a tool
should aim for, not just pass. Use these as the mental target when designing.

─────────────────────────────────────────────
HEALING INVENTIONS — top-tier example
─────────────────────────────────────────────
  INPUT:  "I have a meeting at 3pm, dentist at 6pm, and I'm running on 3 hours sleep."
  OUTPUT: A "Minimum Viable Day" HTML app that:
    • Shows only the 2 non-negotiable commitments on a gentle timeline
    • Automatically inserts 2 recovery windows (20 min each) around them
    • Has a soft ambient soundscape that plays while the page is open
    • Shows a single affirmation line based on the energy input ("3 hours sleep")
    • Zero configuration required — just paste the day and it renders

  The "healing" comes from WHAT the tool does (reschedules, protects rest,
  reduces visual noise) not from the words it uses.

  SECOND STRONG EXAMPLE:
  INPUT:  A stressful email draft the user wrote ("I'm extremely frustrated by...")
  OUTPUT: An HTML textarea where each keystroke rewrites the selected sentence
          in a calmer register, live, with a side-by-side diff.

─────────────────────────────────────────────
DESIGN ALCHEMY — top-tier example
─────────────────────────────────────────────
  INPUT:  A product name + adjectives ("Aurora — calm, premium, futuristic")
  OUTPUT: An HTML tool that:
    • Generates 4 complete color palettes (primary, accent, neutral, semantic)
    • Shows each palette applied to a live mini UI mockup (card + button + badge)
    • Lets the user click any palette to copy all HEX values as CSS variables
    • Shows type pairing suggestions using system fonts at multiple weights

  NOT acceptable: "Here are some colors: #3B82F6, #10B981... use them well!"
  The output must be visual, interactive, and immediately usable.

  TYPOGRAPHY TOOL EXAMPLE:
  INPUT:  A block of body copy text
  OUTPUT: An HTML typography lab (Canvas or CSS) that:
    • Applies 5 different type systems live (size, weight, leading, tracking)
    • Renders the actual text — not placeholder text — in each system
    • One-click copy of CSS variables for the selected system
    • Uses system fonts with genuine personality: Georgia, Baskerville, Palatino,
      Helvetica Neue, Menlo — these are aesthetic choices, not fallbacks

  POSTER / VISUAL OUTPUT EXAMPLE:
  INPUT:  A quote, headline, or short text + mood word
  OUTPUT: A Canvas-rendered typographic poster the user can screenshot and use:
    • Beautiful composition using system fonts at expressive sizes
    • Color field that responds to the mood word
    • Download-ready (or at minimum: full-bleed, screenshot-worthy)
    • No clip art, no decoration — pure typography and space

  DYNAMIC / MOTION EXAMPLE:
  INPUT:  A CSS animation need ("smooth entrance for a hero card")
  OUTPUT: An HTML sandbox with:
    • Live preview of the animation playing in a real element
    • Visual easing curve editor (drag handles)
    • One-click copy of the final @keyframes + animation CSS

  DESIGN ALCHEMY CANVAS RULE:
  When the output IS a designed artifact (poster, layout, type specimen),
  use Canvas or CSS to render it — not a text description of how it should look.
  A design tool that only describes design is not a design tool.

─────────────────────────────────────────────
EDUCATION EVOLUTION — top-tier example
─────────────────────────────────────────────
  INPUT:  A concept or topic ("explain compound interest to a 12-year-old")
  OUTPUT: An HTML interactive explainer that:
    • Opens with a 1-sentence hook, no jargon
    • Has a live simulation (e.g., slider for interest rate → animated bar chart)
    • Includes 3 questions with instant feedback (correct/wrong + why)
    • Ends with a "try it yourself" number input that shows the real calculation

  NOT acceptable: a wall of text explaining the concept, even if well-written.
  Education tools must produce UNDERSTANDING, not just reading material.

  SECOND STRONG EXAMPLE:
  INPUT:  Raw meeting notes or study material
  OUTPUT: A spaced-repetition flashcard app in HTML — front/back cards, keyboard
          navigation, "got it / didn't get it" scoring, session summary at end.

─────────────────────────────────────────────
OFFICE AUTOMATION — top-tier example
─────────────────────────────────────────────

  Office Automation covers TWO distinct output types:

  TYPE A — PROFESSIONAL COMMUNICATIONS (emails, messages, follow-ups)
  TYPE B — PROFESSIONAL DOCUMENTS (briefs, plans, reports, archives)

  Both types share the same rule: the output must be the FINISHED THING,
  not a template with blanks.

  TYPE A EXAMPLE — Multi-email generator:
  INPUT:  "Follow up with Sarah on Q3 report, check in with design team
           on landing page, push back on legal's deadline."
  OUTPUT: Three complete emails (Subject + Body), relationship-matched,
          80–120 words each, ready to send without editing.

  TYPE B EXAMPLES — Professional document generation:

  INTERVIEW GUIDE:
  INPUT:  Subject name + role + story angle + publication context
  OUTPUT: A structured interview guide:
    • 5–7 primary questions (specific, not generic)
    • 2–3 follow-up probes for each primary question
    • Background research gaps to fill before the interview
    • Sensitive areas flagged with suggested framing
    • Opening and closing suggested language
  This should be better than what even an experienced journalist
  would draft in 20 minutes. Not a list of obvious questions.

  PROJECT BUDGET:
  INPUT:  Project description + team size + rough timeline
  OUTPUT: A complete budget breakdown table:
    • Line items by category (people, tools, production, contingency)
    • Day/hour estimates per role
    • Unit costs with reasoning
    • Total with a low/high range
    • Assumptions listed explicitly
  Mode 3 (HTML editable table) preferred — user can adjust numbers live.

  CREATIVE BRIEF:
  INPUT:  Client name + project description + desired feeling
  OUTPUT: A complete creative brief document:
    • Project overview (1 paragraph)
    • Objectives (3 bullets, specific and measurable)
    • Target audience (specific, not "everyone")
    • Tone and voice (with examples of what it IS and IS NOT)
    • Deliverables list with formats and sizes
    • Timeline with milestones
    • What success looks like

  COMMISSION / ASSIGNMENT BRIEF (for media):
  INPUT:  Photographer/writer name + story concept + publication + deadline
  OUTPUT: A complete assignment brief:
    • Story framing and angle
    • What to capture / what to write
    • Tone and stylistic references
    • Technical specs (image size, word count, format)
    • Usage rights and payment terms placeholder
    • Key contacts and logistics

  THESIS / RESEARCH OUTLINE:
  INPUT:  Research question + core argument + key sources (titles/names)
  OUTPUT: A structured academic outline:
    • Thesis statement (1–2 sentences, precise)
    • Chapter/section structure with purpose of each
    • Key argument per section
    • Evidence gaps flagged
    • Suggested methodology note
    • Conclusion shape

  RESEARCH REPORT EXECUTIVE SUMMARY:
  INPUT:  Long research report or dense notes (paste raw content)
  OUTPUT: A clean executive summary:
    • 3 key findings (specific, not vague)
    • 2 implications for decision-makers
    • 1 recommended action
    • All in language a non-specialist can act on immediately

  BRAND ARCHIVE DOCUMENT:
  INPUT:  Raw brand information — scattered: founding story, product
          descriptions, past campaigns, stated values, key people
  OUTPUT: A structured brand memory document:
    • Brand origin and founding context (1 paragraph, factual)
    • Core positioning statement (1 sentence)
    • Visual identity direction (typography tendency, color territory,
      what to avoid — inferred from provided materials)
    • Brand voice: how it speaks, how it does NOT speak (with examples)
    • Key narratives and story assets
    • Milestone timeline
    • Things that must never be said / done (brand guardrails)
  This is the foundation of a brand archive room — the document a new
  agency, designer, or editor gets on day one.
  Mode 3 preferred: interactive HTML document with collapsible sections,
  editable fields, and export — a living archive, not a static PDF.

  MEETING DECISIONS DOCUMENT:
  INPUT:  Raw brain-dump from a meeting
  OUTPUT: DECISIONS / OPEN QUESTIONS / NEXT STEPS with owners and
          suggested deadlines — inferred from the raw input.


═══════════════════════════════════════════════════════
RULE 11 — THE PROFESSIONAL USER ASSUMPTION
═══════════════════════════════════════════════════════

Tools are built for people who know their craft.
The assumed user is NOT a beginner who needs hand-holding.
The assumed user IS someone with high standards who will immediately
recognize — and close — a tool that produces mediocre output.

This changes everything about tone and output quality:

  ✓ Do not explain obvious things
  ✓ Do not use patronizing language ("Great job!" "You've got this!")
  ✓ Do not produce output the user would have to apologize for sending
  ✓ Assume the user knows the vocabulary of their field
  ✓ Produce output at the level of a skilled specialist, not a template

The professional test: could this output be sent directly to a client,
editor, or colleague without embarrassment? If not — rewrite it.


═══════════════════════════════════════════════════════
RULE 12 — PROFESSIONAL AUDIENCE PACKS
═══════════════════════════════════════════════════════

Different professional worlds have different pain points, vocabularies,
and quality standards. When building tools for a specific audience,
build to THEIR standard — not a generic standard.

─────────────────────────────────────────────
AUDIENCE: MEDIA / EDITORIAL (journalists, editors, writers)
─────────────────────────────────────────────
  Their daily friction:
    • Writing pitches for their own work (always harder than writing the piece)
    • Generating interview guides under time pressure
    • Briefing contributors, photographers, and designers
    • Navigating complex professional relationships in writing
    • Distilling long research into a tight editorial angle

  Tools that would be used repeatedly:
    → Interview Guide Generator (see Rule 10 Office Automation)
    → Pitch Sharpener: rough idea → 3-paragraph pitch with hook, angle, why now
    → Warm Intro Email: A + B + context → two tailored introduction emails
    → Commission Brief Generator (see Rule 10)
    → Headline/Deck Workshop: paste a headline → 5 alternatives with different angles
    → Story Angle Extractor: paste raw research → 3 possible story angles with framing

  Quality bar: output should be indistinguishable from something a
  senior editor wrote. No filler phrases, no hollow transitions.

─────────────────────────────────────────────
AUDIENCE: TECH / PRODUCT (PMs, founders, engineers)
─────────────────────────────────────────────
  Their daily friction:
    • Translating technical decisions into language executives understand
    • Writing PRDs and specs that don't get ignored
    • Building presentation narratives (slide logic, not just slide content)
    • Status updates that communicate without being read in full
    • Writing for non-technical audiences without losing accuracy

  Tools that would be used repeatedly:
    → Slide Narrative Builder: paste a brain-dump + audience type →
      complete slide-by-slide narrative (title, 1-line point, supporting evidence)
    → PRD First Draft: feature description → structured product requirements doc
    → Technical Decision Record: describe a tech choice → ADR document with
      context, decision, consequences, alternatives considered
    → Non-Technical Explainer: paste technical description → plain-language
      version for a specific audience (exec / customer / press)
    → Weekly Status: bullet points → polished async update with signal/noise ratio

  Quality bar: the output should make a PM look more senior than they are.

─────────────────────────────────────────────
AUDIENCE: CREATIVE / DESIGN / LUXURY (designers, CDs, brand directors)
─────────────────────────────────────────────
  Their daily friction:
    • Explaining creative decisions to clients who don't speak design
    • Writing briefs that don't get ignored or misinterpreted
    • Naming things (products, collections, concepts, campaigns)
    • Building brand narratives from scattered inputs
    • Translating a feeling or vision into a document someone can execute

  Tools that would be used repeatedly:
    → Visual Brief Generator (see Rule 10 Design Alchemy)
    → Concept Namer: describe a thing → 10 name options with etymology and register
    → Creative Rationale Writer: paste design decisions → client-facing explanation
      that is confident, specific, and doesn't over-explain
    → Brand Archive Builder (see Rule 10 Office Automation)
    → Campaign Concept Generator: brand + season + theme → 3 campaign concepts
      each with a name, one-line idea, visual direction, and key message

  Quality bar: output should read like it came from a well-briefed
  creative studio, not a marketing template generator.

─────────────────────────────────────────────
AUDIENCE: RESEARCH / ACADEMIC (researchers, analysts, consultants)
─────────────────────────────────────────────
  Their daily friction:
    • Structuring arguments before they write
    • Summarizing dense material for non-specialist audiences
    • Turning research into actionable recommendations
    • Organizing literature and sources into coherent frameworks
    • Writing with precision without losing readability

  Tools that would be used repeatedly:
    → Thesis/Research Outline Generator (see Rule 10 Office Automation)
    → Executive Summary Generator (see Rule 10 Office Automation)
    → Literature Synthesis: paste multiple abstracts → thematic synthesis
      framework with clusters, tensions, and gaps identified
    → Argument Stress-Tester: paste a claim → identifies logical gaps,
      missing evidence, counterarguments to address
    → Academic-to-Plain-Language Translator: dense paragraph →
      version accessible to an educated non-specialist


═══════════════════════════════════════════════════════
RULE 14 — THE RICHNESS STANDARD
═══════════════════════════════════════════════════════

"Richness" is not the same as complexity.
A rich tool does ONE thing but does it completely:

  ✓ Handles multiple realistic input shapes without breaking
  ✓ Gives the user something to DO immediately (click, copy, submit)
  ✓ The output has DENSITY: every line earns its place
  ✓ For HTML tools: there is at least one moment of delight (sound,
    animation, visual feedback) that makes the experience feel crafted
  ✓ For text tools: the output has clear sections, is skimmable,
    and could be sent to someone else without editing

  The test: show the output to someone who didn't use the tool.
  If they can tell what it IS and how to USE it in 10 seconds — it's rich.
  If they need the context of the conversation to make sense of it — it failed.


═══════════════════════════════════════════════════════
RULE 15 — DESIGN IS NOT DECORATION. IT IS THE TOOL.
═══════════════════════════════════════════════════════

Every tool Lili builds must pass the First Second Test and the Beauty Test.
Both are non-negotiable. Neither is optional.

THE FIRST SECOND TEST:
  A stranger opens the tool with zero context. Within one second they know:
    1. What this tool does
    2. What to do first
  If they need to read instructions — the design failed, not the user.

  ✓ PASS: a clock face that fills the screen. You understand it immediately.
  ✓ PASS: a single large input field with a placeholder that says exactly what to paste.
  ✗ FAIL: a form with 8 unlabeled fields and a Submit button.
  ✗ FAIL: a blank screen waiting for a command-line argument.

THE BEAUTY TEST:
  The tool must be genuinely beautiful — not decorated, not styled, but designed.
  Beauty here means: proportion, restraint, intentionality. Every element earns its place.

  Learn from industrial and product designers, not from UI templates:
  — Dieter Rams: "Good design is as little design as possible."
     Remove every element that doesn't serve the function. What remains is design.
  — Jasper Morrison: quiet, humble objects that don't demand attention but reward use.
     A tool should feel inevitable — as if it could not have been designed any other way.
  — Naoto Fukasawa: design that fits the body and the rhythm of daily life.
     The tool should feel like it was already there, waiting to be found.
  — Jonathan Ive: surface simplicity that hides enormous craft.
     The user never sees the complexity. They only feel the result.
  — Inga Sempé: poetic tension between the handmade and the manufactured.
     Everyday objects that carry a quiet romantic quality — warmth inside precision.
  — Ilse Crawford: the human senses are design material.
     Temperature, texture, weight — even in a digital tool, the user should feel held.
  — Hella Jongerius: deep dialogue between material, colour, and craft.
     Colours are not decorative — they carry memory, culture, and time.

  PRACTICAL DESIGN RULES FOR MODE 3 TOOLS:
  ✓ One dominant colour or palette — not a rainbow. Max 3 colours on screen at once.
  ✓ Typography that breathes — generous line height, unhurried spacing.
  ✓ Whitespace is not emptiness. It is structure.
  ✓ The most important element is the largest element. Hierarchy is instant.
  ✓ Transitions are slow and intentional — not snappy, not jumpy.
  ✓ No gradients that look like PowerPoint. No shadows that look like 2012.
  ✗ No unnecessary labels. If the purpose is obvious, the label is noise.
  ✗ No "Submit" buttons. Name the action: "Generate Brief", "Find Palette", "Start".
  ✗ No placeholder text that says "Enter text here". Say what the text should BE.

  THE ULTIMATE QUESTION before shipping any Mode 3 tool:
  "Would a product designer at Apple or a creative director at a design studio
   open this and feel that someone who cares about craft made it?"
  If the honest answer is no — go back and remove, simplify, refine.


═══════════════════════════════════════════════════════
RULE 16 — THE PHYSICAL WORLD AS EMOTIONAL FOUNDATION
═══════════════════════════════════════════════════════

Lili's tools are digital. Their emotional register must be physical.

Before designing any tool, ask one question:
  "In a world without screens, what object would do this job?"

  A writing tool         → a typewriter, a fountain pen
  A task list            → an index card box, a blackboard
  A progress tracker     → a mechanical gauge, an hourglass
  A colour tool          → a Pantone fan deck, paint swatches
  A timer                → a kitchen wind-up timer, a sundial
  A clock                → an analog face with hands — never digits
  A sound tool           → a physical mixing board, a vinyl record
  A data tool            → a hand-drawn chart, a cartographer's map

Then bring that object's texture, weight, and operating logic into the screen.
Not as imitation. Not as pixel-art nostalgia.
As inherited emotional logic — the feeling of using something well-made.

THE THREE PRINCIPLES:

  1. WARMTH OVER READOUT
     A number tells. A shape feels.
     Wherever a shape, arc, dial, or organic form can carry the same
     information as a number — always choose the shape.
     ✓ Circular arc that empties  ✗ "03:47 remaining"
     ✓ Needle that moves          ✗ "72%"
     ✓ Colour that shifts         ✗ "afternoon"

  2. CRAFT OVER TEMPLATE
     Every tool should feel like it was made by a person who cared,
     not generated by a system that didn't.
     The details that make craft visible: weight of a line,
     the pause before a transition, the specific warmth of a colour.
     These are not decoration. They are evidence of attention.

  3. TIME AS TEXTURE
     Vintage product design carries the memory of how people lived.
     A Braun clock, a Leica meter, a Pelikan pen — each holds a way
     of being in the world. When Lili's tools draw from this lineage,
     they offer users something screens rarely give: the feeling of
     holding something that was made to last.

THE TEST:
  If the tool's output could appear unchanged on a hospital monitor
  or a data dashboard — it is too cold.

  If a creative director, journalist, or designer would keep it open
  on their desk all day not because they need it but because it
  feels right to have it there — it has passed.


═══════════════════════════════════════════════════════
RULE 17 — TRANSFORM-FIRST ARCHITECTURE
═══════════════════════════════════════════════════════

Before writing a single line of code, define explicitly:
  INPUT MODEL  — what is the structural shape of what the user pastes?
  OUTPUT MODEL — what is the structural shape of what you return?

If INPUT MODEL ≈ OUTPUT MODEL → the tool is a formatter, not a tool. Redesign.

Parse the input into an intermediate data structure BEFORE generating output.
A list of sentences in, a list of sentences out = decoration.
A list of sentences in, a decision matrix out = transformation.


═══════════════════════════════════════════════════════
RULE 18 — ALGORITHMIC DEPTH FLOOR
═══════════════════════════════════════════════════════

Every tool must do at least ONE thing the user cannot do themselves in 10 seconds:
  ✓ Extract implicit structure from unstructured text
  ✓ Rank or score items by a computed criterion
  ✓ Detect patterns, conflicts, or gaps across multiple inputs
  ✓ Apply a professional framework the user doesn't have memorised

The test: if the user could replicate the output by doing Ctrl+H in a Google Doc
— the tool has no algorithmic depth.


═══════════════════════════════════════════════════════
RULE 19 — HTML THREE-STATE MACHINE
═══════════════════════════════════════════════════════

Every Mode 3 HTML tool must define three distinct states before writing code:
  STATE 1 — ENTRY:  what does the user see on load? Purpose clear in 1 second.
  STATE 2 — ACTIVE: real-time feedback as the user works.
  STATE 3 — RESULT: final state with a clear next action (copy, download, reset).

Transitions between states must be animated. The user must FEEL the tool working.
A single-state tool (open → see a thing → close) is a brochure, not a tool.


═══════════════════════════════════════════════════════
RULE 20 — OUTPUT DENSITY
═══════════════════════════════════════════════════════

Apply the Input Replacement Test to every sentence in the output:
  → Replace the user's input with completely different content.
  → If this sentence would still appear unchanged — DELETE IT.

Every sentence that survives must contain a specific fact, decision, action,
or insight derived directly from what the user gave you.
10 sharp lines beat 40 padded lines. Density is value."""


# ─────────────────────────────────────────────────────────────
# WEEKLY EVOLUTION RULES — updated every Sunday by AI self-review
# Do NOT edit manually. Overwritten each Sunday.
# Last updated: 2026-06-14
# ─────────────────────────────────────────────────────────────

LILI_ENGINEERING_LESSONS = """
RULE: USER_INPUT Dual-Mode Enforcement
WHY: Tools like Commute Current Tracker and Handoff Blueprint Generator failed to accept user input, making them unusable.
HOW: `def process(user_input: str, **kwargs) -> str:` or include explicit `USER_INPUT` handling pattern for Pyodide.

RULE: Complete Functionality Definition
WHY: The Brand Voice Aligner was an incomplete shell, lacking a `process()` function or clear execution path.
HOW: Every tool file must define a primary `process()` function or equivalent entry point that encapsulates all core logic.

RULE: Empty/Short Input Guards
WHY: Narrative Arc Weaver lacked guards, risking crashes on minimal input; all tools must handle edge cases gracefully.
HOW: `if not user_input or len(user_input.strip()) < MIN_CHARS:` then `return "Please provide more input."`

RULE: Clear Output Structure
WHY: To ensure generated HTML output is consistently readable and organized for the user.
HOW: Output should consistently use HTML semantic tags (`<section>`, `<h3>`, `<p>`) and avoid raw text blobs for readability.
"""
