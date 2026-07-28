import sys
from main import process

def test_process():
    # Example from spec
    svg1 = "<svg viewBox='0 0 100 100'><g opacity='0' fill='none' stroke='none'><rect x='10' y='10' width='80' height='80' fill='red'/></g><g aria-label='decorative'><circle cx='50' cy='50' r='10' fill='blue'/></g></svg>"
    out1 = process(svg1)
    assert out1, "Output should not be empty"
    assert "<svg" in out1 and "</svg>" in out1
    # opacity='0' must be removed from <g>
    assert 'opacity="0"' not in out1
    # aria-label must remain
    assert 'aria-label="decorative"' in out1

    # Second, different input with multiple groups and a visibility='hidden' that should be removed
    svg2 = "<svg><g fill='none' stroke='red' visibility='hidden'><circle r='5'/></g><g aria-hidden='true' display='none'><rect/></g></svg>"
    out2 = process(svg2)
    assert out2
    assert "fill='none'" not in out2 and 'fill="none"' not in out2
    assert 'visibility="hidden"' not in out2
    assert 'display="none"' not in out2
    # stroke='red' is not in target, should persist
    assert 'stroke="red"' in out2 or "stroke='red'" in out2
    # aria-hidden should persist
    assert 'aria-hidden="true"' in out2 or "aria-hidden='true'" in out2

    # Third, empty input returns empty string
    out3 = process("")
    assert out3 == ""

    # Ensure different inputs produce different outputs
    assert out1 != out2
    assert out1 != out3

if __name__ == "__main__":
    test_process()
    print("All tests passed.")