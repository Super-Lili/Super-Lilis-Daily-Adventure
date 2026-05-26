class UserFeed:
    def __init__(self, username):
        self.username = username
        self.explicit_interests = []
        self.trusted_connections = []
        self.content_queue = []

    def add_interest(self, interest):
        if interest not in self.explicit_interests:
            self.explicit_interests.append(interest)

    def add_trusted_connection(self, connection_id):
        if connection_id not in self.trusted_connections:
            self.trusted_connections.append(connection_id)

    def receive_content(self, content_item):
        self.content_queue.append(content_item)

    def get_curated_feed(self) -> list:
        curated_feed = []
        for content in self.content_queue:
            if content.get('author_id') in self.trusted_connections:
                curated_feed.append(content)
        for content in self.content_queue:
            if any(interest in content.get('tags', []) for interest in self.explicit_interests) and \
               content not in curated_feed:
                curated_feed.append(content)
        return curated_feed

    def generate_curated_feed(self):
        feed = self.get_curated_feed()
        print(f"\n--- {self.username}'s Authenticity Engine Feed ---")
        if not feed:
            print("Your curated feed is empty. Try adding more connections or interests!")
        for item in feed:
            print(f"[{item.get('author_id', 'Unknown')}] - '{item.get('text', 'No content')}' (Tags: {', '.join(item.get('tags', []))})")
        print("--------------------------------------------------")


def process(text: str = "") -> str:
    """Simulate a user-curated feed. Paste interests/connections or use defaults.

    Format (optional):
      interests: AI ethics, creative activism
      connections: DigitalNomad_X, ArtRebel_Y
    """
    import re
    interests = []
    connections = []
    if text.strip():
        m = re.search(r'interests?:\s*(.+)', text, re.IGNORECASE)
        if m:
            interests = [i.strip() for i in m.group(1).split(',') if i.strip()]
        m = re.search(r'connections?:\s*(.+)', text, re.IGNORECASE)
        if m:
            connections = [c.strip() for c in m.group(1).split(',') if c.strip()]
    if not interests:
        interests = ["AI ethics", "creative activism"]
    if not connections:
        connections = ["DigitalNomad_X", "ArtRebel_Y"]

    feed_obj = UserFeed("You")
    for i in interests:
        feed_obj.add_interest(i)
    for c in connections:
        feed_obj.add_trusted_connection(c)

    content_stream = [
        {'author_id': 'DigitalNomad_X', 'text': 'Thought-provoking article on AI bias in image generation.', 'tags': ['AI ethics', 'tech']},
        {'author_id': 'RandomInfluencer', 'text': 'My new morning routine!', 'tags': ['lifestyle', 'wellness']},
        {'author_id': 'ArtRebel_Y', 'text': 'New street art project challenging corporate surveillance.', 'tags': ['creative activism', 'art']},
        {'author_id': 'NewsBot', 'text': 'Breaking news on market fluctuations.', 'tags': ['finance', 'news']},
        {'author_id': 'DigitalNomad_X', 'text': 'Quick update on my latest activism hack.', 'tags': ['creative activism', 'digital rights']},
        {'author_id': 'DataWhiz', 'text': 'Deep dive into privacy concerns with AI models.', 'tags': ['AI ethics', 'data privacy']},
        {'author_id': 'ArtRebel_Y', 'text': 'Behind the scenes of our latest protest installation.', 'tags': ['creative activism', 'social justice']},
        {'author_id': 'LocalBakery', 'text': 'Fresh sourdough loaves available!', 'tags': ['food', 'local']},
    ]
    for item in content_stream:
        feed_obj.receive_content(item)

    curated = feed_obj.get_curated_feed()
    out = [f"## Authenticity Engine: Your Curated Feed", "",
           f"Interests: {', '.join(interests)}",
           f"Trusted connections: {', '.join(connections)}", "",
           f"Showing {len(curated)} of {len(content_stream)} posts:", ""]
    for item in curated:
        tags = ', '.join(item.get('tags', []))
        out.append(f"- **[{item['author_id']}]** {item['text']}  _(tags: {tags})_")
    if not curated:
        out.append("No matching posts found. Try adding more interests or connections.")
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(process(""))