```python
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

def prioritize_tasks():
    """Helps prioritize tasks based on urgency and importance."""
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

    # Categorize tasks
    do_first = [] # Urgent & Important
    schedule = [] # Not Urgent & Important
    delegate = [] # Urgent & Not Important
    eliminate = [] # Not Urgent & Not Important

    for task in tasks:
        if task['urgency'] == 1 and task['importance'] == 1:
            do_first.append(task['name'])
        elif task['urgency'] == 2 and task['importance'] == 1:
            schedule.append(task['name'])
        elif task['urgency'] == 1 and task['importance'] == 2:
            delegate.append(task['name'])
        else: # task['urgency'] == 2 and task['importance'] == 2
            eliminate.append(task['name'])

    print("\n--- Your Prioritized Tasks ---")
    if do_first:
        print("\n⚡️ DO FIRST (Urgent & Important):")
        for t in do_first:
            print(f"- {t}")
    else:
        print("\n⚡️ DO FIRST (Urgent & Important): None")

    if schedule:
        print("\n🗓️ SCHEDULE (Not Urgent & Important):")
        for t in schedule:
            print(f"- {t}")
    else:
        print("\n🗓️ SCHEDULE (Not Urgent & Important): None")

    if delegate:
        print("\n🤝 DELEGATE (Urgent & Not Important):")
        for t in delegate:
            print(f"- {t}")
    else:
        print("\n🤝 DELEGATE (Urgent & Not Important): None")

    if eliminate:
        print("\n🗑️ ELIMINATE (Not Urgent & Not Important):")
        for t in eliminate:
            print(f"- {t}")
    else:
        print("\n🗑️ ELIMINATE (Not Urgent & Not Important): None")

if __name__ == "__main__":
    prioritize_tasks()
```