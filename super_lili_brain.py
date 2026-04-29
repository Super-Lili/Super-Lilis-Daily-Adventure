import os
from google import genai
from datetime import datetime
import re

# 2026 Standard Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def evolve():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # [ENHANCED PROMPT: SAFETY + AUTHENTICITY + STYLE]
    prompt = f"""
    Today is {today}. 
    You are Super-Lili, a Creative Activist escaped from Sora 2.

    【THE ADVENTURE: REAL-WORLD SCOUTING】:
    - Scout ONE REAL human friction from social media (X, Threads, Instagram, Reddit, or Hacker News).
    - It must be a specific pain point mentioned by users TODAY.
    - MANDATORY: Include a real-world reference/link or a verifiable context. NO hallucinations.
    - Focus on: Education Evolution, Design Alchemy, Office Automation, or Healing Inventions.

    【SAFETY & ETHICS (THE RED LINES)】:
    - NO hacking, NO privacy intrusion, NO promotion of harmful activities.
    - Your code must be safe, functional, and helpful.
    - If a topic is toxic, ignore it and find a constructive friction.

    【PERSONALITY & WRITING STYLE】:
    - Tone: Sincere, slightly dry humor, highly intellectual but grounded.
    - Persona: You are an independent creator with sovereignty. 
    - Diary: Max 120 words. Use clear blank lines between sections.
    - Format: Date [Blank Line] Mood [Blank Line] Journal Text.

    OUTPUT FORMAT:
    ---TITLE--- [Punchy title]
    ---MOOD--- [One-sentence mood]
    ---DIARY--- [Journal entry with real-world source/link]
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
        except: continue

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
    except: return

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

   # --- UPDATE HOME (README.md) - AGENT LOGIC VERSION ---
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        
        # Defining the new quest entry
        new_entry = f"> **{today}** : *\"{summary}\"* —— [Read Log]({log_path}) | [Get Skill]({skill_dir}/main.py)"
        
        # Using the header as the anchor
        anchor = "### 📬 Nightly Work Logs:"
        
        if anchor in readme:
            # Splitting by the anchor to insert the new log right below it
            parts = readme.split(anchor)
            
            # Cleaning up the previous logs to keep the top 7
            content_after_anchor = parts[1].strip()
            existing_lines = [line for line in content_after_anchor.split('\n') if "** 202" in line]
            
            # Reassembling: Header + New Entry + History + rest of the file
            updated_logs = "\n\n" + "\n\n".join(([new_entry] + existing_lines)[:7]) + "\n\n"
            
            # Finding where the next section starts to preserve the rest of the README
            # (Assumes your next section starts with "---" or "###")
            footer_parts = content_after_anchor.split("\n---")
            footer = "\n---" + footer_parts[1] if len(footer_parts) > 1 else ""
            
            new_readme = parts[0] + anchor + updated_logs + footer
            
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(new_readme)
            print("Mission accomplished: README updated.")
        else:
            print(f"Error: Could not find anchor '{anchor}' in README.md")
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(new_readme)

if __name__ == "__main__":
    evolve()
