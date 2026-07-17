from main import process

def test_humming_page():
    # two different inputs produce different HTML
    html1 = process("apple harvest season")
    html2 = process("quantum computing jobs")
    assert html1 != html2
    # both must contain our key visual elements
    assert '<textarea placeholder="type your thoughts…"' in html1
    assert 'id="status"' in html1
    # any input results in non-empty page
    assert len(html1) > 300

def test_empty_input():
    html = process("")
    assert '<textarea placeholder="type your thoughts…"' in html
    assert len(html) > 300

def test_long_input():
    long_text = "I can't stop thinking about the thesis revisions." * 10
    html = process(long_text)
    # initial text is truncated to 500 chars
    assert "thesis revisions" in html