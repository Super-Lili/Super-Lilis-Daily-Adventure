import re


def analyze_instagram_feed(feed_posts: list) -> dict:
    """Analyze a list of post dicts with 'type' keys."""
    counts = {'followed_user': 0, 'ad': 0, 'suggested_page': 0, 'total': 0}
    for post in feed_posts:
        post_type = post.get('type')
        if post_type in counts:
            counts[post_type] += 1
        counts['total'] += 1
    non_followed = counts['ad'] + counts['suggested_page']
    non_pct = (non_followed / counts['total'] * 100) if counts['total'] > 0 else 0
    return {
        'followed_posts': counts['followed_user'],
        'ads': counts['ad'],
        'suggested_pages': counts['suggested_page'],
        'total_posts': counts['total'],
        'non_followed_percentage': round(non_pct, 2)
    }


def format_feed_report(r: dict) -> str:
    total = r['total_posts']
    followed = r['followed_posts']
    ads = r['ads']
    suggested = r['suggested_pages']
    pct = r['non_followed_percentage']
    followed_pct = round(followed / total * 100, 1) if total else 0
    lines = [
        "## Feed Transparency Alchemist Report",
        "",
        f"| Type | Count | % of feed |",
        "|---|---|---|",
        f"| Followed user posts | {followed} | {followed_pct}% |",
        f"| Advertisements | {ads} | {round(ads/total*100,1) if total else 0}% |",
        f"| Suggested pages | {suggested} | {round(suggested/total*100,1) if total else 0}% |",
        f"| **Total** | **{total}** | 100% |",
        "",
        f"**Non-followed content (ads + suggested): {pct}%**",
    ]
    if pct > 60:
        lines.append("Your feed is dominated by non-followed content. Consider curating your follows or using a chronological feed mode.")
    elif pct > 30:
        lines.append("A significant portion of your feed is ads or suggested content.")
    else:
        lines.append("Your feed is mostly from people you follow. Healthy ratio!")
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Analyze feed composition from counts or auto-use example data.

    Input format (optional): 'followed=6 ads=15 suggested=14'
    Or just paste the text and defaults will parse what's there.
    """
    followed = ads = suggested = None
    if text.strip():
        m = re.search(r'followed\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            followed = int(m.group(1))
        m = re.search(r'ads?\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            ads = int(m.group(1))
        m = re.search(r'suggested\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            suggested = int(m.group(1))
        # Try bare numbers: e.g. "6 15 14"
        if followed is None:
            nums = re.findall(r'\d+', text)
            if len(nums) >= 3:
                followed, ads, suggested = int(nums[0]), int(nums[1]), int(nums[2])
    if followed is None:
        followed, ads, suggested = 6, 15, 14
    posts = (
        [{'type': 'followed_user'}] * followed +
        [{'type': 'ad'}] * ads +
        [{'type': 'suggested_page'}] * suggested
    )
    result = analyze_instagram_feed(posts)
    return format_feed_report(result)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(process("followed=6 ads=15 suggested=14"))