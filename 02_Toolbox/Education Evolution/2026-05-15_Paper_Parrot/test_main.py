import os
import pandas as pd
import unittest
from unittest.mock import patch, mock_open
from io import StringIO

# Assuming the functions extract_text_from_pdf, identify_key_points,
# and save_insights_to_csv are in a file named `paper_parrot_tool.py`
# For this test, we'll import them directly as they are in the same output block.

# Import the actual functions to be tested
from __main__ import extract_text_from_pdf, identify_key_points, save_insights_to_csv, main

class TestPaperParrot(unittest.TestCase):

    def setUp(self):
        self.dummy_pdf_path = "test_dummy_paper.pdf"
        self.output_csv_path = "test_paper_parrot_insights.csv"
        self.demo_pdf_content = """
        A Groundbreaking Study on Memory Retention
        
        Abstract
        This paper proposes a novel framework for enhancing long-term memory in adults. Our methodology involved a longitudinal study design with a cohort of 100 participants. We utilized fMRI scans and daily cognitive tasks to measure brain activity and recall rates. The study revealed significant improvements in recall for the experimental group. Data indicate that active recall techniques are superior. We found a strong correlation between engagement and retention.

        Introduction
        Memory decline is a critical challenge. We argue that existing interventions are often passive. This research aims to demonstrate the effectiveness of active learning strategies.

        Methodology
        Our approach employed a personalized adaptive learning system. Participants were divided into two groups: passive review and active recall. The experimental design involved a 12-week intervention period. We utilized a custom-developed mobile application for delivering daily tasks.

        Results
        Our results showed a 20% increase in information retention for the active recall group. We observed that fMRI scans displayed increased hippocampal activity. The data indicate that the novel framework is highly effective.

        Conclusion
        This study demonstrates the significant impact of active recall on memory. We suggest further research should explore the neurobiological underpinnings.
        """
        
        # Create a dummy PDF file for testing
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        try:
            c = canvas.Canvas(self.dummy_pdf_path, pagesize=letter)
            textobject = c.beginText()
            textobject.setTextOrigin(50, 750)
            textobject.setFont("Helvetica", 12)
            for line in self.demo_pdf_content.split('\n'):
                textobject.textLine(line)
            c.drawText(textobject)
            c.save()
        except ImportError:
            # Handle case where reportlab isn't installed in test environment
            with open(self.dummy_pdf_path, 'w') as f:
                f.write(self.demo_pdf_content) # Write as plain text for basic text extraction test
        except Exception as e:
            print(f"Warning: Could not create actual PDF for testing: {e}. Proceeding with plain text file.")
            with open(self.dummy_pdf_path, 'w') as f:
                f.write(self.demo_pdf_content)


    def tearDown(self):
        if os.path.exists(self.dummy_pdf_path):
            os.remove(self.dummy_pdf_path)
        if os.path.exists(self.output_csv_path):
            os.remove(self.output_csv_path)

    def test_extract_text_from_pdf_success(self):
        # This test relies on the dummy_pdf_path being a readable PDF or text file.
        text = extract_text_from_pdf(self.dummy_pdf_path)
        self.assertIn("memory retention", text.lower())
        self.assertIn("fMRI scans", text)
        self.assertGreater(len(text), 100)

    def test_extract_text_from_pdf_not_found(self):
        non_existent_path = "non_existent.pdf"
        text = extract_text_from_pdf(non_existent_path)
        self.assertEqual(text, "")

    def test_identify_key_points(self):
        text = self.demo_pdf_content
        insights = identify_key_points(text)
        self.assertGreater(len(insights), 0)

        # Check for specific types and content
        argument_found = any(i['Type'] == 'Argument' for i in insights)
        methodology_found = any(i['Type'] == 'Methodology' for i in insights)
        finding_found = any(i['Type'] == 'Finding' for i in insights)

        self.assertTrue(argument_found, "Should find at least one argument")
        self.assertTrue(methodology_found, "Should find at least one methodology")
        self.assertTrue(finding_found, "Should find at least one finding")

        # Check a specific question/prompt structure
        found_question = any("What is the main argument or proposal of this section?" in i['Question'] for i in insights)
        self.assertTrue(found_question)
        
        found_answer_prompt = any("Summarize the argument presented:" in i['Answer Prompt'] for i in insights)
        self.assertTrue(found_answer_prompt)


    def test_save_insights_to_csv(self):
        insights_data = [
            {"Type": "Argument", "Question": "Q1", "Answer Prompt": "A1", "Original Snippet": "S1", "Source Paragraph": 1},
            {"Type": "Methodology", "Question": "Q2", "Answer Prompt": "A2", "Original Snippet": "S2", "Source Paragraph": 2},
        ]
        save_insights_to_csv(insights_data, self.output_csv_path)
        self.assertTrue(os.path.exists(self.output_csv_path))

        df = pd.read_csv(self.output_csv_path)
        self.assertEqual(len(df), 2)
        self.assertIn("Question", df.columns)
        self.assertEqual(df["Type"].iloc[0], "Argument")

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_functionality(self, mock_stdout):
        # Ensure main runs without errors and creates the output file
        main(args=["--input_pdf", self.dummy_pdf_path, "--output_csv", self.output_csv_path])
        self.assertTrue(os.path.exists(self.output_csv_path))
        
        # Check if expected output messages are printed
        output = mock_stdout.getvalue()
        self.assertIn("Flapping wings for Paper Parrot", output)
        self.assertIn("Insights successfully saved", output)
        self.assertIn("Paper Parrot finished its squawk!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_insights(self, mock_stdout):
        # Create a PDF with content that won't trigger any patterns
        sparse_pdf_path = "sparse_paper.pdf"
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        try:
            c = canvas.Canvas(sparse_pdf_path, pagesize=letter)
            textobject = c.beginText()
            textobject.setTextOrigin(50, 750)
            textobject.setFont("Helvetica", 12)
            textobject.textLine("This is a very simple document with no academic phrases.")
            textobject.textLine("It just has some random sentences.")
            c.drawText(textobject)
            c.save()
        except ImportError:
            with open(sparse_pdf_path, 'w') as f:
                f.write("This is a very simple document with no academic phrases.\nIt just has some random sentences.")
        
        main(args=["--input_pdf", sparse_pdf_path, "--output_csv", "no_insights.csv"])
        
        output = mock_stdout.getvalue()
        self.assertIn("couldn't find any prominent arguments", output)
        self.assertFalse(os.path.exists("no_insights.csv"))
        if os.path.exists(sparse_pdf_path):
            os.remove(sparse_pdf_path)


if __name__ == '__main__':
    unittest.main()