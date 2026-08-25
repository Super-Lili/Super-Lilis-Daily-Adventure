from main import process

def test_process_returns_html_for_bezier():
    out = process("cubic-bezier(0.36, 0.07, 0.19, 0.97)")
    assert out
    assert "<!DOCTYPE html>" in out
    assert "Easing Curve Rosetta" in out

def test_process_changes_for_different_inputs():
    a = process("cubic-bezier(0.36, 0.07, 0.19, 0.97)")
    b = process("power2.inOut")
    assert a
    assert b
    assert a != b

def test_process_ae_input_contains_ae_artifacts():
    out = process("out=70%/in=60%")
    assert "cubic-bezier(" in out
    assert "AE Influence" in out