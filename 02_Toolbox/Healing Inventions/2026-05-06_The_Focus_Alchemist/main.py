```python
import time

def pomodoro_timer(work_minutes=25, break_minutes=5, cycles=4):
    """
    A customizable Pomodoro timer to help with focus and mindful breaks.
    """
    work_seconds = work_minutes * 60
    break_seconds = break_minutes * 60

    print(f"Starting The Focus Alchemist for {cycles} cycles.")

    for i in range(1, cycles + 1):
        print(f"\n--- Cycle {i}/{cycles}: WORK ({work_minutes} min) ---")
        time_left = work_seconds
        while time_left > 0:
            mins, secs = divmod(time_left, 60)
            print(f"Focus for: {mins:02d}:{secs:02d}", end='\r')
            time.sleep(1)
            time_left -= 1
        print("\nWork session ended! Time for a break.")

        if i < cycles:
            print(f"--- Cycle {i}/{cycles}: BREAK ({break_minutes} min) ---")
            time_left = break_seconds
            while time_left > 0:
                mins, secs = divmod(time_left, 60)
                print(f"Relax for: {mins:02d}:{secs:02d}", end='\r')
                time.sleep(1)
                time_left -= 1
            print("\nBreak ended! Back to work.")
        else:
            print("\nAll cycles complete! You've earned a longer rest.")

if __name__ == "__main__":
    # Example usage: 25 minutes work, 5 minutes break, 4 cycles
    # You can customize these values
    pomodoro_timer(work_minutes=25, break_minutes=5, cycles=4)
```