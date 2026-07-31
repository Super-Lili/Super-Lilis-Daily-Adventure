from main import process

def test_notebook():
    in1 = "Today, Jamal re-explained diffusion using his basketball practice—no diagrams, just motion and sweat. I didn't grade it. I just wrote it down."
    out1 = process(in1)
    assert isinstance(out1, str) and len(out1) > 500
    assert "Jamal" in out1
    assert "<textarea" in out1

    in2 = "Another quiet observation. No judgement."
    out2 = process(in2)
    assert isinstance(out2, str) and len(out2) > 500
    assert "Another quiet observation" in out2
    assert out1 != out2

    in3 = ""
    out3 = process(in3)
    assert "Ungraded Notebook" in out3

if __name__ == "__main__":
    test_notebook()
    print("All tests passed.")