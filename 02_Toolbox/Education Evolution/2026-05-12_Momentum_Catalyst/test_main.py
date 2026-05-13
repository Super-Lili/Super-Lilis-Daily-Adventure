import unittest
import os
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
import time

# Assuming the tool's code is in a file named `momentum_catalyst.py`
# For the purpose of this test, we'll assume direct import is possible.
# In a real scenario, you might structure your project differently or
# import specific functions.
from momentum_catalyst import setup_cli_arguments, get_micro_tasks, run_micro_sprint, log_progress, main_workflow

class TestMomentumCatalyst(unittest.TestCase):

    def setUp(self):
        """Set up test environment: create a dummy log file path."""
        self.test_log_file = Path("test_momentum_log.csv")
        if self.test_log_file.exists():
            os.remove(self.test_log_file)
        self.console_mock = MagicMock()
        self.console_mock.print = print # Ensure rich-like output is visible for debugging
        self.console_mock.input = input

    def tearDown(self):
        """Clean up test environment."""
        if self.test_log_file.exists():
            os.remove(self.test_log_file)
        # Clean up any demo files created during __main__ execution if they exist
        if Path("demo_momentum_log_1.csv").exists():
            os.remove("demo_momentum_log_1.csv")
        if Path("demo_momentum_log_no_rich.csv").exists():
            os.remove("demo_momentum_log_no_rich.csv")


    def test_setup_cli_arguments(self):
        """Test argument parsing."""
        test_args = ["--main_task", "Test Task", "--log_file", "test.csv", "--sprint_duration", "10", "--no_rich"]
        with patch("sys.argv", ["momentum_catalyst.py"] + test_args):
            args = setup_cli_arguments()
            self.assertEqual(args.main_task, "Test Task")
            self.assertEqual(args.log_file, "test.csv")
            self.assertEqual(args.sprint_duration, 10)
            self.assertTrue(args.no_rich)

    @patch('builtins.input', side_effect=['task1', 'task2', ''])
    def test_get_micro_tasks(self, mock_input):
        """Test interactive micro-task input."""
        tasks = get_micro_tasks(self.console_mock)
        self.assertEqual(tasks, ['task1', 'task2'])
        mock_input.assert_any_call("   Micro-task 1: ")
        mock_input.assert_any_call("   Micro-task 2: ")
        mock_input.assert_any_call("   Micro-task 3: ")

    @patch('builtins.input', side_effect=['y'])
    @patch('time.sleep', return_value=None) # Speed up tests
    @patch('momentum_catalyst.Progress', return_value=None) # Disable rich progress bar for testing
    def test_run_micro_sprint_completed(self, mock_progress, mock_sleep, mock_input):
        """Test a completed micro-sprint."""
        result = run_micro_sprint("Test Sprint", 1, self.console_mock)
        self.assertTrue(result)
        mock_sleep.assert_called_with(60) # 1 minute = 60 seconds
        mock_input.assert_called_once()

    @patch('builtins.input', side_effect=['n'])
    @patch('time.sleep', return_value=None) # Speed up tests
    @patch('momentum_catalyst.Progress', return_value=None) # Disable rich progress bar for testing
    def test_run_micro_sprint_skipped(self, mock_progress, mock_sleep, mock_input):
        """Test a skipped micro-sprint."""
        result = run_micro_sprint("Test Sprint", 1, self.console_mock)
        self.assertFalse(result)
        mock_sleep.assert_called_with(60)
        mock_input.assert_called_once()

    def test_log_progress_new_file(self):
        """Test logging to a new file."""
        main_task = "Main Task A"
        micro_task = "Micro Task 1"
        log_progress(self.test_log_file, main_task, micro_task, True)

        self.assertTrue(self.test_log_file.exists())
        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["Timestamp", "Main Task", "Micro Task", "Completed"])
            row = next(reader)
            self.assertIn(main_task, row)
            self.assertIn(micro_task, row)
            self.assertIn("Yes", row)
            self.assertEqual(len(row), 4)

    def test_log_progress_append_file(self):
        """Test logging appends to an existing file."""
        # Log first entry
        log_progress(self.test_log_file, "Main Task B", "Micro Task X", True)

        # Log second entry
        log_progress(self.test_log_file, "Main Task B", "Micro Task Y", False)

        with open(self.test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) # Read header
            self.assertEqual(header, ["Timestamp", "Main Task", "Micro Task", "Completed"])
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertIn("Micro Task X", rows)
            self.assertIn("Yes", rows)
            self.assertIn("Micro Task Y", rows)
            self.assertIn("No", rows)

    @patch('momentum_catalyst.get_micro_tasks', return_value=['Task A.1', 'Task A.2'])
    @patch('momentum_catalyst.run_micro_sprint', side_effect=[True, False]) # Simulate one complete, one skipped
    @patch('momentum_catalyst.log_progress', return_value=None) # Mock logging to avoid actual file I/O here
    @patch('momentum_catalyst.Console') # Mock rich.Console
    def test_main_workflow(self, mock_console_class, mock_log_progress, mock_run_sprint, mock_get_tasks):
        """Test the main workflow orchestration."""
        mock_console_instance = MagicMock()
        mock_console_class.return_value = mock_console_instance
        mock_console_instance.input.side_effect = ['y', 'n'] # For interactive prompts if any in main_workflow

        class MockArgs:
            def __init__(self, main_task: str, log_file: str, sprint_duration: int, no_rich: bool):
                self.main_task = main_task
                self.log_file = log_file
                self.sprint_duration = sprint_duration
                self.no_rich = no_rich
        
        args = MockArgs(
            main_task="Test Project",
            log_file=str(self.test_log_file),
            sprint_duration=1,
            no_rich=False
        )
        
        main_workflow(args)

        mock_get_tasks.assert_called_once()
        self.assertEqual(mock_run_sprint.call_count, 2)
        
        # Check that log_progress was called correctly for each task
        mock_log_progress.assert_any_call(Path(args.log_file), args.main_task, 'Task A.1', True)
        mock_log_progress.assert_any_call(Path(args.log_file), args.main_task, 'Task A.2', False)
        self.assertEqual(mock_log_progress.call_count, 2)

        # Verify console output calls
        mock_console_instance.print.assert_any_call(unittest.mock.ANY) # Check for general print calls

if __name__ == '__main__':
    unittest.main()