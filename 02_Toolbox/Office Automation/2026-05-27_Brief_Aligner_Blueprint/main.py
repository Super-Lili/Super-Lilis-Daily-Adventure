# requirements: regex, matplotlib, python-dateutil
import re
import os
import textwrap
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import regex as re_extended # Using 'regex' for advanced features
from dateutil import parser as date_parser # Using 'python-dateutil' for parsing dates
from collections import Counter # Added for dominant year logic

def _extract_patterns(text: str) -> dict:
    """
    Extracts key information like decisions, actions, and scope from the input text
    using regular expressions.
    """
    extracted = {
        "decisions": [],
        "action_items": [],
        "scope_details": [],
        "dates": []
    }

    # Regex for decisions (e.g., "We agreed on...", "Decision: ...", "Confirmed at...")
    decision_patterns = [
        r"(?:agreed on|decision:|confirmed at|set for|will be|established as)\s*([^.;,]+)",
        r"(?:key message:|message:)\s*['\"]?([^'\";,]+)['\"]?", # Capture key messages like "Authenticity over Perfection"
        r"target(?:ing)?\s*([^.;,]+)", # General targeting statements
        r"confirm target audience as\s*([^.;,]+)", # Specific target audience confirmation
        r"exclude\s*([^.;,]+)\s*(?:from|due to|for)"
    ]
    for pattern in decision_patterns:
        extracted["decisions"].extend(re_extended.findall(pattern, text, re_extended.IGNORECASE))

    # Regex for action items (e.g., "Initial assets due...", "Let's pencil that in...", "Next check-in...")
    action_patterns = [
        r"(?:assets due by|explore a partnership with|next check-in scheduled for)\s*([^.;,]+)",
        r"pencil that in for\s*([^.;,]+)", # For "Let's pencil that in for June 1st to explore."
        r"(?:I'll|we'll)\s*(add it to the brief|confirm the deliverable count)",
        r"confirm\s*([^.;,]+)\s*(?:when you send the brief|as)" # Capture actions like "confirm the deliverable count"
    ]
    for pattern in action_patterns:
        extracted["action_items"].extend(re_extended.findall(pattern, text, re_extended.IGNORECASE))

    # Regex for scope details (e.g., "targeting Gen Z", "10 unique social posts", "exclude Facebook")
    scope_patterns = [
        r"(?:targeting|focus on|target audience as)\s*([^.;,]+)", # Unified target audience capture for scope
        r"(\d+\s*unique\s*social\s*posts)",
        r"partnership with\s*([^.;,]+)", # Capture influencer partnerships
        r"(?:exclude|include)\s*([^.;,]+)\s*(?:from|for|in initial push)"
    ]
    for pattern in scope_patterns:
        extracted["scope_details"].extend(re_extended.findall(pattern, text, re_extended.IGNORECASE))

    # --- Date Extraction & Year Inference Improvement ---
    date_mentions_raw = re_extended.findall(
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?\b|\d{1,2}/\d{1,2}(?:/\d{2,4})?',
        text, re_extended.IGNORECASE
    )
    
    # First pass: parse all dates and collect all explicit years mentioned in the *raw date string*
    all_parsed_dates_temp = []
    explicit_years_found = []
    for date_str in date_mentions_raw:
        try:
            parsed_date = date_parser.parse(date_str, fuzzy=True, yearfirst=False)
            all_parsed_dates_temp.append(parsed_date)
            if re.search(r'\d{4}', date_str): # Check if the raw date string contains a 4-digit year
                explicit_years_found.append(parsed_date.year)
        except date_parser.ParserError:
            pass

    dominant_year = None
    if explicit_years_found:
        year_counts = Counter(explicit_years_found)
        if year_counts: # Ensure there are counts before trying to get most_common
            dominant_year = year_counts.most_common(1)[0][0]

    # Second pass: populate extracted["dates"], applying the dominant year if a date seems to have defaulted
    for parsed_date in all_parsed_dates_temp:
        # If the parsed date's year is the current year (likely default for year-less dates)
        # or an improbably old year for a project brief (e.g., < 2000), and a dominant_year from the text is found, apply it.
        # This handles cases like "June 5th" being parsed as "June 5th, 2024" when the document context is "2026".
        if dominant_year and (parsed_date.year == datetime.now().year or parsed_date.year < 2000):
            parsed_date = parsed_date.replace(year=dominant_year)
        extracted["dates"].append(parsed_date)
    # --- End Date Extraction & Year Inference Improvement ---

    # Clean and deduplicate. Changed .capitalize() to just .strip() to preserve original casing.
    for key in extracted:
        if key != "dates":
            extracted[key] = sorted(list(set([item.strip() for item in extracted[key] if item.strip()])))
    
    # Deduplicate and sort dates after potential year correction
    extracted["dates"] = sorted(list(set(extracted["dates"])))
    
    return extracted

