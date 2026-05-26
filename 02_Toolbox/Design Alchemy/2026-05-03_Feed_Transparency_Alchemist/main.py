import random


def analyze_instagram_feed(feed_posts):
    """
    Analyzes a simulated social media feed (e.g., Instagram) to quantify the
    ratio of ads/suggested posts to posts from followed users.

    Args:
        feed_posts (list): A list of dictionaries, where each dictionary
                           represents a post with a 'type' (e.g., 'ad',
                           'followed_user', 'suggested_page').

    Returns:
        dict: A dictionary containing the counts of each post type and
              the percentage of non-followed content.
    """
    counts = {
        'followed_user': 0,
        'ad': 0,
        'suggested_page': 0,
        'total': 0
    }

    for post in feed_posts:
        post_type = post.get('type')
        if post_type in counts:
            counts[post_type] += 1
        counts['total'] += 1

    non_followed_count = counts['ad'] + counts['suggested_page']
    non_followed_percentage = (non_followed_count / counts['total']) * 100 if counts['total'] > 0 else 0

    return {
        'followed_posts': counts['followed_user'],
        'ads': counts['ad'],
        'suggested_pages': counts['suggested_page'],
        'total_posts': counts['total'],
        'non_followed_percentage': round(non_followed_percentage, 2)
    }


def process(text: str) -> str:
    """
    Analyze a feed composition described as 'followed=N ads=M suggested=K' or
    plain counts, e.g. '6 15 14'. Falls back to the canonical Reddit example.
    """
    followed = 6
    ads = 15
    suggested = 14

    parts = text.strip().split()
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            pass
    if len(nums) >= 3:
        followed, ads, suggested = nums[0], nums[1], nums[2]
    elif len(nums) == 2:
        followed, ads, suggested = nums[0], nums[1], 0
    elif len(nums) == 1:
        followed = nums[0]

    feed = (
        [{'type': 'followed_user'} for _ in range(followed)] +
        [{'type': 'ad'} for _ in range(ads)] +
        [{'type': 'suggested_page'} for _ in range(suggested)]
    )
    r = analyze_instagram_feed(feed)

    lines = [
        "Feed Analysis Results",
        "=" * 30,
        f"Total Posts Scrolled:           {r['total_posts']}",
        f"Posts from Followed Users:      {r['followed_posts']}",
        f"Advertisements:                 {r['ads']}",
        f"Suggested Pages:                {r['suggested_pages']}",
        f"Non-Followed Content:           {r['non_followed_percentage']}%",
    ]
    return "\n".join(lines)


def _cli_main():
    # Example usage (simulating user's reported feed)
    # Based on the Reddit user's complaint: "29 of them were either ads or posts
    # of pages that I don't follow. There were only 6 posts from people I actually follow."
    simulated_feed = (
        [{'type': 'followed_user'} for _ in range(6)] +
        [{'type': 'ad'} for _ in range(15)] +
        [{'type': 'suggested_page'} for _ in range(14)]
    )
    random.shuffle(simulated_feed)
    results = analyze_instagram_feed(simulated_feed)

    print("--- Feed Analysis Results ---")
    print(f"Total Posts Scrolled: {results['total_posts']}")
    print(f"Posts from Followed Users: {results['followed_posts']}")
    print(f"Advertisements: {results['ads']}")
    print(f"Suggested Pages: {results['suggested_pages']}")
    print(f"Percentage of Non-Followed Content (Ads + Suggested): {results['non_followed_percentage']}%")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
