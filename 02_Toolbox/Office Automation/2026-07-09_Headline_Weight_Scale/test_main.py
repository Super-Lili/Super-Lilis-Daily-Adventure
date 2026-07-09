from main import process

def test_headline_tool():
    # Input 1: the spec test case
    out1 = process("Residents Struggle Amid Affordable Housing Shortage")
    assert isinstance(out1, str)
    assert "Overall Score:" in out1
    assert "Agency Score:" in out1
    assert "Flagged Patterns:" in out1
    assert len(out1) > 50

    # Input 2: a headline with agency
    out2 = process("City Council Votes to Expand Public Housing")
    assert isinstance(out2, str)
    assert "Overall Score:" in out2
    # Expect different phrasing triggers different flags
    assert "Missing systemic actor" not in out2, "should not flag missing actor when council is present"
    assert len(out2) > 50

    # Input 3: minimal text without agency
    out3 = process("Families cope with water shortage")
    assert isinstance(out3, str)
    assert "Victim-blaming syntax" in out3 or "Missing systemic actor" in out3

    # Ensure outputs are different from each other
    assert out1 != out2
    assert out2 != out3

test_headline_tool()
print("All tests passed.")