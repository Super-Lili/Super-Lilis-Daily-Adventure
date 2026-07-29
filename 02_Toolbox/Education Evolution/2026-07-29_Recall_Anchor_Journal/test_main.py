from main import process


def test_process_returns_html():
    result = process("")
    assert result is not None
    assert len(result) > 500
    assert "<!DOCTYPE html>" in result
    assert "Recall Anchor Journal" in result


def test_process_idempotent():
    r1 = process("hello")
    r2 = process("world")
    assert r1 == r2  # same HTML shell regardless of input text


def test_process_contains_javascript():
    result = process("test concept")
    assert "localStorage" in result
    assert "Math.pow" in result
    assert "computeInterval" in result
    assert "buildData" in result
    assert "updateUI" in result
    assert "logRecall" in result


def test_process_timeline_elements():
    result = process("x")
    assert "tl-bar" in result
    assert "timeline" in result
    assert "today" in result


def test_process_queue_section():
    result = process("x")
    assert "todayQueue" in result
    assert "No concepts due" in result