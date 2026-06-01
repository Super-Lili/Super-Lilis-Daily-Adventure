"""
Sun Light Color Clock — 太阳光色彩时钟
A browser clock that mirrors the colour of natural daylight throughout the day.
Opens and works immediately. No input needed.

requirements:
# (no extra dependencies — pure Python standard library)
"""

import sys
sys.argv = ['tool']


# ── Daylight colour palette ────────────────────────────────────────────────
# Each anchor: (hour_float, bg_hex, text_hex, label)
# Interpolated smoothly between anchors every second in the browser.
_ANCHORS = [
    (0.0,  "#0b0c1e", "#4a4a6a", "deep night"),
    (4.5,  "#1a1040", "#7070a0", "before dawn"),
    (5.5,  "#6b3a5a", "#f0c0b0", "first light"),
    (6.5,  "#e07b3a", "#fff8f0", "sunrise"),
    (8.0,  "#f4c36a", "#5a3a10", "morning gold"),
    (10.0, "#fef9e7", "#4a3a20", "late morning"),
    (12.5, "#e8f4fd", "#1a3a5a", "noon"),
    (15.0, "#fde8c0", "#5a3a10", "afternoon"),
    (17.0, "#f0934a", "#fff0e8", "golden hour"),
    (18.5, "#c0463a", "#ffe8e0", "sunset"),
    (20.0, "#6a3070", "#f0d0f8", "dusk"),
    (21.5, "#1e1030", "#8070a8", "evening"),
    (23.0, "#0b0c1e", "#4a4a6a", "night"),
    (24.0, "#0b0c1e", "#4a4a6a", "deep night"),
]


def process(text: str = "") -> str:
    """Return a self-contained HTML sun-light colour clock.
    No input required — the clock reads the browser's local time.
    """
    anchors_js = str([
        {"h": h, "bg": bg, "fg": fg, "label": label}
        for h, bg, fg, label in _ANCHORS
    ]).replace("'", '"').replace("True", "true").replace("False", "false")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sun Light Color Clock</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    width: 100%; height: 100%;
    overflow: hidden;
    font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
  }}
  body {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: background-color 4s ease, color 4s ease;
    min-height: 100vh;
  }}
  #time {{
    font-size: clamp(4rem, 18vw, 13rem);
    font-weight: 200;
    letter-spacing: -0.04em;
    line-height: 1;
    transition: color 4s ease;
    font-variant-numeric: tabular-nums;
  }}
  #period {{
    margin-top: 2rem;
    font-size: clamp(0.65rem, 2vw, 0.85rem);
    font-weight: 500;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    opacity: 0.45;
    transition: color 4s ease, opacity 0.5s ease;
  }}
  #date {{
    margin-top: 0.6rem;
    font-size: clamp(0.6rem, 1.5vw, 0.75rem);
    font-weight: 400;
    letter-spacing: 0.18em;
    opacity: 0.28;
    transition: color 4s ease;
  }}
</style>
</head>
<body>
<div id="time">00:00</div>
<div id="period">—</div>
<div id="date">—</div>

<script>
const ANCHORS = {anchors_js};

function hexToRgb(hex) {{
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return [r,g,b];
}}

function lerp(a, b, t) {{
  return Math.round(a + (b - a) * t);
}}

function blendHex(hex1, hex2, t) {{
  const [r1,g1,b1] = hexToRgb(hex1);
  const [r2,g2,b2] = hexToRgb(hex2);
  const r = lerp(r1,r2,t).toString(16).padStart(2,'0');
  const g = lerp(g1,g2,t).toString(16).padStart(2,'0');
  const b = lerp(b1,b2,t).toString(16).padStart(2,'0');
  return '#' + r + g + b;
}}

function getColors(hourFloat) {{
  for (let i = 0; i < ANCHORS.length - 1; i++) {{
    const a = ANCHORS[i], b = ANCHORS[i+1];
    if (hourFloat >= a.h && hourFloat < b.h) {{
      const t = (hourFloat - a.h) / (b.h - a.h);
      const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
      return {{
        bg: blendHex(a.bg, b.bg, eased),
        fg: blendHex(a.fg, b.fg, eased),
        label: t < 0.5 ? a.label : b.label,
      }};
    }}
  }}
  return {{ bg: ANCHORS[0].bg, fg: ANCHORS[0].fg, label: ANCHORS[0].label }};
}}

const timeEl   = document.getElementById('time');
const periodEl = document.getElementById('period');
const dateEl   = document.getElementById('date');

const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function tick() {{
  const now = new Date();
  const h = now.getHours();
  const m = now.getMinutes();
  const s = now.getSeconds();
  const hourFloat = h + m/60 + s/3600;

  const hh = String(h).padStart(2,'0');
  const mm = String(m).padStart(2,'0');
  timeEl.textContent = hh + ':' + mm;

  const colors = getColors(hourFloat);
  document.body.style.backgroundColor = colors.bg;
  document.body.style.color = colors.fg;
  timeEl.style.color = colors.fg;
  periodEl.style.color = colors.fg;
  dateEl.style.color = colors.fg;
  periodEl.textContent = colors.label;

  const day = DAYS[now.getDay()];
  const date = now.getDate();
  const mon = MONTHS[now.getMonth()];
  dateEl.textContent = day + ' · ' + mon + ' ' + date;
}}

tick();
setInterval(tick, 10000);
setTimeout(tick, 1000 - new Date().getMilliseconds());
</script>
</body>
</html>"""


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    out = "sun_light_color_clock.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(process())
    print(f"✓ Saved to {out} — open in browser to see the clock.")
