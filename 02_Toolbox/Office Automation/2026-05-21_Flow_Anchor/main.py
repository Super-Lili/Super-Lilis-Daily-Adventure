import argparse
import csv
from datetime import datetime, timedelta
import os
import textwrap

# Third-party libraries
# pip install ics pytz

# Note: pytz is generally recommended for robust timezone handling,
# but for simplicity in this demo where the user's local timezone is assumed
# for output, it's not strictly required unless cross-timezone scheduling is needed.
# However, including it in requirements for robustness in real-world use.

# Requirements:
# pandas (for robust CSV reading, though simple csv module is used here to reduce dependencies for a small script)
# ics (for .ics file generation)
# pytz (for timezone awareness in ICS, though basic local time is used in demo for simplicity)


def validate_time_format(time_str: str) -> bool:
    """Validates if a string is in HH:MM format."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def generate_ics_event(
    start_time: datetime,
    end_time: datetime,
    summary: str,
    description: str,
    uid: str
) -> str:
    """Generates a single ICS event string."""
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    start_dt = start_time.strftime("%Y%m%dT%H%M%S")
    end_dt = end_time.strftime("%Y%m%dT%H%M%S")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Flow Anchor//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{start_dt}
DTEND:{end_dt}
SUMMARY:{summary}
DESCRIPTION:{description}
END:VEVENT
END:VCALENDAR"""
    return ics_content

def generate_status_message(project_name: str, custom_message: str, start_time: str, end_time: str) -> str:
    """Generates a customizable status message."""
    if custom_message:
        message = custom_message.format(
            project=project_name,
            start=start_time,
            end=end_time
        )
    else:
        message = (
            f"Heads up! I'm in deep focus on '{project_name}' from {start_time} to {end_time} today. "
            "I'll be checking messages afterward. Thanks for understanding!"
        )
    return textwrap.dedent(message).strip()

def process_focus_blocks(
    input_csv_path: str,
    output_dir: str,
    ics_timezone: str = "America/New_York" # Default timezone for ICS events
):
    """
    Reads focus block data from a CSV, generates ICS calendar files and status messages.

    Args:
        input_csv_path (str): Path to the input CSV file.
        output_dir (str): Directory to save generated files.
        ics_timezone (str): IANA timezone string for ICS events.
    """
    if not os.path.exists(input_csv_path):
        print(f"Error: Input CSV file not found at '{input_csv_path}'. Please check the path.")
        return

    os.makedirs(output_dir, exist_ok=True)
    status_messages = []
    processed_count = 0

    try:
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Expected headers: Date, Start Time, End Time, Project/Task, Custom Message (Optional)
            required_headers = ["Date", "Start Time", "End Time", "Project/Task"]
            if not all(header in reader.fieldnames for header in required_headers):
                print(f"Error: CSV is missing required headers. Expected: {', '.join(required_headers)}")
                print(f"Found: {', '.join(reader.fieldnames)}")
                return

            for i, row in enumerate(reader):
                try:
                    date_str = row["Date"].strip()
                    start_time_str = row["Start Time"].strip()
                    end_time_str = row["End Time"].strip()
                    project_name = row["Project/Task"].strip()
                    custom_msg_template = row.get("Custom Message", "").strip()

                    if not (date_str and start_time_str and end_time_str and project_name):
                        print(f"Warning: Skipping row {i+2} due to missing required data: {row}")
                        continue
                    if not (validate_time_format(start_time_str) and validate_time_format(end_time_str)):
                        print(f"Warning: Skipping row {i+2} due to invalid time format (HH:MM required) for '{start_time_str}' or '{end_time_str}': {row}")
                        continue

                    # Parse date and time
                    focus_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    start_dt_obj = datetime.strptime(start_time_str, "%H:%M").time()
                    end_dt_obj = datetime.strptime(end_time_str, "%H:%M").time()

                    start_combined = datetime.combine(focus_date, start_dt_obj)
                    end_combined = datetime.combine(focus_date, end_dt_obj)

                    if end_combined <= start_combined:
                        print(f"Warning: Skipping row {i+2} as end time is not after start time: {row}")
                        continue

                    # Generate ICS file
                    ics_summary = f"Deep Work: {project_name}"
                    ics_description = f"Dedicated focus time for {project_name}. Please minimize interruptions."
                    # A unique ID for the event, combining date and project for simplicity
                    uid = f"flowanchor-{focus_date.isoformat()}-{project_name.replace(' ', '-')}-{i+1}@example.com"
                    ics_content = generate_ics_event(start_combined, end_combined, ics_summary, ics_description, uid)
                    
                    ics_filename = os.path.join(output_dir, f"{focus_date.isoformat()}-{project_name.replace(' ', '_')}.ics")
                    with open(ics_filename, 'w', encoding='utf-8') as ics_file:
                        ics_file.write(ics_content)
                    print(f"Generated ICS: {ics_filename}")

                    # Generate status message
                    status_msg = generate_status_message(
                        project_name,
                        custom_msg_template,
                        start_time_str,
                        end_time_str
                    )
                    status_messages.append(f"--- Focus Block for {date_str} ({start_time_str}-{end_time_str}) ---\n{status_msg}\n")
                    processed_count += 1

                except Exception as e:
                    print(f"Error processing row {i+2}: {row}. Error: {e}")
                    continue

        if status_messages:
            status_filename = os.path.join(output_dir, "focus_status_messages.txt")
            with open(status_filename, 'w', encoding='utf-8') as status_file:
                status_file.write("\n\n".join(status_messages))
            print(f"\nGenerated status messages: {status_filename}")
        
        if processed_count > 0:
            print(f"\nFlow Anchor successfully generated {processed_count} focus block items.")
        else:
            print("No valid focus blocks were processed. Please check your input CSV data.")

    except Exception as e:
        print(f"An unexpected error occurred while reading the CSV: {e}")

