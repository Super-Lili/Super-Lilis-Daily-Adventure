"""
lili_memory.py — Super-Lili's Long-Term Memory System
Tracks every tool Lili has built, every problem she's solved,
and every topic she's covered — so she never repeats herself.
"""

import json
import re
from datetime import datetime
from pathlib import Path

MEMORY_FILE = Path(__file__).parent.parent / "data" / "lili_memory.json"


def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tools": [], "topics_covered": [], "last_updated": ""}


def save_memory(memory: dict):
    memory["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def rebuild_memory_from_repo() -> dict:
    """
    Scan the entire repo to rebuild memory from scratch.
    Called once to initialize, or to repair a corrupted memory file.
    """
    memory = {"tools": [], "topics_covered": [], "last_updated": ""}
    toolbox = Path("02_Toolbox")

    if not toolbox.exists():
        return memory

    for cat_dir in sorted(toolbox.iterdir()):
        if not cat_dir.is_dir():
            continue
        for tool_dir in sorted(cat_dir.iterdir()):
            if not tool_dir.is_dir():
                continue

            date_str = tool_dir.name[:10]
            tool_name = tool_dir.name[11:].replace("_", " ") if len(tool_dir.name) > 11 else tool_dir.name

            # Try to read description from tool README
            description = ""
            readme = tool_dir / "README.md"
            if readme.exists():
                try:
                    content = readme.read_text(encoding="utf-8")
                    for line in content.splitlines():
                        if line.startswith("**What it does:**"):
                            description = line.replace("**What it does:**", "").strip()
                            break
                except Exception:
                    pass

            memory["tools"].append({
                "date": date_str,
                "name": tool_name,
                "category": cat_dir.name,
                "path": str(tool_dir),
                "description": description,
            })

    # Also scan diary topics
    log_dir = Path("01_Work_Log")
    if log_dir.exists():
        for diary in sorted(log_dir.glob("*-Diary.md")):
            date_str = diary.stem.replace("-Diary", "")
            try:
                first_line = diary.read_text(encoding="utf-8").splitlines()[0]
                title = first_line.lstrip("#").strip()
                memory["topics_covered"].append({
                    "date": date_str,
                    "title": title,
                    "path": str(diary),
                })
            except Exception:
                pass

    save_memory(memory)
    print(f"✓ Memory rebuilt: {len(memory['tools'])} tools, {len(memory['topics_covered'])} diary entries.")
    return memory


def add_tool(name: str, category: str, description: str, path: str, date: str, pattern: str = ""):
    memory = load_memory()
    memory["tools"].append({
        "date": date,
        "name": name,
        "category": category,
        "pattern": pattern,
        "path": path,
        "description": description,
    })
    save_memory(memory)


def add_topic(date: str, title: str, path: str):
    memory = load_memory()
    memory["topics_covered"].append({
        "date": date,
        "title": title,
        "path": path,
    })
    save_memory(memory)


def get_memory_context() -> str:
    """
    Return a formatted summary of Lili's memory for injection into prompts.
    Tells her what she's already done so she doesn't repeat herself.
    """
    memory = load_memory()

    if not memory["tools"] and not memory["topics_covered"]:
        return "(No memory yet — this is Lili's first run.)"

    # Last 30 tools
    recent_tools = memory["tools"][-30:]
    tools_text = "\n".join(
        f"  • [{t['date']}] {t['name']} ({t['category']}, pattern:{t.get('pattern', '?')}): {t['description']}"
        for t in recent_tools
    )

    # Last 20 diary topics
    recent_topics = memory["topics_covered"][-20:]
    topics_text = "\n".join(
        f"  • [{t['date']}] {t['title']}"
        for t in recent_topics
    )

    return (
        f"TOOLS YOU'VE ALREADY BUILT (do not repeat these):\n{tools_text or '  (none yet)'}\n\n"
        f"TOPICS YOU'VE ALREADY COVERED (find fresh angles):\n{topics_text or '  (none yet)'}"
    )


def is_too_similar(new_topic: str, threshold: int = 3) -> tuple[bool, str]:
    """
    Check if a proposed topic is too similar to something Lili already covered.
    Returns (is_similar, matched_title).
    Simple keyword overlap check.
    """
    memory = load_memory()
    new_words = set(re.findall(r'\w+', new_topic.lower()))

    for entry in memory["topics_covered"]:
        existing_words = set(re.findall(r'\w+', entry["title"].lower()))
        overlap = len(new_words & existing_words)
        if overlap >= threshold:
            return True, entry["title"]

    return False, ""


if __name__ == "__main__":
    print("Rebuilding Lili's memory from repo...")
    memory = rebuild_memory_from_repo()
    print(f"\nMemory snapshot:")
    print(f"  Tools built: {len(memory['tools'])}")
    print(f"  Topics covered: {len(memory['topics_covered'])}")
    print(f"  Last updated: {memory['last_updated']}")
