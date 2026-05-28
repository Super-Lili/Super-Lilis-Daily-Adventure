import unittest
import os
import re
from EchoBloom import process, generate_ambient_properties, create_svg_pattern, _cli_main, _write_output_files

class TestEchoBloom(unittest.TestCase):

    def setUp(self):
        # Clean up any previously created files from tests
        for f in os.listdir('.'):
            if f.startswith('test_rhythm_') and (f.endswith('.txt') or f.endswith('.svg')):
                os.remove(os.path.join('.', f))

    def tearDown(self):
        # Clean up files created during this test run
        for f in os.listdir('.'):
            if f.startswith('test_rhythm_') and (f.endswith('.txt') or f.endswith('.svg')):
                os.remove(os.path.join('.', f))

    def test_process_valid_input(self):
        mood_input = "I'm feeling like a soft, gentle rain today, very low energy but present. I need peace and quiet."
        output = process(mood_input)

        self.assertIsInstance(output, str)
        self.assertIn("Today's Ambient Echo:", output)
        self.assertIn("Suggested Mood Color (HEX):", output)
        self.assertIn("--- SVG Pattern ---", output)
        self.assertIn("</svg>", output)
        
        # Check if the output contains a valid HEX color code
        self.assertIsNotNone(re.search(r'#[0-9A-Fa-f]{6}', output))

    def test_process_short_input(self):
        mood_input = "tired"
        output = process(mood_input)
        self.assertIn("Please tell me a little more", output)

        mood_input_empty = ""
        output_empty = process(mood_input_empty)
        self.assertIn("Please tell me a little more", output_empty)

    def test_generate_ambient_properties_keywords(self):
        descriptor, color, pattern = generate_ambient_properties("feeling gentle and quiet")
        self.assertIn("gentle", descriptor.lower() + " " + color.lower() + " " + pattern.lower())
        self.assertIn("quiet", descriptor.lower() + " " + color.lower() + " " + pattern.lower())
        self.assertTrue(re.match(r'#[0-9A-Fa-f]{6}', color))
        self.assertIn(pattern, ["circles", "waves", "dots", "stripes"])

    def test_generate_ambient_properties_no_keywords(self):
        descriptor, color, pattern = generate_ambient_properties("just a normal day")
        self.assertIsInstance(descriptor, str)
        self.assertTrue(re.match(r'#[0-9A-Fa-f]{6}', color))
        self.assertIn(pattern, ["circles", "waves", "dots", "stripes"])
        self.assertNotIn("normal", descriptor.lower()) # Should use generic gentle phrases

    def test_create_svg_pattern(self):
        svg_content = create_svg_pattern("circles", "#abcdef")
        self.assertIn("<svg", svg_content)
        self.assertIn("background-color: #abcdef;", svg_content)
        self.assertIn("<circle", svg_content)
        self.assertIn("pattern-grid", svg_content)
        self.assertIn("</svg>", svg_content)

        svg_content_waves = create_svg_pattern("waves", "#123456")
        self.assertIn("<path", svg_content_waves)

    def test_cli_main_output_files(self):
        # Simulate CLI arguments
        import sys
        sys.argv = ['EchoBloom.py', '--mood', 'a very calm and peaceful day', '--output_prefix', 'test_rhythm']

        _cli_main()

        # Check if files were created
        txt_file_found = False
        svg_file_found = False
        generated_files = []

        for f in os.listdir('.'):
            if f.startswith('test_rhythm_') and f.endswith('.txt'):
                txt_file_found = True
                generated_files.append(f)
                with open(f, 'r') as f_read:
                    content = f_read.read()
                    self.assertIn("Today's Ambient Echo:", content)
                    self.assertIn("Suggested Mood Color (HEX):", content)
            elif f.startswith('test_rhythm_') and f.endswith('.svg'):
                svg_file_found = True
                generated_files.append(f)
                with open(f, 'r') as f_read:
                    content = f_read.read()
                    self.assertIn("<svg", content)
                    self.assertIn("</svg>", content)
        
        self.assertTrue(txt_file_found, "Text file was not created by _cli_main.")
        self.assertTrue(svg_file_found, "SVG file was not created by _cli_main.")

        # Clean up files created in this specific test
        for f in generated_files:
            os.remove(f)

if __name__ == '__main__':
    unittest.main()