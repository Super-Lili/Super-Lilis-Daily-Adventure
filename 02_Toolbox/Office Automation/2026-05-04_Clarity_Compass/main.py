import re


def categorize_tasks(tasks: list) -> dict:
    """Categorize tasks into Eisenhower matrix quadrants."""
    do_first, schedule, delegate, eliminate = [], [], [], []
    for task in tasks:
        u = task.get('urgency', 2)
        i = task.get('importance', 2)
        if u == 1 and i == 1:
            do_first.append(task['name'])
        elif u == 2 and i == 1:
            schedule.append(task['name'])
        elif u == 1 and i == 2:
            delegate.append(task['name'])
        else:
            eliminate.append(task['name'])
    return {"do_first": do_first, "schedule": schedule, "delegate": delegate, "eliminate": eliminate}


def process(text: str = "") -> str:
    """Parse a task list and sort into the Eisenhower priority matrix.

    Format: one task per line. Optionally append [urgent] and/or [important] tags.
    Lines without tags are treated as non-urgent and important (schedule).
    """
    if not text.strip():
        return (
            "Paste your task list (one per line) to sort into the Eisenhower Matrix.\n\n"
            "Add tags to each line: [urgent] [important] — e.g.:\n"
            "  Fix production bug [urgent] [important]\n"
            "  Write weekly report [important]\n"
            "  Reply to newsletter [urgent]\n"
            "  Browse social media"
        )
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    tasks = []
    for line in lines:
        urgent = 1 if re.search(r'\[urgent\]', line, re.IGNORECASE) else 2
        important = 1 if re.search(r'\[important\]', line, re.IGNORECASE) else 2
        name = re.sub(r'\[(urgent|important)\]', '', line, flags=re.IGNORECASE).strip()
        if name:
            tasks.append({'name': name, 'urgency': urgent, 'importance': important})
    if not tasks:
        return "No tasks found. Paste one task per line."
    cats = categorize_tasks(tasks)
    out = ["## Clarity Compass: Eisenhower Matrix", ""]

    def section(title, items):
        result = [f"### {title}"]
        if items:
            for t in items:
                result.append(f"- {t}")
        else:
            result.append("- (none)")
        return result

    out += section("DO FIRST — Urgent & Important", cats["do_first"])
    out += [""]
    out += section("SCHEDULE — Not Urgent & Important", cats["schedule"])
    out += [""]
    out += section("DELEGATE — Urgent & Not Important", cats["delegate"])
    out += [""]
    out += section("ELIMINATE — Not Urgent & Not Important", cats["eliminate"])
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    demo = (
        "Fix production bug [urgent] [important]\n"
        "Write weekly report [important]\n"
        "Reply to newsletter [urgent]\n"
        "Browse social media"
    )
    print(process(demo))