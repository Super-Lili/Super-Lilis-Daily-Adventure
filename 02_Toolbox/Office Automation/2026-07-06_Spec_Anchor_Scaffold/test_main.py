from main import process

def test_empty_source():
    out = process("")
    assert len(out) > 0
    assert "FAIL" in out

def test_hardcoded_tool():
    src = "def process(text):\n    return '<html>sample</html>'\n"
    out = process(src)
    assert "PARSER CHECK: PASS" in out
    # Should fail static output test or fallback
    assert "FAIL" in out or "STATIC OUTPUT TEST: FAIL" in out or "FALLBACK/ERROR HANDLING: FAIL" in out

def test_dynamic_tool():
    src = "def process(text):\n    return text.upper()\n"
    out = process(src)
    assert "FINAL VERDICT: PASS" in out