import re


def check_status_text(page_text: str, keywords: list) -> list:
    """Check a text body for presence of keywords."""
    page_lower = page_text.lower()
    found = [kw for kw in keywords if kw.lower() in page_lower]
    return found


def process(text: str = "") -> str:
    """Scan provided page text for status keywords and report findings."""
    if not text.strip():
        return (
            "Paste the text content of a status page to scan for update keywords.\n\n"
            "Default keywords checked: resolved, restored, operational, update, rescheduled, back online"
        )
    default_keywords = ["resolved", "restored", "operational", "update", "rescheduled", "back online"]
    found = check_status_text(text, default_keywords)
    lines = ["## Status Sentinel Report", ""]
    lines.append(f"**Text scanned:** {len(text)} characters")
    lines.append(f"**Keywords checked:** {', '.join(default_keywords)}")
    lines.append("")
    if found:
        lines.append(f"**Status keywords found ({len(found)}):**")
        for kw in found:
            lines.append(f"- '{kw}'")
        lines.append("")
        lines.append("An update or resolution may be present in this text.")
    else:
        lines.append("**No status-change keywords found.** The situation may still be ongoing.")
    return "\n".join(lines)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Status Sentinel runs as a live monitor — browser mode uses process() above.
    # For live monitoring, run from terminal with a URL and keywords.
    print("Status Sentinel: browser/Pyodide mode active. Pass page text via USER_INPUT.")