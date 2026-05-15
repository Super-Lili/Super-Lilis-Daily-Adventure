# requirements.txt
# rich>=13.0.0

import argparse
import json
from datetime import datetime
import time
import os
from rich.console import Console
from rich.text import Text
import csv # Added csv module for logging

# Initialize Rich Console for pretty output
console = Console()

def load_config(config_path: str) -> dict:
    """Loads activity configurations from a JSON file."""
    if not os.path.exists(config_path):
        console.print(f"[bold red]Error:[/bold red] Configuration file not found at '{config_path}'")
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not isinstance(config, dict) or not all(isinstance(v, str) for v in config.values()):
            console.print("[bold red]Error:[/bold red] Invalid configuration format. Expected a dictionary of activity_name: intention_string.")
            raise ValueError("Invalid config format")
        
        return config
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON format in '{config_path}'. Please check your file.")
        raise ValueError("Invalid JSON format")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not load configuration: {e}")
        raise

def start_mindful_moment(activity_name: str, intention: str, duration_minutes: int | None) -> str:
    """
    Guides the user through a mindful digital moment: sets intention, waits, prompts reflection.
    Returns the user's reflection text.
    """
    console.print(Text(f"\n✨ Starting your Mindful Digital Moment for: [bold yellow]{activity_name}[/bold yellow] ✨", justify="center"))
    console.print(f"\n[italic blue]Your Intention:[/italic blue] {intention}")
    console.print(Text("\nTake a deep breath. Center yourself. When you're ready, proceed with your activity.", justify="center"))
    
    if duration_minutes:
        console.print(f"[bold green]This moment will last approximately {duration_minutes} minutes.[/bold green]")
        console.print("\nPress [bold cyan]Enter[/bold cyan] to start the timer and begin your activity...")
        console.input() # Wait for user to start
        start_time_display = datetime.now()
        console.print(f"\n[italic]Timer started at {start_time_display.strftime('%H:%M:%S')} for {duration_minutes} minutes...[/italic]")
        time.sleep(duration_minutes * 60)
        console.print("\n[bold green]Time's up![/bold green] Please wrap up your activity.")
    else:
        console.print("\nPress [bold cyan]Enter[/bold cyan] when you are ready to begin your activity. Take your time!")
        console.input() # Wait for user to indicate they're starting
        console.print("\n[italic]Activity in progress...[/italic]")
        console.print("\nPress [bold cyan]Enter[/bold cyan] when you have completed your activity and are ready to reflect.")
        console.input() # Wait for user to indicate completion

    console.print(Text("\n--- REFLECTION TIME ---", justify="center", style="bold magenta"))
    console.print(f"\nHow did that feel? Did you stick to your intention for '[bold yellow]{activity_name}[/bold yellow]'?")
    console.print("What did you notice about your attention, your mood, or the content?")
    reflection = console.input("[bold cyan]Your reflection (press Enter when done):[/bold cyan] ")
    return reflection

