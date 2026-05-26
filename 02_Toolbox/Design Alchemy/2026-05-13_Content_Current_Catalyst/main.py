import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict, Any, Tuple


class ContentStrategyGenerator:
    """
    Generates tailored weekly content strategies and post ideas for small businesses.
    """
    def __init__(self):
        self.business_types = {
            "cafe": ["Coffee Shop", "Bakery", "Smoothie Bar"],
            "retail": ["Boutique", "Bookstore", "Gift Shop", "Clothing Store"],
            "service": ["Consulting", "Coaching", "Freelance Design", "Pet Grooming", "Fitness Instructor"],
            "craft": ["Handmade Jewelry", "Pottery", "Art Prints", "Custom Goods"],
            "food": ["Restaurant", "Catering", "Food Truck", "Specialty Foods"],
            "wellness": ["Yoga Studio", "Therapy Practice", "Spa", "Holistic Health"],
        }
        self.goals = {
            "engagement": ["Spark conversations", "Build community", "Increase comments/shares"],
            "sales": ["Drive product/service inquiries", "Boost website traffic", "Generate leads"],
            "awareness": ["Expand reach", "Introduce brand values", "Attract new followers"],
            "education": ["Share expertise", "Provide value", "Position as authority"],
        }
        self.content_pillars = {
            "Inspire": ["Inspirational Quote", "Success Story", "Behind-the-scenes glimpse", "Customer Spotlight"],
            "Educate": ["Tip/Trick", "How-to Guide", "Myth vs. Fact", "Industry Insight", "Process walkthrough"],
            "Promote": ["Product/Service Showcase", "Limited-time Offer", "Customer Testimonial", "Event Announcement", "New Arrival"],
            "Engage": ["Question of the Day", "Poll/Quiz", "Fill-in-the-blank", "This or That", "Community Shout-out"],
            "Entertain": ["Funny Moment", "Relatable Meme", "Lighthearted Story", "Behind-the-scenes blooper"],
        }
        self.action_types = {
            "engagement": "Ask a question, prompt a share, encourage comments.",
            "sales": "Direct link in bio, DM for details, visit website, call to action button.",
            "awareness": "Tag a friend, share this post, visit profile.",
            "education": "Save this post, visit our blog, link to resource in bio.",
        }

    def _get_business_category(self, business_input: str) -> str:
        """Categorizes user's business type based on input."""
        business_input_lower = business_input.lower()
        for category, types in self.business_types.items():
            if business_input_lower in category or any(bt.lower() in business_input_lower for bt in types):
                return category
        return "general"

    def _generate_weekly_theme(self, goal: str, business_type: str) -> str:
        """Generates a high-level theme for the week."""
        themes = {
            "engagement": f"Connecting with Our Community: A Week of Conversations for Your {business_type.title()}!",
            "sales": f"Unlock Your Best: Special Offers & Solutions from Your {business_type.title()}!",
            "awareness": f"Discover the Heart of Your {business_type.title()}: Our Story & Values!",
            "education": f"Mastering [Topic]: Insights from Your {business_type.title()} Experts!",
            "general": f"Bringing Joy to Your Week with Your {business_type.title()}!"
        }
        return themes.get(goal, themes["general"])

    def _get_content_suggestion(self, pillar: str, business_type: str) -> str:
        """Provides a specific content idea based on a pillar and business type."""
        if business_type == "cafe":
            if pillar == "Promote": return random.choice(["New seasonal drink showcase", "Pastry of the day highlight", "Loyalty program reminder"])
            if pillar == "Educate": return random.choice(["How coffee beans are sourced", "The art of latte foam", "Health benefits of tea"])
            if pillar == "Engage": return random.choice(["Your favorite coffee order?", "Coffee vs. Tea: What's your pick?", "Best spot to enjoy your drink?"])
        if business_type == "retail":
            if pillar == "Promote": return random.choice(["New collection drop", "Weekend sale announcement", "Gift guide for [occasion]"])
            if pillar == "Educate": return random.choice(["How to style [product]", "Behind the brand: [designer]", "Care tips for [material]"])
            if pillar == "Engage": return random.choice(["What's on your wishlist?", "Pick your favorite look!", "Your go-to outfit?"])
        if business_type == "service":
            if pillar == "Promote": return random.choice(["Client success story", "Limited-time service package", "Book a free consultation"])
            if pillar == "Educate": return random.choice(["3 tips for [problem]", "Common misconceptions about [service]", "What to expect from [service]"])
            if pillar == "Engage": return random.choice(["Your biggest challenge with [problem]?", "What service could make your life easier?", "Ask me anything about [topic]!"])

        return random.choice(self.content_pillars.get(pillar, ["General post idea"]))

    def generate_weekly_plan(self, business_type_input: str, target_audience: str, main_goal: str, start_date_str: str) -> List[Dict[str, str]]:
        """Generates a detailed 7-day content plan."""
        business_category = self._get_business_category(business_type_input)
        weekly_theme = self._generate_weekly_theme(main_goal, business_category)

        daily_pillars = [
            "Promote", "Educate", "Engage", "Inspire", "Promote", "Educate", "Engage"
        ]

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        plan = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day_of_week = current_date.strftime("%A")

            pillar = daily_pillars[i]
            content_idea = self._get_content_suggestion(pillar, business_category)
            call_to_action = self.action_types.get(main_goal, "Tell us what you think!")

            plan.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Day": day_of_week,
                "Pillar": pillar,
                "Content Idea": content_idea,
                "Call to Action": call_to_action,
                "Goal Focus": main_goal.capitalize(),
                "Weekly Theme": weekly_theme,
                "Business Type": business_type_input
            })
        return plan

    def format_plan_text(self, plan: List[Dict[str, str]]) -> str:
        """Formats the content plan as plain text."""
        if not plan:
            return "No content plan generated."

        first_day = plan[0]["Date"]
        last_day = plan[-1]["Date"]
        weekly_theme = plan[0]["Weekly Theme"]
        business_category = self._get_business_category(plan[0].get('Business Type', 'business'))

        lines = []
        lines.append(f"Content Current Catalyst: Your Weekly Spark! ({first_day} to {last_day})")
        lines.append("=" * 60)
        lines.append(f"Business: {business_category.title()}")
        lines.append(f"Weekly Theme: {weekly_theme}")
        lines.append("")
        lines.append(f"{'Date':<12} {'Day':<10} {'Pillar':<12} {'Content Idea':<35} {'Goal':<10}")
        lines.append("-" * 85)

        for entry in plan:
            lines.append(
                f"{entry['Date']:<12} {entry['Day']:<10} {entry['Pillar']:<12} "
                f"{entry['Content Idea'][:34]:<35} {entry['Goal Focus']:<10}"
            )

        lines.append("")
        lines.append("Remember, this is your canvas! Adapt, personalize, and let your unique magic shine through.")
        return "\n".join(lines)

    def display_plan(self, plan: List[Dict[str, str]]):
        """Displays the generated content plan to stdout."""
        print(self.format_plan_text(plan))

    def save_to_markdown(self, plan: List[Dict[str, str]], output_path: Path):
        """Saves the content plan to a Markdown file."""
        if not plan:
            print(f"No plan to save to {output_path}.")
            return

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Content Current Catalyst: Your Weekly Spark! ({plan[0]['Date']} to {plan[-1]['Date']})\n\n")
            f.write(f"## Weekly Theme: {plan[0]['Weekly Theme']}\n\n")
            f.write("--- \n\n")

            for entry in plan:
                f.write(f"### {entry['Day']}, {entry['Date']}\n")
                f.write(f"- **Focus Pillar:** {entry['Pillar']}\n")
                f.write(f"- **Content Idea:** {entry['Content Idea']}\n")
                f.write(f"- **Call to Action:** {entry['Call to Action']}\n")
                f.write(f"- **Primary Goal:** {entry['Goal Focus']}\n\n")
            f.write("---\n\n")
            f.write("*Remember, this is your starting point! Adapt, personalize, and let your unique magic shine through.*\n")

        print(f"\nPlan saved to Markdown: {output_path}")

    def save_to_csv(self, plan: List[Dict[str, str]], output_path: Path):
        """Saves the content plan to a CSV file."""
        if not plan:
            print(f"No plan to save to {output_path}.")
            return

        fieldnames = ["Date", "Day", "Pillar", "Content Idea", "Call to Action", "Goal Focus", "Weekly Theme", "Business Type"]
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(plan)

        print(f"Plan saved to CSV: {output_path}")


