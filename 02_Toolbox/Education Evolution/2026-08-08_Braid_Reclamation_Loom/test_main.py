from main import process

def test_basic():
    # Without input it returns a placeholder.
    out = process("")
    assert "Braid" in out

def test_with_data():
    inp = "2006 — Broke the city hall corruption story that forced two resignations."
    out = process(inp)
    assert "Set the Loom" in out
    assert "2006" in out

def test_different_inputs():
    a = process("2011 — Won a national award")
    b = process("2023 — Reported from inside a flooded hospital")
    assert a != b