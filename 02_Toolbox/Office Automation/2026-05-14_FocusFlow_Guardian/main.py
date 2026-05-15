# requirements: pandas, python-dateutil
import argparse
import pandas as pd
from datetime import datetime, timedelta, time
from dateutil.parser import parse
from pathlib import Path
import csv

def parse_time_flexible(time_str):
    """Parses a time string, handling common formats."""
    try:
        return parse(time_str).time()
    except ValueError:
        raise ValueError(f"Could not parse time: {time_str}. Please use HH:MM format.")

def calculate_overlap(start1, end1, start2, end2):
    """Calculates the overlap in minutes between two time intervals."""
    if start1 >= end1 or start2 >= end2:
        return 0 # Invalid intervals

    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)

    if latest_start < earliest_end:
        return (earliest_end - latest_start).total_seconds() / 60
    return 0

def find_available_slots(day_meetings, day_start_time, day_end_time, min_block_minutes):
    """Identifies available time slots in a day, given a list of meetings."""
    
    if not isinstance(day_start_time, time) or not isinstance(day_end_time, time):
        raise TypeError("day_start_time and day_end_time must be datetime.time objects.")

    # Convert meetings to datetime objects for accurate comparison within the day
    current_date = datetime.now().date() # Use a dummy date for comparison
    meetings_dt = []
    for _, row in day_meetings.iterrows():
        try:
            m_start_dt = datetime.combine(current_date, parse_time_flexible(row['Start Time']))
            m_end_dt = datetime.combine(current_date, parse_time_flexible(row['End Time']))
            meetings_dt.append((m_start_dt, m_end_dt))
        except ValueError as e:
            print(f"Warning: Skipping meeting due to time parsing error: {e} for row {row}.")
            continue

    meetings_dt.sort()

    available_slots = []
    current_free_time = datetime.combine(current_date, day_start_time)

    for m_start, m_end in meetings_dt:
        if current_free_time < m_start:
            # Found a free slot before this meeting
            if (m_start - current_free_time).total_seconds() / 60 >= min_block_minutes:
                available_slots.append((current_free_time, m_start))
        current_free_time = max(current_free_time, m_end) # Move past the current meeting

    # Check for free time after the last meeting until the end of the day
    day_end_dt = datetime.combine(current_date, day_end_time)
    if current_free_time < day_end_dt:
        if (day_end_dt - current_free_time).total_seconds() / 60 >= min_block_minutes:
            available_slots.append((current_free_time, day_end_dt))

    return available_slots

def generate_focus_schedule(
    meetings_df: pd.DataFrame, 
    focus_ratio: float, 
    min_focus_block_minutes: int,
    work_day_start: str, 
    work_day_end: str,
    output_path: Path
) -> None:
    """
    Generates a proposed schedule of focus blocks based on existing meetings.

    Args:
        meetings_df (pd.DataFrame): DataFrame with meeting data.
        focus_ratio (float): Ratio of focus time to meeting time (e.g., 1.0 for 1:1).
        min_focus_block_minutes (int): Minimum duration for a focus block in minutes.
        work_day_start (str): Start time of the typical workday (e.g., "09:00").
        work_day_end (str): End time of the typical workday (e.g., "17:00").
        output_path (Path): Path to save the generated focus schedule CSV.
    """
    if meetings_df.empty:
        print("No meetings found to generate a focus schedule.")
        return

    try:
        meetings_df['Date'] = pd.to_datetime(meetings_df['Date']).dt.date
    except Exception as e:
        print(f"Error parsing 'Date' column: {e}. Ensure dates are in a readable format (YYYY-MM-DD).")
        return

    work_start_time = parse_time_flexible(work_day_start)
    work_end_time = parse_time_flexible(work_day_end)

    all_focus_blocks = []

    for date, daily_meetings in meetings_df.groupby('Date'):
        total_meeting_minutes = 0
        for _, row in daily_meetings.iterrows():
            try:
                start_dt = datetime.combine(date, parse_time_flexible(row['Start Time']))
                end_dt = datetime.combine(date, parse_time_flexible(row['End Time']))
                total_meeting_minutes += (end_dt - start_dt).total_seconds() / 60
            except ValueError as e:
                print(f"Warning: Skipping meeting {row.get('Title', 'Untitled')} on {date} due to time parsing error: {e}.")
                continue

        target_focus_minutes = total_meeting_minutes * focus_ratio
        if target_focus_minutes < min_focus_block_minutes:
            # Ensure at least one minimum block if there's any meeting time
            if total_meeting_minutes > 0:
                target_focus_minutes = min_focus_block_minutes
            else:
                target_focus_minutes = 0 # No meetings, no target focus time

        if target_focus_minutes == 0:
            continue

        available_slots = find_available_slots(daily_meetings, work_start_time, work_end_time, min_focus_block_minutes)
        
        current_focus_minutes_assigned = 0
        for slot_start, slot_end in available_slots:
            if current_focus_minutes_assigned >= target_focus_minutes:
                break

            slot_duration_minutes = (slot_end - slot_start).total_seconds() / 60
            
            # Prioritize longer blocks up to target, or min_focus_block_minutes
            block_to_assign = min(slot_duration_minutes, target_focus_minutes - current_focus_minutes_assigned)
            
            if block_to_assign >= min_focus_block_minutes:
                focus_end = slot_start + timedelta(minutes=block_to_assign)
                all_focus_blocks.append({
                    'Date': date.isoformat(),
                    'Start Time': slot_start.strftime('%H:%M'),
                    'End Time': focus_end.strftime('%H:%M'),
                    'Title': 'Focus Block: Deep Work',
                    'Duration_Minutes': int(block_to_assign)
                })
                current_focus_minutes_assigned += block_to_assign

            elif slot_duration_minutes >= min_focus_block_minutes: # If slot itself is min_block_minutes or more, but remaining target is less
                 # Take the min_focus_block_minutes if it helps meet the target
                if current_focus_minutes_assigned + min_focus_block_minutes <= target_focus_minutes:
                    focus_end = slot_start + timedelta(minutes=min_focus_block_minutes)
                    all_focus_blocks.append({
                        'Date': date.isoformat(),
                        'Start Time': slot_start.strftime('%H:%M'),
                        'End Time': focus_end.strftime('%H:%M'),
                        'Title': 'Focus Block: Deep Work',
                        'Duration_Minutes': int(min_focus_block_minutes)
                    })
                    current_focus_minutes_assigned += min_focus_block_minutes
        
    if not all_focus_blocks:
        print("No suitable focus blocks could be generated with the given parameters. Try adjusting the focus ratio or minimum block duration.")
        return

    focus_df = pd.DataFrame(all_focus_blocks)
    focus_df = focus_df.sort_values(by=['Date', 'Start Time'])
    
    try:
        focus_df.to_csv(output_path, index=False)
        print(f"Proposed focus schedule saved to: {output_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")