def process(text: str) -> str:
    """
    Generate a 7-day content plan.
    Input: 'business_type goal' e.g. 'cafe engagement' or 'consulting sales'.
    Falls back to cafe/engagement demo if no input.
    """
    catalyst = ContentStrategyGenerator()
    parts = text.strip().split()
    business_type = parts[0] if len(parts) >= 1 else "cafe"
    goal = parts[1] if len(parts) >= 2 else "engagement"
    valid_goals = ["engagement", "sales", "awareness", "education"]
    if goal not in valid_goals:
        goal = "engagement"

    plan = catalyst.generate_weekly_plan(
        business_type,
        "local customers",
        goal,
        datetime.now().strftime("%Y-%m-%d")
    )
    return catalyst.format_plan_text(plan)


def _cli_main():
    parser = argparse.ArgumentParser(
        description="The Content Current Catalyst helps small business owners generate a weekly social media content plan.",
        epilog="Example: python main.py \"local bakery\" \"foodies and families\" \"engagement\" --start-date 2026-05-13 -o my_content_plan"
    )
    parser.add_argument(
        "business_type",
        type=str,
        help="Your business type (e.g., 'cafe', 'boutique', 'consulting', 'handmade jewelry')."
    )
    parser.add_argument(
        "target_audience",
        type=str,
        help="Who are you trying to reach? (e.g., 'young professionals', 'eco-conscious consumers')."
    )
    parser.add_argument(
        "main_goal",
        type=str,
        choices=["engagement", "sales", "awareness", "education"],
        help="Your primary goal for the week."
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="The start date for your content plan in YYYY-MM-DD format (defaults to today)."
    )
    parser.add_argument(
        "-o", "--output-basename",
        type=str,
        default="social_media_plan",
        help="Base name for output files."
    )

    args = parser.parse_args()
    catalyst = ContentStrategyGenerator()

    try:
        plan = catalyst.generate_weekly_plan(
            args.business_type,
            args.target_audience,
            args.main_goal,
            args.start_date
        )

        catalyst.display_plan(plan)

        output_dir = Path("./content_plans")
        output_dir.mkdir(parents=True, exist_ok=True)

        catalyst.save_to_markdown(plan, output_dir / f"{args.output_basename}.md")
        catalyst.save_to_csv(plan, output_dir / f"{args.output_basename}.csv")

    except ValueError as e:
        print(f"Input Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Demo with realistic sample data
    demo_output_dir = Path("./content_plans_demo")
    import shutil
    if demo_output_dir.exists():
        shutil.rmtree(demo_output_dir)
    demo_output_dir.mkdir(parents=True, exist_ok=True)

    print("Running Content Current Catalyst Demo...")

    catalyst_demo_1 = ContentStrategyGenerator()
    plan_1 = catalyst_demo_1.generate_weekly_plan("cafe", "local coffee lovers", "engagement", "2026-05-13")
    catalyst_demo_1.display_plan(plan_1)
    catalyst_demo_1.save_to_markdown(plan_1, demo_output_dir / "demo_cafe_engagement.md")
    catalyst_demo_1.save_to_csv(plan_1, demo_output_dir / "demo_cafe_engagement.csv")

    next_week_start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    catalyst_demo_2 = ContentStrategyGenerator()
    plan_2 = catalyst_demo_2.generate_weekly_plan("consulting", "small business owners", "sales", next_week_start)
    catalyst_demo_2.display_plan(plan_2)
    catalyst_demo_2.save_to_markdown(plan_2, demo_output_dir / "demo_consulting_sales.md")
    catalyst_demo_2.save_to_csv(plan_2, demo_output_dir / "demo_consulting_sales.csv")

    print(f"\nContent Current Catalyst Demo Complete! Check the '{demo_output_dir}' folder.")
