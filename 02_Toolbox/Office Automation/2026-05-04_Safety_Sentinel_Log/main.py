import datetime


def format_incident_log(descriptions: list) -> str:
    """Format a list of incident descriptions into a timestamped log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"## Safety Sentinel Log — {timestamp}", ""]
    for i, desc in enumerate(descriptions, 1):
        lines.append(f"{i}. [INCIDENT] {desc}")
    lines += ["", f"Total incidents recorded: {len(descriptions)}",
              "Stay vigilant and report recurring issues to your safety officer."]
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Log safety incidents from provided text (one per line)."""
    if not text.strip():
        return "Paste safety incident descriptions (one per line) to generate a timestamped log."
    incidents = [l.strip().lstrip("-*•1234567890. ").strip() for l in text.strip().splitlines() if l.strip()]
    if not incidents:
        return "No incidents found. Paste one incident description per line."
    return format_incident_log(incidents)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    demo = "Wet floor not marked near entrance\nFire exit blocked by delivery boxes\nBroken handrail on staircase"
    print(process(demo))