import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# --- Configuration for simulated environment ---
# This data simulates a basic understanding of locations and travel times.
# It is NOT keyword lookup for input/output but a model for algorithmic depth.
_SIMULATED_LOCATION_DATA = {
    "1st Ave & 23rd St": {
        "Grand Central": {
            "Bus M15": {"duration": timedelta(minutes=20), "delay_factor": 1.2},
            "Walk": {"duration": timedelta(minutes=45), "delay_factor": 1.0},
            "Subway 6": {"duration": timedelta(minutes=15), "delay_factor": 1.1},
            "Taxi": {"duration": timedelta(minutes=10), "delay_factor": 1.3}
        }
    },
    "Grand Central": {
        "White Plains": {
            "Metro-North": {"duration": timedelta(minutes=40), "delay_factor": 1.05},
            "Bus B1": {"duration": timedelta(minutes=70), "delay_factor": 1.15},
            "Taxi": {"duration": timedelta(minutes=35), "delay_factor": 1.3}
        },
        "Harlem-125th St": { # Example connection for Metro-North disruption
            "Metro-North": {"duration": timedelta(minutes=10), "delay_factor": 1.05},
            "Subway 4/5/6": {"duration": timedelta(minutes=15), "delay_factor": 1.1}
        }
    },
    # Add more simulated connections for robust alternative generation
    "White Plains": {
        "Grand Central": {
            "Metro-North": {"duration": timedelta(minutes=40), "delay_factor": 1.05}
        }
    }
}

# --- Current date for simulation ---
_TODAY = datetime(2026, 6, 13)

class Leg:
    """Represents a single leg of a journey."""
    def __init__(self, mode: str, start_point: str, end_point: str,
                 planned_start_time: datetime, planned_end_time: datetime,
                 duration: timedelta, original_text: str):
        self.mode = mode
        self.start_point = start_point
        self.end_point = end_point
        self.planned_start_time = planned_start_time
        self.planned_end_time = planned_end_time
        self.duration = duration
        self.original_text = original_text
        self.current_start_time = planned_start_time
        self.current_end_time