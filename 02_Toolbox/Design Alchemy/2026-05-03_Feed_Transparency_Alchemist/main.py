```python
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

# --- Example Usage (simulating user's reported feed) ---
# Based on the Reddit user's complaint: "29 of them were either ads or posts
# of pages that I don't follow. There were only 6 posts from people I actually follow."
# Total = 35 posts.
simulated_feed_from_complaint = (
    [{'type': 'followed_user'} for _ in range(6)] +
    [{'type': 'ad'} for _ in range(15)] +  # Arbitrary split for non-followed
    [{'type': 'suggested_page'} for _ in range(14)]
)

# Shuffle the simulated feed to represent a mixed experience
random.shuffle(simulated_feed_from_complaint)

# Analyze the feed
feed_analysis_results = analyze_instagram_feed(simulated_feed_from_complaint)

# Print the results to the console
print("--- Feed Analysis Results ---")
print(f"Total Posts Scrolled: {feed_analysis_results['total_posts']}")
print(f"Posts from Followed Users: {feed_analysis_results['followed_posts']}")
print(f"Advertisements: {feed_analysis_results['ads']}")
print(f"Suggested Pages: {feed_analysis_results['suggested_pages']}")
print(f"Percentage of Non-Followed Content (Ads + Suggested): {feed_analysis_results['non_followed_percentage']}%")

# Expected output based on the user's complaint (approximate due to random split of non-followed)
# Total Posts Scrolled: 35
# Posts from Followed Users: 6
# Advertisements: (around 15)
# Suggested Pages: (around 14)
# Percentage of Non-Followed Content (Ads + Suggested): (around 82.86)%
```