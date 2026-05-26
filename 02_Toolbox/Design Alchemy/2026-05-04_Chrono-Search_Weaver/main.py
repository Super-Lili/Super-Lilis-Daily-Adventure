import re


mock_content_db = {
    "travel": {
        "2026": ["UserA: Sunset over the Mars colony domes!", "UserB: My first trip to Neo-Kyoto's holographic gardens."],
        "2023": ["UserC: Throwback to when we could actually fly without a biometric scan.", "UserD: Venice, before the sea walls."],
        "2018": ["UserE: That backpacking trip through Patagonia, pure bliss."],
        "default": ["UserF: Dream destinations for the digital nomad.", "UserG: Exploring local hidden gems."]
    },
    "food": {
        "2025": ["UserH: Replicating ancient Roman recipes with my food printer!", "UserI: The best synth-sushi in Sector 7."],
        "default": ["UserJ: What's cooking tonight?", "UserK: Gastro-sensory overload!"]
    },
    "art": {
        "2024": ["UserL: My latest AI-generated masterpiece, tell me what you think.", "UserM: Vintage oil painting techniques revisited."],
        "default": ["UserN: Infinite creative possibilities.", "UserO: Inspiration strikes!"]
    }
}


def chrono_search_weaver(query: str, year: str = None, platform: str = "Instagram (Hypothetical)") -> str:
    """Run a simulated chronological search and return results as text."""
    lower_query = query.lower()
    results_found = []
    if lower_query in mock_content_db:
        if year and year in mock_content_db[lower_query]:
            results_found.extend([f"- {post} (Year: {year})" for post in mock_content_db[lower_query][year]])
        elif not year:
            for y_key, posts in mock_content_db[lower_query].items():
                if y_key != "default":
                    results_found.extend([f"- {post} (Year: {y_key})" for post in posts])
            if "default" in mock_content_db[lower_query]:
                results_found.extend([f"- {post} (General/Undated)" for post in mock_content_db[lower_query]["default"]])

    lines = [f"## Chrono-Search Weaver: '{query}'" + (f" ({year})" if year else "") + f" on {platform}", ""]
    if results_found:
        lines.append(f"Found {len(results_found)} result(s):")
        lines += results_found
    else:
        lines.append("No matching content found in the simulated database.")
        lines.append("Try: travel, food, or art — optionally with a year like 2018 or 2024.")
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Simulate a chronological content search. Input: 'query [year]' e.g. 'travel 2018'"""
    if not text.strip():
        return chrono_search_weaver("travel")
    parts = text.strip().split()
    year_match = re.search(r'\b(20\d{2})\b', text)
    year = year_match.group(1) if year_match else None
    query_parts = [p for p in parts if not re.match(r'^20\d{2}$', p)]
    query = " ".join(query_parts).strip() or "travel"
    return chrono_search_weaver(query, year)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(chrono_search_weaver("travel", "2018"))
    print()
    print(chrono_search_weaver("food"))