def log_reflection(output_path: str, activity: str, intention: str, 
                   start_time: datetime, end_time: datetime, reflection_text: str):
    """Appends a new reflection entry to the CSV log file."""
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir: # Only create if path is not just a filename
        os.makedirs(output_dir, exist_ok=True)

    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(output_path)
    
    # Define the headers explicitly
    fieldnames = [
        'timestamp', 
        'activity', 
        'intention', 
        'start_time', 
        'end_time', 
        'duration_seconds', 
        'reflection'
    ]

    new_entry = {
        'timestamp': datetime.now().isoformat(),
        'activity': activity,
        'intention': intention,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_seconds': (end_time - start_time).total_seconds(),
        'reflection': reflection_text
    }
    
    try:
        with open(output_path, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader() # Write header only if file is new
            
            writer.writerow(new_entry)
        
        console.print(f"\n[bold green]Reflection logged successfully to '{output_path}'![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not write to log file '{output_path}': {e}")
        raise

def main(args=None):
    """Main function to parse arguments and orchestrate the tool."""
    parser = argparse.ArgumentParser(
        description="Help you cultivate presence by setting intentions for digital activities "
                    "and reflecting afterwards. Reclaim your attention, one mindful moment at a time!",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--config', 
        type=str, 
        required=True,
        help="Path to a JSON configuration file defining your digital activities and their intentions.\n"
             "Example content:\n"
             "{\n"
             "  \"Check Instagram\": \"Connect with close friends, avoid endless scrolling\",\n"
             "  \"Read News\": \"Understand today's top headlines, avoid doomscrolling\",\n"
             "  \"Answer Emails\": \"Process urgent messages, clear inbox for deep work\"\n"
             "}"
    )
    parser.add_argument(
        '--activity', 
        type=str, 
        required=True,
        help="The specific digital activity you want to engage with mindfully.\n"
             "Must match a key in your config file (e.g., 'Check Instagram')."
    )
    parser.add_argument(
        '--duration', 
        type=int, 
        default=None,
        help="Optional: The approximate duration (in minutes) for this mindful activity.\n"
             "The tool will prompt you to reflect after this time.\n"
             "If not provided, the tool waits for you to indicate completion."
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default="mindful_moments_log.csv",
        help="Path to the CSV file where your mindful moments will be logged."
    )

    if args is None:
        parsed_args = parser.parse_args()
    else:
        parsed_args = parser.parse_args(args)

    try:
        config = load_config(parsed_args.config)
    except (FileNotFoundError, ValueError):
        # Error message already printed by load_config
        return

    activity_name = parsed_args.activity
    if activity_name not in config:
        console.print(f"[bold red]Error:[/bold red] Activity '[bold yellow]{activity_name}[/bold yellow]' not found in your configuration file.")
        console.print(f"Available activities are: {', '.join(config.keys())}")
        return

    intention = config[activity_name]
    
    start_time = datetime.now()
    try:
        reflection_text = start_mindful_moment(activity_name, intention, parsed_args.duration)
    except KeyboardInterrupt:
        console.print("\n[bold red]Mindful moment interrupted.[/bold red] No reflection logged.")
        return
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during the mindful moment:[/bold red] {e}")
        return
    end_time = datetime.now()

    try:
        log_reflection(parsed_args.output, activity_name, intention, start_time, end_time, reflection_text)
    except Exception:
        # Error message already printed by log_reflection
        return

if __name__ == "__main__":
    demo_config_path = "demo_presence_weaver_config.json"
    demo_output_path = "demo_mindful_moments.csv"

    # Create a demo configuration file
    demo_config_content = {
        "Check Instagram": "Connect with close friends, avoid endless scrolling and comparison traps.",
        "Read News": "Understand today's top headlines, focus on facts, avoid emotional reactivity.",
        "Answer Emails": "Process urgent messages, maintain professional boundaries, clear inbox for deep work.",
        "Browse LinkedIn": "Network constructively, learn from industry insights, avoid 'availability performance'."
    }
    try:
        with open(demo_config_path, 'w', encoding='utf-8') as f:
            json.dump(demo_config_content, f, indent=2, ensure_ascii=False)
        console.print(f"[green]Demo configuration created at:[/green] {demo_config_path}")
    except Exception as e:
        console.print(f"[bold red]Error creating demo config:[/bold red] {e}")
        exit(1)

    # Ensure a fresh or empty demo log file
    if os.path.exists(demo_output_path):
        os.remove(demo_output_path)
    console.print(f"[green]Ensured fresh demo log file at:[/green] {demo_output_path}")

    # Simulate running the tool with demo data for a short duration
    console.print("\n[bold cyan]--- Running Presence Weaver Demo (Instagram, 1 minute) ---[/bold cyan]")
    # For automated demo, we need to mock console.input.
    # In a real user scenario, they would press Enter.
    # Here, we'll run main directly, assuming the console.input for `Enter` to start/finish
    # and the reflection input will be handled manually by the environment running this demo.
    # For CI/CD or automated testing, these inputs would be patched.
    
    console.print("\n[italic]The following demo will ask for input twice. Press ENTER to proceed, then type a short reflection.[/italic]")
    try:
        main([
            "--config", demo_config_path, 
            "--activity", "Check Instagram", 
            "--duration", "1", # 1 minute for demo
            "--output", demo_output_path
        ])
    except KeyboardInterrupt:
        console.print("\n[red]Demo interrupted by user (Ctrl+C).[/red]")
    except Exception as e:
        console.print(f"\n[red]An error occurred during Instagram demo: {e}[/red]")

    console.print("\n[bold cyan]--- Running Presence Weaver Demo (Read News, no duration) ---[/bold cyan]")
    console.print("\n[italic]This demo will also ask for input twice. Press ENTER to start, ENTER to finish, then type a reflection.[/italic]")
    try:
        main([
            "--config", demo_config_path, 
            "--activity", "Read News", 
            "--output", demo_output_path
        ])
    except KeyboardInterrupt:
        console.print("\n[red]Demo interrupted by user (Ctrl+C).[/red]")
    except Exception as e:
        console.print(f"\n[red]An error occurred during News demo: {e}[/red]")
    
    console.print(f"\n[bold green]Demo finished. Check '{demo_output_path}' for your logged mindful moments and '{demo_config_path}' for the configuration.[/bold green]")

    # It's good practice to leave demo files for the user to inspect.
    # If this were part of an automated testing suite, cleanup would happen here.