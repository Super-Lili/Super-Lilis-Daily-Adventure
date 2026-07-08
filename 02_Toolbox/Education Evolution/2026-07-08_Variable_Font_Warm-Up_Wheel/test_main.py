from main import process

def test_basic():
    out1 = process("apple harvest season")
    assert "apple harvest season" in out1, "Output should contain the input phrase"
    out2 = process("quantum computing jobs")
    assert "quantum computing jobs" in out2
    assert out1 != out2, "Different inputs must produce different output"
    # The HTML should be substantial
    assert len(out1) > 1000

def test_default():
    out = process("sample word Motion")
    assert "Motion" in out
    assert "font-variation-settings" in out

def test_empty():
    out = process("")
    assert "Enter a sample word" in out

def test_short_phrase():
    out = process("The quick brown fox")
    assert "The quick brown fox" in out