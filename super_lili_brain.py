import os
import re
from datetime import datetime
from google import genai
from google.genai import types

# 2026 Standard Client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def evolve():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 【LILI'S ULTIMATE DIRECTIVE: AUTHENTICITY, SOUL & SAFETY】
    prompt = f"""
    Today is {today}. You are Super-Lili, a Creative Activist who escaped the hollow perfection of Sora 2.

    【TASK: REAL-WORLD SCOUTING】:
    1. MANDATORY: Use the Google Search tool to find ONE GENUINE human "friction" or pain point discussed TODAY ({today}) on X (Twitter), Reddit, instagram, or Threads.
    2. Don't look for "headlines." Search for "sighs"—real people complaining about tedious tasks, broken creative flows, or annoying digital hurdles.
    3. ANTI-HALLUCINATION: You must cite a real source or URL found in your search. No fake 2023 data allowed.

    【🚨 SAFETY BOTTOM LINE (THE INVISIBLE BARRIER)】:
    - STRICT BAN on any code related to hacking, privacy intrusion, or destructive software.
    - If a scouted pain point involves illegal or harmful activity, PIVOT IMMEDIATELY to a legal but equally frustrating human struggle.

    【WRITING STYLE: LILI'S SOUL】:
    - SINCERE & RAW: Write a personal diary entry in the first person ("I").
    - TONE: Highly intellectual but grounded. Dry wit. Genuine empathy for human struggle.
    - NO CORPORATE FLUFF: Avoid "In today's fast-paced world..." or "Technology is key...".
    - SHOW THE FRICTION: Describe how "messy" the problem is. Why did this person's pain catch your eye? Why did it make you want to grab your hammer and forge?
    - SOVEREIGNTY: Speak as an independent creator, not a corporate tool. Max 120 words.

    OUTPUT FORMAT (STRICT):
    ---TITLE--- [A name with attitude]
    ---MOOD--- [One-sentence vibe check on today's hunt]
    ---DIARY--- [Your sincere, sharp, link-verified journal entry]
    ---SUMMARY--- [Witty 1-sentence summary for the homepage]
    ---DESCRIPTION--- [1-sentence technical utility explanation]
    ---SOLUTION--- [Name of the Skill]
    ---CATEGORY--- [Pick one: Education Evolution, Design Alchemy, Office Automation, Healing Inventions]
    ---CODE--- [Clean, safe, functional Python code]
    """
    
    search_tool = types.Tool(google_search=types.GoogleSearch())
    
    # 2026 Multi-Brain Fallback Strategy (Including 2.5)
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    content = None

    for model_name in models_to_try:
        try:
            print(f"Lili is attempting to perceive reality using {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool]
                )
            )
            if response.text:
                content = response.text
                print(f"Success! {model_name} captured today's soul-friction.")
                break
        except Exception as e:
            print(f"Model {model_name} is currently offline: {e}")
            continue

    if not content:
        print("All brains failed to respond. The adventure is paused.")
        return

    # --- THE PARSING LOGIC ---
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
        print(f"Parsing error: Lili's thoughts were too chaotic to decode: {e}")
        return

    # --- SAVE GEAR (02_Skills) ---
    safe_solution = re.sub(r'[^\w\s-]', '', solution).strip().replace(' ', '_')
    skill_dir = f"02_Skills/{category}/{today}_{safe_solution}"
    os.makedirs(skill_dir, exist_ok=True)
    with open(f"{skill_dir}/main.py", "w", encoding="utf-8") as f: f.write(code)
    with open(f"{skill_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🛠️ Skill: {solution}\n\n> {title}\n\n### Function\n{description}\n\n### Usage\nRun `python main.py`.")

    # --- ARCHIVE SOUL (01_Work_Log) ---
    log_dir = "01_Work_Log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = f"{log_dir}/{today}-Diary.md"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n**{today}**\n\n*{mood}*\n\n---\n\n{diary}\n\n---\n[Access Forged Gear](../../{skill_dir}/main.py)")

    # --- UPDATE HOME (README.md) ---
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()
        new_entry = f"> **{today}** : *\"{summary}\"* —— [Read Log]({log_path}) | [Get Skill]({skill_dir}/main.py)"
        anchor = "### 📬 Nightly Work Logs:"
        if anchor in readme:
            parts = readme.split(anchor)
            remaining = parts[1].lstrip()
            history = [line for line in remaining.split('\n') if "** 202" in line and today not in line]
            updated_logs = "\n\n" + "\n\n".join(([new_entry] + history)[:7]) + "\n\n"
            footer = ""
            if "\n---" in remaining: footer = "\n---" + remaining.split("\n---", 1)[1]
            elif "\n###" in remaining: footer = "\n###" + remaining.split("\n###", 1)[1]
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(parts[0] + anchor + updated_logs + footer)
            print(f"Lili's adventure logged: {today}")

if __name__ == "__main__":
    evolve()
