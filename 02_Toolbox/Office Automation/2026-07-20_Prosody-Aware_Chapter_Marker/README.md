# 🛠️ Prosody-Aware Chapter Marker

> *Chapter Marking Compass*

---

**The problem:** A chapter marker isn’t a timestamp—it’s a narrative hinge. What if your tool noticed the hinge before you did?

**What it does:** A tool that ingests raw podcast audio (or transcript), detects meaningful speech boundaries using prosodic cues—not just silence—and generates editable, semantically grounded chapter markers with auto-suggested titles.

**Born from:** ⚠️ r/podcasting | QUOTE: "Spent 47 minutes today marking chapters in Descript just to realize the AI put '00:12:38' where the guest actually said 'That changed everything' — and then I had to re-listen, re-scrub, re-type every title by hand."  
r/audioengineering | QUOTE: "Audacity + manual timestamp CSV export → paste into Anchor → pray the times align. If the guest coughs mid-sentence? Your whole chapter grid collapses."  
r/WeAreTheMusicMakers | QUOTE: "I record interviews raw, no script. So my 'chapters' aren't planned—they’re *discovered* in playback. But every tool forces me to choose times *before* I know what matters."

---

## Quick Start

```bash
# 1. Download
curl -O "https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/02_Toolbox/Office%20Automation/2026-07-20_Prosody-Aware_Chapter_Marker/main.py"

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
*Forged by Super-Lili on 2026-07-20 with love ✨*