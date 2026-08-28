from main import process


def test_process_spec_input():
    text = (
        "The Atlantic|Atlantic Vendor Portal|Dana Ruiz|d.ruiz@theatlantic.com|INV-0391|$1,250|2026-06-19|30|2026-07-29|1|Awaiting accounting approval\n"
        "Condé Nast / Bon Appétit|Condé Nast Vendor Portal|Marcus Lee|mlee@condenast.com|INV-0445|$900|2026-07-03|45|2026-08-10|0|No response yet\n"
        "Wired|Wired AP Portal|Priya Singh|priya.singh@wired.com|INV-0412|$850|2026-07-11|30|2026-08-01|2|Payment run scheduled next week"
    )
    result = process(text)
    assert len(result) > 300
    assert "RANKED FOLLOW-UP SEQUENCE" in result
    assert "EMAIL DRAFTS" in result
    assert "The Atlantic" in result
    assert "INV-0445" in result
    assert "---" in result
    assert result.count("Escalation Level:") >= 3


def test_process_changes_and_handles_small_input():
    out1 = process("Acme|Portal|Sam|s@x.com|INV-1|$100|2026-07-01|30|2026-08-01|0|No response")
    out2 = process("Beta|Portal|Alex|a@x.com|INV-2|$200|2026-07-02|45|2026-08-02|1|Checking")
    assert out1 and out2
    assert out1 != out2
    assert "Acme" in out1
    assert "Beta" in out2