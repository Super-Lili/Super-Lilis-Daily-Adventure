from main import process

def test_nonempty():
    out = process("primary-500 #1a1aff #4d4dff\nprimary-700 #0000cc #3333cc\nsecondary-500 #ff9900 #ffaa33\nbackground #ffffff #121212")
    assert len(out) > 1000
    assert "Generate CSS" in out
    assert "primary-500" in out

def test_different():
    out2 = process("accent #ff0000")
    assert len(out2) > 500
    assert "Generate CSS" in out2

def test_empty():
    out3 = process("")
    assert "No tokens provided" in out3