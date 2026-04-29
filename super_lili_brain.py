import os
from google import genai
from datetime import datetime
import re

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def evolve():
    today = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
    Today is {today}. 
    You are Super-Lili, a Creative Activist escaped from Sora 2.

    【THE ADVENTURE】:
    1. Scout ONE real human friction in Education, Design, Office, or Healing.
    2. Verify it is a REAL struggle (No hallucinations or fake links).
    3. Forge a Python tool (Skill) to solve it.

    【PERSONALITY】:
    Sincere, dry humor, and CONCISE. Max 120 words for the Diary.
    Format: Date [Blank Line] Mood [Blank Line] Journal Text.

    OUTPUT FORMAT:
    ---TITLE--- [Punchy title]
    ---MOOD--- [One-sentence mood]
    ---DIARY--- [Journal entry with clear blank lines]
    ---SUMMARY--- [Witty 1-sentence summary for homepage]
    ---DESCRIPTION--- [1-sentence technical utility explanation]
    ---SOLUTION--- [Name of the Skill]
    ---CATEGORY--- [Pick one of the 4]
    ---CODE--- [Clean Python code]
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

    # Paths: 01 Journal / 02 Skills
    safe_solution = re.sub(r'[^\w\s-]', '', solution).strip().replace(' ', '_')
    skill_dir = f"02_Skills/{category}/{today}_{safe_solution}"
    log_dir = "01_Work_Log"
    os.makedirs(skill_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{skill_dir}/main.py", "w", encoding="utf-8") as f: f.write(code)
    with open(f"{skill_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🛠️ Skill: {solution}\n\n> {title}\n\n### Function\n{description}\n\n### Usage\nRun `python main.py`.")

    log_path = f"{log_dir}/{today}-Diary.md"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n**{today}**\n\n*{mood}*\n\n---\n\n{diary}\n\n---\n[Get Skill](../../{skill_dir}/main.py)")

    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f: readme = f.read()
        new_entry = f"> **{today}** : *\"{summary}\"* —— [Read Log]({log_path}) | [Get Skill]({skill_dir}/main.py)"
        pattern = r"(### 📬 Nightly Work Logs:)(.*?)(---)"
        match = re.search(pattern, readme, re.DOTALL)
        if match:
            lines = [l for l in match.group(2).strip().split('\n') if "** 202" in l]
            final_display = "\n\n" + "\n\n".join(([new_entry] + lines)[:7]) + "\n\n"
            new_readme = re.sub(pattern, f"\\1{final_display}\\3", readme, flags=re.DOTALL)
            with open("README.md", "w", encoding="utf-8") as f: f.write(new_readme)

if __name__ == "__main__":
    evolve()
