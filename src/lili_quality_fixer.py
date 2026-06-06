"""
lili_quality_fixer.py - Super-Lili Quality Fixer
Runs after each daily tool is generated.
Detects empty-shell or broken tools and rewrites them using Gemini.
ASCII-only source: no em-dashes, no Unicode checkmarks.
"""

import os
import re
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
DOCS_TOOLS_DIR = REPO_ROOT / "docs" / "tools"
TOOLBOX_DIR = REPO_ROOT / "02_Toolbox"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-2.0-flash"

# ── Helpers ───────────────────────────────────────────────────────────────────

def today_str() -> str:
    tz = ZoneInfo("Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d")


def find_todays_tool_html(date_str: str) -> Path | None:
    """Find the HTML tool page generated today."""
    for d in DOCS_TOOLS_DIR.iterdir():
        if d.is_dir() and d.name.startswith(date_str):
            html = d / "index.html"
            if html.exists():
                return html
    return None


def extract_srcdoc(html_text: str) -> str | None:
    """Extract the srcdoc string from the iframe script block."""
    # Match: frame.srcdoc = `...` or frame.srcdoc = "..."
    m = re.search(r'frame\.srcdoc\s*=\s*`([\s\S]+?)`\s*;', html_text)
    if m:
        return m.group(1)
    # Fallback: assigned via appHTML variable
    m = re.search(r'const appHTML\s*=\s*`([\s\S]+?)`;', html_text)
    if m:
        return m.group(1)
    return None


def is_empty_shell(srcdoc: str) -> tuple[bool, str]:
    """
    Returns (is_bad, reason) where is_bad=True means the tool is a shell.
    Checks for known anti-patterns.
    """
    reasons = []

    # Anti-pattern 1: alert() used as the primary action
    if re.search(r"onclick=['\"]alert\(", srcdoc):
        reasons.append("button onclick triggers alert() - no real processing")

    # Anti-pattern 2: srcdoc is very short (< 1500 chars) - likely no real logic
    if len(srcdoc) < 1500:
        reasons.append(f"srcdoc too short ({len(srcdoc)} chars) - likely no real implementation")

    # Anti-pattern 3: no function definitions - pure static HTML
    if srcdoc.count("function ") < 2:
        reasons.append("fewer than 2 functions defined - no real interactivity")

    # Anti-pattern 4: placeholder text still present
    placeholder_phrases = [
        "handled by the tool backend",
        "coming soon",
        "not yet implemented",
        "TODO",
        "placeholder",
    ]
    for phrase in placeholder_phrases:
        if phrase.lower() in srcdoc.lower():
            reasons.append(f"placeholder text found: '{phrase}'")

    # Anti-pattern 5: input exists but no processing (textarea + no real handler)
    has_textarea = "<textarea" in srcdoc
    has_processing = srcdoc.count("function ") >= 3
    if has_textarea and not has_processing:
        reasons.append("has input textarea but no processing functions")

    if reasons:
        return True, "; ".join(reasons)
    return False, ""


def get_tool_description(date_str: str) -> str:
    """Read the tool README to understand what it should do."""
    for cat_dir in TOOLBOX_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        for tool_dir in cat_dir.iterdir():
            if tool_dir.is_dir() and tool_dir.name.startswith(date_str):
                readme = tool_dir / "README.md"
                if readme.exists():
                    return readme.read_text(encoding="utf-8")
    return ""


