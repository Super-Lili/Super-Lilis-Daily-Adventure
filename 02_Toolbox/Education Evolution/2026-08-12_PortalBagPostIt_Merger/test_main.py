from main import process

def test_process():
    # Two different partial inputs to verify the tool processes and produces distinct HTML
    input1 = "DISCHARGE SUMMARY: Metformin 500 mg twice daily with meals. Lisinopril 10 mg once daily in the morning on empty stomach."
    input2 = "PHARMACY LEAFLET: METFORMIN 500 mg take with breakfast and dinner. LISINOPRIL 10 mg take once daily, with or without food. ATORVASTATIN 20 mg take at bedtime."

    out1 = process(input1)
    out2 = process(input2)

    # Both must return non-empty HTML
    assert out1 and len(out1) > 100, "Output 1 too short"
    assert out2 and len(out2) > 100, "Output 2 too short"

    # Should contain a table (reconciled schedule)
    assert '<table>' in out1
    assert '<table>' in out2

    # Outputs must differ because inputs are different
    assert out1 != out2, "Outputs should differ for different inputs"

    # Title is always present
    assert 'Medication Merge' in out1
    assert 'Medication Merge' in out2

test_process()
print("All tests passed.")