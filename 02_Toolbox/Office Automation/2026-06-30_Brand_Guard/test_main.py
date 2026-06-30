from main import process

# Test 1: Spec test case
output1 = process("In a Q3 sales deck exported from Keynote, the primary brand blue (#1A3C6E) was measured at #2A4C7E on slide 7. This is a 15-degree hue shift toward teal. The deck was built from an old template that used a different blue. The asset owner is a new marketing coordinator who doesn't have design training. The deck was sent to the client 45 minutes ago.")
assert len(output1) > 100, "Output 1 too short"
assert "Delta-E" in output1, "Missing color metrics"
assert "guardrail" in output1.lower(), "Missing guardrail"
assert "Keynote" in output1, "Missing tool reference"

# Test 2: Typography violation
output2 = process("In a Figma design for the annual report, the heading font was set to Comic Sans instead of the approved brand typeface. The designer said they liked the 'friendly' look.")
assert len(output2) > 100, "Output 2 too short"
assert output2 != output1, "Outputs should differ between inputs"
assert "typography" in output2.lower() or "font" in output2.lower(), "Missing violation type"

# Test 3: Minimal input
output3 = process("The logo was stretched on the website banner.")
assert len(output3) > 50, "Output 3 too short"
assert output3 != output1, "All outputs must differ"
assert output3 != output2, "All outputs must differ"

print("All tests passed.")