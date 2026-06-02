from main import process
import datetime

def test_process_returns_html_string():
    """Test that process function returns a non-empty HTML string."""
    output = process()
    assert isinstance(output, str)
    assert output.strip().startswith('<!DOCTYPE html>')
    assert "<div id=\"clock\"></div>" in output
    assert "<script>" in output
    assert "<style>" in output

def test_html_contains_required_elements():
    """Test for critical HTML elements and CSS properties."""
    output = process()
    assert 'font-family: -apple-system' in output # System font
    assert 'transition: background-color 1.5s ease-in-out;' in output # Smooth transition
    assert 'font-size: clamp(2rem, 15vw, 10rem);' in output # Responsive font size

def test_javascript_color_points_exist():
    """Test that colorPoints array is present in the JavaScript."""
    output = process()
    assert 'const colorPoints = [' in output
    assert '{h: 0, m: 0, r: 25, g: 25, b: 70}' in output # Check for a specific color point
    assert '{h: 24, m: 0, r: 25, g: 25, b: 70}' in output # Check for the loop-back point

def test_javascript_update_function_exists():
    """Test for the presence of the updateClock JavaScript function."""
    output = process()
    assert 'function updateClock() {' in output
    assert 'setInterval(updateClock, 1000);' in output # Ensures continuous update
    assert 'root.style.setProperty('--bg-color',' in output # Ensures color update logic

# You would typically run these tests by saving the output to an HTML file
# and manually verifying its behavior in a browser, especially for visual
# and time-dependent aspects. Automated end-to-end browser tests are
# beyond the scope of this self-contained testing environment.