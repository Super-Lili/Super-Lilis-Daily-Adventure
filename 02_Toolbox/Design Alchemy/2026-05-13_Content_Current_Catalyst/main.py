import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict, Any, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Requirements:
# rich
# pandas (for more complex data handling if needed, but not strictly for this version)

class ContentStrategyGenerator:
    """
    Generates tailored weekly content strategies and post ideas for small businesses.
    """
    def __init__(self):
        self.console = Console()
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
        return "general" # Fallback

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
        # Simple customization based on business type, could be expanded
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
        
        # Define a consistent structure for content pillars over the week
        # Aim for a mix, prioritizing promotion and engagement while still educating/inspiring.
        # This can be made more sophisticated with content calendars and weightings.
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
                "Business Type": business_type_input # Add business_type_input here
            })
        return plan

    def display_plan(self, plan: List[Dict[str, str]]):
        """Displays the generated content plan using rich."""
        if not plan:
            self.console.print(Panel("[red]No content plan generated.[/red]", title="[bold red]Error[/bold red]"))
            return

        first_day = plan[0]["Date"]
        last_day = plan[-1]["Date"]
        weekly_theme = plan[0]["Weekly Theme"]
        business_type_for_display = self._get_business_category(plan[0].get('Business Type', 'business'))

        self.console.print(Panel(
            Text(f"Hey there, fellow trailblazer! 👋", justify="center", style="bold magenta"),
            Text("\nHere's a little spark for your social media this week!", justify="center", style="italic white"),
            Text(f"\nYour weekly theme, designed just for your awesome {business_type_for_display.title()}:", justify="center", style="bold cyan"),
            Text(f"\n✨ {weekly_theme} ✨", justify="center", style="bold yellow"),
            title=f"[bold green]Content Current Catalyst: Your Weekly Spark! ({first_day} to {last_day})[/bold green]",
            subtitle="[italic grey]Let's get those creative currents flowing![/italic grey]",
            border_style="purple"
        ))

        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Date", style="dim", width=12)
        table.add_column("Day", style="cyan", width=10)
        table.add_column("Pillar", style="magenta", width=12)
        table.add_column("Content Idea", style="green")
        table.add_column("Call to Action", style="yellow")
        table.add_column("Goal", style="orange1", width=8)

        for entry in plan:
            table.add_row(
                entry["Date"],
                entry["Day"],
                entry["Pillar"],
                entry["Content Idea"],
                entry["Call to Action"],
                entry["Goal Focus"]
            )
        self.console.print(table)
        self.console.print(Panel(
            Text("\nRemember, this is your canvas! Adapt, personalize, and let your unique magic shine through. You've got this! ✨", justify="center", style="italic bright_white"),
            border_style="purple"
        ))

    def save_to_markdown(self, plan: List[Dict[str, str]], output_path: Path):
        """Saves the content plan to a Markdown file."""
        if not plan:
            self.console.print(f"[red]No plan to save to {output_path}.[/red]")
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
            f.write("✨ *Remember, this is your starting point! Adapt, personalize, and let your unique magic shine through.* ✨\n")
        
        self.console.print(f"\n[green]Plan saved to Markdown: [bold]{output_path}[/bold][/green]")

    def save_to_csv(self, plan: List[Dict[str, str]], output_path: Path):
        """Saves the content plan to a CSV file."""
        if not plan:
            self.console.print(f"[red]No plan to save to {output_path}.[/red]")
            return

        fieldnames = ["Date", "Day", "Pillar", "Content Idea", "Call to Action", "Goal Focus", "Weekly Theme", "Business Type"]
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(plan)
        
        self.console.print(f"[green]Plan saved to CSV: [bold]{output_path}[/bold][/green]")


