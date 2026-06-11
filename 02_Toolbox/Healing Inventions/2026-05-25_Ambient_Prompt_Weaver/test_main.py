import os
import pandas as pd
import shutil
from main import main, create_demo_csv, process_tasks

# Define paths for testing
TEST_INPUT_CSV = "test_tasks_input.csv"
TEST_OUTPUT_DIR = "test_ambient_cues_output"

def setup_test_environment():
    """Ensures a clean slate for each test."""
    if os.path.exists(TEST_INPUT_CSV):
        os.remove(TEST_INPUT_CSV)
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

def teardown_test_environment():
    """Cleans up files and directories created during tests."""
    if os.path.exists(TEST_INPUT_CSV):
        os.remove(TEST_INPUT_CSV)
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)

def test_create_demo_csv():
    """Test if create_demo_csv generates a valid CSV."""
    setup_test_environment()
    create_demo_csv(TEST_INPUT_CSV)
    assert os.path.exists(TEST_INPUT_CSV), "Demo CSV file was not created."
    df = pd.read_csv(TEST_INPUT_CSV)
    assert not df.empty, "Demo CSV file is empty."
    assert 'task_name' in df.columns, "Demo CSV is missing 'task_name' column."
    assert 'time_block' in df.columns, "Demo CSV is missing 'time_block' column."
    teardown_test_environment()

def test_process_tasks_generates_files():
    """Test if process_tasks generates HTML files for defined time blocks."""
    setup_test_environment()
    create_demo_csv(TEST_INPUT_CSV) # Create a valid input
    
    # Run the processing logic directly for testing
    process_tasks(TEST_INPUT_CSV, TEST_OUTPUT_DIR)

    expected_time_blocks = ['morning', 'afternoon', 'evening']
    for block in expected_time_blocks:
        filename = os.path.join(TEST_OUTPUT_DIR, f"ambient_cue_{block}.html")
        assert os.path.exists(filename), f"HTML file for '{block}' was not created."
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert f"Ambient Cue - {block.capitalize()}" in content, f"HTML title missing for {block}."
            assert "<h1>Your Gentle Nudge:</h1>" in content, f"HTML content missing for {block}."
    teardown_test_environment()

def test_process_tasks_empty_input_file():
    """Test handling of an empty input CSV file."""
    setup_test_environment()
    # Create an empty CSV file
    pd.DataFrame(columns=['task_name', 'time_block']).to_csv(TEST_INPUT_CSV, index=False)
    
    process_tasks(TEST_INPUT_CSV, TEST_OUTPUT_DIR)
    assert not os.listdir(TEST_OUTPUT_DIR), "No files should be generated for an empty CSV."
    teardown_test_environment()

def test_process_tasks_missing_columns():
    """Test handling of an input CSV with missing required columns."""
    setup_test_environment()
    # Create a CSV with missing columns
    pd.DataFrame({'wrong_col': ['task1'], 'another_wrong_col': ['morning']}).to_csv(TEST_INPUT_CSV, index=False)
    
    process_tasks(TEST_INPUT_CSV, TEST_OUTPUT_DIR)
    assert not os.listdir(TEST_OUTPUT_DIR), "No files should be generated for CSV with missing columns."
    teardown_test_environment()

def test_main_with_args():
    """Test main function with argparse arguments."""
    setup_test_environment()
    create_demo_csv(TEST_INPUT_CSV)
    
    # Simulate command-line arguments
    main_args = ["--input_file", TEST_INPUT_CSV, "--output_dir", TEST_OUTPUT_DIR]
    main(main_args)

    expected_time_blocks = ['morning', 'afternoon', 'evening']
    for block in expected_time_blocks:
        filename = os.path.join(TEST_OUTPUT_DIR, f"ambient_cue_{block}.html")
        assert os.path.exists(filename), f"HTML file for '{block}' was not created by main with args."
    teardown_test_environment()

# Run all tests
print("Running tests for Ambient Prompt Weaver...")
test_create_demo_csv()
test_process_tasks_generates_files()
test_process_tasks_empty_input_file()
test_process_tasks_missing_columns()
test_main_with_args()
print("All Ambient Prompt Weaver tests passed!")