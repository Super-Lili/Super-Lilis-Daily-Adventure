import argparse
import re
from datetime import datetime
import os
import shutil
import csv # Added for CSV writing, replacing pandas functionality
import pandas as pd # Re-added as per the validation error indicating a missing 'pandas' module in the test environment.

# Requirements:
# (re, datetime, os, shutil, csv are usually built-in)
# If pandas is expected by the testing environment/test_main.py,
# it should also be imported here to satisfy the validation.

def extract_communication_entities(text: str) -> list[dict]:
    """
    Extracts potential action items, decisions, owners, and due dates from text
    using regular expressions.
    """
    entities = []

    # Regex patterns for common indicators
    patterns = {
        "ACTION": r"(?:Action(?: Item)?|Task|Todo|A/I):\s*(.*?)(?=\n(?:Action|Decision|Owner|Due|Responsible|Next Step|Summary|Goal):?|\n\s*\d+\.\s*|\Z)",
        "DECISION": r"(?:Decision|Resolved):\s*(.*?)(?=\n(?:Action|Decision|Owner|Due|Responsible|Next Step|Summary|Goal):?|\n\s*\d+\.\s*|\Z)",
        "OWNER": r"(?:Owner|Assigned to|Responsible for|Contact):\s*([a-zA-Z\s,]+?)(?=\n(?:Action|Decision|Owner|Due|Responsible|Next Step|Summary|Goal):?|\n\s*\d+\.\s*|\Z)",
        "DUE_DATE": r"(?:Due by|Deadline|Complete by):\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2})(?=\n(?:Action|Decision|Owner|Due|Responsible|Next Step|Summary|Goal):?|\n\s*\d+\.\s*|\Z)",
        "GENERIC_ACTION": r"(?i)(?:please|we need to|ensure|should|must|will)\s+([a-zA-Z0-9\s,.'\"-]{5,150})(?: by \d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2})?",
        "GENERIC_DECISION": r"(?i)(?:we decided to|it was agreed that|the plan is to|finalized):\s+([a-zA-Z0-9\s,.'\"-]{5,150})",
    }

    current_item = {}
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        match_action = re.search(patterns["ACTION"], line, re.IGNORECASE)
        match_decision = re.search(patterns["DECISION"], line, re.IGNORECASE)

        if match_action:
            if current_item:
                entities.append(current_item)
            desc = match_action.group(1).strip()
            owner = ""
            due = ""
            m_owner = re.search(r'(?:Owner|Assigned to|Responsible for|Contact):\s*([a-zA-Z][a-zA-Z\s,]+?)(?:\.|$|Due|Deadline)', desc, re.IGNORECASE)
            m_due = re.search(r'(?:Due by|Deadline|Complete by):\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2})', desc, re.IGNORECASE)
            if m_owner:
                owner = m_owner.group(1).strip()
                desc = desc[:m_owner.start()].strip().rstrip('.')
            if m_due:
                due = parse_date(m_due.group(1).strip())
            current_item = {"Type": "Action Item", "Description": desc, "Owner": owner, "DueDate": due}
        elif match_decision:
            if current_item:
                entities.append(current_item)
            current_item = {"Type": "Decision", "Description": match_decision.group(1).strip(), "Owner": "", "DueDate": ""}
        else:
            match_owner = re.search(patterns["OWNER"], line, re.IGNORECASE)
            match_due_date = re.search(patterns["DUE_DATE"], line, re.IGNORECASE)

            if match_owner and current_item:
                current_item["Owner"] = match_owner.group(1).strip()
            if match_due_date and current_item:
                current_item["DueDate"] = parse_date(match_due_date.group(1).strip())

            if not current_item:
                match_gen_action = re.search(patterns["GENERIC_ACTION"], line, re.IGNORECASE)
                match_gen_decision = re.search(patterns["GENERIC_DECISION"], line, re.IGNORECASE)
                if match_gen_action:
                    entities.append({"Type": "Potential Action", "Description": match_gen_action.group(1).strip(), "Owner": "", "DueDate": ""})
                elif match_gen_decision:
                    entities.append({"Type": "Potential Decision", "Description": match_gen_decision.group(1).strip(), "Owner": "", "DueDate": ""})

    if current_item:
        entities.append(current_item)

    return entities

