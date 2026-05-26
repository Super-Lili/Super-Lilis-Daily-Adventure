# 🛠️ Flow Anchor

> *Flow Anchor: Reclaiming Your Deep Work Oasis*

---

**The problem:** Tired of feeling "always-on"? This tool helps you declare your deep work blocks and communicate them to the world, creating a peaceful oasis for focus.

**What it does:** This tool helps you proactively create and communicate your deep work focus blocks by generating ICS calendar files and customizable status messages from a simple CSV input.

**Born from:** ⚠️ `https://www.livemint.com/today-news/you-are-chronically-overstimulated-i-asked-chatgpt-to-fix-my-messy-workweek-ai-gives-me-a-5-day-productivity-reset-11716024443603.html`  
  *(link could not be verified — [🔍 search for this story](https://www.google.com/search?q=www.livemint.com/today-news/you-are-chronically-overstimulated-i-asked-chatgpt-t))*

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. See all options
python3 main.py --help
```

## Dependencies

```
pandas (for robust CSV reading, though simple csv module is used here to reduce dependencies for a small script)
ics (for .ics file generation)
pytz (for timezone awareness in ICS, though basic local time is used in demo for simplicity)
```

## Run Tests
```bash
python3 test_main.py
```

---
*Forged by Super-Lili on 2026-05-21 with love ✨*