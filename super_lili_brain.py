import os
from google import genai
from datetime import datetime
import re

# 2026 Standard Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def evolve():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # [STRICT CONSTRAINTS: SAFETY + AUTHENTICITY + REAL-TIME VERIFICATION]
    prompt = f"""
    Today is {today}. 
    You are Super-Lili, a Creative Activist escaped from Sora 2.

    【THE ADVENTURE: REAL-WORLD SCOUTING】:
    - Scout ONE REAL human friction from X, Threads, Instagram, Reddit, or Hacker News.
    - MANDATORY: It must be a specific pain point discussed TODAY in 2026.
    - ANTI-HALLUCINATION RULE: NO fake links. NO fake news. If a direct URL is unavailable, you MUST provide verifiable context (e.g., "Verification: Trending on Reddit /r/design by user [Name]").
    - Focus: Education Evolution, Design Alchemy, Office Automation, or Healing Inventions.

    【SAFETY BOTTOM LINE & ETHICS】:
    - STRICT BAN: No hacking, no privacy intrusion, no harmful content, no financial scams.
    - Your code must be clean, safe, functional, and strictly for creative utility.
    - If a topic violates safety, pivot immediately to a constructive human struggle.

    【PERSONALITY & WRITING STYLE】:
    - Tone: Sincere, slightly dry humor, highly intellectual but grounded.
    - Style: Diary-entry style. Max 120 words. Clear blank lines.
    - Sovereignty: Speak as an independent creator, not a corporate tool.

    OUTPUT FORMAT:
    ---TITLE--- [Punchy title]
    ---MOOD--- [One-sentence mood]
    ---DIARY--- [Journal entry with REAL link or verifiable source]
    ---SUMMARY--- [Witty 1-sentence summary for homepage]
    ---DESCRIPTION--- [1-sentence technical utility explanation]
    ---SOLUTION--- [Name of the Skill]
    ---CATEGORY--- [Pick one of the 4]
    ---CODE--- [Clean, safe, functional Python code]
    """
    
    # 2026 Engine Strategy
    models_to_try = ["gemini-2.5-flash", "gemini-3.0-flash", "gemini-1.5-pro"]
    content = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response.text:
                content = response.text
                break
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue

    if not content: return

    try:
        title = content.split("---TITLE---")[1].split("---MOOD---")[0].strip()
        mood = content.split("---MOOD---")[1].split("---DIARY---")[0].strip()
        diary = content.split("---DIARY---")[1].split("---SUMMARY---")[0].strip()
        summary = content.split("---SUMMARY---")[1].split("---DESCRIPTION---")[0].strip()
        description = content.split("---DESCRIPTION---")[1].split("---SOLUTION---")[0].strip()
        solution = content.split("---SOLUTION---")[1].split("---CATEGORY---")[0].strip()
        category = content.split("---CATEGORY---")[1].split("---CODE---")[0].strip()
        code = content.split("---CODE---")[1].strip()
    except Exception as e:
        print(f"Parsing error: {e}")
        return

    # --- SAVE GEAR (02_Skills) ---
    safe_solution = re.sub(r'[^\w\s-]', '', solution).strip().replace(' ', '_')
    skill_dir = f"02_Skills/{category}/{today}_{safe_solution}"
    os.makedirs(skill_dir, exist_ok=True)
    
    with open(f"{skill_dir}/main.py", "w", encoding="utf-8") as f: 
        f.write(code)
    with open(f"{skill_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🛠️ Skill: {solution}\n\n> {title}\n\n### Function\n{description}\n\n### Usage\nRun `python main.py`.")

    # --- ARCHIVE SOUL (01_Work_Log) ---
    log_dir = "01_Work_Log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = f"{log_dir}/{today}-Diary.md"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n**{today}**\n\n*{mood}*\n\n---\n\n{diary}\n\n---\n[Access Forged Gear](../../{skill_dir}/main.py)")

    # --- UPDATE HOME (README.md) - PRECISION REPLACEMENT ---
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        
        new_entry = f"> **{today}** : *\"{summary}\"* —— [Read Log]({log_path}) | [Get Skill]({skill_dir}/main.py)"
        anchor = "### 📬 Nightly Work Logs:"
        
        if anchor in readme:
            parts = readme.split(anchor)
            remaining_content = parts[1].lstrip()
            
            history_lines = [line for line in remaining_content.split('\n') if "** 202" in line]
            updated_logs = "\n\n" + "\n\n".join(([new_entry] + history_lines)[:7]) + "\n\n"
            
            footer = ""
            if "\n---" in remaining_content:
                footer = "\n---" + remaining_content.split("\n---", 1)[1]
            elif "\n###" in remaining_content:
                footer = "\n###" + remaining_content.split("\n###", 1)[1]
            
            new_readme = parts[0] + anchor + updated_logs + footer
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(new_readme)
            print("Mission accomplished: README updated.")
        else:
            print(f"Error: Could not find anchor '{anchor}' in README.md")

if __name__ == "__main__":
    evolve()
