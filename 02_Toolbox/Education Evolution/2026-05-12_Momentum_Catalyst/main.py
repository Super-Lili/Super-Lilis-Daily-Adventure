import argparse
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# rich is optional — falls back to plain print if not available (e.g. in Pyodide)
try:
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TimeElapsedColumn
    from rich.text import Text
    _RICH_AVAILABLE = True
except ImportError:
    Console = None
    Progress = None
    _RICH_AVAILABLE = False


def setup_cli_arguments() -> argparse.Namespace:
    """Sets up and parses command-line arguments for the Momentum Catalyst tool."""
    parser = argparse.ArgumentParser(
        description="Momentum Catalyst: Break down big tasks into tiny 'ignition tasks' and build momentum.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--main_task", type=str, required=True,
                        help="The main, overwhelming task you need to start.")
    parser.add_argument("--log_file", type=str, default="momentum_log.csv",
                        help="Path to the CSV file where your progress will be logged.")
    parser.add_argument("--sprint_duration", type=int, default=5,
                        help="Duration in minutes for each micro-sprint. Default is 5 minutes.")
    parser.add_argument("--no_rich", action="store_true",
                        help="Disable rich console output even if the library is installed.")
    parser.add_argument("--run_demos", action="store_true",
                        help="Run demonstration scenarios instead of the main tool.")
    return parser.parse_args()


def get_micro_tasks(console: Any) -> List[str]:
    """Interactively prompts the user to define tiny, actionable micro-tasks."""
    if console:
        console.print(Text("\nOkay, let's break that monster down! Think *tiny* steps.", style="bold green"))
        console.print(Text("Type 'done' or press Enter on an empty line when finished.", style="italic dim"))
    else:
        print("\nOkay, let's break that monster down! Think *tiny* steps.")
        print("Type 'done' or press Enter on an empty line when finished.")

    micro_tasks: List[str] = []
    task_num = 1
    while True:
        task = input(f"   Micro-task {task_num}: ").strip()
        if not task or task.lower() == 'done':
            break
        micro_tasks.append(task)
        task_num += 1

    if not micro_tasks:
        if console:
            console.print(Text("No micro-tasks added. Let's try again with at least one!", style="bold red"))
        else:
            print("No micro-tasks added. Let's try again with at least one!")
        return get_micro_tasks(console)
    return micro_tasks


def run_micro_sprint(task_name: str, duration_minutes: int, console: Any) -> bool:
    """Runs a timed micro-sprint for a given task."""
    duration_seconds = duration_minutes * 60

    if console and Progress and _RICH_AVAILABLE:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task(f"[yellow]Sprinting on '{task_name}'...", total=duration_seconds)
            start_time = time.monotonic()
            while not progress.finished:
                elapsed = time.monotonic() - start_time
                progress.update(task_id, completed=elapsed)
                time.sleep(1)
        console.print(Text(f"\nTime's up for '{task_name}'!", style="bold magenta"))
        choice = console.input(Text("Did you complete this micro-task? (y/n): ", style="cyan")).lower()
    else:
        print(f"\n--- Starting sprint for: '{task_name}' ({duration_minutes} minutes) ---")
        print("Focus! You've got this!")
        time.sleep(duration_seconds)
        print(f"\nTime's up for '{task_name}'!")
        choice = input("Did you complete this micro-task? (y/n): ").lower()

    return choice == 'y'


