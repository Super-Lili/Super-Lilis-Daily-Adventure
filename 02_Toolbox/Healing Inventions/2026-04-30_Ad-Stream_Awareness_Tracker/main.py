import re


def analyze_ad_session(ad_count: int, session_minutes: float) -> str:
    """Analyze ad frequency for a browsing session."""
    total_seconds = session_minutes * 60
    lines = ["## Ad-Stream Awareness Tracker: Session Report", ""]
    lines.append(f"- Session duration: {session_minutes:.1f} minutes")
    lines.append(f"- Ads encountered: {ad_count}")
    if ad_count > 0 and total_seconds > 0:
        avg_secs = total_seconds / ad_count
        lines.append(f"- Average time between ads: {avg_secs:.0f} seconds ({avg_secs/60:.1f} min)")
        ads_per_hour = (ad_count / session_minutes) * 60
        lines.append(f"- Ad rate: ~{ads_per_hour:.0f} ads/hour")
        lines += [""]
        if ads_per_hour > 30:
            lines.append("Heavy ad load. Consider an ad blocker or ad-free subscription.")
        elif ads_per_hour > 15:
            lines.append("Moderate ad load. A digital detox or ad-free mode might help.")
        else:
            lines.append("Relatively light ad load for this session.")
    elif ad_count == 0:
        lines += ["", "No ads logged — great session!"]
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Analyze an ad-tracking session from text description.

    Input format: 'ads=12 minutes=30' or just numbers like '12 ads in 30 minutes'
    """
    if not text.strip():
        return (
            "Paste your session summary to analyze ad frequency.\n\n"
            "Format: ads=12 minutes=30\n"
            "Or just describe it: '12 ads in 30 minutes'"
        )
    ad_count = 0
    session_min = 10.0
    m = re.search(r'ads?\s*[=:]\s*(\d+)', text, re.IGNORECASE)
    if m:
        ad_count = int(m.group(1))
    m = re.search(r'(?:minutes?|mins?)\s*[=:]\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if m:
        session_min = float(m.group(1))
    # fallback: bare numbers
    if not re.search(r'ads?\s*[=:]', text, re.IGNORECASE):
        nums = re.findall(r'\d+(?:\.\d+)?', text)
        if len(nums) >= 2:
            ad_count = int(float(nums[0]))
            session_min = float(nums[1])
        elif len(nums) == 1:
            ad_count = int(float(nums[0]))
    return analyze_ad_session(ad_count, session_min)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(process("ads=18 minutes=20"))