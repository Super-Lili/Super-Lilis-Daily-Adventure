import os
import re
import pandas as pd
from datetime import datetime
import shutil

# Assuming the main tool is in a file named 'decision_digestor.py'
# We will import its functions directly for testing.
# To run this test: python test_main.py

# A minimal representation of the functions needed for testing, copied from the main script.
# In a real scenario, you'd import these from the tool's file.
# For self-containment, we'll re-define necessary parts here.

def extract_communication_entities(text: str) -> list[dict]:
    entities = []
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
            m_o = re.search(r'(?:Owner|Assigned to|Responsible for|Contact):\s*([A-Za-z][A-Za-z\s]+?)(?:\.|$|Due|Deadline)', desc, re.IGNORECASE)
            m_d = re.search(r'(?:Due by|Deadline|Complete by):\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}/\d{2})', desc, re.IGNORECASE)
            if m_o:
                owner = m_o.group(1).strip()
                desc = desc[:m_o.start()].strip().rstrip('.')
            if m_d:
                due = parse_date(m_d.group(1).strip())
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

def process_communication_file(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        return pd.DataFrame()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return pd.DataFrame()
    extracted_data = extract_communication_entities(content)
    if not extracted_data:
        return pd.DataFrame(columns=["Type", "Description", "Owner", "DueDate"])
    df = pd.DataFrame(extracted_data)
    for col in ["Type", "Description", "Owner", "DueDate"]:
        if col not in df.columns:
            df[col] = ""
    return df[["Type", "Description", "Owner", "DueDate"]]

def generate_report(dataframe: pd.DataFrame, output_path: str, format: str = 'csv') -> None:
    if dataframe.empty:
        return
    try:
        if format.lower() == 'csv':
            dataframe.to_csv(output_path, index=False, encoding='utf-8')
        elif format.lower() == 'md':
            markdown_content = dataframe.to_markdown(index=False)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Decision Digestor Report\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(markdown_content)
    except Exception:
        pass # Allow test to fail if file not created

# Test Cases
def test_decision_digestor():
    print("Running tests for Decision Digestor...")

    # Setup: Create a temporary directory for test files
    test_dir = "test_decision_digestor_data"
    os.makedirs(test_dir, exist_ok=True)

    # Test 1: Basic extraction and CSV output
    test_input_content_1 = """
    Meeting Notes - Project Alpha
    Decision: We will use the new cloud provider for stage 2.
    Action: Migrate existing data to the new provider. Owner: Jane Doe. Due by: 2026-06-30.
    Another Decision: The budget for Q3 is approved.
    Action Item: Draft the Q3 budget report. Responsible for: John Smith. Deadline: 07/15/2026.
    Please ensure all team members are informed.
    """
    input_file_1 = os.path.join(test_dir, "test_input_1.txt")
    output_csv_1 = os.path.join(test_dir, "test_output_1.csv")

    with open(input_file_1, "w", encoding="utf-8") as f:
        f.write(test_input_content_1)

    df1 = process_communication_file(input_file_1)
    generate_report(df1, output_csv_1, 'csv')

    assert not df1.empty, "Test 1 Failed: DataFrame should not be empty."
    assert os.path.exists(output_csv_1), "Test 1 Failed: CSV output file not created."
    
    read_df1 = pd.read_csv(output_csv_1)
    assert len(read_df1) == 4, "Test 1 Failed: Incorrect number of rows in CSV."
    assert "Decision" in read_df1["Type"].values, "Test 1 Failed: 'Decision' not found in Type column."
    assert "Action Item" in read_df1["Type"].values, "Test 1 Failed: 'Action Item' not found in Type column."
    assert "Jane Doe" in read_df1["Owner"].values, "Test 1 Failed: 'Jane Doe' not found in Owner column."
    assert "2026-06-30" in read_df1["DueDate"].values, "Test 1 Failed: '2026-06-30' not found in DueDate column."
    print("Test 1 Passed: Basic extraction and CSV output work correctly.")

    # Test 2: Markdown output
    test_input_content_2 = """
    Standup Update
    Action: Review code changes for sprint 3. Owner: Alex. Due by: 05/20.
    Decision: Proceed with client demo next week.
    """
    input_file_2 = os.path.join(test_dir, "test_input_2.txt")
    output_md_2 = os.path.join(test_dir, "test_output_2.md")

    with open(input_file_2, "w", encoding="utf-8") as f:
        f.write(test_input_content_2)
    
    df2 = process_communication_file(input_file_2)
    generate_report(df2, output_md_2, 'md')

    assert not df2.empty, "Test 2 Failed: DataFrame should not be empty."
    assert os.path.exists(output_md_2), "Test 2 Failed: Markdown output file not created."
    
    with open(output_md_2, 'r', encoding='utf-8') as f:
        md_content = f.read()
    assert "Decision Digestor Report" in md_content, "Test 2 Failed: Markdown title missing."
    assert "| Action Item | Review code changes for sprint 3. | Alex | 2026-05-20 |" in md_content, "Test 2 Failed: Markdown content incorrect."
    print("Test 2 Passed: Markdown output works correctly.")


    # Test 3: Empty input file
    input_file_3 = os.path.join(test_dir, "empty.txt")
    output_csv_3 = os.path.join(test_dir, "empty_output.csv")
    with open(input_file_3, "w", encoding="utf-8") as f:
        f.write("")
    
    df3 = process_communication_file(input_file_3)
    generate_report(df3, output_csv_3, 'csv') # Should not create file for empty df

    assert df3.empty, "Test 3 Failed: DataFrame should be empty for empty input."
    assert not os.path.exists(output_csv_3), "Test 3 Failed: CSV file should not be created for empty data."
    print("Test 3 Passed: Handles empty input file gracefully.")

    # Test 4: Missing input file
    input_file_4 = os.path.join(test_dir, "non_existent.txt")
    df4 = process_communication_file(input_file_4)
    assert df4.empty, "Test 4 Failed: DataFrame should be empty for missing input file."
    print("Test 4 Passed: Handles missing input file gracefully.")

    # Test 5: Generic actions/decisions without keywords
    test_input_content_5 = """
    Quick Chat
    It was agreed that the team would hold a daily standup.
    We need to finalize the client proposal by next Tuesday.
    Ensure all documentation is up to date by 05/28/2026.
    """
    input_file_5 = os.path.join(test_dir, "test_input_5.txt")
    output_csv_5 = os.path.join(test_dir, "test_output_5.csv")
    with open(input_file_5, "w", encoding="utf-8") as f:
        f.write(test_input_content_5)
    
    df5 = process_communication_file(input_file_5)
    generate_report(df5, output_csv_5, 'csv')

    assert not df5.empty, "Test 5 Failed: DataFrame should not be empty."
    assert len(df5) == 3, "Test 5 Failed: Incorrect number of generic items."
    assert "Potential Decision" in df5["Type"].values, "Test 5 Failed: 'Potential Decision' not found."
    assert "Potential Action" in df5["Type"].values, "Test 5 Failed: 'Potential Action' not found."
    assert "2026-05-28" in df5["DueDate"].values, "Test 5 Failed: Generic due date not extracted."
    print("Test 5 Passed: Extracts generic actions and decisions.")


    # Cleanup
    shutil.rmtree(test_dir)
    print("Cleaned up test directory.")
    print("All tests completed.")

if __name__ == "__main__":
    test_decision_digestor()