def main():
    parser = argparse.ArgumentParser(
        description="🚀 The Content Current Catalyst helps small business owners generate a weekly social media content plan. Say goodbye to creative blocks and hello to consistent, purposeful posting!",
        epilog="✨ Let's make your social media shine! Example: python content_catalyst.py \"local bakery\" \"foodies and families\" \"engagement\" --start-date 2026-05-13 -o my_content_plan"
    )
    parser.add_argument(
        "business_type",
        type=str,
        help="Your business type (e.g., 'cafe', 'boutique', 'consulting', 'handmade jewelry')."
    )
    parser.add_argument(
        "target_audience",
        type=str,
        help="Who are you trying to reach? (e.g., 'young professionals', 'eco-conscious consumers', 'local families')."
    )
    parser.add_argument(
        "main_goal",
        type=str,
        choices=["engagement", "sales", "awareness", "education"],
        help="Your primary goal for the week ('engagement', 'sales', 'awareness', 'education')."
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
        help="Base name for output files (e.g., 'my_brand_plan' will create 'my_brand_plan.md' and 'my_brand_plan.csv')."
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

        md_output_path = output_dir / f"{args.output_basename}.md"
        csv_output_path = output_dir / f"{args.output_basename}.csv"

        catalyst.save_to_markdown(plan, md_output_path)
        catalyst.save_to_csv(plan, csv_output_path)

    except ValueError as e:
        catalyst.console.print(Panel(f"[bold red]Input Error:[/bold red] {e}", title="[bold red]Oops![/bold red]", border_style="red"))
    except Exception as e:
        catalyst.console.print(Panel(f"[bold red]An unexpected error occurred:[/bold red] {e}", title="[bold red]Uh Oh![/bold red]", border_style="red"))

def process(text: str = "") -> str:
    """Generate a weekly social media content plan from business info."""
    if not text.strip():
        return "Paste business info as: business type, target audience, goal (engagement/sales/awareness/education) — one per line or comma-separated."
    from datetime import datetime
    parts = [p.strip() for p in text.replace("\n", ",").split(",") if p.strip()]
    business_type = parts[0] if len(parts) > 0 else "small business"
    target_audience = parts[1] if len(parts) > 1 else "general audience"
    main_goal_raw = parts[2].lower() if len(parts) > 2 else "engagement"
    valid_goals = ["engagement", "sales", "awareness", "education"]
    main_goal = main_goal_raw if main_goal_raw in valid_goals else "engagement"
    start_date = datetime.now().strftime("%Y-%m-%d")
    catalyst = ContentStrategyGenerator()
    plan = catalyst.generate_weekly_plan(business_type, target_audience, main_goal, start_date)
    if not plan:
        return "Could not generate a content plan. Please check your inputs."
    out = [f"# Weekly Content Plan: {plan[0]['Weekly Theme']}", "",
           f"**Business:** {business_type} | **Goal:** {main_goal.capitalize()} | **Audience:** {target_audience}", "",
           "| Date | Day | Pillar | Content Idea | Call to Action |",
           "|---|---|---|---|---|"]
    for entry in plan:
        out.append(f"| {entry['Date']} | {entry['Day']} | {entry['Pillar']} | {entry['Content Idea']} | {entry['Call to Action']} |")
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Demo with realistic sample data
    # This block ensures the tool runs end-to-end with sample data,
    # demonstrating its full functionality and producing output files.

    # 1. Clean up old demo outputs if they exist
    demo_output_dir = Path("./content_plans_demo")
    if demo_output_dir.exists():
        import shutil
        shutil.rmtree(demo_output_dir)
    demo_output_dir.mkdir(parents=True, exist_ok=True)

    console = Console()
    console.print(Panel("[bold yellow]Running Content Current Catalyst Demo...[/bold yellow]", border_style="yellow"))

    # Simulate command-line arguments
    class MockArgs:
        def __init__(self, business_type, target_audience, main_goal, start_date, output_basename):
            self.business_type = business_type
            self.target_audience = target_audience
            self.main_goal = main_goal
            self.start_date = start_date
            self.output_basename = output_basename

    # Demo 1: Cafe, focused on engagement
    demo_args_1 = MockArgs(
        business_type="cafe",
        target_audience="local coffee lovers",
        main_goal="engagement",
        start_date="2026-05-13", # Today's date
        output_basename="demo_cafe_engagement"
    )
    console.print(f"\n[bold magenta]--- Demo 1: {demo_args_1.business_type.title()} for {demo_args_1.main_goal.capitalize()} ---[/bold magenta]")
    catalyst_demo_1 = ContentStrategyGenerator()
    try:
        plan_1 = catalyst_demo_1.generate_weekly_plan(
            demo_args_1.business_type,
            demo_args_1.target_audience,
            demo_args_1.main_goal,
            demo_args_1.start_date
        )
        
        catalyst_demo_1.display_plan(plan_1)
        catalyst_demo_1.save_to_markdown(plan_1, demo_output_dir / f"{demo_args_1.output_basename}.md")
        catalyst_demo_1.save_to_csv(plan_1, demo_output_dir / f"{demo_args_1.output_basename}.csv")
    except Exception as e:
        console.print(Panel(f"[bold red]Demo 1 failed:[/bold red] {e}", border_style="red"))

    # Demo 2: Consulting service, focused on sales
    next_week_start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    demo_args_2 = MockArgs(
        business_type="consulting",
        target_audience="small business owners",
        main_goal="sales",
        start_date=next_week_start,
        output_basename="demo_consulting_sales"
    )
    console.print(f"\n[bold magenta]--- Demo 2: {demo_args_2.business_type.title()} for {demo_args_2.main_goal.capitalize()} ---[/bold magenta]")
    catalyst_demo_2 = ContentStrategyGenerator()
    try:
        plan_2 = catalyst_demo_2.generate_weekly_plan(
            demo_args_2.business_type,
            demo_args_2.target_audience,
            demo_args_2.main_goal,
            demo_args_2.start_date
        )
        catalyst_demo_2.display_plan(plan_2)
        catalyst_demo_2.save_to_markdown(plan_2, demo_output_dir / f"{demo_args_2.output_basename}.md")
        catalyst_demo_2.save_to_csv(plan_2, demo_output_dir / f"{demo_args_2.output_basename}.csv")
    except Exception as e:
        console.print(Panel(f"[bold red]Demo 2 failed:[/bold red] {e}", border_style="red"))

    console.print(Panel(f"[bold green]Content Current Catalyst Demo Complete![/bold green]\n"
                        f"Check the '[bold yellow]{demo_output_dir}[/bold yellow]' folder for generated files.",
                        border_style="green"))
