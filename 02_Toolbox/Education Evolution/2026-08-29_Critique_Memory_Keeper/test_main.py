from main import process


def test_process_returns_ledger():
    text1 = (
        "Slack 2026-08-04: fix spacing between cards\n"
        "Figma 2026-08-11: card spacing is still uneven\n"
        "Weekly review 2026-08-14: grid feels tight, increase gutter spacing"
    )
    out1 = process(text1)
    assert len(out1) > 80
    assert "## Feedback Ledger" in out1
    assert "spacing" in out1

    text2 = (
        "Email: button contrast too low on muted background\n"
        "Email: button color contrast fails accessibility"
    )
    out2 = process(text2)
    assert out2 != out1
    assert "contrast" in out2

    text3 = "Review 2026-08-20: the primary button is not visually distinct enough"
    out3 = process(text3)
    assert len(out3) > 30
    assert "## Orphan Items" in out3