"""
Tool: Identity Anchor Notebook
Category: Healing Inventions
Format: D – Live canvas / real-time transformer
Mode: 3 – Interactive HTML (Rule 8)

Algorithmic depth (Steps 1–6 exactly per spec):
  1) Capture current Date on submission.
  2) Compute hue = (hour * 360 / 24) % 360, saturation 70%, lightness 60% for card background.
  3) Compute polynomial hash: hash = 0; for each char: hash = (hash * 31 + ord(char)) & 0xFFFFFF.
  4) Derive shape parameters:
       - angle = hash % 360 for a thin diagonal line, positioned near top-left with offset derived from hash.
       - radius = (20 + (hash % 60))% of card height for a faint circle at bottom-right with hash-derived position.
  5) Construct card DOM element with these computed CSS values.
  6) Append to gallery container preserving insertion order.
"""
from jinja2 import Template
from typing import Optional

TEMPLATE_STR = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Identity Anchor Notebook</title>
<style>
body{background:#fdfcf8;font-family:Georgia,'Times New Roman',serif;margin:0;padding:0;display:flex;flex-direction:column;align-items:center;min-height:100vh}
.container{width:100%;max-width:600px;padding:2rem 1rem;display:flex;flex-direction:column;align-items:center}
.input-area{width:100%;margin-bottom:2rem;display:flex;flex-direction:column;align-items:center}
.input-row{display:flex;width:100%;max-width:500px;gap:0.5rem}
input[type="text"]{flex:1;padding:0.75rem 1rem;font-size:1.1rem;border:1px solid #ccc;border-radius:0.5rem;background:white;font-family:Georgia,serif}
button{background:#e0d7c6;border:1px solid #b8a997;border-radius:0.5rem;padding:0.75rem 1rem;font-size:1.2rem;cursor:pointer;color:#3e3226;transition:background 0.2s}
button:hover{background:#d1c6b0}
.hint{font-size:0.9rem;color:#8c8279;margin-top:0.25rem}
.gallery{width:100%;max-width:500px;display:flex;flex-direction:column;gap:1rem;min-height:100px;margin-bottom:2rem}
.empty-message{color:#aaa9a6;text-align:center;font-style:italic;padding:2rem}
.card{position:relative;border-radius:1rem;padding:1.25rem;box-shadow:0 2px 8px rgba(0,0,0,0.08);overflow:hidden;animation:slideUp 0.4s ease-out;color:#1a1a1a;display:flex;flex-direction:column;gap:0.5rem}
@keyframes slideUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
.card-text{font-family:Georgia,serif;font-size:1.1rem;line-height:1.5;word-wrap:break-word;position:relative;z-index:2}
.card-time{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:0.8rem;color:#4a4242;opacity:0.8;position:relative;z-index:2}
.shape-container{position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:1}
.diagonal-line{position:absolute;width:1px;background:rgba(255,255,255,0.5);transform-origin:top left}
.circle{position:absolute;border-radius:50%;background:rgba(255,255,255,0.3)}
.export-btn{margin-top:1rem;font-size:0.9rem;background:#f3efe9;border:1px solid #ccc;padding:0.5rem 1rem}
</style>
</head>
<body>
<div class="container">
  <div class="input-area">
    <div class="input-row">
      <input type="text" id="anchorInput" placeholder="What did you notice today?" aria-label="Describe a small sensory moment that felt like you">
      <button id="addBtn" title="Add anchor">+</button>
    </div>
    <p class="hint">Describe a small sensory moment that felt like you.</p>
  </div>
  <div class="gallery" id="gallery">
    <p class="empty-message" id="emptyMsg">Your anchors will appear here.</p>
  </div>
  <button class="export-btn" id="copyAllBtn">Copy All Anchors</button>
</div>
<script>
(function(){
  var input = document.getElementById('anchorInput');
  var addBtn = document.getElementById('addBtn');
  var gallery = document.getElementById('gallery');
  var emptyMsg = document.getElementById('emptyMsg');
  var copyAllBtn = document.getElementById('copyAllBtn');

  function hashString(s) {
    var h = 0;
    for (var i = 0; i < s.length; i++) {
      h = (h * 31 + s.charCodeAt(i)) & 0xFFFFFF;
    }
    return h;
  }

  function addAnchor() {
    var text = input.value.trim();
    if (!text) return;

    /* Step 1: capture current Date */
    var now = new Date();
    /* Step 2: hue from hour */
    var hue = (now.getHours() * 360 / 24) % 360;
    var bg = 'hsl(' + hue + ', 70%, 60%)';

    /* Step 3: hash of text */
    var hash = hashString(text);

    /* Step 4: shape parameters with position derived from hash */
    var angle = hash % 360;
    var radiusPct = 20 + (hash % 60);

    /* Additional position offsets from hash bits (lightweight but adds variation) */
    var offsetX = (hash & 0x7F) * 0.2;          /* 0..25.4 % from left */
    var offsetY = ((hash >> 7) & 0x7F) * 0.2;   /* 0..25.4 % from top */
    var circleRight = -5 + ((hash >> 14) & 0x1F) * 0.3;  /* right offset in % */
    var circleBottom = -5 + ((hash >> 9) & 0x1F) * 0.3;

    createCard(text, now, bg, angle, radiusPct, offsetX, offsetY, circleRight, circleBottom);
    input.value = '';
    if (emptyMsg) emptyMsg.style.display = 'none';
  }

  function createCard(text, ts, bg, angle, radiusPct, offX, offY, circR, circB) {
    var card = document.createElement('div');
    card.className = 'card';
    card.style.backgroundColor = bg;

    var sh = document.createElement('div');
    sh.className = 'shape-container';

    var line = document.createElement('div');
    line.className = 'diagonal-line';

    var circ = document.createElement('div');
    circ.className = 'circle';

    sh.appendChild(line);
    sh.appendChild(circ);

    var txtDiv = document.createElement('div');
    txtDiv.className = 'card-text';
    txtDiv.textContent = text;

    var timeDiv = document.createElement('div');
    timeDiv.className = 'card-time';
    var opts = { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    timeDiv.textContent = ts.toLocaleString(undefined, opts);

    card.appendChild(sh);
    card.appendChild(txtDiv);
    card.appendChild(timeDiv);

    /* Step 6: append to gallery preserving insertion order */
    gallery.appendChild(card);

    /* Set sizes after DOM layout */
    var cardHeight = card.offsetHeight;
    var cardWidth = card.offsetWidth;
    if (cardHeight > 0 && cardWidth > 0) {
      var lineLen = cardHeight * 0.4;
      line.style.height = lineLen + 'px';
      line.style.left = (offX / 100 * cardWidth) + 'px';
      line.style.top = (offY / 100 * cardHeight) + 'px';
      line.style.transform = 'rotate(' + angle + 'deg)';

      var radiusPx = (cardHeight * radiusPct) / 100;
      var diam = radiusPx * 2;
      circ.style.width = diam + 'px';
      circ.style.height = diam + 'px';
      circ.style.right = (circR / 100 * cardWidth) + 'px';
      circ.style.bottom = (circB / 100 * cardHeight) + 'px';
    } else {
      /* Fallback if layout not yet available */
      line.style.height = '40px';
      line.style.transform = 'rotate(' + angle + 'deg)';
      circ.style.width = '40px';
      circ.style.height = '40px';
    }

    card.addEventListener('click', function() {
      if (card.classList.contains('expanded')) {
        var pr = card.querySelector('.still-you-prompt');
        if (pr) pr.remove();
        card.classList.remove('expanded');
      } else {
        var pr = document.createElement('div');
        pr.className = 'still-you-prompt';
        pr.style.cssText = 'font-size:0.85rem;font-style:italic;margin-top:0.5rem;opacity:0.7;position:relative;z-index:2;';
        pr.textContent = 'Still you?';
        card.appendChild(pr);
        card.classList.add('expanded');
      }
    });
  }

  addBtn.addEventListener('click', addAnchor);
  input.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') addAnchor();
  });

  copyAllBtn.addEventListener('click', function() {
    var cards = gallery.querySelectorAll('.card');
    var texts = [];
    cards.forEach(function(c) {
      var t = c.querySelector('.card-text');
      if (t) texts.push(t.textContent);
    });
    if (texts.length === 0) { alert('No anchors yet.'); return; }
    navigator.clipboard.writeText(texts.join('\n')).then(function() {
      var orig = copyAllBtn.textContent;
      copyAllBtn.textContent = 'Copied!';
      setTimeout(function() { copyAllBtn.textContent = orig; }, 1500);
    }).catch(function() { alert('Could not copy.'); });
  });
})();
</script>
</body>
</html>'''

TEMPLATE = Template(TEMPLATE_STR)

def process(text: str) -> str:
    """Return the interactive Identity Anchor Notebook HTML page."""
    # The page is static; all logic runs client-side.
    # The text argument is not used beyond providing a consistent entry point.
    return TEMPLATE.render()

def _cli_main() -> None:
    import sys
    print(process(sys.argv[1] if len(sys.argv) > 1 else ""))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()