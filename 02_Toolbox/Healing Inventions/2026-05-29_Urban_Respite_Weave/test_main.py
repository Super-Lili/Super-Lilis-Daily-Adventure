import os
import json
from urban_respite_weave import process, _get_theme_config, _generate_gradient_colors

# Mock the random choices for consistent testing if needed, though for an ambient tool,
# variability is acceptable.
# For simplicity and directness, this test will focus on output structure and basic functionality.

def test_process_empty_input():
    """Test that process() works with empty input and produces valid HTML."""
    html_output = process("")
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<title>Urban Respite Weave</title>" in html_output
    assert "A quiet moment, woven just for you." in html_output
    assert '<canvas id="visualCanvas"' in html_output
    assert '<button id="toggleSoundButton">Start Sound</button>' in html_output
    assert '<button id="changeThemeButton">Change Theme</button>' in html_output

def test_process_with_theme_input():
    """Test that process() works with a specific theme input."""
    html_output = process("forest")
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<title>Urban Respite Weave</title>" in html_output
    assert "A quiet moment, woven just for you." in html_output # Message is static
    assert 'visual_colors": ["#A5D6A7", "#81C784", "#66BB6A", "#4CAF50", "#388E3C"]' in html_output
    assert 'sounds": [{"freq": 120, "gain": 0.08, "type": "sine", "label": "Soft Forest Hum"}' in html_output


def test_get_theme_config():
    """Test the theme configuration retrieval function."""
    config_forest = _get_theme_config("forest")
    assert isinstance(config_forest, dict)
    assert config_forest["visual_colors"][0] == "#A5D6A7"
    assert len(config_forest["sounds"]) == 2
    assert config_forest["sounds"][0]["label"] == "Soft Forest Hum"

    config_invalid = _get_theme_config("nonexistent_theme")
    assert isinstance(config_invalid, dict)
    # Check that it falls back to a valid, if random, set
    assert "visual_colors" in config_invalid
    assert "sounds" in config_invalid

def test_generate_gradient_colors():
    """Test that gradient colors are generated and are valid hsl strings."""
    c1, c2 = _generate_gradient_colors()
    assert c1.startswith("hsl(") and c1.endswith("%)")
    assert c2.startswith("hsl(") and c2.endswith("%)")

# To run tests in CLI: python -m pytest test_urban_respite_weave.py (if pytest is installed)
# Or, for a simpler, self-contained run:
def run_all_tests():
    print("Running tests for Urban Respite Weave...")
    test_process_empty_input()
    print("test_process_empty_input passed.")
    test_process_with_theme_input()
    print("test_process_with_theme_input passed.")
    test_get_theme_config()
    print("test_get_theme_config passed.")
    test_generate_gradient_colors()
    print("test_generate_gradient_colors passed.")
    print("All tests passed!")

if __name__ == "__main__":
    run_all_tests()