def _generate_brief_text(extracted_data: dict) -> str:
    """
    Formats the extracted data into a human-readable client alignment brief.
    """
    brief_lines = []
    brief_lines.append("# Client Alignment Brief\n")
    brief_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    brief_lines.append("---")

    if extracted_data["decisions"]:
        brief_lines.append("\n## Confirmed Decisions:")
        for item in extracted_data["decisions"]:
            brief_lines.append(f"- {item}")

    if extracted_data["scope_details"]:
        brief_lines.append("\n## Project Scope & Audience:")
        for item in extracted_data["scope_details"]:
            brief_lines.append(f"- {item}")

    if extracted_data["action_items"]:
        brief_lines.append("\n## Key Action Items & Next Steps:")
        for item in extracted_data["action_items"]:
            brief_lines.append(f"- {item}")

    if extracted_data["dates"]:
        # Sort dates for better presentation, but only if they are relevant to a specific item
        # For this brief, just listing unique dates is sufficient for context
        unique_sorted_dates = sorted(list(set(d.date() for d in extracted_data["dates"])))
        if unique_sorted_dates:
            brief_lines.append("\n## Important Dates Mentioned:")
            for date_item in unique_sorted_dates:
                brief_lines.append(f"- {date_item.strftime('%B %d, %Y')}")

    brief_lines.append("\n---")
    brief_lines.append("Please review this brief for accuracy and completeness. Your explicit confirmation ensures we're fully aligned for successful project delivery. Reply 'CONFIRMED' or highlight any points needing adjustment.")

    return textwrap.dedent("\n".join(brief_lines)).strip()

def _generate_summary_chart(extracted_data: dict, output_filepath: str):
    """
    Generates a simple bar chart summarizing the categories of extracted information.
    """
    categories = ["Decisions", "Scope Details", "Action Items"]
    counts = [
        len(extracted_data["decisions"]),
        len(extracted_data["scope_details"]),
        len(extracted_data["action_items"])
    ]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(categories, counts, color=['#66c2a5', '#fc8d62', '#8da0cb'])

    ax.set_ylabel('Number of Items')
    ax.set_title('Client Alignment Brief Summary')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, int(yval), ha='center', va='bottom') # Cast to int for cleaner label

    plt.tight_layout()
    plt.savefig(output_filepath)
    plt.close(fig) # Close the plot to free memory

def process(text: str, output_prefix: str = "client_brief") -> str:
    """
    Core logic: takes plain text input, extracts information, generates a brief,
    and creates a summary chart. Returns confirmation message.
    """
    if not text.strip():
        return "Oops! Looks like there's no communication text to process. Please provide some input!"

    extracted_info = _extract_patterns(text)
    brief_content = _generate_brief_text(extracted_info)

    brief_filepath = f"{output_prefix}.txt"
    chart_filepath = f"{output_prefix}_summary.png"

    try:
        with open(brief_filepath, "w", encoding="utf-8") as f:
            f.write(brief_content)
        _generate_summary_chart(extracted_info, chart_filepath)
        return (f"Awesome! Your Client Alignment Brief is ready at '{brief_filepath}' "
                f"and a visual summary is saved as '{chart_filepath}'. "
                "Time to get that clarity confirmed! ✨")
    except IOError as e:
        return f"Uh oh, couldn't write the output files: {e}. Maybe check your permissions?"
    except Exception as e:
        return f"Something unexpected happened: {e}. Let's try again, shall we!"

def _cli_main():
    import argparse
    import sys

    p = argparse.ArgumentParser(
        description="Transforms scattered client communications into a clear, scannable Client Alignment Brief and a visual summary. "
                    "Helps freelancers get explicit confirmation on project details."
    )
    p.add_argument(
        "--input",
        required=True,
        help="Paste your raw communication text (emails, chat logs, meeting notes) directly, or provide a path to a text file containing them."
    )
    p.add_argument(
        "--output_prefix",
        default="client_brief",
        help="Prefix for the output text file (.txt) and summary chart (.png). Default: client_brief"
    )
    args = p.parse_args()

    input_text = ""
    if os.path.exists(args.input):
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                input_text = f.read()
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        input_text = args.input # Assume direct text input

    print(process(input_text, args.output_prefix))

# Dual-mode: browser (Pyodide sets USER_INPUT) OR local CLI
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    # In browser, we can't write to local filesystem directly, so we return the brief text
    # The image generation will fail in Pyodide without a proper file system access for matplotlib,
    # but the brief text part can still be useful.
    # For a real Pyodide scenario, the UI would need to handle saving files.
    # For this exercise, we'll return the text and note the image limitation.
    extracted_info_browser = _extract_patterns(_browser_input)
    brief_content_browser = _generate_brief_text(extracted_info_browser)
    print("--- Client Alignment Brief (Text Output for Browser) ---\n")
    print(brief_content_browser)
    print("\nNote: Image generation for the summary chart is not directly supported in this browser environment.")
elif __name__ == "__main__":
    _cli_main()