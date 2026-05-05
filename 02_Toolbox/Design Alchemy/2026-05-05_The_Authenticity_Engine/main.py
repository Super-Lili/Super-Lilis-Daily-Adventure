```python
class UserFeed:
    def __init__(self, username):
        self.username = username
        self.explicit_interests = []  # User explicitly defines these
        self.trusted_connections = [] # User explicitly defines these
        self.content_queue = []       # Simulates incoming content

    def add_interest(self, interest):
        """Adds a specific interest to the user's explicit preferences."""
        if interest not in self.explicit_interests:
            self.explicit_interests.append(interest)
            print(f"{self.username} added interest: '{interest}'.")

    def add_trusted_connection(self, connection_id):
        """Adds a trusted connection (e.g., another user ID) to prioritize content from."""
        if connection_id not in self.trusted_connections:
            self.trusted_connections.append(connection_id)
            print(f"{self.username} added trusted connection: '{connection_id}'.")

    def receive_content(self, content_item):
        """Simulates receiving a new piece of content into the general queue."""
        self.content_queue.append(content_item)

    def generate_curated_feed(self):
        """Generates a curated feed prioritizing trusted connections and explicit interests."""
        curated_feed = []

        # 1. Prioritize content from trusted connections
        for content in self.content_queue:
            if content.get('author_id') in self.trusted_connections:
                curated_feed.append(content)

        # 2. Then, prioritize content matching explicit interests (avoiding duplicates)
        for content in self.content_queue:
            if any(interest in content.get('tags', []) for interest in self.explicit_interests) and \
               content not in curated_feed:
                curated_feed.append(content)
        
        # Output the curated feed
        print(f"\n--- {self.username}'s Authenticity Engine Feed (May 5, 2026) ---")
        if not curated_feed:
            print("Your curated feed is empty. Try adding more connections or interests!")
        for item in curated_feed:
            print(f"[{item.get('author_id', 'Unknown')}] - '{item.get('text', 'No content')}' (Tags: {', '.join(item.get('tags', []))})")
        print("--------------------------------------------------")

# Example Usage:
if __name__ == "__main__":
    lili = UserFeed("SuperLili")
    lili.add_interest("AI ethics")
    lili.add_interest("creative activism")
    lili.add_trusted_connection("DigitalNomad_X")
    lili.add_trusted_connection("ArtRebel_Y")

    # Simulate various content pieces flowing into the system
    content_stream = [
        {'author_id': 'DigitalNomad_X', 'text': 'Thought-provoking article on AI bias in image generation.', 'tags': ['AI ethics', 'tech']},
        {'author_id': 'RandomInfluencer', 'text': 'My new morning routine!', 'tags': ['lifestyle', 'wellness']},
        {'author_id': 'ArtRebel_Y', 'text': 'New street art project challenging corporate surveillance.', 'tags': ['creative activism', 'art']},
        {'author_id': 'NewsBot', 'text': 'Breaking news on market fluctuations.', 'tags': ['finance', 'news']},
        {'author_id': 'DigitalNomad_X', 'text': 'Quick update on my latest activism hack.', 'tags': ['creative activism', 'digital rights']},
        {'author_id': 'LocalBakery', 'text': 'Fresh sourdough loaves available!', 'tags': ['food', 'local']},
        {'author_id': 'DataWhiz', 'text': 'Deep dive into privacy concerns with AI models.', 'tags': ['AI ethics', 'data privacy']},
        {'author_id': 'ArtRebel_Y', 'text': 'Behind the scenes of our latest protest installation.', 'tags': ['creative activism', 'social justice']},
    ]

    for item in content_stream:
        lili.receive_content(item)

    lili.generate_curated_feed()
```