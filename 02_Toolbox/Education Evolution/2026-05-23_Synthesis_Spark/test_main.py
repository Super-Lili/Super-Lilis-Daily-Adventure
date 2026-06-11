import unittest
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from main import main, load_learning_material, extract_and_refine_concepts, define_relationships, generate_recall_questions, save_structured_knowledge, save_recall_questions

class TestSynthesisSpark(unittest.TestCase):

    def setUp(self):
        self.demo_content_1 = """
        This article introduces the core concept of 'Data Flow Diagrams'.
        A key concept is that DFDs illustrate how data moves through a system.
        They are not about process logic, but rather the information path.
        Another key concept is 'External Entities', which are sources or sinks of data.
        DFDs often relate to 'Process Modeling' in software engineering.
        """
        self.demo_content_2 = """
        Understanding 'System Analysis' requires grasping several tools.
        'Use Case Diagrams' are another important tool, showing user interactions.
        They enable 'Requirements Gathering' by focusing on user goals.
        Data Flow Diagrams are a component of wider system analysis.
        The goal of System Analysis is to build robust 'Information Systems'.
        """
        self.file1 = Path("test_learning_1.txt")
        self.file2 = Path("test_learning_2.txt")
        self.file1.write_text(self.demo_content_1)
        self.file2.write_text(self.demo_content_2)
        self.output_prefix = "test_synthesis"
        self.knowledge_output = Path(f"{self.output_prefix}_knowledge.md")
        self.questions_output = Path(f"{self.output_prefix}_questions.txt")

    def tearDown(self):
        self.file1.unlink(missing_ok=True)
        self.file2.unlink(missing_ok=True)
        self.knowledge_output.unlink(missing_ok=True)
        self.questions_output.unlink(missing_ok=True)

    def test_load_learning_material(self):
        combined_text = load_learning_material([self.file1, self.file2])
        self.assertIn("Data Flow Diagrams", combined_text)
        self.assertIn("System Analysis", combined_text)
        self.assertIn("Use Case Diagrams", combined_text)
        self.assertNotIn("NonExistentKeyword", combined_text)

        # Test with a non-existent file
        non_existent_file = Path("non_existent.txt")
        captured_output = StringIO()
        sys.stdout = captured_output
        text_with_missing = load_learning_material([self.file1, non_existent_file])
        sys.stdout = sys.__stdout__
        self.assertIn("Error: File not found", captured_output.getvalue())
        self.assertIn("Data Flow Diagrams", text_with_missing)

    @patch('builtins.input', side_effect=['Data Flow Diagrams', 'System Analysis', 'Use Case Diagrams', 'done'])
    def test_extract_and_refine_concepts(self, mock_input):
        concepts = extract_and_refine_concepts(self.demo_content_1 + self.demo_content_2)
        self.assertIn("Data Flow Diagrams", concepts)
        self.assertIn("System Analysis", concepts)
        self.assertIn("Use Case Diagrams", concepts)
        self.assertEqual(len(concepts), 3) # Based on side_effect

    @patch('builtins.input', side_effect=['enables', '', 'is a part of'])
    def test_define_relationships(self, mock_input):
        # Pairs in order: A-B (enables), A-C (skipped), B-C (is a part of)
        concepts = ["Concept A", "Concept B", "Concept C"]
        relationships = define_relationships(concepts, "Concept A enables Concept B. Concept B is a part of Concept C.")
        self.assertIn("Concept A", relationships)
        self.assertIn("Concept B", relationships["Concept A"])
        self.assertEqual(relationships["Concept A"]["Concept B"], "enables")
        self.assertIn("Concept B", relationships)
        self.assertIn("Concept C", relationships["Concept B"])
        self.assertEqual(relationships["Concept B"]["Concept C"], "is a part of")


    def test_generate_recall_questions(self):
        structured_knowledge = {
            "concepts": ["Data Flow Diagrams", "System Analysis"],
            "relationships": {
                "Data Flow Diagrams": {"System Analysis": "is a tool in"},
            }
        }
        questions = generate_recall_questions(structured_knowledge)
        self.assertGreater(len(questions), 0)
        self.assertIn("Explain 'Data Flow Diagrams' in your own words, assuming I know nothing about it.", questions)
        self.assertIn("How does 'Data Flow Diagrams' 'is a tool in' 'System Analysis'? Provide a specific example.", questions)

    def test_save_structured_knowledge(self):
        test_data = {
            "date": "2026-05-23",
            "concepts": ["Test Concept 1", "Test Concept 2"],
            "relationships": {"Test Concept 1": {"Test Concept 2": "relates to"}},
            "full_text_snippet": "This is a snippet of the test content."
        }
        save_structured_knowledge(test_data, self.knowledge_output)
        self.assertTrue(self.knowledge_output.exists())
        content = self.knowledge_output.read_text()
        self.assertIn("# Synthesis Spark: Your Knowledge Weave", content)
        self.assertIn("- Test Concept 1", content)
        self.assertIn("- **Test Concept 1** relates to **Test Concept 2**", content)

    def test_save_recall_questions(self):
        test_questions = ["What is the meaning of life?", "How does it all connect?"]
        save_recall_questions(test_questions, self.questions_output)
        self.assertTrue(self.questions_output.exists())
        content = self.questions_output.read_text()
        self.assertIn("# Synthesis Spark: Your Recall Questions", content)
        self.assertIn("1. What is the meaning of life?", content)

    @patch('builtins.input', side_effect=['DFD', 'System Analysis', 'done', 'is used for'])
    def test_main_execution(self, mock_input):
        # Mocking print to suppress output during test
        with patch('sys.stdout', new=StringIO()) as fake_out:
            main(["--files", str(self.file1), str(self.file2), "--output_prefix", self.output_prefix])
            
            self.assertTrue(self.knowledge_output.exists())
            self.assertTrue(self.questions_output.exists())
            
            knowledge_content = self.knowledge_output.read_text()
            self.assertIn("- DFD", knowledge_content)
            self.assertIn("- System Analysis", knowledge_content)
            # The 'is used for' relationship for DFD -> System Analysis from mock_input
            self.assertIn("**DFD** is used for **System Analysis**", knowledge_content) 
            
            questions_content = self.questions_output.read_text()
            self.assertIn("Explain 'DFD'", questions_content)
            self.assertIn("How does 'DFD' 'is used for' 'System Analysis'", questions_content)


if __name__ == '__main__':
    unittest.main()