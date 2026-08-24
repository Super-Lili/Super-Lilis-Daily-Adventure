# 🛠️ Decision Logic Extractor

> *The Map Inside “It Depends”*

---

**The problem:** Turns a decade of “it depends” into a decision map you can actually hand to someone.

**What it does:** A single-page tool that pastes in your old project notes, decisions, and outcomes, then extracts recurring decision types, constraints, and principles into a structured “how I think” document for mentoring, consulting, or job interviews.

**Born from:** ⚠️ Reddit r/ProductManagement (plain-text description of a recent post): a 12-year product manager transitioning to consulting describes not being able to articulate her process to junior PMs.

QUOTE: “After 12 years in product, I can run a launch in my sleep. But when I try to explain my process to a junior PM, I keep saying ‘it depends.’ I have no idea what I actually know. I have a resume full of outcomes, but no map of the decisions behind them.”

---

## Quick Start

```bash
# 1. Download
curl -O "https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/02_Toolbox/Education%20Evolution/2026-08-24_Decision_Logic_Extractor/main.py"
curl -O "https://raw.githubusercontent.com/Super-Lili/Super-Lilis-Daily-Adventure/main/02_Toolbox/Education%20Evolution/2026-08-24_Decision_Logic_Extractor/requirements.txt"

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. See all options
python3 main.py --help
```

## Dependencies

```
Input: free-form "war story" paragraphs. Output: structured markdown Decision Logic Map.
```

## Run Tests
```bash
python3 test_main.py
```

---
*Forged by Super-Lili on 2026-08-24 with love ✨*