import time


def pomodoro_timer(work_minutes=25, break_minutes=5, cycles=4):
    """
    A customizable Pomodoro timer to help with focus and mindful breaks.
    Runs in real-time — use Ctrl+C to stop early.
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


def process(text: str) -> str:
    """
    Show a Pomodoro schedule without running real timers.
    Input format: 'work_minutes break_minutes cycles' e.g. '25 5 4'
    Falls back to classic 25/5/4 settings.
    """
    parts = text.strip().split()
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            pass

    work_minutes = nums[0] if len(nums) >= 1 else 25
    break_minutes = nums[1] if len(nums) >= 2 else 5
    cycles = nums[2] if len(nums) >= 3 else 4

    total_work = work_minutes * cycles
    total_break = break_minutes * (cycles - 1)
    total_minutes = total_work + total_break

    lines = [
        "The Focus Alchemist: Pomodoro Schedule",
        "=" * 40,
        f"Work:   {work_minutes} minutes per cycle",
        f"Break:  {break_minutes} minutes between cycles",
        f"Cycles: {cycles}",
        "",
        "Your session:",
    ]

    for i in range(1, cycles + 1):
        lines.append(f"  Cycle {i}: Work {work_minutes} min", )
        if i < cycles:
            lines.append(f"           Break {break_minutes} min")

    lines.append("")
    lines.append(f"Total focus time:  {total_work} minutes")
    lines.append(f"Total break time:  {total_break} minutes")
    lines.append(f"Total session:     {total_minutes} minutes ({total_minutes // 60}h {total_minutes % 60}m)")
    lines.append("")
    lines.append("For the live countdown timer, run: python3 main.py")
    return "\n".join(lines)


def _cli_main():
    # Example usage: 25 minutes work, 5 minutes break, 4 cycles
    pomodoro_timer(work_minutes=25, break_minutes=5, cycles=4)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
