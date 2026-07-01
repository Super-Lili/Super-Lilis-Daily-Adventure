from main import process

def test_process_basic_input():
    input_text = "My day was full of bright CMYK palettes and constant email pings. I need 20 minutes to reset."
    output = process(input_text)
    assert isinstance(output, str)
    assert len(output) > 500  # Ensure substantial output
    assert "Session Duration: 20 minutes" in output
    assert "Visual Transition Plan" in output
    assert "Auditory Transition Plan" in output
    assert "CSS Initial State" in output
    assert "Web Audio API Note" in output

def test_process_different_duration():
    input_text = "Lots of screen glare and background office chatter. I need 10 min to clear my head."
    output = process(input_text)
    assert isinstance(output, str)
    assert "Session Duration: 10 minutes" in output
    assert "Initial Sensory Assessment" in output
    assert "Phase 1 (0-2 min)" in output # 20% of 10 minutes
    assert "Phase 2 (2-6 min)" in output # 20%-60%
    assert "filter: saturate(" in output # Check for CSS property hint

def test_process_empty_input():
    input_text = ""
    output = process(input_text)
    assert "Error: Please provide a description" in output

def test_process_low_intensity_input():
    input_text = "Just a bit tired, need 5 minutes."
    output = process(input_text)
    assert isinstance(output, str)
    assert "Session Duration: 5 minutes" in output
    assert "Visual Intensity: 10% inferred" in output # Default low intensity
    assert "Auditory Intensity: 10% inferred" in output
    assert "Proposed CSS Initial State" in output # Should still provide state for a low start