def get_pomodoro_plan(work_minutes: int = 25, break_minutes: int = 5, cycles: int = 4) -> str:
    """Returns a Pomodoro session plan as text."""
    total_work = work_minutes * cycles
    total_break = break_minutes * (cycles - 1)
    total_time = total_work + total_break
    lines = [
        f"## The Focus Alchemist: Pomodoro Plan",
        f"",
        f"- **Work block:** {work_minutes} min",
        f"- **Break block:** {break_minutes} min",
        f"- **Cycles:** {cycles}",
        f"- **Total session time:** {total_time} min",
        f"",
        f"### Schedule:",
    ]
    elapsed = 0
    for i in range(1, cycles + 1):
        lines.append(f"  Cycle {i}: Work {elapsed:02d}m → {elapsed + work_minutes:02d}m")
        elapsed += work_minutes
        if i < cycles:
            lines.append(f"  Break:   {elapsed:02d}m → {elapsed + break_minutes:02d}m")
            elapsed += break_minutes
    lines += ["", "Start your timer and focus — you've got this!"]
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Return a Pomodoro session plan. Optionally parse 'work=25 break=5 cycles=4' from text."""
    import re
    work, brk, cycles = 25, 5, 4
    if text.strip():
        m = re.search(r'work\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            work = int(m.group(1))
        m = re.search(r'break\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            brk = int(m.group(1))
        m = re.search(r'cycles?\s*[=:]\s*(\d+)', text, re.IGNORECASE)
        if m:
            cycles = int(m.group(1))
    return get_pomodoro_plan(work, brk, cycles)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Example usage: 25 minutes work, 5 minutes break, 4 cycles
    print(get_pomodoro_plan(work_minutes=25, break_minutes=5, cycles=4))