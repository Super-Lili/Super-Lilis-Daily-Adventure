import os
import shutil
import unittest
from main import process # Assuming the tool is saved as brief_aligner_blueprint.py

class TestBriefAlignerBlueprint(unittest.TestCase):

    def setUp(self):
        # Create a clean directory for test outputs
        self.test_dir = "test_output"
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_prefix = os.path.join(self.test_dir, "test_brief")
        self.brief_filepath = f"{self.test_prefix}.txt"
        self.chart_filepath = f"{self.test_prefix}_summary.png"

    def tearDown(self):
        # Clean up test outputs
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_sample_input_file(self, content: str, filename="sample_input.txt"):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_empty_input(self):
        result = process("")
        self.assertIn("no communication text to process", result)

    def test_basic_extraction_and_output(self):
        sample_text = """
        Subject: Project Neptune Update
        Hi team,
        Confirmed: We are proceeding with the blue design variant. Decision was made on Tuesday.
        Action: Lili to prepare initial mockups by Friday, June 7th.
        Scope: Focus strictly on the landing page and contact form. Exclude the blog section for now.
        Budget: Approved at $5,000.
        Next Call: Monday, June 10th.
        """
        input_filepath = self._create_sample_input_file(sample_text)
        result_message = process(sample_text, self.test_prefix)

        self.assertIn("Your Client Alignment Brief is ready", result_message)
        self.assertTrue(os.path.exists(self.brief_filepath))
        self.assertTrue(os.path.exists(self.chart_filepath))

        with open(self.brief_filepath, "r", encoding="utf-8") as f:
            brief_content = f.read()

        self.assertIn("Confirmed Decisions:", brief_content)
        self.assertIn("- Approved at $5,000", brief_content)
        self.assertIn("- We are proceeding with the blue design variant", brief_content)
        self.assertIn("Project Scope & Audience:", brief_content)
        self.assertIn("- Exclude the blog section for now", brief_content)
        self.assertIn("Key Action Items & Next Steps:", brief_content)
        self.assertIn("- Lili to prepare initial mockups by Friday, June 7th", brief_content)

    def test_complex_input_with_deduplication(self):
        sample_text = """
        Email 1: We agreed on a budget of $15k. Also, target audience is Gen Z.
        Slack: Just to confirm, $15,000 is the budget. And yes, Gen Z focus confirmed.
        Notes: Deliverable count: 10 social posts.
        """
        result_message = process(sample_text, self.test_prefix)
        self.assertIn("Your Client Alignment Brief is ready", result_message)
        self.assertTrue(os.path.exists(self.brief_filepath))

        with open(self.brief_filepath, "r", encoding="utf-8") as f:
            brief_content = f.read()

        # Check for deduplication
        self.assertEqual(brief_content.count("Budget of $15k"), 1)
        self.assertEqual(brief_content.count("Target audience is gen z"), 1)
        self.assertIn("- 10 social posts", brief_content)

if __name__ == '__main__':
    unittest.main()