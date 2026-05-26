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


def process(text: str) -> str:
    """
    Analyze a reported ad count and session duration.
    Input format: 'ad_count [session_minutes]' e.g. '15 30'
    Falls back to an awareness report if no input.
    """
    parts = text.strip().split()
    nums = []
    for p in parts:
        try:
            nums.append(float(p))
        except ValueError:
            pass

    if len(nums) >= 2:
        ad_count = int(nums[0])
        session_minutes = nums[1]
        total_seconds = session_minutes * 60
    elif len(nums) == 1:
        ad_count = int(nums[0])
        total_seconds = 30 * 60  # assume 30 minutes
        session_minutes = 30
    else:
        # Show awareness tips without specific data
        lines = [
            "Ad-Stream Awareness Tracker",
            "=" * 35,
            "How many ads do you see per session?",
            "",
            "Industry averages suggest:",
            "  - Free social media: 1 ad every 3-5 posts",
            "  - Streaming platforms: 4-10 ads per 30 minutes",
            "  - General browsing: 20-50 ads per hour",
            "",
            "Tips to reduce ad exposure:",
            "  - Use ad-blockers on desktop browsers",
            "  - Consider premium/paid tiers of services you use often",
            "  - Take regular breaks from algorithmically-driven feeds",
            "  - Try the 30-day digital detox challenge",
        ]
        return "\n".join(lines)

    avg_time_between_ads = total_seconds / ad_count if ad_count > 0 else float('inf')
    ads_per_hour = (ad_count / (total_seconds / 3600)) if total_seconds > 0 else 0

    lines = [
        "Ad-Stream Awareness Report",
        "=" * 35,
        f"Session Duration:      {session_minutes:.0f} minutes",
        f"Ads Encountered:       {ad_count}",
        f"Ads per Hour:          {ads_per_hour:.1f}",
    ]

    if ad_count > 0:
        lines.append(f"Avg. time between ads: {avg_time_between_ads:.0f} seconds")

    lines.append("")
    if ads_per_hour > 30:
        lines.append("High ad exposure detected. Consider a digital detox or ad-free alternatives.")
    elif ads_per_hour > 10:
        lines.append("Moderate ad exposure. You're seeing quite a few ads — worth noticing.")
    else:
        lines.append("Relatively low ad exposure this session.")

    return "\n".join(lines)


def _cli_main():
    ad_tracker_session()


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
