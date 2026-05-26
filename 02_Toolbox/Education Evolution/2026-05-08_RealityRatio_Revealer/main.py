import re


def affordability_comparison(generation_data: dict) -> str:
    """
    Compares hypothetical home affordability across generations.
    generation_data: dict of {name: (home_price, income)}
    Returns formatted markdown table.
    """
    lines = ["## Generational Affordability Snapshot", "",
             "| Generation | Home Price | Annual Income | Years of Income Needed |",
             "|---|---|---|---|"]
    for generation, data in generation_data.items():
        home_price, income = data
        if income > 0:
            ratio = home_price / income
            lines.append(f"| {generation} | ${home_price:,.0f} | ${income:,.0f} | {ratio:.1f} years |")
        else:
            lines.append(f"| {generation} | ${home_price:,.0f} | N/A | N/A |")
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Parse generation data and show affordability ratios.

    Input format (one per line): GenerationName, home_price, income
    Example: Boomer Era, 65000, 15000
    """
    default_data = {
        "Boomer Era (e.g., 1970s-1980s)": (65000, 15000),
        "Millennial Era (e.g., 2020s)": (400000, 70000),
    }
    if not text.strip():
        return affordability_comparison(default_data)
    parsed = {}
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            try:
                name = parts[0]
                price = float(re.sub(r'[^\d.]', '', parts[1]))
                income = float(re.sub(r'[^\d.]', '', parts[2]))
                parsed[name] = (price, income)
            except (ValueError, IndexError):
                pass
    if not parsed:
        return affordability_comparison(default_data)
    return affordability_comparison(parsed)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    illustrative_data = {
        "Boomer Era (e.g., 1970s-1980s)": (65000, 15000),
        "Millennial Era (e.g., 2020s)": (400000, 70000),
    }
    print(affordability_comparison(illustrative_data))