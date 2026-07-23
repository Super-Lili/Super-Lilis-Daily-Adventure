import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from main import process

def test_empty():
    out = process("")
    assert "<html" in out and "canvas" in out
    assert "legal" in out and "chosen" in out

def test_two_names():
    out1 = process("Alice|Bob")
    out2 = process("Elena Vasquez|Ellie V.|0.6")
    assert out1 != out2
    assert "Alice" in out1 and "Bob" in out1
    assert "Elena Vasquez" in out2 and "Ellie V." in out2
    assert "weight" in out2

def test_slider():
    out = process("X||0.8")
    assert "value=\"0.8\"" in out or "0.8" in out

if __name__ == "__main__":
    test_empty()
    test_two_names()
    test_slider()
    print("All tests passed.")