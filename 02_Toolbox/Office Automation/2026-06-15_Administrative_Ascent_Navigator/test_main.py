"""Test file for Administrative Ascent Navigator."""
from main import process

def test_process_returns_valid_output():
    """Test that process returns a non-empty HTML string."""
    result = process("My divorce lawyer sent me the Uniform Child Support Order to fill out, and I need to cut off Netflix, Amazon, and shared Google Photos.")
    assert isinstance(result, str), "Output must be a string"
    assert len(result) > 200, "Output must contain substantial HTML"
    assert "<!DOCTYPE html>" in result, "Output must be valid HTML"
    assert "Ascent Path" in result, "Output must contain dashboard elements"

def test_process_different_inputs():
    """Test that different inputs produce different outputs."""
    input1 = "I need to cancel my Netflix and Amazon Prime accounts."
    input2 = "My legal documents need organizing and my bank account needs to be closed."
    result1 = process(input1)
    result2 = process(input2)
    assert result1 != result2, "Different inputs must produce different outputs"

def test_process_contains_categories():
    """Test that output contains task categories."""
    result = process("I have Netflix and Amazon accounts to close.")
    assert "Digital River Crossing" in result or "Financial Clearing" in result, \
        "Output should contain recognized category names"

def test_process_handles_empty_input():
    """Test graceful handling of short input."""
    result = process("")
    assert len(result) > 50, "Should return a help message, not empty"
    assert "describe" in result.lower(), "Should prompt for more input"

def test_process_contains_gamification():
    """Test that output contains gamification elements."""
    result = process("Divorce lawyer sent me legal forms to fill out and I need to close joint accounts.")
    assert "points" in result.lower(), "Output should mention points"
    assert "badge" in result.lower() or "milestone" in result.lower(), \
        "Output should contain badge or milestone references"

def test_process_structural_properties():
    """Test structural properties of the HTML output."""
    result = process("I need to organize legal documents and cancel shared subscriptions.")
    assert "task-card" in result, "Output must contain task cards"
    assert "checkbox" in result.lower(), "Output must contain checkboxes"
    assert "reset" in result.lower() or "new ascent" in result.lower(), \
        "Output must contain a reset option"
```