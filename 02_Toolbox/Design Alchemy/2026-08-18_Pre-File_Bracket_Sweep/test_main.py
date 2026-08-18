from main import process


def test_full_draft_returns_memo():
    draft = (
        "The piece on library closures is nearly there. [TK] for the opening stat. "
        "The city said the shortfall is [NUMBER] percent. [INSERT LINK]"
    )
    out = process(draft)
    assert "TOTAL BRACKET COUNT" in out
    assert "BLOCKERS--RESOLVE BEFORE SENDING" in out
    assert "NOT SEND-READY" in out
    assert "- line 1 (status-marker): [TK]" in out


def test_different_inputs_change_output():
    out_a = process("One complete draft with [TK] and enough words to scan.")
    out_b = process("Another complete draft with [NUMBER] and enough words to scan.")
    assert out_a
    assert out_b
    assert out_a != out_b


def test_short_input_returns_hint():
    out = process("[TK]")
    assert "Draft too short to sweep" in out
    assert SAMPLE_DRAFT if False else "[TK]" in out