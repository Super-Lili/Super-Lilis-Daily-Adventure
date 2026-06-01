"""
Sun Light Color Clock — 太阳光色彩时钟
An analog clock whose colours follow natural daylight through the day.
Opens and works immediately. No input needed.

requirements:
# (no extra dependencies — pure Python standard library)
"""

import sys
sys.argv = ['tool']


# ── Daylight colour palette ────────────────────────────────────────────────
# Each anchor: (hour_float, bg_hex, face_hex, hand_hex, label)
_ANCHORS = [
    (0.0,  "#08091a", "#12153a", "#6060a0", "deep night"),
    (4.5,  "#0f0a2e", "#1e1650", "#8878b8", "before dawn"),
    (5.5,  "#5a2a48", "#8a4a6a", "#f8d0c0", "first light"),
    (6.5,  "#c05a20", "#e08040", "#fff4e8", "sunrise"),
    (8.0,  "#d4943a", "#e8b860", "#3a2008", "morning gold"),
    (10.5, "#f0e8d0", "#faf4e8", "#3a3020", "late morning"),
    (12.5, "#d8eef8", "#eef6fc", "#1a3050", "noon"),
    (15.0, "#e8d8a8", "#f4e8c0", "#4a3010", "afternoon"),
    (17.0, "#d06828", "#e88840", "#fff0e0", "golden hour"),
    (18.5, "#a03028", "#c05040", "#ffe8e0", "sunset"),
    (20.0, "#502858", "#704878", "#f0d0f8", "dusk"),
    (21.5, "#180e2e", "#281840", "#9080c0", "evening"),
    (23.0, "#08091a", "#12153a", "#6060a0", "night"),
    (24.0, "#08091a", "#12153a", "#6060a0", "deep night"),
]


def process(text: str = "") -> str:
    """Return a self-contained HTML analog sun-light colour clock.
    No input required — the clock reads the browser's local time.
    """
    anchors_js = str([
        {"h": h, "bg": bg, "face": face, "hand": hand, "label": label}
        for h, bg, face, hand, label in _ANCHORS
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
    min-height: 100vh;
    transition: background-color 8s ease;
  }}
  #clock-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }}
  canvas {{
    display: block;
    border-radius: 50%;
  }}
  #label {{
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    opacity: 0.4;
    transition: color 8s ease;
  }}
</style>
</head>
<body>
<div id="clock-wrap">
  <canvas id="c"></canvas>
  <div id="label">—</div>
</div>

<script>
const ANCHORS = {anchors_js};

function hexToRgb(hex) {{
  return [
    parseInt(hex.slice(1,3),16),
    parseInt(hex.slice(3,5),16),
    parseInt(hex.slice(5,7),16)
  ];
}}

function lerp(a,b,t) {{ return a + (b-a)*t; }}

function blendHex(h1,h2,t) {{
  const [r1,g1,b1]=hexToRgb(h1), [r2,g2,b2]=hexToRgb(h2);
  const r=Math.round(lerp(r1,r2,t)), g=Math.round(lerp(g1,g2,t)), b=Math.round(lerp(b1,b2,t));
  return '#'+[r,g,b].map(v=>v.toString(16).padStart(2,'0')).join('');
}}

function ease(t) {{ return t<0.5?2*t*t:-1+(4-2*t)*t; }}

function getColors(hf) {{
  for (let i=0;i<ANCHORS.length-1;i++) {{
    const a=ANCHORS[i], b=ANCHORS[i+1];
    if (hf>=a.h && hf<b.h) {{
      const t=ease((hf-a.h)/(b.h-a.h));
      return {{
        bg:   blendHex(a.bg,   b.bg,   t),
        face: blendHex(a.face, b.face, t),
        hand: blendHex(a.hand, b.hand, t),
        label: t<0.5 ? a.label : b.label,
      }};
    }}
  }}
  return {{bg:ANCHORS[0].bg, face:ANCHORS[0].face, hand:ANCHORS[0].hand, label:ANCHORS[0].label}};
}}

const canvas = document.getElementById('c');
const ctx    = canvas.getContext('2d');
const label  = document.getElementById('label');

function resize() {{
  const s = Math.min(window.innerWidth, window.innerHeight) * 0.62;
  canvas.width  = s;
  canvas.height = s;
}}

function drawHand(cx, cy, angle, length, width, color, lineCap) {{
  ctx.save();
  ctx.beginPath();
  ctx.lineWidth   = width;
  ctx.strokeStyle = color;
  ctx.lineCap     = lineCap || 'round';
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.moveTo(0, -length * 0.12);
  ctx.lineTo(0, -length);
  ctx.stroke();
  ctx.restore();
}}

function draw() {{
  const now  = new Date();
  const h    = now.getHours();
  const m    = now.getMinutes();
  const s    = now.getSeconds();
  const ms   = now.getMilliseconds();
  const hf   = h + m/60 + s/3600;
  const colors = getColors(hf);

  const W = canvas.width, H = canvas.height;
  const cx = W/2, cy = H/2;
  const R  = W/2;
  const r  = R * 0.88;   // face radius

  // background fill
  document.body.style.backgroundColor = colors.bg;
  label.style.color = colors.hand;
  label.textContent = colors.label;

  ctx.clearRect(0,0,W,H);

  // ── Clock face ───────────────────────────────────────────────
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI*2);
  ctx.fillStyle = colors.face;
  ctx.fill();

  // Subtle ring
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI*2);
  ctx.strokeStyle = colors.hand + '30';
  ctx.lineWidth = R * 0.012;
  ctx.stroke();

  // ── Hour markers ─────────────────────────────────────────────
  for (let i=0; i<12; i++) {{
    const a  = (i / 12) * Math.PI * 2 - Math.PI/2;
    const isDot4 = (i % 3 === 0);
    const dot  = isDot4 ? r * 0.07 : r * 0.03;
    const dist = r * (isDot4 ? 0.80 : 0.83);
    ctx.beginPath();
    ctx.arc(cx + Math.cos(a)*dist, cy + Math.sin(a)*dist, dot, 0, Math.PI*2);
    ctx.fillStyle = colors.hand + (isDot4 ? 'cc' : '55');
    ctx.fill();
  }}

  // ── Smooth second angle ──────────────────────────────────────
  const secAngle = ((s + ms/1000) / 60) * Math.PI*2 - Math.PI/2;
  const minAngle = ((m + s/60)    / 60) * Math.PI*2 - Math.PI/2;
  const hrAngle  = ((h % 12 + m/60) / 12) * Math.PI*2 - Math.PI/2;

  // Hour hand — thick, short
  drawHand(cx, cy, hrAngle,  r*0.48, R*0.045, colors.hand);

  // Minute hand — medium
  drawHand(cx, cy, minAngle, r*0.68, R*0.028, colors.hand);

  // Second hand — thin, long, slight contrast
  const secColor = colors.hand + 'cc';
  drawHand(cx, cy, secAngle, r*0.78, R*0.014, secColor);

  // Centre dot
  ctx.beginPath();
  ctx.arc(cx, cy, R*0.025, 0, Math.PI*2);
  ctx.fillStyle = colors.hand;
  ctx.fill();

  requestAnimationFrame(draw);
}}

window.addEventListener('resize', () => {{ resize(); }});
resize();
draw();
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
