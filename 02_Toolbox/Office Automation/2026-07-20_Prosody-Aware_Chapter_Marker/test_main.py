from main import process

def test_process():
    # Test 1: empty input returns a helpful message
    out1 = process("")
    assert "Paste a transcript or upload audio" in out1

    # Test 2: a transcript with speaker labels and timestamps
    inp2 = "Host: Welcome. (0:10)\nGuest: Hello. (0:25)"
    out2 = process(inp2)
    assert "Prosody-Aware Chapter Marker" in out2
    assert len(out2) > 500

    # Test 3: a different transcript should produce a different output
    inp3 = "Alice: Hi. (0:05)\nBob: Hey there. (0:15)"
    out3 = process(inp3)
    assert out3 != out2
    assert "Chapter" in out3 or "chapter" in out3

if __name__ == "__main__":
    test_process()
    print("All tests passed.")