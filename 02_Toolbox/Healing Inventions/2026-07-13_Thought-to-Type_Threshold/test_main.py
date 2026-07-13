from main import process

def test_process_different_inputs():
    # Two different inputs produce different HTML output
    out1 = process("")
    out2 = process("int main() { return 0; }")
    out3 = process("x + y")
    # All outputs should be non-empty HTML
    assert len(out1) > 100, "Empty input should still produce a full HTML page"
    assert len(out2) > 100
    assert len(out3) > 100
    # Outputs must differ because the initial visible text is embedded
    assert out1 != out2, "Different inputs must produce different HTML"
    assert out2 != out3

def test_structural():
    out = process("test")
    # Should contain the heading, slider, typing area, and the input text embedded
    assert "Thought → Type Threshold" in out
    assert 'id="delay-slider"' in out
    assert 'id="typing-area"' in out
    # The initial text should appear in the embedded JavaScript (as a JSON string)
    assert '"test"' in out  # the JSON representation
    assert "Start typing" in out

def test_empty_initial():
    out = process("   ")
    # Should still contain full structure, no text preloaded
    assert len(out) > 100
    assert '""' in out or "'" not in out  # empty string JSON