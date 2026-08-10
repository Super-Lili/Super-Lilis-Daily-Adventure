from main import process

def test_process_returns_html_with_title():
    result = process("any input")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Naming Validator" in result

def test_process_consistent_output():
    r1 = process("first")
    r2 = process("second")
    # Same static tool regardless of input
    assert r1 == r2

def test_html_contains_required_elements():
    html = process("")
    assert "patternInput" in html
    assert "dropZone" in html
    assert "reportTable" in html