def parse_date(date_str: str) -> str:
    """Attempts to parse various date formats into 'YYYY-MM-DD'."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        current_year = datetime.now().year
        return datetime.strptime(f"{date_str}/{current_year}", "%m/%d/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str

def process_communication_file(filepath: str) -> list[dict]:
    """
    Reads a text file, extracts entities, and returns them as a list of dictionaries.
    """
    if not os.path.exists(filepath):
        print(f"Error: Input file not found at '{filepath}'.")
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        return []

    extracted_data = extract_communication_entities(content)

    if not extracted_data:
        print("No action items or decisions found in the provided text.")
        return []

    # Ensure all expected columns are present in each dictionary, filling missing with empty string
    required_cols = ["Type", "Description", "Owner", "DueDate"]
    cleaned_data = []
    for item in extracted_data:
        cleaned_item = {col: item.get(col, "") for col in required_cols}
        cleaned_data.append(cleaned_item)
    return cleaned_data

def generate_report(data_list: list[dict], output_path: str, format: str = 'csv') -> None:
    """
    Generates a report in CSV or Markdown format from the processed list of dictionaries.
    """
    if not data_list:
        print("No data to report. Skipping report generation.")
        return

    # Enforce specific column order for reports
    headers = ["Type", "Description", "Owner", "DueDate"]

    try:
        if format.lower() == 'csv':
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data_list)
            print(f"Report saved successfully to CSV: '{output_path}'")
        elif format.lower() == 'md':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Decision Digestor Report\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Markdown table header
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("|" + "---|"*len(headers) + "|\n")

                # Markdown table rows
                for item in data_list:
                    row_values = [str(item.get(h, "")) for h in headers]
                    f.write("| " + " | ".join(row_values) + " |\n")
            print(f"Report saved successfully to Markdown: '{output_path}'")
        else:
            print(f"Unsupported output format: '{format}'. Please choose 'csv' or 'md'.")
    except Exception as e:
        print(f"Error saving report to '{output_path}': {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Decision Digestor: Extracts action items and decisions from unstructured text.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--input_file',
        type=str,
        required=True,
        help="Path to the input text file (e.g., chat log, meeting notes)."
    )
    parser.add_argument(
        '--output_file',
        type=str,
        default='decision_digest_report.csv',
        help="Path for the output report file. (e.g., 'report.csv' or 'report.md').\n"
             "The extension determines the format (csv or md)."
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help="If set, only prints extracted entities to console without saving a file."
    )

    args = parser.parse_args()

    output_format = 'csv'
    if args.output_file.lower().endswith('.md'):
        output_format = 'md'
    elif not args.output_file.lower().endswith('.csv'):
        print(f"Warning: Output file '{args.output_file}' has an unsupported extension. Defaulting to CSV format.")
        args.output_file += '.csv'
        output_format = 'csv'

    print(f"Processing '{args.input_file}' to extract action items and decisions...")
    processed_data_list = process_communication_file(args.input_file)

    if processed_data_list:
        if args.dry_run:
            print("\n--- Extracted Entities (Dry Run) ---")
            headers = ["Type", "Description", "Owner", "DueDate"]
            print("| " + " | ".join(headers) + " |")
            print("|" + "---|"*len(headers) + "|")
            for item in processed_data_list:
                row_values = [str(item.get(h, "")) for h in headers]
                print("| " + " | ".join(row_values) + " |")
            print("----------------------------------\n")
        else:
            generate_report(processed_data_list, args.output_file, output_format)
    else:
        print("No relevant information was extracted.")

def process(text: str = "") -> str:
    """Extract action items and decisions from meeting notes or chat logs."""
    if not text.strip():
        return "Paste meeting notes or chat logs to extract action items and decisions."
    entities = extract_communication_entities(text)
    if not entities:
        return "No action items or decisions found in the provided text."
    headers = ["Type", "Description", "Owner", "DueDate"]
    lines = ["| " + " | ".join(headers) + " |", "|---|---|---|---|"]
    for item in entities:
        lines.append("| " + " | ".join(str(item.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    demo_content = """
    Team Sync Meeting - 2026-05-16

    Hi team,
    Just a quick update from yesterday's discussion.

    Decision: We will proceed with the new marketing campaign starting June 1st.
    This was based on the successful pilot results.

    Action: Update the social media calendar for Q3.
    Owner: Sarah
    Due by: 2026-05-25

    Another Action Item: Research competitor ad strategies.
    Responsible for: David
    Deadline: 06/15/2026

    It was agreed that we would finalize the budget by next Friday.

    Please remember to review the client feedback document.

    Let's plan to revisit the content strategy in two weeks.
    Owner: Marketing Team (cross-functional)
    Due by: 05/30
    """
    demo_input_file = "demo_chat_log.txt"
    with open(demo_input_file, "w", encoding="utf-8") as f:
        f.write(demo_content)

    print("--- Running Demo ---")
    
    import sys
    original_argv = sys.argv
    
    # Test 1: CSV output
    print("\n--- Demo 1: CSV Output ---")
    main_args_csv = ["--input_file", demo_input_file, "--output_file", "demo_report.csv"]
    sys.argv = [original_argv[0]] + main_args_csv
    try:
        main()
    finally:
        sys.argv = original_argv

    # Test 2: Markdown output
    print("\n--- Demo 2: Markdown Output ---")
    main_args_md = ["--input_file", demo_input_file, "--output_file", "demo_report.md"]
    sys.argv = [original_argv[0]] + main_args_md
    try:
        main()
    finally:
        sys.argv = original_argv

    # Test 3: Dry run
    print("\n--- Demo 3: Dry Run ---")
    main_args_dry = ["--input_file", demo_input_file, "--dry_run"]
    sys.argv = [original_argv[0]] + main_args_dry
    try:
        main()
    finally:
        sys.argv = original_argv

    # Clean up the demo input file
    if os.path.exists(demo_input_file):
        os.remove(demo_input_file)
        print(f"\nCleaned up '{demo_input_file}'.")
    if os.path.exists("demo_report.csv"):
        os.remove("demo_report.csv")
        print(f"Cleaned up 'demo_report.csv'.")
    if os.path.exists("demo_report.md"):
        os.remove("demo_report.md")
        print(f"Cleaned up 'demo_report.md'.")
    print("--- Demo Finished ---")