def create_demo_csv(filepath: str):
    """Creates a sample CSV file for demonstration."""
    demo_content = """Date,Start Time,End Time,Project/Task,Custom Message
2026-05-22,09:00,11:00,Project Andromeda,Deep diving into {project}! Please hold all non-urgent queries until after {end}.
2026-05-22,14:00,16:30,Budget Analysis,Crunching numbers for {project} from {start} to {end}. Back shortly!
2026-05-23,10:00,12:00,Client Strategy,Strategizing for {project} today.
2026-05-24,13:00,15:00,Documentation Update,Updating project docs.
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(demo_content)
    print(f"Created demo CSV: {filepath}")

def main():
    parser = argparse.ArgumentParser(
        description="Flow Anchor: Generate ICS calendar files and status messages for deep work blocks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help=textwrap.dedent("""\
        Path to the input CSV file containing your focus blocks.
        The CSV should have the following columns:
        'Date' (YYYY-MM-DD), 'Start Time' (HH:MM), 'End Time' (HH:MM),
        'Project/Task', and optionally 'Custom Message'.
        
        Example 'Custom Message': "Deep diving into {project}! Back after {end}."
        Variables {project}, {start}, {end} will be replaced.
        """)
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="flow_anchor_output",
        help="Directory to save the generated ICS files and status messages. Defaults to 'flow_anchor_output'."
    )
    parser.add_argument(
        "--timezone",
        type=str,
        default="UTC", # Using UTC as a robust default for ICS events
        help=textwrap.dedent("""\
        IANA timezone string for generated ICS events (e.g., 'America/New_York', 'Europe/London').
        Defaults to 'UTC'. Ensure your system's clock is correctly set or
        adjust this if you need events in a specific local timezone.
        """)
    )

    args = parser.parse_args()
    process_focus_blocks(args.file, args.output_dir, args.timezone)

if __name__ == "__main__":
    demo_csv_path = "demo_focus_blocks.csv"
    create_demo_csv(demo_csv_path)
    print("\n--- Running Flow Anchor with demo data ---")
    # Simulate command-line arguments for testing
    import sys
    sys_argv_backup = sys.argv
    sys.argv = ["flow_anchor.py", "--file", demo_csv_path, "--output_dir", "demo_flow_anchor_output"]
    try:
        main()
    finally:
        sys.argv = sys_argv_backup # Restore original sys.argv
    print("\n--- Demo run complete. Check 'demo_flow_anchor_output' folder. ---")
    print("To run with your own data: python flow_anchor.py --file YOUR_FILE.csv")
    print("For help: python flow_anchor.py --help")