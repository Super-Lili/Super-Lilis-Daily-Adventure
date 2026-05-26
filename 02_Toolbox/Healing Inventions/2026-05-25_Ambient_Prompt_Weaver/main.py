import pandas as pd
import random
import argparse
from datetime import datetime
import os

# Requirements:
# pandas

def create_demo_csv(filepath="tasks_input.csv"):
    """
    Creates a sample CSV file for demonstration purposes.
    """
    data = {
        'task_name': [
            "Drink water", "Stretch for 5 minutes", "Review morning emails",
            "Take a short walk", "Hydrate again", "Process 2 urgent items",
            "Plan tomorrow's top 3 tasks", "Quick tidy up desk", "Read a chapter"
        ],
        'time_block': [
            "morning", "morning", "morning",
            "afternoon", "afternoon", "afternoon",
            "evening", "evening", "evening"
        ]
    }
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    print(f"Demo CSV '{filepath}' created successfully.")

def generate_cue_card_html(task_name, output_dir, time_block, title_prefix="Ambient Cue"):
    """
    Generates a minimalist HTML file displaying a single ambient task prompt.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title_prefix} - {time_block.capitalize()}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f4f8; /* Soft, calming background */
                color: #334e68;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                box-sizing: border-box;
                text-align: center;
            }}
            .card {{
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
                padding: 40px 30px;
                max-width: 600px;
                width: 100%;
                border-left: 6px solid #6699ff; /* Subtle accent color */
            }}
            h1 {{
                font-size: 2.5em;
                margin-bottom: 20px;
                color: #4a6fa5;
            }}
            p {{
                font-size: 1.2em;
                line-height: 1.6;
                color: #555;
            }}
            .timestamp {{
                margin-top: 30px;
                font-size: 0.85em;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Your Gentle Nudge:</h1>
            <p>{task_name}</p>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>
    </body>
    </html>
    """
    filename = os.path.join(output_dir, f"ambient_cue_{time_block}.html")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename
    except IOError as e:
        print(f"Error writing file {filename}: {e}")
        return None

def process_tasks(input_filepath: str, output_dir: str):
    """
    Reads tasks from a CSV, groups them by time block, and generates
    a single ambient cue HTML file for each time block.
    """
    if not os.path.exists(input_filepath):
        print(f"Error: Input file '{input_filepath}' not found. Please check the path.")
        return

    try:
        df = pd.read_csv(input_filepath)
    except pd.errors.EmptyDataError:
        print(f"Error: Input file '{input_filepath}' is empty.")
        return
    except Exception as e:
        print(f"Error reading CSV file '{input_filepath}': {e}")
        return

    if df.empty:
        print("No tasks found in the input file. Nothing to generate.")
        return

    required_columns = ['task_name', 'time_block']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV must contain the columns: {', '.join(required_columns)}")
        return

    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    for time_block, group_df in df.groupby('time_block'):
        if not group_df.empty:
            chosen_task = random.choice(group_df['task_name'].tolist())
            print(f"Generating cue for {time_block.capitalize()}: '{chosen_task}'")
            html_file = generate_cue_card_html(chosen_task, output_dir, time_block)
            if html_file:
                generated_files.append(html_file)
        else:
            print(f"No tasks defined for time block: {time_block}")

    if generated_files:
        print(f"\nSuccessfully generated {len(generated_files)} ambient cue files in '{output_dir}':")
        for f in generated_files:
            print(f"- {os.path.basename(f)}")
        print("\nTip: Keep these files open in separate browser tabs for gentle, ambient reminders throughout your day!")
    else:
        print("No ambient cue files were generated.")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Ambient Prompt Weaver: Creates subtle HTML cue cards for daily tasks, "
                    "helping with focus without overwhelming visual clutter. "
                    "Each cue card displays one randomly selected task for a specific time block."
    )
    parser.add_argument(
        '--input_file',
        type=str,
        default='tasks_input.csv',
        help="Path to the CSV file containing tasks. "
             "It must have 'task_name' and 'time_block' columns. "
             "Example time_blocks: 'morning', 'afternoon', 'evening'."
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='ambient_cues',
        help="Directory to save the generated HTML ambient cue files."
    )
    parser.add_argument(
        '--create_demo',
        action='store_true',
        help="Create a sample 'tasks_input.csv' file in the current directory and exit."
    )

    parsed_args = parser.parse_args(args)

    if parsed_args.create_demo:
        create_demo_csv(parsed_args.input_file)
        return

    process_tasks(parsed_args.input_file, parsed_args.output_dir)

def process(text: str = "") -> str:
    """Parse task list and generate ambient cue suggestions grouped by time block."""
    if not text.strip():
        return "Paste tasks in CSV format (task_name,time_block per line) or as plain text to get ambient cue suggestions."
    import io
    import csv as _csv
    tasks_by_block = {}
    # Try CSV parse first
    try:
        reader = _csv.DictReader(io.StringIO(text.strip()))
        rows = list(reader)
        if rows and "task_name" in (reader.fieldnames or []):
            for row in rows:
                name = row.get("task_name", "").strip()
                block = row.get("time_block", "general").strip().lower()
                if name:
                    tasks_by_block.setdefault(block, []).append(name)
        else:
            raise ValueError("not csv with headers")
    except Exception:
        # Treat each line as a task
        for line in text.strip().splitlines():
            line = line.strip().lstrip("-*• ")
            if line:
                tasks_by_block.setdefault("general", []).append(line)
    if not tasks_by_block:
        return "No tasks found. Try pasting tasks as plain text (one per line) or CSV with task_name,time_block columns."
    import random as _random
    out = ["## Ambient Cue Suggestions", ""]
    for block, tasks in sorted(tasks_by_block.items()):
        chosen = _random.choice(tasks)
        out.append(f"**{block.capitalize()} focus:** {chosen}")
        out.append(f"  _(from {len(tasks)} task(s) in this block)_")
        out.append("")
    out.append("Tip: Keep a tab open with your ambient cue for gentle, distraction-free reminders!")
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Create a demo input file for the test run
    demo_input_filename = "demo_tasks_for_weaver.csv"
    create_demo_csv(demo_input_filename)

    # Run the main function with the demo file and a specific output directory
    output_directory = "demo_ambient_cues"
    main(["--input_file", demo_input_filename, "--output_dir", output_directory])

    # Clean up demo files after potential inspection
    # import shutil
    # if os.path.exists(output_directory):
    #     shutil.rmtree(output_directory)
    # if os.path.exists(demo_input_filename):
    #     os.remove(demo_input_filename)