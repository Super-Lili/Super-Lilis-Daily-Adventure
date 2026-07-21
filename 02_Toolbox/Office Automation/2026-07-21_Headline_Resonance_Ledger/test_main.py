import json
from main import process

def test_piped():
    inp = "2026-05-10 | Product Launch | Eager | Introducing the new X\n2026-06-15 | Summer Campaign | Summer Scatter | Beat the heat with Y\n2026-07-01 | Post-Election | Fatigue | Let's get back to work"
    out = process(inp)
    assert out and len(out) > 500, "Output should contain full HTML"
    assert "Introducing the new X" in out
    assert "Beat the heat with Y" in out

def test_csv():
    inp = "date,headline,campaign,mood\n2026-05-10,Intro X,Product Launch,Eager\n2026-06-20,Summer Deals,Summer Campaign,Summer Scatter"
    out = process(inp)
    assert out and "Intro X" in out and "Summer Deals" in out

def test_empty():
    out = process("")
    assert "No data" in out or "newsletter" in out.lower()
    assert len(out) > 0

test_piped()
test_csv()
test_empty()
print("All tests passed.")