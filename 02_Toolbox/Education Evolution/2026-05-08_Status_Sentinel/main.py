```python
import requests
import time
from bs4 import BeautifulSoup
import winsound # For Windows-specific sound notification

def check_status(url, keywords, interval_seconds=300):
    """
    Monitors a given URL for specific keywords, indicating a status change.
    Sends a notification if keywords are found.
    """
    print(f"Monitoring {url} for updates (checking every {interval_seconds} seconds)...")
    last_known_status = ""
    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract relevant text - e.g., from paragraphs, div with status info
            page_text = soup.get_text().lower()
            
            current_status = ""
            for keyword in keywords:
                if keyword.lower() in page_text:
                    current_status += f"'{keyword}' found. "
            
            if current_status and current_status != last_known_status:
                print(f"\n--- IMPORTANT UPDATE DETECTED! ---")
                print(f"Keywords found: {current_status}")
                print(f"Check the status page: {url}")
                winsound.Beep(1000, 2000) # Beep for 2 seconds (Windows only)
                last_known_status = current_status
            elif not current_status and last_known_status:
                print(f"\n--- STATUS CLEARED OR KEYWORDS NO LONGER PRESENT! ---")
                print(f"Check the status page: {url}")
                winsound.Beep(800, 1000)
                last_known_status = ""
            elif not current_status and not last_known_status:
                print(f"No specified keywords found. Still waiting for updates. Last checked: {time.ctime()}")
            else:
                print(f"Status unchanged. Last checked: {time.ctime()}")

        except requests.exceptions.RequestException as e:
            print(f"Error accessing {url}: {e}. Retrying...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Example usage for the Canvas outage page
    canvas_status_url = "https://www.utsa.edu/today/2026/05/story/canvas-disruption.html" #
    
    # Keywords to look for indicating resolution or significant updates
    # These would need to be adapted based on expected update language.
    important_keywords = ["resolved", "restored", "operational", "update", "rescheduled", "back online"] 
    
    # Check every 5 minutes (300 seconds)
    check_status(canvas_status_url, important_keywords, interval_seconds=300)
```