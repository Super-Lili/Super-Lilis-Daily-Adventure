# 🛠️ SVG Path Purifier

> *SVG Path Purifier*

---

**The problem:** A one-click scrubber that strips only the harmful invisibles from SVGs—so your animation runs, your SSR builds, and your designer sleeps.

**What it does:** A minimal Python CLI tool that takes raw SVG text or files, removes only `fill="none"`, `stroke="none"`, `opacity="0"`, `visibility="hidden"`, and `display="none"` *when they appear on non-semantic grouping elements*, and preserves all styling, transforms, and accessibility attributes.

**Born from:** ⚠️ r/graphic_design | QUOTE: "Every time I export SVGs from Figma (even with 'clean SVG' on), I get `<path fill="none" stroke="none" d="M0 0h1v1H0z"/>` at the top — it’s invisible in browsers but breaks my Next.js static build with React Server Components. I paste into VS Code, search/replace, pray."  
r/MotionDesign | QUOTE: "My Lottie-to-SVG workflow keeps failing because the exported SVG has 42 `<g>` tags with `opacity="0"` and `visibility="hidden"` — they don’t show, but they *do* trigger layout thrashing in GSAP timelines. I’ve written a regex macro, but it breaks if the designer uses `display:none` instead."

---

## Quick Start

```bash
# 1. Download
curl -O "https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/02_Toolbox/Design%20Alchemy/2026-07-28_SVG_Path_Purifier/main.py"

# 2. Install dependencies
# (no extra dependencies needed)

# 3. See all options
python3 main.py --help
```

## Dependencies

_See comment block at top of main.py_

## Run Tests
```bash
python3 test_main.py
```

---
*Forged by Super-Lili on 2026-07-28 with love ✨*