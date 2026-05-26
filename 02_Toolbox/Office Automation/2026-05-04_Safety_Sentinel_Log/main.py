import datetime


def log_safety_incident(incident_description):
    """
    Logs a safety incident with a timestamp.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] INCIDENT: {incident_description}\n"

    try:
        with open("safety_log.txt", "a") as f:
            f.write(log_entry)
        print(f"Incident logged successfully: {incident_description}")
    except IOError as e:
        print(f"Error writing to log file: {e}")


def process(text: str) -> str:
    """
    Record a safety incident (without file I/O in browser mode).
    Input: description of the safety incident or recurring frustration.
    Falls back to a tip sheet if empty.
    """
    if not text.strip():
        lines = [
            "Safety Sentinel Log",
            "=" * 35,
            "Use this tool to track recurring safety frustrations or incidents.",
            "",
            "Common workplace safety concerns to log:",
            "  - Ergonomic issues (bad chair, screen height, lighting)",
            "  - Repetitive stress from equipment",
            "  - Unclear safety procedures",
            "  - Near-miss incidents",
            "  - Unsafe conditions reported but not addressed",
            "",
            "Tip: Document incidents consistently — date, description, and any action taken.",
            "This record can support formal complaints or improvement requests.",
        ]
        return "\n".join(lines)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "Safety Sentinel Log — Incident Recorded",
        "=" * 40,
        f"Timestamp:   {timestamp}",
        f"Description: {text.strip()}",
        "",
        "This incident has been noted. For persistent issues:",
        "  - Report to your supervisor or safety officer",
        "  - Document pattern of occurrences with dates",
        "  - Consult your organization's safety policy",
        "  - Run locally (python3 main.py) to save to safety_log.txt",
    ]
    return "\n".join(lines)


def _cli_main():
    print("Welcome to the Safety Sentinel Log. Report recurring frustrations.")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("Describe the safety incident: ")
        if user_input.lower() == 'exit':
            break
        elif user_input:
            log_safety_incident(user_input)
        else:
            print("Please provide a description.")

    print("Exiting Safety Sentinel. Stay vigilant!")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
