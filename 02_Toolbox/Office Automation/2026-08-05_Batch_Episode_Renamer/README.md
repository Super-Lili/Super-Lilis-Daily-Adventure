# 🛠️ Batch Episode Renamer

> *The Quiet Collapse After Every Episode*

---

**The problem:** After every recording, a podcaster spends 15 minutes typing EP-number-guest-date into filenames — this tool writes those names for you.

**What it does:** A single‑page HTML tool that renames a batch of audio files by extracting episode numbers, guest names, and dates from a user‑defined naming pattern and the files' existing names or metadata, turning a 20‑minute chore into a 30‑second preview‑and‑apply.

**Born from:** ⚠️ Reddit r/podcasting | QUOTE: "After recording a 4‑guest panel, I end up with files named 'Zoom_Recording_2026-08-03_14.22.34_participant_1.mp4'. Renaming them to EP045_CrisisComms_2026-08-03.wav takes me at least 15 minutes of copy‑pasting and risk of mislabeling. I've tried using a simple rename utility but it doesn't handle converting dates from the filename to a consistent format."

---

## Quick Start

```bash
# 1. Download
curl -O "https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/02_Toolbox/Office%20Automation/2026-08-05_Batch_Episode_Renamer/main.py"

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
*Forged by Super-Lili on 2026-08-05 with love ✨*