def create_demo_csv(filepath: Path):
    """Creates a sample meeting data CSV for demonstration."""
    sample_data = [
        ["2026-05-14", "09:00", "10:00", "Team Standup"],
        ["2026-05-14", "10:30", "11:00", "Daily Sync"],
        ["2026-05-14", "14:00", "15:30", "Client Review"],
        ["2026-05-15", "09:30", "10:00", "Weekly Check-in"],
        ["2026-05-15", "11:00", "12:00", "Project Brainstorm"],
        ["2026-05-15", "15:00", "15:30", "Quick Catch-up"],
        ["2026-05-16", "10:00", "11:00", "Leadership Update"],
        ["2026-05-16", "13:00", "14:00", "Vendor Call"]
    ]
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Start Time", "End Time", "Title"])
        writer.writerows(sample_data)
    print(f"Created demo meeting data at {filepath}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Analyzes your meeting schedule and proposes focus blocks.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--meetings_file",
        type=Path,
        required=True,
        help="Path to the CSV file containing your meeting schedule.\n"
             "Required columns: 'Date' (YYYY-MM-DD), 'Start Time' (HH:MM), 'End Time' (HH:MM), 'Title'."
    )
    parser.add_argument(
        "--output_file",
        type=Path,
        default=Path("focus_schedule.csv"),
        help="Path to save the generated focus schedule CSV file."
    )
    parser.add_argument(
        "--focus_ratio",
        type=float,
        default=0.75,
        help="Ratio of desired focus time to actual meeting time (e.g., 1.0 for 1:1, 0.5 for 1:2).\n"
             "A value of 0.75 means for every 1 hour of meetings, the tool tries to add 45 minutes of focus time."
    )
    parser.add_argument(
        "--min_focus_block",
        type=int,
        default=30,
        help="Minimum duration for a single focus block, in minutes. Blocks shorter than this will not be suggested."
    )
    parser.add_argument(
        "--work_start",
        type=str,
        default="08:00",
        help="The start time of your typical workday (HH:MM). Focus blocks will not be scheduled before this time."
    )
    parser.add_argument(
        "--work_end",
        type=str,
        default="17:00",
        help="The end time of your typical workday (HH:MM). Focus blocks will not be scheduled after this time."
    )

    if args:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    if not parsed_args.meetings_file.exists():
        print(f"Error: The meetings file '{parsed_args.meetings_file}' does not exist.")
        return

    try:
        meetings_df = pd.read_csv(parsed_args.meetings_file)
    except Exception as e:
        print(f"Error reading meetings CSV file: {e}. Please ensure it's a valid CSV.")
        return

    required_columns = ['Date', 'Start Time', 'End Time', 'Title']
    if not all(col in meetings_df.columns for col in required_columns):
        print(f"Error: Meetings CSV must contain columns: {', '.join(required_columns)}")
        return
    
    # Validate time formats for work_start and work_end
    try:
        parse_time_flexible(parsed_args.work_start)
        parse_time_flexible(parsed_args.work_end)
    except ValueError as e:
        print(f"Error: Invalid work start/end time format: {e}.")
        return

    generate_focus_schedule(
        meetings_df=meetings_df,
        focus_ratio=parsed_args.focus_ratio,
        min_focus_block_minutes=parsed_args.min_focus_block,
        work_day_start=parsed_args.work_start,
        work_day_end=parsed_args.work_end,
        output_path=parsed_args.output_file
    )

if __name__ == "__main__":
    demo_meetings_file = Path("demo_meetings.csv")
    create_demo_csv(demo_meetings_file)
    
    # Run the tool with demo data
    main([
        "--meetings_file", str(demo_meetings_file),
        "--output_file", "my_focus_plan.csv",
        "--focus_ratio", "1.0",
        "--min_focus_block", "45",
        "--work_start", "08:30",
        "--work_end", "17:30"
    ])