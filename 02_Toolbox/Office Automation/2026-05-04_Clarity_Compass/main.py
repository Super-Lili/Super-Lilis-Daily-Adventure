def get_task_input(prompt):
    """Gets validated integer input for task priority."""
    while True:
        try:
            value = int(input(prompt))
            if value in [1, 2]:
                return value
            else:
                print("Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def categorize_tasks(tasks):
    """Categorize a list of task dicts into the Eisenhower Matrix quadrants."""
    do_first = []
    schedule = []
    delegate = []
    eliminate = []

    for task in tasks:
        u = task['urgency']
        i = task['importance']
        if u == 1 and i == 1:
            do_first.append(task['name'])
        elif u == 2 and i == 1:
            schedule.append(task['name'])
        elif u == 1 and i == 2:
            delegate.append(task['name'])
        else:
            eliminate.append(task['name'])

    return do_first, schedule, delegate, eliminate


def format_prioritized_tasks(do_first, schedule, delegate, eliminate):
    """Format the categorized tasks as a plain-text report."""
    lines = ["\n--- Your Prioritized Tasks ---"]

    lines.append("\nDO FIRST (Urgent & Important):")
    lines.extend([f"- {t}" for t in do_first] if do_first else ["- None"])

    lines.append("\nSCHEDULE (Not Urgent & Important):")
    lines.extend([f"- {t}" for t in schedule] if schedule else ["- None"])

    lines.append("\nDELEGATE (Urgent & Not Important):")
    lines.extend([f"- {t}" for t in delegate] if delegate else ["- None"])

    lines.append("\nELIMINATE (Not Urgent & Not Important):")
    lines.extend([f"- {t}" for t in eliminate] if eliminate else ["- None"])

    return "\n".join(lines)


def process(text: str) -> str:
    """
    Prioritize tasks using the Eisenhower Matrix.
    Input format: one task per line as 'task name | urgency(1/2) | importance(1/2)'
    Example:
      Fix server bug | 1 | 1
      Update docs | 2 | 1
      Reply to low-prio email | 1 | 2
      Clean old reports | 2 | 2
    Falls back to a demo if empty.
    """
    tasks = []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    if lines:
        for line in lines:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                try:
                    u = int(parts[1])
                    i = int(parts[2])
                    if u in (1, 2) and i in (1, 2):
                        tasks.append({'name': parts[0], 'urgency': u, 'importance': i})
                except ValueError:
                    pass
            elif len(parts) == 1 and parts[0]:
                # Just a task name — default to urgent + important
                tasks.append({'name': parts[0], 'urgency': 1, 'importance': 1})

    if not tasks:
        tasks = [
            {'name': 'Fix critical production bug', 'urgency': 1, 'importance': 1},
            {'name': 'Write quarterly review', 'urgency': 2, 'importance': 1},
            {'name': 'Answer routine email', 'urgency': 1, 'importance': 2},
            {'name': 'Reorganize old archive folder', 'urgency': 2, 'importance': 2},
        ]

    do_first, schedule, delegate, eliminate = categorize_tasks(tasks)
    return format_prioritized_tasks(do_first, schedule, delegate, eliminate)


def prioritize_tasks():
    """Interactive version: Helps prioritize tasks based on urgency and importance."""
    tasks = []
    print("Welcome to Clarity Compass! Let's prioritize your tasks.")
    print("For each task, tell me: (1) Urgent, (2) Not Urgent; and (1) Important, (2) Not Important.")

    while True:
        task_name = input("\nEnter a task (or 'done' to finish): ").strip()
        if task_name.lower() == 'done':
            break

        print(f"\n--- Task: {task_name} ---")
        urgency = get_task_input("Is this task (1) Urgent or (2) Not Urgent? ")
        importance = get_task_input("Is this task (1) Important or (2) Not Important? ")

        tasks.append({'name': task_name, 'urgency': urgency, 'importance': importance})

    if not tasks:
        print("\nNo tasks to prioritize. Exiting Clarity Compass.")
        return

    do_first, schedule, delegate, eliminate = categorize_tasks(tasks)
    print(format_prioritized_tasks(do_first, schedule, delegate, eliminate))


def _cli_main():
    prioritize_tasks()


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
