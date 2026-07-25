from main import process

def test_memo():
    out = process("any")
    assert "Pre-Meeting Intent Memo" in out
    assert len(out) > 500
    out2 = process("different")
    assert out == out2  # mode 3 returns the same template