import unittest
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Import the main functions/classes from the tool's code
# Assuming the tool's code is in a file named 'content_catalyst.py'
# For the purpose of this test, we'll assume the code is accessible directly
# or we would import from a module if it were structured as such.

# To make this self-contained, I'll copy relevant parts for testing directly
# In a real scenario, you'd do:
# from content_catalyst import ContentStrategyGenerator, main as catalyst_main

# --- Start of necessary parts from content_catalyst.py for testing ---
# (Simplified versions where full Rich Console or Argparse isn't strictly needed for file output tests)
class MockConsole:
    """A mock console to prevent Rich output during tests."""
    def print(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        # Allow calling any method on the mock console without error
        return lambda *args, **kwargs: None

class MockArgParseArgs:
    """A mock class to simulate argparse arguments."""
    def __init__(self, business_type, target_audience, main_goal, start_date, output_basename):
        self.business_type = business_type
        self.target_audience = target_audience
        self.main_goal = main_goal
        self.start_date = start_date
        self.output_basename = output_basename

# Re-implementing ContentStrategyGenerator and its core methods for isolated testing
# without requiring the full rich console setup, but preserving logic for file operations.
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class ContentStrategyGeneratorTestable:
    def __init__(self):
        self.console = MockConsole() # Use mock console for testing
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
        business_input_lower = business_input.lower()
        for category, types in self.business_types.items():
            if business_input_lower in category or any(bt.lower() in business_input_lower for bt in types):
                return category
        return "general"

    def _generate_weekly_theme(self, goal: str, business_type: str) -> str:
        themes = {
            "engagement": f"Connecting with Our Community: A Week of Conversations for Your {business_type.title()}!",
            "sales": f"Unlock Your Best: Special Offers & Solutions from Your {business_type.title()}!",
            "awareness": f"Discover the Heart of Your {business_type.title()}: Our Story & Values!",
            "education": f"Mastering [Topic]: Insights from Your {business_type.title()} Experts!",
            "general": f"Bringing Joy to Your Week with Your {business_type.title()}!"
        }
        return themes.get(goal, themes["general"])

    def _get_content_suggestion(self, pillar: str, business_type: str) -> str:
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
                "Business Type": business_type_input # Add for saving consistency
            })
        return plan

    def save_to_markdown(self, plan: List[Dict[str, str]], output_path: Path):
        if not plan: return
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
            f.write("✨ *Remember, this is your starting point! Adapt, personalize, and let your unique magic shine through.* ✨\n")
    
    def save_to_csv(self, plan: List[Dict[str, str]], output_path: Path):
        if not plan: return
        fieldnames = ["Date", "Day", "Pillar", "Content Idea", "Call to Action", "Goal Focus", "Weekly Theme", "Business Type"]
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(plan)
# --- End of necessary parts from content_catalyst.py for testing ---


class TestContentCurrentCatalyst(unittest.TestCase):

    def setUp(self):
        """Set up for each test: create a temporary output directory."""
        self.test_dir = Path("test_content_plans")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.catalyst = ContentStrategyGeneratorTestable()

    def tearDown(self):
        """Clean up after each test: remove the temporary output directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_plan_generation(self):
        """Test if a 7-day plan is correctly generated."""
        business_type = "cafe"
        target_audience = "coffee lovers"
        main_goal = "engagement"
        start_date = "2026-05-13" # Current date
        
        plan = self.catalyst.generate_weekly_plan(business_type, target_audience, main_goal, start_date)
        
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan), 7)
        self.assertIsInstance(plan, list)
        self.assertIsInstance(plan[0], dict)
        self.assertIn("Date", plan[0])
        self.assertIn("Day", plan[0])
        self.assertIn("Pillar", plan[0])
        self.assertIn("Content Idea", plan[0])
        self.assertIn("Call to Action", plan[0])
        self.assertIn("Goal Focus", plan[0])
        self.assertIn("Weekly Theme", plan[0])
        
        # Check dates are sequential
        first_date = datetime.strptime(start_date, "%Y-%m-%d")
        for i, entry in enumerate(plan):
            expected_date = (first_date + timedelta(days=i)).strftime("%Y-%m-%d")
            self.assertEqual(entry["Date"], expected_date)
            self.assertEqual(entry["Goal Focus"].lower(), main_goal)

    def test_markdown_file_output(self):
        """Test if the plan is saved correctly to a Markdown file."""
        business_type = "retail"
        target_audience = "shoppers"
        main_goal = "sales"
        start_date = "2026-05-14"
        output_basename = "test_retail_sales_plan"
        
        plan = self.catalyst.generate_weekly_plan(business_type, target_audience, main_goal, start_date)
        for entry in plan: # Add business type as it's used in save_to_csv/markdown
            entry["Business Type"] = business_type
        
        md_output_path = self.test_dir / f"{output_basename}.md"
        self.catalyst.save_to_markdown(plan, md_output_path)
        
        self.assertTrue(md_output_path.exists())
        with open(md_output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"Weekly Theme:", content)
            self.assertIn(f"Content Current Catalyst:", content)
            self.assertIn(plan[0]["Content Idea"], content)
            self.assertIn(plan[3]["Call to Action"], content)
            self.assertIn("### Monday", content) # Assuming Monday is day 0+1

    def test_csv_file_output(self):
        """Test if the plan is saved correctly to a CSV file."""
        business_type = "service"
        target_audience = "clients"
        main_goal = "awareness"
        start_date = "2026-05-15"
        output_basename = "test_service_awareness_plan"

        plan = self.catalyst.generate_weekly_plan(business_type, target_audience, main_goal, start_date)
        for entry in plan: # Add business type as it's used in save_to_csv/markdown
            entry["Business Type"] = business_type
        
        csv_output_path = self.test_dir / f"{output_basename}.csv"
        self.catalyst.save_to_csv(plan, csv_output_path)
        
        self.assertTrue(csv_output_path.exists())
        with open(csv_output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            self.assertIn("Date", headers)
            self.assertIn("Content Idea", headers)
            self.assertIn("Goal Focus", headers)
            
            rows = list(reader)
            self.assertEqual(len(rows), 7)
            self.assertEqual(rows[0]["Content Idea"], plan[0]["Content Idea"])
            self.assertEqual(rows[2]["Goal Focus"].lower(), main_goal)

    def test_empty_plan_handling(self):
        """Test that saving empty plans doesn't crash and creates no files."""
        empty_plan = []
        md_output_path = self.test_dir / "empty_plan.md"
        csv_output_path = self.test_dir / "empty_plan.csv"

        self.catalyst.save_to_markdown(empty_plan, md_output_path)
        self.catalyst.save_to_csv(empty_plan, csv_output_path)

        self.assertFalse(md_output_path.exists())
        self.assertFalse(csv_output_path.exists())

    def test_business_category_mapping(self):
        """Test if business type input maps correctly to categories."""
        self.assertEqual(self.catalyst._get_business_category("Coffee Shop"), "cafe")
        self.assertEqual(self.catalyst._get_business_category("Yoga Studio"), "wellness")
        self.assertEqual(self.catalyst._get_business_category("boutique"), "retail")
        self.assertEqual(self.catalyst._get_business_category("freelance design"), "service")
        self.assertEqual(self.catalyst._get_business_category("Unknown Business"), "general")


if __name__ == "__main__":
    unittest.main()
