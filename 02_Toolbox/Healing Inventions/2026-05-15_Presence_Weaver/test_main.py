# test_main.py
import unittest
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
from io import StringIO
from unittest.mock import patch

# IMPORTANT: This test assumes the main tool code is saved in a file named `presence_weaver.py`
# in the same directory as this test file.

# Dynamically import the main module to test it
try:
    import presence_weaver
except ImportError:
    # If not found, create a dummy module for local testing/linting purposes
    print("Warning: presence_weaver.py not found. Mocking imports for local test environment.")
    class MockConsole:
        def print(self, *args, **kwargs): pass
        def input(self, *args, **kwargs): return ""
    presence_weaver = type('module', (object,), {
        'load_config': lambda x: {}, 
        'log_reflection': lambda *args: None, 
        'main': lambda *args: None,
        'console': MockConsole()
    })

class TestPresenceWeaver(unittest.TestCase):

    def setUp(self):
        # Create unique names for test files to avoid conflicts if multiple tests run
        self.test_config_path = f"test_config_{os.getpid()}.json"
        self.test_output_path = f"test_log_{os.getpid()}.csv"
        
        # Create a sample config file for tests
        self._create_sample_config(self.test_config_path)
        
        # Ensure output file is clean before each test
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)

        # Patch console input to provide automated responses for interactive prompts
        # First input for starting, second for completion/reflection.
        # It needs two "enters" for non-timed activities, and one "enter" then reflection for timed activities.
        self.mock_input_patcher = patch('presence_weaver.console.input', side_effect=['\n', 'This is a test reflection.'])
        self.mock_input = self.mock_input_patcher.start()
        
        # Patch time.sleep to make tests run instantly
        self.mock_sleep_patcher = patch('time.sleep', return_value=None)
        self.mock_sleep = self.mock_sleep_patcher.start()

        # Redirect rich console output to prevent clutter during tests
        self.console_capture = StringIO()
        self.patcher_console_print = patch('presence_weaver.console.print', new=lambda *args, **kwargs: self.console_capture.write(' '.join(map(str, args)) + '\n'))
        self.patcher_console_print.start()

    def tearDown(self):
        # Clean up test files
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)
        
        # Stop all patches
        self.mock_input_patcher.stop()
        self.mock_sleep_patcher.stop()
        self.patcher_console_print.stop()

    def _create_sample_config(self, filepath: str):
        sample_config_content = {
            "Test Social": "Quick check for updates.",
            "Test Work": "Respond to critical messages."
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(sample_config_content, f, indent=2)

    def test_load_config_success(self):
        config = presence_weaver.load_config(self.test_config_path)
        self.assertIn("Test Social", config)
        self.assertEqual(config["Test Work"], "Respond to critical messages.")

    def test_load_config_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            presence_weaver.load_config("non_existent_config.json")

    def test_log_reflection_success(self):
        activity = "Test Social"
        intention = "Quick check for updates."
        start_time = datetime.now() - timedelta(minutes=5)
        end_time = datetime.now()
        reflection_text = "Felt focused."

        presence_weaver.log_reflection(self.test_output_path, activity, intention, start_time, end_time, reflection_text)
        
        self.assertTrue(os.path.exists(self.test_output_path))
        df = pd.read_csv(self.test_output_path)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, 'activity'], activity)
        self.assertEqual(df.loc[0, 'reflection'], reflection_text)
        # Using assertAlmostEqual for duration due to potential floating point inaccuracies
        self.assertAlmostEqual(df.loc[0, 'duration_seconds'], 300.0, delta=1) # 5 minutes = 300 seconds

    def test_main_workflow_short_duration(self):
        test_args = [
            "--config", self.test_config_path, 
            "--activity", "Test Social", 
            "--duration", "1", # 1 minute duration, mocked to be instant
            "--output", self.test_output_path
        ]
        
        presence_weaver.main(test_args) 

        self.assertTrue(os.path.exists(self.test_output_path))
        df = pd.read_csv(self.test_output_path)
        self.assertGreaterEqual(len(df), 1)
        self.assertEqual(df.loc[0, 'activity'], "Test Social")
        self.assertIn("This is a test reflection", df.loc[0, 'reflection'])

    def test_main_workflow_no_duration(self):
        # Reset mock_input for this specific test case, as it needs different input sequence
        self.mock_input.stop() # Stop the existing patch
        # Input sequence: Enter to start activity, Enter to finish activity, then reflection
        self.mock_input_patcher = patch('presence_weaver.console.input', side_effect=['\n', '\n', 'This is another test reflection.'])
        self.mock_input = self.mock_input_patcher.start()

        test_args = [
            "--config", self.test_config_path, 
            "--activity", "Test Work", 
            "--output", self.test_output_path
        ]
        
        presence_weaver.main(test_args)

        self.assertTrue(os.path.exists(self.test_output_path))
        df = pd.read_csv(self.test_output_path)
        # Check if the last entry is for "Test Work" with the correct reflection
        self.assertIn("Test Work", df['activity'].tolist())
        self.assertIn("This is another test reflection", df['reflection'].tolist())
        self.assertGreaterEqual(len(df), 1) # Ensure at least one entry

    def test_main_invalid_activity(self):
        test_args = [
            "--config", self.test_config_path, 
            "--activity", "NonExistentActivity", 
            "--output", self.test_output_path
        ]
        
        presence_weaver.main(test_args)
        # Ensure no output file is created or existing one is not modified
        self.assertFalse(os.path.exists(self.test_output_path))
        # Check if error message was printed to console
        self.assertIn("Error: Activity 'NonExistentActivity' not found", self.console_capture.getvalue())

    def test_main_missing_config_file(self):
        test_args = [
            "--config", "missing_config.json", 
            "--activity", "Test Social", 
            "--output", self.test_output_path
        ]
        
        presence_weaver.main(test_args)
        self.assertFalse(os.path.exists(self.test_output_path))
        self.assertIn("Error: Configuration file not found", self.console_capture.getvalue())

# To run these tests:
# 1. Save the main tool code (from the CODE block above) into a file named `presence_weaver.py`
# 2. Save this test code into a file named `test_main.py` in the same directory.
# 3. Open your terminal in that directory and run: `python -m unittest test_main.py`