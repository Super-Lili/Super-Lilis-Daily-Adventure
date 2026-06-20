from main import process

# Test 1: journalism text extracts structured sections
result1 = process(
    "The company announced a 40% revenue increase last quarter, said CEO John Smith. "
    "Analysts confirmed the growth was driven by AI products. "
    "It remains unclear whether this trend will continue into 2026. "
    "Competitors have not yet responded to the announcement. "
    "Investors are watching the situation closely."
)
assert len(result1) > 150
assert "KEY CLAIMS" in result1
assert "OPEN QUESTIONS" in result1
assert "RECURRING THEMES" in result1

# Test 2: different input produces different output
result2 = process(
    "Climate scientists warned that global temperatures rose by 1.5 degrees, according to the report. "
    "The government has not yet announced any policy response. "
    "Who will take responsibility for the delay? "
    "Renewable energy investments reached 300 billion dollars last year. "
    "Experts argue that immediate action is required to prevent further damage."
)
assert result1 != result2
assert "ATTRIBUTED QUOTES" in result2

# Test 3: empty input returns helpful message, not crash
result3 = process("")
assert len(result3) > 10
assert "KEY CLAIMS" not in result3
