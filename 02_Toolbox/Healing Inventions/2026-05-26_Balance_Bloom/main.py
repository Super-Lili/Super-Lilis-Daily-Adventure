# No external dependencies — pure Python standard library + string SVG generation

import datetime
import json


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    return f'#{r:02x}{g:02x}{b:02x}'


def interpolate_color(c1: tuple, c2: tuple, factor: float) -> tuple:
    return tuple(max(0, min(255, int(c1[i] + (c2[i] - c1[i]) * factor))) for i in range(3))


def generate_bloom_svg(start_hex: str, end_hex: str, cycle_hours: int, now: datetime.datetime) -> str:
    seconds_today = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    factor = (seconds_today % (cycle_hours * 3600)) / (cycle_hours * 3600)

    c1 = hex_to_rgb(start_hex)
    c2 = hex_to_rgb(end_hex)
    top = interpolate_color(c1, c2, factor * 0.5)
    bot = interpolate_color(c2, c1, factor * 0.5)
    top_hex = rgb_to_hex(*top)
    bot_hex = rgb_to_hex(*bot)

    hour_str = now.strftime("%H:%M")
    progress_pct = int(factor * 100)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <defs>
    <linearGradient id="bloom" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{top_hex}"/>
      <stop offset="100%" stop-color="{bot_hex}"/>
    </linearGradient>
  </defs>
  <rect width="400" height="400" fill="url(#bloom)" rx="16"/>
  <circle cx="200" cy="200" r="80" fill="rgba(255,255,255,0.12)"/>
  <circle cx="200" cy="200" r="55" fill="rgba(255,255,255,0.10)"/>
  <text x="200" y="195" text-anchor="middle" font-family="Georgia, serif"
        font-size="28" fill="rgba(255,255,255,0.85)">{hour_str}</text>
  <text x="200" y="225" text-anchor="middle" font-family="Georgia, serif"
        font-size="13" fill="rgba(255,255,255,0.60)">day {progress_pct}% complete</text>
  <text x="200" y="360" text-anchor="middle" font-family="Georgia, serif"
        font-size="12" fill="rgba(255,255,255,0.45)">breathe · things are moving</text>
</svg>"""


def process(text: str = "") -> str:
    """Generate a calming SVG that shifts color slowly through the day.
    Optionally accepts JSON: {"start_color": "#hex", "end_color": "#hex", "cycle_hours": 24}
    """
    start_hex = "#AEC6CF"
    end_hex   = "#C7B8E8"
    cycle_hours = 24

    if text.strip():
        try:
            p = json.loads(text)
            start_hex   = p.get("start_color", start_hex)
            end_hex     = p.get("end_color", end_hex)
            cycle_hours = int(p.get("cycle_hours", cycle_hours))
        except (json.JSONDecodeError, ValueError):
            pass

    return generate_bloom_svg(start_hex, end_hex, cycle_hours, datetime.datetime.now())


def _cli_main():
    import argparse, os
    p = argparse.ArgumentParser(description="Balance Bloom — a visual anchor for financial anxiety.")
    p.add_argument("--start-color", default="#AEC6CF", help="Start hex color (default: pastel blue)")
    p.add_argument("--end-color",   default="#C7B8E8", help="End hex color (default: pastel purple)")
    p.add_argument("--cycle-hours", type=int, default=24, help="Cycle length in hours (default: 24)")
    p.add_argument("--output",      default="balance_bloom.svg", help="Output SVG path")
    args = p.parse_args()

    svg = process(json.dumps({
        "start_color": args.start_color,
        "end_color": args.end_color,
        "cycle_hours": args.cycle_hours,
    }))
    with open(args.output, "w") as f:
        f.write(svg)
    print(f"✓ Saved to {args.output}  ({args.cycle_hours}h cycle, {datetime.datetime.now().strftime('%H:%M')})")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
