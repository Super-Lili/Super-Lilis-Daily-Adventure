```python
import unittest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, time
import csv
import os

# Assume the main tool's functions are in a file named 'focus_flow_guardian.py'
# For testing purposes, we'll import directly or copy relevant functions.
# In a real scenario, you'd import `main` and `create_demo_csv` from your tool's file.

# Copying relevant functions here for self-contained testing, but ideally, you'd import them.
# Make sure these functions exactly match the ones in your main tool code.

def parse_time_flexible(time_str):
    """Parses a time string, handling common formats."""
    try:
        # Using a fixed date to ensure consistent datetime object comparison
        return datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        raise ValueError(f"Could not parse time: {time_str}. Please use HH:MM format.")

def calculate_overlap(start1, end1, start2, end2):
    """Calculates the overlap in minutes between two time intervals."""
    if start1 >= end1 or start2 >= end2:
        return 0

    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)

    if latest_start < earliest_end:
        return (earliest_end - latest_start).total_seconds() / 60
    return 0

def find_available_slots(day_meetings, day_start_time, day_end_time, min_block_minutes):
    """Identifies available time slots in a day, given a list of meetings."""
    
    if not isinstance(day_start_time, time) or not isinstance(day_end_time, time):
        raise TypeError("day_start_time and day_end_time must be datetime.time objects.")

    current_date = datetime.now().date()
    meetings_dt = []
    for _, row in day_meetings.iterrows():
        try:
            m_start_dt = datetime.combine(current_date, parse_time_flexible(row['Start Time']))
            m_end_dt = datetime.combine(current_date, parse_time_flexible(row['End Time']))
            meetings_dt.append((m_start_dt, m_end_dt))
        except ValueError as e:
            # print(f"Warning: Skipping meeting due to time parsing error: {e} for row {row}.")
            continue

    meetings_dt.sort()

    available_slots = []
    current_free_time = datetime.combine(current_date, day_start_time)

    for m_start, m_end in meetings_dt:
        if current_free_time < m_start:
            if (m_start - current_free_time).total_seconds() / 60 >= min_block_minutes:
                available_slots.append((current_free_time, m_start))
        current_free_time = max(current_free_time, m_end)

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
    if meetings_df.empty:
        # print("No meetings found to generate a focus schedule.")
        return

    try:
        meetings_df['Date'] = pd.to_datetime(meetings_df['Date']).dt.date
    except Exception as e:
        # print(f"Error parsing 'Date' column: {e}. Ensure dates are in a readable format (YYYY-MM-DD).")
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
                # print(f"Warning: Skipping meeting {row.get('Title', 'Untitled')} on {date} due to time parsing error: {e}.")
                continue

        target_focus_minutes = total_meeting_minutes * focus_ratio
        if target_focus_minutes < min_focus_block_minutes:
            if total_meeting_minutes > 0:
                target_focus_minutes = min_focus_block_minutes
            else:
                target_focus_minutes = 0

        if target_focus_minutes == 0:
            continue

        available_slots = find_available_slots(daily_meetings, work_start_time, work_end_time, min_focus_block_minutes)
        
        current_focus_minutes_assigned = 0
        for slot_start, slot_end in available_slots:
            if current_focus_minutes_assigned >= target_focus_minutes:
                break

            slot_duration_minutes = (slot_end - slot_start).total_seconds() / 60
            
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
            elif slot_duration_minutes >= min_focus_block_minutes:
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
        # print("No suitable focus blocks could be generated with the given parameters. Try adjusting the focus ratio or minimum block duration.")
        return

    focus_df = pd.DataFrame(all_focus_blocks)
    focus_df = focus_df.sort_values(by=['Date', 'Start Time'])
    
    try:
        focus_df.to_csv(output_path, index=False)
        # print(f"Proposed focus schedule saved to: {output_path}")
    except Exception as e:
        # print(f"Error saving output file: {e}")
        pass

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

class TestFocusFlowGuardian(unittest.TestCase):
    def setUp(self):
        self.demo_meetings_file = Path("test_demo_meetings.csv")
        self.output_file = Path("test_focus_schedule.csv")
        create_demo_csv(self.demo_meetings_file)

    def tearDown(self):
        if self.demo_meetings_file.exists():
            os.remove(self.demo_meetings_file)
        if self.output_file.exists():
            os.remove(self.output_file)

    def test_create_demo_csv(self):
        self.assertTrue(self.demo_meetings_file.exists())
        df = pd.read_csv(self.demo_meetings_file)
        self.assertFalse(df.empty)
        self.assertIn('Date', df.columns)

    def test_generate_focus_schedule_basic(self):
        meetings_df = pd.read_csv(self.demo_meetings_file)
        generate_focus_schedule(
            meetings_df=meetings_df,
            focus_ratio=1.0,
            min_focus_block_minutes=30,
            work_day_start="08:00",
            work_day_end="17:00",
            output_path=self.output_file
        )
        self.assertTrue(self.output_file.exists())
        focus_df = pd.read_csv(self.output_file)
        self.assertFalse(focus_df.empty)
        self.assertIn('Focus Block: Deep Work', focus_df['Title'].values)
        
        # Check if durations are sensible (at least min_focus_block_minutes)
        self.assertTrue((focus_df['Duration_Minutes'] >= 30).all())

    def test_generate_focus_schedule_no_meetings(self):
        empty_meetings_file = Path("empty_meetings.csv")
        with open(empty_meetings_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Start Time", "End Time", "Title"])
        
        meetings_df = pd.read_csv(empty_meetings_file)
        generate_focus_schedule(
            meetings_df=meetings_df,
            focus_ratio=1.0,
            min_focus_block_minutes=30,
            work_day_start="08:00",
            work_day_end="17:00",
            output_path=self.output_file
        )
        self.assertFalse(self.output_file.exists()) # Should not create an output if no blocks generated
        os.remove(empty_meetings_file)

    def test_generate_focus_schedule_different_ratio(self):
        meetings_df = pd.read_csv(self.demo_meetings_file)
        generate_focus_schedule(
            meetings_df=meetings_df,
            focus_ratio=0.5, # Half the focus time
            min_focus_block_minutes=30,
            work_day_start="08:00",
            work_day_end="17:00",
            output_path=self.output_file
        )
        self.assertTrue(self.output_file.exists())
        focus_df = pd.read_csv(self.output_file)
        # Verify that fewer or shorter blocks might be created compared to 1.0 ratio
        # Exact number depends on slot fragmentation, so we'll check for non-empty
        self.assertFalse(focus_df.empty)

    def test_find_available_slots(self):
        test_meetings_data = [
            ["2026-05-14", "09:00", "10:00", "Meeting 1"],
            ["2026-05-14", "11:30", "12:30", "Meeting 2"],
            ["2026-05-14", "14:00", "15:00", "Meeting 3"]
        ]
        test_df = pd.DataFrame(test_meetings_data, columns=['Date', 'Start Time', 'End Time', 'Title'])
        
        start_time_obj = time(8, 0)
        end_time_obj = time(17, 0)
        
        slots = find_available_slots(test_df, start_time_obj, end_time_obj, 30)
        
        # Expected slots:
        # 08:00 - 09:00 (60 min)
        # 10:00 - 11:30 (90 min)
        # 12:30 - 14:00 (90 min)
        # 15:00 - 17:00 (120 min)
        
        self.assertEqual(len(slots), 4)
        self.assertEqual(slots[0][0].strftime('%H:%M'), "08:00")
        self.assertEqual(slots[0][1].strftime('%H:%M'), "09:00")
        self.assertEqual(slots[1][0].strftime('%H:%M'), "10:00")
        self.assertEqual(slots[1][1].strftime('%H:%M'), "11:30")
        self.assertEqual(slots[2][0].strftime('%H:%M'), "12:30")
        self.assertEqual(slots[2][1].strftime('%H:%M'), "14:00")
        self.assertEqual(slots[3][0].strftime('%H:%M'), "15:00")
        self.assertEqual(slots[3][1].strftime('%H:%M'), "17:00")

    def test_find_available_slots_no_slots_too_small(self):
        test_meetings_data = [
            ["2026-05-14", "08:00", "08:45", "M1"],
            ["2026-05-14", "09:00", "17:00", "M2"]
        ]
        test_df = pd.DataFrame(test_meetings_data, columns=['Date', 'Start Time', 'End Time', 'Title'])
        slots = find_available_slots(test_df, time(8, 0), time(17, 0), 30)
        # Expected: A 15-minute gap between 08:45 and 09:00, which is less than min_block_minutes (30)
        self.assertEqual(len(slots), 0)

    def test_parse_time_flexible_valid(self):
        self.assertEqual(parse_time_flexible("09:00"), time(9, 0))
        self.assertEqual(parse_time_flexible("14:30"), time(14, 30))

    def test_parse_time_flexible_invalid(self):
        with self.assertRaises(ValueError):
            parse_time_flexible("25:00")
        with self.assertRaises(ValueError):
            parse_time_flexible("invalid-time")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
```