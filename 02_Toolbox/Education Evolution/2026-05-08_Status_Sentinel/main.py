import time


def check_status_once(url, keywords):
    """
    Performs a single check of a URL for specified keywords.
    Returns a status summary string. Requires 'requests' library.
    """
    try:
        import urllib.request
        import html.parser

        class TextExtractor(html.parser.HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style'):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ('script', 'style'):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    self.text_parts.append(data)

        with urllib.request.urlopen(url, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='ignore')

        extractor = TextExtractor()
        extractor.feed(html_content)
        page_text = ' '.join(extractor.text_parts).lower()

        found = [kw for kw in keywords if kw.lower() in page_text]
        if found:
            return f"Keywords found on {url}: {', '.join(found)}"
        else:
            return f"No specified keywords found on {url}. Still waiting for updates."
    except Exception as e:
        return f"Error accessing {url}: {e}"


def check_status(url, keywords, interval_seconds=300):
    """
    Monitors a given URL for specific keywords, indicating a status change.
    Runs in a loop — press Ctrl+C to stop.
    """
    print(f"Monitoring {url} for updates (checking every {interval_seconds} seconds)...")
    print("Press Ctrl+C to stop.")
    last_known_status = ""
    while True:
        result = check_status_once(url, keywords)
        if result != last_known_status:
            print(f"\n--- STATUS UPDATE: {time.ctime()} ---")
            print(result)
            last_known_status = result
        else:
            print(f"Status unchanged. Last checked: {time.ctime()}")
        time.sleep(interval_seconds)


def process(text: str) -> str:
    """
    Check a URL once for keywords.
    Input format: 'url keyword1 keyword2 ...'
    Falls back to a demo Canvas outage check if no input.
    """
    parts = text.strip().split()
    if len(parts) >= 2:
        url = parts[0]
        keywords = parts[1:]
    elif len(parts) == 1:
        url = parts[0]
        keywords = ["resolved", "restored", "operational", "update"]
    else:
        url = "https://www.utsa.edu/today/2026/05/story/canvas-disruption.html"
        keywords = ["resolved", "restored", "operational", "update", "rescheduled", "back online"]

    return check_status_once(url, keywords)


def _cli_main():
    # Example usage for the Canvas outage page
    canvas_status_url = "https://www.utsa.edu/today/2026/05/story/canvas-disruption.html"
    important_keywords = ["resolved", "restored", "operational", "update", "rescheduled", "back online"]
    check_status(canvas_status_url, important_keywords, interval_seconds=300)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
