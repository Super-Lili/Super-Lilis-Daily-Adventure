from main import process

def test_empty_input():
    html = process("")
    assert html, "Output should not be empty"
    assert "Batch Episode Renamer" in html
    assert "Paste filenames" in html

def test_single_filename():
    html = process("Zoom_Recording_2026-08-05_14.30.45_Participant_1234567890.mp3")
    assert "1234567890" in html
    assert "Episode" in html

def test_two_filenames_space_separated():
    html = process("Zoom_Recording_2026-08-05_14.30.45_Participant_1234567890.mp3 Zoom_Recording_2026-08-05_14.32.12_Participant_9876543210.mp3")
    assert "9876543210" in html
    assert "[No Match]" not in html  # Both should match