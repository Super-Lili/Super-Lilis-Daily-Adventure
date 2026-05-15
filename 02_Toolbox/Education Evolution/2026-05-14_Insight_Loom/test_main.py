import unittest
import sys
from io import StringIO
from unittest.mock import patch
from pathlib import Path
import json
import matplotlib.pyplot as plt
import os
import pandas as pd # Import pandas for DataFrame checks

# Assuming the main script is named 'insight_loom.py'
from insight_loom import main, create_concept_map_data, save_concept_map_data, draw_concept_graph

class TestInsightLoom(unittest.TestCase):

    def setUp(self):
        self.demo_file_path = Path("test_demo_notes.txt")
        self.output_json_path = Path("test_concept_map.json")
        self.output_png_path = Path("test_concept_map.png")

        # Ensure no old files are hanging around
        for path in [self.demo_file_path, self.output_json_path, self.output_png_path]:
            if path.exists():
                path.unlink()

        # Create a dummy input file for testing
        self.demo_content = """
        The attention economy is a system where human attention is treated as a commodity.
        Platforms like social media compete for user engagement, often employing
        algorithms designed to maximize time spent on the app. This constant demand for
        attention can lead to cognitive overload and diminish our capacity for deep work
        and sustained learning.
        """
        with open(self.demo_file_path, "w", encoding="utf-8") as f:
            f.write(self.demo_content)

        # Mock matplotlib.pyplot.savefig and close to prevent interactive windows and actual file writing during some tests
        self.patcher_savefig = patch.object(plt, 'savefig')
        self.mock_savefig = self.patcher_savefig.start()
        self.patcher_close = patch.object(plt, 'close')
        self.mock_close = self.patcher_close.start()

    def tearDown(self):
        # Clean up created files
        for path in [self.demo_file_path, self.output_json_path, self.output_png_path]:
            if path.exists():
                path.unlink()

        self.patcher_savefig.stop()
        self.patcher_close.stop()

    @patch('builtins.input', side_effect=[
        "Attention Economy", "System treating human attention as commodity.",
        "Cognitive Overload", "Mental state due to excessive information.",
        "Deep Work", "Focused attention without distraction.",
        "Joy of Learning", "Intrinsic motivation for knowledge acquisition.",
        "done", # Finish concepts
        "Attention Economy", "Cognitive Overload", "causes",
        "Cognitive Overload", "Deep Work", "hinders",
        "Attention Economy", "Joy of Learning", "can_diminish",
        "done" # Finish relationships
    ])
    def test_create_concept_map_data_and_save_files(self, mock_input):
        # Redirect stdout to capture print output
        captured_output = StringIO()
        sys.stdout = captured_output

        create_concept_map_data(self.demo_file_path, self.output_json_path, self.output_png_path)
        sys.stdout = sys.__stdout__ # Restore stdout

        # Assert output files were created
        self.assertTrue(self.output_json_path.exists())
        self.assertTrue(self.output_png_path.exists()) 

        # Verify content of JSON file
        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn("concepts", data)
        self.assertIn("relationships", data)
        self.assertEqual(len(data["concepts"]), 4)
        self.assertEqual(len(data["relationships"]), 3)

        self.assertIn("Attention Economy", data["concepts"])
        self.assertEqual(data["concepts"]["Attention Economy"], "System treating human attention as commodity.")

        # Check if savefig was called, indicating graph generation
        self.mock_savefig.assert_called_once_with(self.output_png_path, format="png", bbox_inches="tight")
        self.mock_close.assert_called_once() # Ensure matplotlib figure is closed

    @patch('builtins.input', side_effect=[
        "Concept A", "Definition A",
        "done", # Finish concepts
        "done" # Finish relationships (not enough concepts for relationships)
    ])
    def test_not_enough_concepts_for_relationships(self, mock_input):
        captured_output = StringIO()
        sys.stdout = captured_output

        create_concept_map_data(self.demo_file_path, self.output_json_path, self.output_png_path)
        sys.stdout = sys.__stdout__

        self.assertTrue(self.output_json_path.exists())
        self.assertFalse(self.output_png_path.exists()) # No graph if no relationships were added

        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(len(data["concepts"]), 1)
        self.assertEqual(len(data["relationships"]), 0)

        self.mock_savefig.assert_not_called() # No graph should have been saved
        self.assertIn("Not enough concepts to form relationships.", captured_output.getvalue())
        self.assertIn("No relationships defined, skipping graph visualization", captured_output.getvalue())


    @patch('builtins.input', side_effect=[
        "done", # No concepts at all
    ])
    def test_no_concepts_added(self, mock_input):
        captured_output = StringIO()
        sys.stdout = captured_output

        create_concept_map_data(self.demo_file_path, self.output_json_path, self.output_png_path)
        sys.stdout = sys.__stdout__
        
        self.assertFalse(self.output_json_path.exists()) # No JSON if no concepts
        self.assertFalse(self.output_png_path.exists())
        self.mock_savefig.assert_not_called()
        self.mock_close.assert_not_called()
        self.assertIn("No concepts added! We need some ideas to connect.", captured_output.getvalue())

    def test_missing_input_file(self):
        non_existent_file = Path("non_existent.txt")
        captured_output = StringIO()
        sys.stdout = captured_output

        create_concept_map_data(non_existent_file, self.output_json_path, self.output_png_path)
        sys.stdout = sys.__stdout__ 
        
        self.assertIn("Oops! The file 'non_existent.txt' doesn't exist.", captured_output.getvalue())
        self.assertFalse(self.output_json_path.exists())
        self.assertFalse(self.output_png_path.exists())
        self.mock_savefig.assert_not_called()
        self.mock_close.assert_not_called()

    @patch('builtins.input', side_effect=[
        "Attention Economy", "System treating human attention as commodity.",
        "Attention Economy", # Duplicate concept name
        "new concept", "a brand new idea",
        "done", # Finish concepts
        "new concept", "Attention Economy", "relates_to",
        "done"
    ])
    def test_duplicate_concept_handling(self, mock_input):
        captured_output = StringIO()
        sys.stdout = captured_output

        create_concept_map_data(self.demo_file_path, self.output_json_path, self.output_png_path)
        sys.stdout = sys.__stdout__

        self.assertIn("'Attention Economy' is already a concept. Let's try a new one or 'done'.", captured_output.getvalue())
        self.assertTrue(self.output_json_path.exists())
        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(len(data["concepts"]), 2) # Only two unique concepts should be saved
        self.assertIn("Attention Economy", data["concepts"])
        self.assertIn("new concept", data["concepts"])
        self.assertEqual(len(data["relationships"]), 1)

if __name__ == '__main__':
    # Save the current working directory, then change to the directory of the test file.
    current_dir = os.getcwd()
    os.chdir(Path(__file__).parent)

    try:
        unittest.main(argv=['first-arg-is-ignored'], exit=False)
    finally:
        # Restore the original working directory
        os.chdir(current_dir)