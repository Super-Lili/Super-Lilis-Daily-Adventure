```python
def affordability_comparison(generation_data):
    """
    Compares hypothetical home affordability across generations based on provided data.
    generation_data: A dictionary where keys are generation names and values are
                     (average_home_price, average_annual_income) tuples.
    """
    print("--- GENERATIONAL AFFORDABILITY SNAPSHOT ---")
    for generation, data in generation_data.items():
        home_price, income = data
        if income > 0:
            years_to_afford_home = home_price / income
            print(f"\n{generation} (Hypothetical):")
            print(f"  Average Home Price: ${home_price:,.2f}")
            print(f"  Average Annual Income: ${income:,.2f}")
            print(f"  Years of income needed to buy a home (approx.): {years_to_afford_home:.1f}")
        else:
            print(f"\n{generation}: Insufficient income data to calculate affordability.")

# Illustrative data based on broad economic trends referenced in the friction point.
# These figures are not precise economic averages but serve to highlight the relative difference.
# (Hypothetical Average Home Price, Hypothetical Average Annual Income)
illustrative_data = {
    "Boomer Era (e.g., 1970s-1980s)": (65000, 15000), # Article mentions $65k home price
    "Millennial Era (e.g., 2020s)": (400000, 70000)
}

affordability_comparison(illustrative_data)
```