from main import process

SPEC_INPUT = (
    "Downloads/charity bake sale flyer final v3.png\n"
    "Charity_Bake_Sale_Poster_2026.jpg\n"
    "School Sports Day Banner.png\n"
    "PTA Meeting Flyer Draft.png\n"
    "School Sports Day Banner Final.png\n"
    "PTA Meeting Flyer Final v2.png"
)

def test_process_returns_html():
    out = process(SPEC_INPUT)
    assert out, "process returned empty string"
    assert "<html" in out.lower(), "output should be HTML"
    assert len(out) > 500, "HTML page should be substantial"

def test_different_inputs_produce_different_pages():
    out1 = process("a.txt\nb.txt")
    out2 = process("c.txt")
    assert out1 != out2

def test_empty_input_returns_valid_html():
    out = process("   ")
    assert "<html" in out.lower()