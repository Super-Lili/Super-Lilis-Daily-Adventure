```python
import time

def ad_tracker_session():
    """
    Simulates a browsing session, allowing the user to log perceived ad interruptions.
    Calculates ad frequency and suggests a digital detox.
    """
    print("--- Ad-Stream Awareness Tracker Initiated ---")
    print("Press 'a' (then Enter) each time you encounter an ad.")
    print("Type 'q' (then Enter) to quit and see your session summary.")
    print("-" * 40)

    ad_count = 0
    total_time_seconds = 0
    start_time = time.time()
    ad_timestamps = []

    while True:
        user_input = input("Action (a/q): ").lower().strip()
        
        if user_input == 'a':
            ad_count += 1
            current_ad_time = time.time() - start_time
            ad_timestamps.append(current_ad_time)
            print(f"Ad logged! Total ads: {ad_count}")
        elif user_input == 'q':
            break
        else:
            print("Invalid input. Please enter 'a' or 'q'.")
    
    end_time = time.time()
    total_time_seconds = end_time - start_time

    print("\n--- Session Summary ---")
    print(f"Session Duration: {total_time_seconds:.2f} seconds")
    print(f"Total Ads Encountered: {ad_count}")

    if ad_count > 0 and total_time_seconds > 0:
        avg_time_per_ad = total_time_seconds / ad_count
        print(f"Average time between ads: {avg_time_per_ad:.2f} seconds")
        print("\nConsider a digital detox or exploring ad-free alternatives.")
    elif ad_count == 0 and total_time_seconds > 0:
        print("Great session! No ads logged.")
    else:
        print("No activity recorded.")

    print("------------------------")

if __name__ == "__main__":
    ad_tracker_session()
```