def affordability_comparison(generation_data):
    """
    Compares hypothetical home affordability across generations based on provided data.
    generation_data: A dictionary where keys are generation names and values are
                     (average_home_price, average_annual_income) tuples.
    """
    lines = ["--- GENERATIONAL AFFORDABILITY SNAPSHOT ---"]
    for generation, data in generation_data.items():
        home_price, income = data
        if income > 0:
            years_to_afford_home = home_price / income
            lines.append(f"\n{generation} (Hypothetical):")
            lines.append(f"  Average Home Price: ${home_price:,.2f}")
            lines.append(f"  Average Annual Income: ${income:,.2f}")
            lines.append(f"  Years of income needed to buy a home (approx.): {years_to_afford_home:.1f}")
        else:
            lines.append(f"\n{generation}: Insufficient income data to calculate affordability.")
    return "\n".join(lines)


def process(text: str) -> str:
    """
    Compare generational home affordability.
    Optionally parse 'home_price income' pairs from text (one per line).
    Falls back to the canonical Boomer vs Millennial example.
    """
    generation_data = {}
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    if lines:
        gen_names = [f"Generation {i+1}" for i in range(len(lines))]
        for i, line in enumerate(lines):
            parts = line.split()
            nums = []
            for p in parts:
                try:
                    nums.append(float(p.replace(',', '')))
                except ValueError:
                    pass
            if len(nums) >= 2:
                generation_data[gen_names[i]] = (nums[0], nums[1])

    if not generation_data:
        generation_data = {
            "Boomer Era (e.g., 1970s-1980s)": (65000, 15000),
            "Millennial Era (e.g., 2020s)": (400000, 70000)
        }

    return affordability_comparison(generation_data)


def _cli_main():
    # Illustrative data based on broad economic trends referenced in the friction point.
    illustrative_data = {
        "Boomer Era (e.g., 1970s-1980s)": (65000, 15000),
        "Millennial Era (e.g., 2020s)": (400000, 70000)
    }
    print(affordability_comparison(illustrative_data))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
