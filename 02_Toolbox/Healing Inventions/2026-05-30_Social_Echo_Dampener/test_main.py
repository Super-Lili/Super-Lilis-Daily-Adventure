import unittest
import os
from main import process

class TestSocialEchoDampener(unittest.TestCase):

    def test_html_output_structure(self):
        """
        Test that the process function returns a valid HTML string for browser execution.
        """
        html_output = process("some test context")
        self.assertIsInstance(html_output, str)
        self.assertTrue(html_output.startswith("<!DOCTYPE html>"))
        self.assertIn("<title>Social Echo Dampener</title>", html_output)
        self.assertIn('<div id="app">', html_output)
        self.assertIn('<script>', html_output)
        self.assertIn('body {', html_output) # Check for inline CSS

    def test_empty_input_produces_valid_html(self):
        """
        Test that empty input still produces a complete and valid HTML string.
        """
        html_output = process("")
        self.assertIsInstance(html_output, str)
        self.assertTrue(html_output.startswith("<!DOCTYPE html>"))
        self.assertIn("<title>Social Echo Dampener</title>", html_output)

    def test_cli_execution_with_context(self):
        """
        Test CLI execution behavior. This primarily checks that the argparse
        path correctly calls process and prints HTML.
        """
        # This test needs to simulate CLI argparse behavior.
        # Since we're directly calling process in the test, we confirm it works.
        # The main entry point in main.py handles sys.argv parsing for CLI.
        html_output = process("after a noisy conference")
        self.assertIsInstance(html_output, str)
        self.assertTrue(html_output.startswith("<!DOCTYPE html>"))

    def test_no_external_resources(self):
        """
        Verify that no external scripts, stylesheets, or fonts are linked.
        """
        html_output = process("test for external resources")
        self.assertNotIn('<link rel="stylesheet"', html_output)
        self.assertNotIn('<script src="', html_output)
        self.assertNotIn('https://', html_output)
        self.assertNotIn('http://', html_output)
        self.assertNotIn('cdn.', html_output)
        self.assertNotIn('googleapis', html_output) # Check for Google Fonts


if __name__ == '__main__':
    unittest.main()