"""
Administrative Ascent Navigator
Category: Office Automation
Format: F - Generator + inline editor, Mode 3 HTML
Transforms overwhelming administrative situations into structured gamified micro-tasks
"""

import json
import re
import html
from typing import Dict, List, Tuple, Any

REQUIREMENTS = ["ast"]  # built-in

MIN_CHARS = 20

# Predefined micro-task templates for recognized entities
ENTITY_TASKS: Dict[str, List[Dict[str, Any]]] = {
    "divorce": [
        {"id": "legal_1", "title": "Read the Uniform Child Support Order completely",
         "effort": 2, "category": "Legal Summit", "milestone": False},
        {"id": "legal_2", "title": "Gather financial documents needed (tax returns, pay stubs)",
         "effort": 3, "category": "Legal Summit", "milestone": True},
        {"id": "legal_3", "title": "Fill out Section A: Parent Information",
         "effort": 2, "category": "Legal Summit", "milestone": False},
        {"id": "legal_4", "title": "Fill out Section B: Child Information",
         "effort": 2, "category": "Legal Summit", "milestone": False},
        {"id": "legal_5", "title": "Calculate income shares using worksheet",
         "effort": 4, "category": "Legal Summit", "milestone": True},
        {"id": "legal_6", "title": "Review completed form for errors",
         "effort": 1, "category": "Legal Summit", "milestone": False},
        {"id": "legal_7", "title": "Send completed form to lawyer for review",
         "effort": 1, "category": "Legal Summit", "milestone": True},
    ],
    "netflix": [
        {"id": "digital_1", "title": "Log into Netflix account",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
        {"id": "digital_2", "title": "Remove ex-partner from profile/plan",
         "effort": 2, "category": "Digital River Crossing", "milestone": True},
        {"id": "digital_3", "title": "Update password and security settings",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
    ],
    "amazon": [
        {"id": "digital_4", "title": "Log into Amazon account settings",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
        {"id": "digital_5", "title": "Manage Household and remove shared member",
         "effort": 2, "category": "Digital River Crossing", "milestone": True},
        {"id": "digital_6", "title": "Check payment methods and shared cards",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
    ],
    "google": [
        {"id": "digital_7", "title": "Open Google Photos settings",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
        {"id": "digital_8", "title": "Download shared family photos",
         "effort": 3, "category": "Digital River Crossing", "milestone": True},
        {"id": "digital_9", "title": "Remove ex-partner from shared albums",
         "effort": 2, "category": "Digital River Crossing", "milestone": False},
    ],
    "location": [
        {"id": "digital_10", "title": "Open location sharing settings on phone",
         "effort": 1, "category": "Digital River Crossing", "milestone": False},
        {"id": "digital_11", "title": "Find and stop sharing with ex-partner",
         "effort": 2, "category": "Digital River Crossing", "milestone": True},
    ],
    "legal": [
        {"id": "legal_8", "title": "Organize legal documents in a folder",
         "effort": 1, "category": "Legal Summit", "milestone": False},
    ],
    "bank": [
        {"id": "finance_1", "title": "Check joint bank accounts",
         "effort": 2, "category": "Financial Clearing", "milestone": True},
    ],
}

# Category metadata
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "Legal Summit": {"icon": "⚖️", "order": 0},
    "Digital River Crossing": {"icon": "🌊", "order": 1},
    "Financial Clearing": {"icon": "💰", "order": 2},
    "General Tasks": {"icon": "📋", "order": 3},
}

MILESTONE_THRESHOLDS = [10, 25, 50, 100]
BADGES = {
    10: "First Steps",
    25: "Climbing Steady",
    50: "Halfway Up",
    100: "Summit Master",
}


def extract_entities(text: str) -> List[Tuple[str, str]]:
    """Extract specific recognized entities from user input."""
    text_lower = text.lower()
    entities = []
    entity_patterns = [
        ("divorce", r"\bdivorce\b"),
        ("netflix", r"\bnetflix\b"),
        ("amazon", r"\bamazon\b"),
        ("google", r"\bgoogle\b"),
        ("location", r"\blocation\b"),
        ("legal", r"\blegal\b|\bcourt\b|\blawyer\b"),
        ("bank", r"\bbank\b|\baccount\b|\bfinancial\b"),
    ]
    for etype, pattern in entity_patterns:
        if re.search(pattern, text_lower):
            entities.append((etype, etype.capitalize()))
    if not entities:
        entities.append(("general", "General"))
    return entities


def assign_tasks_from_entities(entities: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Generate micro-tasks based on recognized entities."""
    tasks = []
    used_ids = set()
    for etype, _ in entities:
        if etype in ENTITY_TASKS:
            for task in ENTITY_TASKS[etype]:
                if task["id"] not in used_ids:
                    tasks.append(dict(task))
                    used_ids.add(task["id"])
    if not tasks:
        tasks.append({
            "id": "general_1",
            "title": "List all accounts and services shared",
            "effort": 2,
            "category": "General Tasks",
            "milestone": False
        })
        tasks.append({
            "id": "general_2",
            "title": "Prioritize which account to close first",
            "effort": 1,
            "category": "General Tasks",
            "milestone": False
        })
    return tasks


def compute_gamification(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate total points, milestones, and badges."""
    total_effort = sum(t["effort"] for t in tasks)
    milestones = []
    badges = {}
    for threshold in MILESTONE_THRESHOLDS:
        if total_effort >= threshold:
            milestones.append(threshold)
            if threshold in BADGES:
                badges[str(threshold)] = BADGES[threshold]
    return {
        "total_effort": total_effort,
        "milestones": milestones,
        "badges": badges,
    }


def categorize_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group tasks by category."""
    categorized: Dict[str, List[Dict[str, Any]]] = {}
    for task in tasks:
        cat = task["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(task)
    return categorized


def generate_dashboard_html(text: str, tasks: List[Dict[str, Any]]) -> str:
    """Generate the full interactive HTML dashboard."""
    gamification = compute_gamification(tasks)
    categorized = categorize_tasks(tasks)
    
    # Sort categories
    sorted_cats = sorted(categorized.keys(), key=lambda c: CATEGORIES.get(c, {}).get("order", 99))
    
    tasks_json = json.dumps(tasks)
    gamification_json = json.dumps(gamification)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Administrative Ascent Navigator</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #f5f2ed;
        color: #2d2a24;
        min-height: 100vh;
        padding: 2rem;
    }}
    .dashboard {{
        max-width: 1100px;
        margin: 0 auto;
    }}
    .ascent-path {{
        background: #e8e2d6;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        position: relative;
        text-align: center;
    }}
    .path-bar {{
        height: 12px;
        background: #d4cdc0;
        border-radius: 6px;
        margin: 1rem 0;
        overflow: hidden;
    }}
    .path-fill {{
        height: 100%;
        background: linear-gradient(90deg, #8b7355, #a0896a);
        border-radius: 6px;
        transition: width 0.8s ease;
        width: 0%;
    }}
    .progress-text {{
        font-size: 1.4rem;
        font-weight: 600;
        color: #5a4d3a;
    }}
    .points-display {{
        font-size: 2rem;
        font-weight: 700;
        color: #3d3527;
    }}
    .badges {{
        display: flex;
        gap: 0.5rem;
        justify-content: center;
        margin-top: 1rem;
    }}
    .badge {{
        background: #c4b8a5;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #2d2a24;
        display: none;
    }}
    .badge.earned {{ display: inline-block; background: #a0896a; color: #f5f2ed; }}
    .tab-section {{
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .tab-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }}
    .tab-icon {{ font-size: 1.5rem; }}
    .tab-title {{ font-size: 1.3rem; font-weight: 600; color: #3d3527; }}
    .task-card {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #faf8f5;
        border-radius: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    .task-card:hover {{ background: #f0ebe3; }}
    .task-card.completed {{
        opacity: 0.6;
        background: #e8e2d6;
    }}
    .task-checkbox {{
        width: 24px;
        height: 24px;
        border: 2px solid #8b7355;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: all 0.2s ease;
    }}
    .task-checkbox.checked {{
        background: #8b7355;
        color: white;
    }}
    .task-title {{
        flex: 1;
        font-size: 1rem;
        line-height: 1.4;
    }}
    .task-effort {{
        background: #e8e2d6;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        color: #5a4d3a;
    }}
    .achievement-log {{
        margin-top: 2rem;
        padding: 1rem;
        background: #e8e2d6;
        border-radius: 12px;
        max-height: 200px;
        overflow-y: auto;
    }}
    .achievement-entry {{
        padding: 0.4rem 0;
        font-size: 0.9rem;
        color: #5a4d3a;
        border-bottom: 1px solid #d4cdc0;
    }}
    .achievement-entry:last-child {{ border: none; }}
    .reset-btn {{
        background: #8b7355;
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-top: 1rem;
    }}
    .reset-btn:hover {{ background: #6d5a41; }}
    .chime {{
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: #a0896a;
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }}
    .chime.show {{ opacity: 1; }}
    @media (max-width: 600px) {{
        body {{ padding: 1rem; }}
        .ascent-path {{ padding: 1rem; }}
    }}
</style>
</head>
<body>
<div class="dashboard">
    <div class="ascent-path">
        <div class="progress-text">Ascent Path</div>
        <div class="points-display" id="pointsDisplay">0</div>
        <div class="path-bar">
            <div class="path-fill" id="pathFill" style="width:0%"></div>
        </div>
        <div class="badges" id="badgesContainer"></div>
    </div>

    <div id="taskSections">
    {''.join(
        f'''<div class="tab-section">
            <div class="tab-header">
                <span class="tab-icon">{CATEGORIES.get(cat, {}).get("icon", "📋")}</span>
                <span class="tab-title">{html.escape(cat)}</span>
            </div>
            {''.join(
                f'''<div class="task-card" data-id="{t["id"]}" data-effort="{t["effort"]}">
                    <div class="task-checkbox" id="cb_{t["id"]}"></div>
                    <span class="task-title">{html.escape(t["title"])}</span>
                    <span class="task-effort">{t["effort"]} pts</span>
                </div>'''
                for t in cat_tasks
            )}
        </div>'''
        for cat, cat_tasks in [(c, categorized.get(c, [])) for c in sorted_cats]
    )}
    </div>

    <div class="achievement-log" id="achievementLog">
        <div class="achievement-entry">✨ Ascent started! Your journey begins.</div>
    </div>

    <button class="reset-btn" onclick="resetAll()">Start New Ascent</button>
</div>

<div class="chime" id="chimeNotification">✓ Task completed!</div>

<script>
    const tasks = {tasks_json};
    const gamification = {gamification_json};
    let earnedPoints = 0;
    let completedTasks = new Set();
    let achievementLog = document.getElementById('achievementLog');

    function playChime() {{
        const chime = document.getElementById('chimeNotification');
        chime.classList.add('show');
        setTimeout(() => chime.classList.remove('show'), 1500);
    }}

    function addAchievement(text) {{
        const entry = document.createElement('div');
        entry.className = 'achievement-entry';
        entry.textContent = text;
        achievementLog.appendChild(entry);
        achievementLog.scrollTop = achievementLog.scrollHeight;
    }}

    function updateProgress() {{
        const totalEffort = gamification.total_effort;
        const pct = totalEffort > 0 ? (earnedPoints / totalEffort) * 100 : 0;
        document.getElementById('pathFill').style.width = Math.min(pct, 100) + '%';
        document.getElementById('pointsDisplay').textContent = earnedPoints;
        
        // Update badges
        document.querySelectorAll('.badge').forEach(b => b.classList.remove('earned'));
        Object.entries(gamification.badges).forEach(([threshold, name]) => {{
            if (earnedPoints >= parseInt(threshold)) {{
                const badgeEl = document.getElementById('badge_' + threshold);
                if (badgeEl) badgeEl.classList.add('earned');
            }}
        }});
    }}

    function completeTask(taskId) {{
        if (completedTasks.has(taskId)) return;
        const task = tasks.find(t => t.id === taskId);
        if (!task) return;
        
        completedTasks.add(taskId);
        earnedPoints += task.effort;
        
        // Update UI
        const card = document.querySelector(`.task-card[data-id="${{taskId}}"]`);
        if (card) {{
            card.classList.add('completed');
            const cb = card.querySelector('.task-checkbox');
            cb.classList.add('checked');
            cb.textContent = '✓';
        }}
        
        playChime();
        addAchievement(`✓ Completed: ${{task.title}} (+${{task.effort}} pts)`);
        updateProgress();
        
        // Milestone check
        Object.entries(gamification.badges).forEach(([threshold, name]) => {{
            if (earnedPoints >= parseInt(threshold) && !document.getElementById('badge_' + threshold)?.classList.contains('earned')) {{
                setTimeout(() => {{
                    addAchievement(`🏆 Milestone: ${{name}}!`);
                    const badgeEl = document.getElementById('badge_' + threshold);
                    if (badgeEl) badgeEl.classList.add('earned');
                }}, 500);
            }}
        }});
        
        // Summit check
        if (earnedPoints >= gamification.total_effort) {{
            setTimeout(() => {{
                document.querySelector('.ascent-path').innerHTML = `
                    <div style="text-align:center;">
                        <div style="font-size:3rem;margin-bottom:1rem;">🎉</div>
                        <div class="progress-text" style="font-size:1.8rem;">Summit Reached!</div>
                        <div class="points-display">${{earnedPoints}} total points earned</div>
                        <div style="margin:1rem 0;">
                            ${Object.values(gamification.badges).map(b => `<span class="badge earned">${{b}}</span>`).join(' ')}
                        </div>
                        <p style="color:#5a4d3a;margin:1rem 0;">You transformed overwhelm into action. Every step counted.</p>
                        <div style="display:flex;gap:0.5rem;justify-content:center;flex-wrap:wrap;">
                            <button class="reset-btn" onclick="window.location.reload()">Review My Journey</button>
                            <button class="reset-btn" onclick="window.location.reload()">Start a New Ascent</button>
                            <button class="reset-btn" onclick="navigator.clipboard.writeText('Ascent Complete! Points: ${{earnedPoints}}')">Export Progress</button>
                        </div>
                    </div>
                `;
                addAchievement('🎯 Summit reached! You did it.');
            }}, 800);
        }}
    }}

    function resetAll() {{
        location.reload();
    }}

    // Initialize badges
    (function initBadges() {{
        const container = document.getElementById('badgesContainer');
        Object.entries(gamification.badges).forEach(([threshold, name]) => {{
            const badge = document.createElement('span');
            badge.className = 'badge';
            badge.id = 'badge_' + threshold;
            badge.textContent = name;
            container.appendChild(badge);
        }});
    }})();

    // Event listeners
    document.querySelectorAll('.task-card').forEach(card => {{
        card.addEventListener('click', function() {{
            completeTask(this.dataset.id);
        }});
    }});

    // Keyboard support
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'Enter' && e.target.classList.contains('task-card')) {{
            completeTask(e.target.dataset.id);
        }}
    }});
</script>
</body>
</html>"""
    return html_content


def process(text: str) -> str:
    """Main entry point: transform overwhelming situation into gamified dashboard."""
    if not text or len(text.strip()) < MIN_CHARS:
        return f"""<div style="font-family:-apple-system,sans-serif;padding:2rem;text-align:center;color:#555;">
            <p style="font-size:1.2rem;">Please describe your situation in more detail.</p>
            <p style="color:#999;margin-top:0.5rem;">Example: My divorce lawyer sent me the Uniform Child Support Order to fill out, and I need to cut off Netflix, Amazon, and shared Google Photos.</p>
        </div>"""
    
    # Parse input
    entities = extract_entities(text)
    tasks = assign_tasks_from_entities(entities)
    
    # Generate dashboard
    return generate_dashboard_html(text, tasks)


def _cli_main() -> None:
    """CLI entry point for direct execution."""
    print("=== Administrative Ascent Navigator ===")
    print("Describe the overwhelming situation you're facing:")
    try:
        user_input = input("> ")
    except EOFError:
        user_input = ""
    if user_input.strip():
        result = process(user_input)
        print(result)
    else:
        print("Please provide a description of your situation.")


# Dual-mode pattern execution
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()