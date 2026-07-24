"""
lili_validators.py - Mechanical checks and response parsing:
URL validation, spec validation, the 8-step validate_tool() chain,
response parsers, and source verification.
"""

import os
import re
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

from lili_llm import call_gemini_simple, call_qwen_critic


# ─────────────────────────────────────────────────────────────
# MODE 3 BROWSER GROUND-TRUTH VALIDATION
# ─────────────────────────────────────────────────────────────

# Console messages that are environment artifacts, not code bugs - surfacing
# these as "errors to fix" wastes a retry on something the model cannot fix
# by writing different code (e.g. headless Chromium blocks Clipboard API
# writes by sandbox policy, regardless of how correct the tool's JS is).
_BROWSER_ENV_NOISE = ("clipboard",)


def _is_environment_noise(console_message: str) -> bool:
    """True if a captured console error is a known headless-browser artifact
    rather than a genuine bug in the tool's own JavaScript."""
    msg = console_message.lower()
    return any(n in msg for n in _BROWSER_ENV_NOISE)


def _browser_interactivity_check(html: str, test_input: str) -> tuple[bool, bool, str]:
    """Actually run a Mode 3 tool in a headless browser to get GROUND TRUTH on whether
    its JavaScript does real work with user input (instead of asking an LLM to guess).

    Returns (ran, changed, detail):
      ran=False     -> inconclusive (Playwright unavailable / crashed). Caller must NOT
                       reject on this - fall back to the LLM Critic. Fail-open by design.
      ran=True,  changed=False -> the page did NOT react to input at all -> static/fake.
      ran=True,  changed=True  -> DOM genuinely changed in response to input -> real.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return False, False, f"playwright unavailable ({type(e).__name__})"

    import tempfile
    html_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
            fh.write(html)
            html_path = fh.name

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.set_default_timeout(8000)

            # Capture real JS runtime errors so a failed probe can tell the model
            # WHY the DOM didn't react (e.g. a TypeError from a bad selector) instead
            # of a generic "make the JS work" that repeats verbatim across retries.
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text)
                    if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))

            page.goto(f"file://{html_path}")
            page.wait_for_timeout(400)

            before = (page.inner_text("body") or "").strip()
            before_nodes = page.eval_on_selector_all("*", "els => els.length")

            # Drive the UI: fill every text field with the test input, fire events,
            # then click every button. This is a generic "does it react" probe.
            sample = (test_input or "The quick brown fox jumps over the lazy dog. "
                      "This is a realistic multi-sentence test input for the tool.")[:600]
            filled = page.evaluate(
                """(val) => {
                    let n = 0;
                    for (const el of document.querySelectorAll('textarea, input[type=text], input:not([type]), [contenteditable=true]')) {
                        try {
                            if (el.isContentEditable) { el.innerText = val; }
                            else { el.value = val; }
                            el.dispatchEvent(new Event('input',  {bubbles:true}));
                            el.dispatchEvent(new Event('change', {bubbles:true}));
                            el.dispatchEvent(new KeyboardEvent('keyup', {bubbles:true}));
                            n++;
                        } catch(e){}
                    }
                    return n;
                }""",
                sample,
            )
            # Drive SELECTION-based controls too - not every real tool is a text
            # box. A tool whose whole interaction model is "pick an option" (a
            # <select>, radio group, checkboxes, or clickable option chips) has
            # zero elements matching the text-fill probe above; without this,
            # such a tool always looks static/fake regardless of whether its JS
            # is real. Pick a non-default <select> option, check radios/boxes,
            # and click anything that looks like a selectable chip/tab/option.
            selected = page.evaluate(
                """() => {
                    let n = 0;
                    document.querySelectorAll('select').forEach(function(el) {
                        try {
                            if (el.options && el.options.length > 1) {
                                el.selectedIndex = el.selectedIndex === 1 ? 2 % el.options.length : 1;
                                el.dispatchEvent(new Event('input',  {bubbles:true}));
                                el.dispatchEvent(new Event('change', {bubbles:true}));
                                n++;
                            }
                        } catch(e){}
                    });
                    document.querySelectorAll('input[type=radio], input[type=checkbox]').forEach(function(el) {
                        try {
                            el.checked = true;
                            el.dispatchEvent(new Event('input',  {bubbles:true}));
                            el.dispatchEvent(new Event('change', {bubbles:true}));
                            n++;
                        } catch(e){}
                    });
                    const chipSel = '[role=option], [role=tab], [role=radio], .chip, .option, ' +
                                    '.choice, [data-value], [data-option]';
                    document.querySelectorAll(chipSel).forEach(function(el) {
                        try { el.click(); n++; } catch(e){}
                    });
                    return n;
                }"""
            )
            # Click buttons / submit-like controls to trigger compute handlers.
            page.evaluate(
                """() => {
                    const sel = 'button, [role=button], input[type=submit], input[type=button], .btn';
                    for (const el of document.querySelectorAll(sel)) {
                        try { el.click(); } catch(e){}
                    }
                }"""
            )
            page.wait_for_timeout(600)

            after = (page.inner_text("body") or "").strip()
            after_nodes = page.eval_on_selector_all("*", "els => els.length")
            browser.close()

        text_changed = after != before and len(after) > 0
        nodes_changed = after_nodes != before_nodes
        changed = bool(text_changed or nodes_changed)
        detail = (f"fields_filled={filled}, selections_made={selected}, "
                  f"text_changed={text_changed}, nodes {before_nodes}->{after_nodes}")
        real_errors = [e for e in console_errors if not _is_environment_noise(e)]
        if real_errors:
            unique_errors = list(dict.fromkeys(real_errors))[:3]
            detail += f", console_errors={unique_errors}"
        return True, changed, detail
    except Exception as e:
        return False, False, f"browser run failed: {type(e).__name__}: {e}"
    finally:
        if html_path:
            try:
                os.unlink(html_path)
            except Exception:
                pass


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

    # Check 2b: algorithmic depth must read as a CONCRETE mechanical procedure, not an
    # aspiration. Aspirational specs ("structure into insightful chapters") let BUILD satisfy
    # them with lazy heuristics (grab first sentence) that the Critic then rejects. Require at
    # least one concrete computational verb so the depth names an operation BUILD can implement.
    concrete_verbs = [
        "split", "count", "measure", "group", "rank", "sort", "detect", "compare", "score",
        "extract", "match", "parse", "token", "frequency", "ratio", "overlap", "cluster",
        "map", "weight", "index", "position", "length", "distance", "pattern", "segment",
        "aggregate", "tally", "normalize", "normalise", "classify by", "step ", "1.", "2.",
    ]
    if not any(v in algo_depth.lower() for v in concrete_verbs):
        return False, (
            f"ALGORITHMIC_DEPTH is aspirational, not a concrete procedure: '{algo_depth[:120]}'. "
            "Rewrite it as named mechanical steps a programmer implements verbatim (e.g. "
            "'split on X; count Y per group; rank by Z; flag where overlap < 0.2'). Use concrete "
            "verbs (split/count/measure/group/rank/detect/score/parse) - no 'understand', "
            "'insight', or 'intelligently' without the actual operation that produces it."
        )

    # Check 3: Q1/Q2/Q3 must be specific
    for label, val in [("Q1_PASS", q1), ("Q2_PASS", q2), ("Q3_PASS", q3)]:
        if len(val) < 10:
            return False, f"{label} is too vague or missing: '{val}'"

    # Check 4: test input must exist
    if len(test_input) < 15:
        return False, f"TEST_INPUT is missing or too short. Got: '{test_input[:50]}'"

    # Check 5: reject un-deliverable promises. The tool is a single self-contained file with
    # no database, no pretrained model, no internet. Specs that promise comparison against a
    # "curated corpus", "database of exemplars", "trained model", or factual knowledge lookups
    # cannot be honestly built - BUILD then fakes it and Critic rejects it as fundamentally fake.
    # Force SPEC to design depth that computes FROM THE INPUT, not from data the tool lacks.
    promise_haystack = f"{algo_depth} {spec.get('transformation','')} {output_model}".lower()
    undeliverable = [
        "corpus", "curated", "exemplar", "database of", "dataset of", "knowledge base",
        "pretrained", "pre-trained", "trained model", "reference set", "large dictionary",
        "industry benchmark", "real-world examples of", "comparison against a set of",
    ]
    hit = next((kw for kw in undeliverable if kw in promise_haystack), None)
    if hit:
        return False, (
            f"ALGORITHMIC_DEPTH promises something a single self-contained file cannot deliver "
            f"(matched: '{hit}'). The tool has no external corpus/database/pretrained model/internet. "
            f"Redesign the depth to COMPUTE FROM THE USER'S INPUT only: measure structure, patterns, "
            f"ratios, positions, consistency, or relationships WITHIN the text the user provides. "
            f"Do not promise comparison against reference data the tool does not contain."
        )

    # Mode 3 (HTML formats C/D/E) is ENABLED - it was force-overridden to Mode A during
    # 2026-06-19~07-03 because weaker models shipped fake interactivity. Now BUILD runs on
    # deepseek-v4-pro with an independent qwen3.7-max Critic + mechanical
    # fake-interactivity guards + the Playwright ground-truth probe, so real Mode 3 tools
    # can be validated properly.
    #
    # EXCEPT B and F, which are dead formats: over 28 days they took 43 attempts and
    # shipped ZERO tools (B 0/25, F 0/18), while D managed 8% and E 11%. The prompt tells
    # the model not to pick them, but the model has a history of ignoring format
    # instructions (2026-06-23: picked B twice in a row, burning both SPEC retries), so
    # rewrite deterministically instead of rejecting and hoping it listens - the
    # transformation/algorithmic content of the spec stays valid, only delivery changes.
    _DEAD_FORMAT_REMAP = {"B": ("A", "1"), "F": ("D", "3")}
    fmt_letter = spec.get("format", "").strip()[:1].upper()
    if fmt_letter in _DEAD_FORMAT_REMAP:
        new_fmt, new_mode = _DEAD_FORMAT_REMAP[fmt_letter]
        print(f"  [!] Spec picked dead FORMAT '{fmt_letter}' (0 ships in 28 days) "
              f"- remapping to '{new_fmt}'")
        spec["format"] = f"{new_fmt} - remapped from dead format {fmt_letter}"
        spec["mode"] = new_mode

    return True, "ok"



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

    # 3b. Import check - catches crashes from unguarded top-level code.
    # `python main.py --help` runs the file as __main__, so anything inside
    # `if __name__ == "__main__":` executes fine. But test_main.py does
    # `from main import process`, which sets __name__ to "main" (not "__main__"),
    # so __main__-guarded code is skipped - any OTHER unguarded top-level statement
    # (an argparse call, a stray function call, a missing import) still runs and
    # can crash on plain import even though --help passed.
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from main import process"],
            capture_output=True, text=True, timeout=15, cwd=skill_dir,
        )
        if result.returncode != 0:
            return False, (
                f"Import crashed: 'from main import process' raised an exception even though "
                f"the file parses and --help works. This means there is unguarded top-level code "
                f"(outside any function and outside 'if __name__ == \"__main__\":') that runs "
                f"immediately on import. Error: {result.stderr[:300]}"
            )
    except subprocess.TimeoutExpired:
        return False, "Import check timed out - main.py may hang on import"
    except Exception as e:
        return False, f"Import check error: {e}"

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

        # Mode 3 (HTML) is allowed again as of 2026-07-03. The fake-interactivity guards
        # below (hardcoded lookup tables, pre-filled data-* nodes, unrendered templates)
        # plus the JS-source Critic review are what keep Mode 3 honest.

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

            # GROUND-TRUTH interactivity probe: actually run the tool in a headless browser,
            # feed it the test input, and verify the DOM reacts. This replaces guessing with
            # execution. Fail-open: if the browser can't run (unavailable/crash), we skip this
            # gate and let the LLM Critic decide, so a browser flake never causes a false reject.
            ran, changed, detail = _browser_interactivity_check(output, demo_input)
            if ran and not changed:
                # Log to the quality ledger so weekly evolution SEES these failures -
                # they happen before the scoring step and were previously invisible to it.
                _append_quality_ledger(
                    tool_name=description or str(skill_dir),
                    category=str(skill_dir).split("/")[-2] if skill_dir else "",
                    eng_score=1, warm_score=1,
                    reason=f"Browser ground-truth: DOM did not react to input ({detail})",
                    passed=False, format_type=format_type, audience=audience,
                )
                return False, (
                    "Browser ground-truth check: the tool's DOM did NOT change when the test "
                    f"input was entered and controls were clicked ({detail}). The JavaScript does "
                    "nothing with user input - this is a static/fake interactive tool. Make the JS "
                    "read the input, compute from it, and update the DOM at runtime."
                )
            if ran:
                print(f"  [OK] Browser interactivity confirmed - DOM reacts to input ({detail}).")
            else:
                print(f"  · Browser probe skipped ({detail}) - falling back to Critic.")
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
            critic_resp = call_qwen_critic(critic_prompt)
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


