# test_main.py
import os
import json
import datetime
import svgwrite

# Assuming the tool's code is in a file named 'balance_bloom_tool.py'
# For testing purposes, we'll import relevant functions directly or simulate the call.
# In a real scenario, you'd import 'process' and '_cli_main' from the main script.

# Mock the core generation logic for predictable testing
def mock_generate_bloom_svg_content_internal(
    start_color_hex: str,
    end_color_hex: str,
    cycle_duration_hours: int,
    current_time: datetime.datetime
) -> str:
    """A mock version of the internal SVG generation for consistent test output."""
    # This mock will produce a minimal, consistent SVG for testing file existence
    # without needing exact color calculations.
    dwg = svgwrite.Drawing(size=('100%', '100%'), profile='full')
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill=start_color_hex))
    return dwg.tostring()

# Override the actual generation function with the mock for testing
# This is a bit of a hack but allows testing the process function's flow
# without datetime dependency complications for reproducible SVG content.
# In a proper module import, you might patch it. Here, we'll re-implement process.

def test_process_function_defaults():
    """Test process function with default parameters."""
    # We will simulate the 'process' function's behavior without the internal dependency
    # to make it truly self-contained for testing.
    # The actual 'process' function would call the _generate_bloom_svg_content_internal.
    # Here, we'll confirm it returns an SVG-like string.
    
    # Simulate a call to process with default parameters
    svg_output = process("") # Pass empty string for default params
    assert isinstance(svg_output, str)
    assert svg_output.startswith('<svg')
    assert svg_output.endswith('</svg>')
    assert "url(#balanceGradient)" in svg_output # Check for gradient definition

def test_process_function_with_json_input():
    """Test process function with custom parameters via JSON string."""
    test_params = {
        "start_color": "#FF0000",
        "end_color": "#0000FF",
        "cycle_duration_hours": 1
    }
    json_input = json.dumps(test_params)
    svg_output = process(json_input)
    
    assert isinstance(svg_output, str)
    assert svg_output.startswith('<svg')
    assert svg_output.endswith('</svg>')
    assert "url(#balanceGradient)" in svg_output

def test_cli_main_generates_file():
    """Test _cli_main function to ensure it generates an SVG file."""
    test_output_path = "test_balance_bloom.svg"
    
    # Clean up any previous test file
    if os.path.exists(test_output_path):
        os.remove(test_output_path)

    # Simulate command-line arguments.
    # We'll temporarily mock sys.argv.
    import sys
    original_argv = sys.argv
    sys.argv = [
        "balance_bloom_tool.py",
        "--output_path", test_output_path,
        "--start_color", "#AAAAAA",
        "--end_color", "#BBBBBB",
        "--cycle_duration_hours", "10"
    ]
    
    try:
        # Call the CLI main function. This will internally call 'process' and save the file.
        _cli_main()
        
        # Assert that the file was created
        assert os.path.exists(test_output_path)
        
        # Read the file content and check for SVG structure
        with open(test_output_path, "r") as f:
            content = f.read()
            assert content.startswith('<svg')
            assert content.endswith('</svg>')
            assert "url(#balanceGradient)" in content

    finally:
        # Clean up the test file and restore sys.argv
        if os.path.exists(test_output_path):
            os.remove(test_output_path)
        sys.argv = original_argv

# Re-define process and _cli_main from the main tool file here for self-contained testing.
# In a real module structure, you'd import them.
# This assumes the full code block for the tool is available above this test block.
# For the purpose of this response, I'm including the full tool code in the main response.
# This test assumes it has access to the functions 'process' and '_cli_main'.

if __name__ == "__main__":
    # Temporarily remove globals.get('USER_INPUT') for consistent CLI testing within this file
    # Or, ensure it's None.
    _browser_input = globals().get('USER_INPUT', None)
    globals()['USER_INPUT'] = None # Force CLI mode for tests

    print("Running tests for Balance Bloom...")
    
    # Ensure all necessary functions are available for the test run.
    # In a real setup, these would be imported from the tool's main file.
    # For this self-contained test, we'll assume they are defined above.
    
    # Make sure _cli_main exists (as it imports argparse, it can't be at top level for browser)
    try:
        from __main__ import process, _cli_main # Assuming the main code is in __main__
    except ImportError:
        print("Could not import process, _cli_main for testing. Ensure the tool's code is correctly structured.")
        exit(1)

    test_process_function_defaults()
    print("test_process_function_defaults passed.")
    
    test_process_function_with_json_input()
    print("test_process_function_with_json_input passed.")
    
    test_cli_main_generates_file()
    print("test_cli_main_generates_file passed.")
    
    print("All Balance Bloom tests passed!")

    # Restore USER_INPUT global if it was set
    if _browser_input is not None:
        globals()['USER_INPUT'] = _browser_input