def log_progress(log_file: Path, main_task: str, micro_task: str, completed: bool) -> None:
    """Logs the completion status of a micro-task to a CSV file."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_exists = log_file.exists()
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Main Task", "Micro Task", "Completed"])
        timestamp = datetime.now().isoformat()
        writer.writerow([timestamp, main_task, micro_task, "Yes" if completed else "No"])


def main_workflow(args: argparse.Namespace) -> None:
    """Orchestrates the main workflow of the Momentum Catalyst tool."""
    use_rich = _RICH_AVAILABLE and Console and not args.no_rich
    console = Console() if use_rich else None

    if console:
        console.print(Text("\nWelcome to Momentum Catalyst! Let's get that brain moving!", style="bold yellow"))
        console.print(Text(f"Your big task for today: '{args.main_task}'", style="italic"))
    else:
        print("\nWelcome to Momentum Catalyst! Let's get that brain moving!")
        print(f"Your big task for today: '{args.main_task}'")

    micro_tasks = get_micro_tasks(console)
    log_path = Path(args.log_file)
    completed_count = 0

    if console:
        console.print(Text("\nReady, set, micro-sprint!", style="bold green"))
    else:
        print("\nReady, set, micro-sprint!")

    for i, task in enumerate(micro_tasks):
        if console:
            console.print(Text(f"\nStarting micro-task {i+1}/{len(micro_tasks)}: '{task}'", style="bold"))
        else:
            print(f"\nStarting micro-task {i+1}/{len(micro_tasks)}: '{task}'")

        if run_micro_sprint(task, args.sprint_duration, console):
            log_progress(log_path, args.main_task, task, True)
            completed_count += 1
            if console:
                console.print(Text("Awesome! One more step towards victory!", style="green"))
            else:
                print("Awesome! One more step towards victory!")
        else:
            log_progress(log_path, args.main_task, task, False)
            if console:
                console.print(Text("No worries, every attempt builds the muscle! Let's try the next one.", style="dim yellow"))
            else:
                print("No worries, every attempt builds the muscle! Let's try the next one.")

        if i < len(micro_tasks) - 1:
            if console:
                console.print(Text("\nTaking a tiny breather before the next spark...", style="italic dim"))
                time.sleep(2)
            else:
                print("\nTaking a tiny breather before the next spark...")
                time.sleep(2)

    if console:
        console.print(Text(f"\n\n--- Session Complete! ---", style="bold yellow"))
        console.print(Text(f"You tackled '{args.main_task}' with {completed_count} completed micro-tasks today!", style="bold green"))
        console.print(Text(f"Check your progress in {log_path}", style="magenta"))
        console.print(Text("Remember, consistency over intensity! You got this!", style="bold yellow"))
    else:
        print(f"\n\n--- Session Complete! ---")
        print(f"You tackled '{args.main_task}' with {completed_count} completed micro-tasks today!")
        print(f"Check your progress in {log_path}")
        print("Remember, consistency over intensity! You got this!")


class MockArgs:
    def __init__(self, main_task: str, log_file: str, sprint_duration: int, no_rich: bool = False, run_demos: bool = False):
        self.main_task = main_task
        self.log_file = log_file
        self.sprint_duration = sprint_duration
        self.no_rich = no_rich
        self.run_demos = run_demos


def process(text: str) -> str:
    """
    Show a Momentum Catalyst plan for the given task (no timers, no interactive input).
    Input: the name of a big task to break down.
    Falls back to a default demo task if empty.
    """
    task = text.strip() or "Write my big project"

    # Suggest a simple micro-task breakdown without running timers
    suggestions = [
        f"Open a blank document for: {task}",
        "Write the title / first heading",
        "Jot down 3 bullet points of what you already know",
        "Set a 5-minute timer and just start typing",
        "Review what you wrote and pick one thing to expand",
    ]

    lines = [
        f"Momentum Catalyst: Breaking Down '{task}'",
        "=" * 50,
        "Here are 5 tiny ignition tasks to get you moving:",
        "",
    ]
    for i, s in enumerate(suggestions, 1):
        lines.append(f"  {i}. {s}")
    lines.append("")
    lines.append("Tip: Do ONE of these right now. Momentum starts with the first step!")
    lines.append("For the full interactive timer experience, run: python3 main.py --main_task \"<your task>\"")
    return "\n".join(lines)


def _run_demos():
    global get_micro_tasks, run_micro_sprint

    print("--- DEMO SCENARIO 1: Starting a new study session ---")
    demo_args_1 = MockArgs(
        main_task="Research for my history presentation",
        log_file="demo_momentum_log_1.csv",
        sprint_duration=1
    )
    original_get_micro_tasks = get_micro_tasks
    get_micro_tasks = lambda console_obj: ["Open research notes document", "Read one article abstract", "Find 2 keywords from reading", "Create a new slide for title"]

    original_run_micro_sprint = run_micro_sprint
    sprint_results_1 = [True, True, False, True]
    sprint_idx_1 = 0

    def mock_run_micro_sprint_1(task_name: str, duration_minutes: int, console: Any) -> bool:
        nonlocal sprint_idx_1
        print(f"Simulating sprint for '{task_name}' (1 minute)...")
        time.sleep(0.5)
        result = sprint_results_1[sprint_idx_1]
        print(f"Simulated completion for '{task_name}': {'Yes' if result else 'No'}")
        sprint_idx_1 += 1
        return result

    run_micro_sprint = mock_run_micro_sprint_1
    main_workflow(demo_args_1)
    print("\n" + "=" * 50 + "\n")

    print("--- DEMO SCENARIO 2: Continuing with another small task ---")
    demo_args_2 = MockArgs(
        main_task="Review math homework problems",
        log_file="demo_momentum_log_1.csv",
        sprint_duration=1
    )
    sprint_results_2 = [True, True]
    sprint_idx_2 = 0

    def mock_run_micro_sprint_2(task_name: str, duration_minutes: int, console: Any) -> bool:
        nonlocal sprint_idx_2
        print(f"Simulating sprint for '{task_name}' (1 minute)...")
        time.sleep(0.5)
        result = sprint_results_2[sprint_idx_2]
        print(f"Simulated completion for '{task_name}': {'Yes' if result else 'No'}")
        sprint_idx_2 += 1
        return result

    run_micro_sprint = mock_run_micro_sprint_2
    get_micro_tasks = lambda console_obj: ["Open textbook to Chapter 3", "Reread example problem 1"]
    main_workflow(demo_args_2)
    print("\n" + "=" * 50 + "\n")

    print("--- DEMO SCENARIO 3: Running without 'rich' library (basic output) ---")
    demo_args_3 = MockArgs(
        main_task="Brainstorm ideas for art project",
        log_file="demo_momentum_log_no_rich.csv",
        sprint_duration=1,
        no_rich=True
    )
    sprint_results_3 = [True, False, True]
    sprint_idx_3 = 0

    def mock_run_micro_sprint_3(task_name: str, duration_minutes: int, console: Any) -> bool:
        nonlocal sprint_idx_3
        print(f"Simulating sprint for '{task_name}' (1 minute)...")
        time.sleep(0.5)
        result = sprint_results_3[sprint_idx_3]
        print(f"Simulated completion for '{task_name}': {'Yes' if result else 'No'}")
        sprint_idx_3 += 1
        return result

    run_micro_sprint = mock_run_micro_sprint_3
    get_micro_tasks = lambda console_obj: ["Sketch 3 quick shapes", "Look at 1 inspiration image", "Draw a blob"]
    main_workflow(demo_args_3)
    print("\n" + "=" * 50 + "\n")

    get_micro_tasks = original_get_micro_tasks
    run_micro_sprint = original_run_micro_sprint

    print(f"Demo log files created: {Path('demo_momentum_log_1.csv').exists()}, {Path('demo_momentum_log_no_rich.csv').exists()}")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    args = setup_cli_arguments()
    if args.run_demos:
        _run_demos()
    else:
        main_workflow(args)