def call_gemini_fix(srcdoc: str, tool_description: str, reasons: str) -> str | None:
    """Ask Gemini to rewrite the broken tool as a real working HTML app."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""You are a senior front-end engineer. Your task is to fix a broken browser tool.

PROBLEM DETECTED:
{reasons}

TOOL DESCRIPTION (what this tool is supposed to do):
{tool_description}

CURRENT BROKEN SRCDOC (the HTML inside the iframe):
```html
{srcdoc[:4000]}
```

TASK:
Rewrite this as a complete, working single-page HTML app that actually does what the description says.

REQUIREMENTS:
- Pure HTML + CSS + JavaScript only. No external libraries. No fetch() calls.
- The tool must actually process user input and produce real output.
- Must have 3 states: entry state (input form) -> processing -> result state (real output).
- At least 3 JavaScript functions with real logic (not just UI helpers).
- No alert(), confirm(), or placeholder text.
- Clean, minimal design. White background. Use #2ABBA8 as accent color.
- Save state to localStorage so results persist on reload.
- The output must be meaningfully different from the input (transformation, not echo).

OUTPUT FORMAT:
Return ONLY the raw HTML content for srcdoc. No markdown fences. No explanation.
Start with <!DOCTYPE html> and end with </html>.
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=8000,
                ),
            )
            result = response.text.strip()
            # Strip markdown fences if present
            result = re.sub(r'^```html?\s*', '', result)
            result = re.sub(r'\s*```$', '', result)
            if result.startswith("<!DOCTYPE") and len(result) > 2000:
                return result
            print(f"[attempt {attempt+1}] Response too short or wrong format ({len(result)} chars), retrying...")
        except Exception as e:
            print(f"[attempt {attempt+1}] Gemini error: {e}")
        time.sleep(15)

    return None


def patch_html_file(html_path: Path, new_srcdoc: str) -> bool:
    """Replace the srcdoc content in the HTML file."""
    html_text = html_path.read_text(encoding="utf-8")

    # Escape backticks in new srcdoc for template literal embedding
    new_srcdoc_escaped = new_srcdoc.replace('`', '\\`').replace('${', '\\${')

    # Strategy 1: replace existing appHTML template literal
    if 'const appHTML = `' in html_text:
        new_html = re.sub(
            r'const appHTML\s*=\s*`[\s\S]+?`;',
            'const appHTML = `' + new_srcdoc_escaped + '`;',
            html_text,
            count=1,
        )
        if new_html != html_text:
            html_path.write_text(new_html, encoding="utf-8")
            return True

    # Strategy 2: replace frame.srcdoc = "..." with appHTML approach
    # Find the script block and replace entirely
    old_script_pattern = r'(<script>\s*\(function\(\) \{)([\s\S]+?)(  \}\)\(\);\s*</script>)'
    if re.search(old_script_pattern, html_text):
        new_script = '''<script>
  (function() {
    const frame = document.getElementById('app-frame');
    const appHTML = `''' + new_srcdoc_escaped + '''`;
    frame.srcdoc = appHTML;
    frame.style.minHeight = '620px';
    frame.addEventListener('load', function() {
      try {
        const h = frame.contentDocument.body.scrollHeight;
        if (h > 300) frame.style.minHeight = (h + 24) + 'px';
      } catch(e) {}
    });
  })();
</script>'''
        new_html = re.sub(old_script_pattern, new_script, html_text, count=1)
        if new_html != html_text:
            html_path.write_text(new_html, encoding="utf-8")
            return True

    print("[patch] Could not find srcdoc injection point in HTML file")
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    date_str = today_str()
    print(f"[quality-fixer] Checking tool for {date_str}")

    if not GEMINI_API_KEY:
        print("[quality-fixer] ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    html_path = find_todays_tool_html(date_str)
    if not html_path:
        print(f"[quality-fixer] No tool found for {date_str} - Lili may not have run yet")
        sys.exit(0)

    print(f"[quality-fixer] Found tool: {html_path}")

    html_text = html_path.read_text(encoding="utf-8")
    srcdoc = extract_srcdoc(html_text)

    if not srcdoc:
        print("[quality-fixer] Could not extract srcdoc - skipping")
        sys.exit(0)

    is_bad, reasons = is_empty_shell(srcdoc)

    if not is_bad:
        print(f"[quality-fixer] Tool passes quality check [OK] - no fix needed")
        sys.exit(0)

    print(f"[quality-fixer] Quality issues detected: {reasons}")
    print("[quality-fixer] Calling Gemini to rewrite tool...")

    tool_description = get_tool_description(date_str)
    new_srcdoc = call_gemini_fix(srcdoc, tool_description, reasons)

    if not new_srcdoc:
        print("[quality-fixer] Gemini could not produce a fix - giving up")
        sys.exit(1)

    print(f"[quality-fixer] Got rewrite ({len(new_srcdoc)} chars) - patching HTML file...")

    patched = patch_html_file(html_path, new_srcdoc)
    if patched:
        print(f"[quality-fixer] [OK] Tool patched successfully")
        # Write a marker file so the workflow knows to commit
        marker = REPO_ROOT / ".quality_fix_applied"
        marker.write_text(f"{date_str}: {reasons[:200]}", encoding="utf-8")
        sys.exit(0)
    else:
        print("[quality-fixer] [NO] Patch failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
