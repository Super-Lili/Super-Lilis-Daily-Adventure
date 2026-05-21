import os
import shutil
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch, mock_open

# Assume the main tool logic is in a file named 'flow_anchor.py'
# For testing purposes, we'll import functions directly.
# In a real setup, you might import like: from flow_anchor import create_demo_csv, process_focus_blocks, main
# For this example, I'll copy the relevant functions or assume they are in the same file as test_main.py
# For this template, I will place the actual functions to test here to be self-contained.

# === Start of relevant functions from flow_anchor.py for testing ===
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
    ics_timezone: str = "America/New_York"
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

                    focus_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    start_dt_obj = datetime.strptime(start_time_str, "%H:%M").time()
                    end_dt_obj = datetime.strptime(end_time_str, "%H:%M").time()

                    start_combined = datetime.combine(focus_date, start_dt_obj)
                    end_combined = datetime.combine(focus_date, end_dt_obj)

                    if end_combined <= start_combined:
                        print(f"Warning: Skipping row {i+2} as end time is not after start time: {row}")
                        continue

                    ics_summary = f"Deep Work: {project_name}"
                    ics_description = f"Dedicated focus time for {project_name}. Please minimize interruptions."
                    uid = f"flowanchor-{focus_date.isoformat()}-{project_name.replace(' ', '-')}-{i+1}@example.com"
                    ics_content = generate_ics_event(start_combined, end_combined, ics_summary, ics_description, uid)
                    
                    ics_filename = os.path.join(output_dir, f"{focus_date.isoformat()}-{project_name.replace(' ', '_')}.ics")
                    with open(ics_filename, 'w', encoding='utf-8') as ics_file:
                        ics_file.write(ics_content)
                    # print(f"Generated ICS: {ics_filename}") # Suppress print during tests

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
            # print(f"\nGenerated status messages: {status_filename}") # Suppress print during tests
        
        if processed_count > 0:
            # print(f"\nFlow Anchor successfully generated {processed_count} focus block items.") # Suppress print
            pass
        else:
            print("No valid focus blocks were processed. Please check your input CSV data.")

    except Exception as e:
        print(f"An unexpected error occurred while reading the CSV: {e}")

# === End of relevant functions from flow_anchor.py for testing ===


class TestFlowAnchor(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output_flow_anchor"
        self.input_csv = os.path.join(self.test_dir, "test_focus_blocks.csv")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_csv(self, content: str, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_basic_processing(self):
        csv_content = """Date,Start Time,End Time,Project/Task,Custom Message
2026-05-22,09:00,11:00,Project X,Custom message for {project} from {start} to {end}!
2026-05-23,14:00,16:30,Report Y,
"""
        self._create_csv(csv_content, self.input_csv)
        process_focus_blocks(self.input_csv, self.test_dir)

        # Check if output directory and files are created
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "2026-05-22-Project_X.ics")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "2026-05-23-Report_Y.ics")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "focus_status_messages.txt")))

        # Check content of status message file
        with open(os.path.join(self.test_dir, "focus_status_messages.txt"), 'r', encoding='utf-8') as f:
            status_content = f.read()
            self.assertIn("Custom message for Project X from 09:00 to 11:00!", status_content)
            self.assertIn("Heads up! I'm in deep focus on 'Report Y' from 14:00 to 16:30 today.", status_content)
        
        # Check content of an ICS file
        with open(os.path.join(self.test_dir, "2026-05-22-Project_X.ics"), 'r', encoding='utf-8') as f:
            ics_content = f.read()
            self.assertIn("SUMMARY:Deep Work: Project X", ics_content)
            self.assertIn("DTSTART:20260522T090000", ics_content)
            self.assertIn("DTEND:20260522T110000", ics_content)

    def test_csv_missing_headers(self):
        csv_content = "Date,Start Time,Project/Task\n2026-05-22,09:00,Project Z"
        self._create_csv(csv_content, self.input_csv)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            process_focus_blocks(self.input_csv, self.test_dir)
            self.assertIn("Error: CSV is missing required headers.", mock_stdout.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2026-05-22-Project_Z.ics")))

    def test_invalid_time_format(self):
        csv_content = """Date,Start Time,End Time,Project/Task
2026-05-22,9:00,11:00,Project Invalid Time
"""
        self._create_csv(csv_content, self.input_csv)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            process_focus_blocks(self.input_csv, self.test_dir)
            self.assertIn("Warning: Skipping row 2 due to invalid time format", mock_stdout.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2026-05-22-Project_Invalid_Time.ics")))

    def test_end_time_before_start_time(self):
        csv_content = """Date,Start Time,End Time,Project/Task
2026-05-22,11:00,09:00,Project Reversed Time
"""
        self._create_csv(csv_content, self.input_csv)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            process_focus_blocks(self.input_csv, self.test_dir)
            self.assertIn("Warning: Skipping row 2 as end time is not after start time", mock_stdout.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "2026-05-22-Project_Reversed_Time.ics")))

    def test_empty_csv(self):
        csv_content = "Date,Start Time,End Time,Project/Task,Custom Message\n"
        self._create_csv(csv_content, self.input_csv)
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            process_focus_blocks(self.input_csv, self.test_dir)
            self.assertIn("No valid focus blocks were processed.", mock_stdout.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "focus_status_messages.txt")))

    def test_input_file_not_found(self):
        non_existent_file = os.path.join(self.test_dir, "non_existent.csv")
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            process_focus_blocks(non_existent_file, self.test_dir)
            self.assertIn("Error: Input CSV file not found at", mock_stdout.getvalue())
        self.assertFalse(os.path.exists(self.test_dir)) # Output dir should not be created if input fails early

    def test_timezone_parameter(self):
        # This test primarily checks if the timezone parameter is accepted,
        # not its functional impact without a full ics library for verification.
        csv_content = """Date,Start Time,End Time,Project/Task
2026-05-22,09:00,10:00,Timezone Test
"""
        self._create_csv(csv_content, self.input_csv)
        process_focus_blocks(self.input_csv, self.test_dir, ics_timezone="Europe/London")
        # Assert that files are still created successfully, implying parameter was processed without error
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "2026-05-22-Timezone_Test.ics")))

# To capture stdout for testing print statements
from io import StringIO
import sys

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)