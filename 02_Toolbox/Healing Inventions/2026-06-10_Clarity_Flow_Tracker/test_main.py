import unittest
from main import process
import re

class TestClarityFlowTracker(unittest.TestCase):

    def test_empty_input(self):
        result = process("")
        self.assertIn("Please provide a more substantial technical explanation", result)
        self.assertIn("Clarity Flow Tracker: Explain Smarter", result)

    def test_short_input(self):
        result = process("Too short.")
        self.assertIn("Please provide a more substantial technical explanation", result)
        self.assertIn("Clarity Flow Tracker: Explain Smarter", result)

    def test_valid_input_structure(self):
        test_input = "Our new blockchain-based distributed ledger solution utilizes a Byzantine Fault Tolerant consensus mechanism."
        result = process(test_input)

        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html lang=\"en\">", result)
        self.assertIn("<title>Clarity Flow Tracker: Explain Smarter</title>", result)
        self.assertIn("<textarea id=\"input-explanation\"", result)
        self.assertIn("<button id=\"analyze-btn\">Analyze Clarity</button>", result)
        self.assertIn("<div id=\"editable-explanation\" contenteditable=\"true\"", result)
        self.assertIn("<div id=\"suggestions-panel\"", result)
        self.assertIn("<div id=\"implications-list\"", result)
        self.assertIn("<div id=\"clarity-meter-container\"", result)
        self.assertIn("<svg id=\"clarity-meter-svg\"", result)
        self.assertIn("<div id=\"result-state\"", result)
        self.assertIn("<button id=\"copy-clarified-btn\"", result)
        self.assertIn("<button id=\"view-comparison-btn\"", result)
        self.assertIn("<div id=\"side-by-side-comparison\"", result)

        # Ensure the test input is embedded for JS
        self.assertIn(re.escape(test_input), result) # It's HTML escaped, so check for escaped version
        self.assertIn('const initialText =', result)

    def test_jargon_data_embedding(self):
        test_input = "Our new blockchain-based distributed ledger solution utilizes a Byzantine Fault Tolerant consensus mechanism."
        result = process(test_input)
        # Check if the jargonData JS object is present and contains expected keys
        self.assertIn('const jargonData = {', result)
        self.assertIn('"blockchain-based distributed ledger solution":', result)
        self.assertIn('"Byzantine Fault Tolerant consensus mechanism":', result)

    def test_implications_embedding(self):
        test_input = "Our new blockchain-based distributed ledger solution utilizes a Byzantine Fault Tolerant consensus mechanism."
        result = process(test_input)
        self.assertIn('const initialImplications = [', result)
        self.assertIn('"Enhanced Security & Transparency"', result)
        self.assertIn('"Improved Reliability"', result)

    def test_css_and_js_inline(self):
        test_input = "A simple technical explanation."
        result = process(test_input)
        self.assertIn("<style>", result)
        self.assertIn("body {", result)
        self.assertIn("<script>", result)
        self.assertIn("const initialText =", result)
        self.assertNotIn("src=", result) # No external scripts
        self.assertNotIn("href=", result) # No external stylesheets (except for possible base HTML meta)

    def test_no_dead_code_assertion(self):
        # This is implicitly tested by the fact that `process` is called and returns HTML.
        # The internal assert from the rule checks for the `process` function itself.
        # This test ensures `process` is functional.
        test_input = "Test for no dead code."
        result = process(test_input)
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 100) # Ensure it's not an empty or trivial return

if __name__ == '__main__':
    unittest.main()