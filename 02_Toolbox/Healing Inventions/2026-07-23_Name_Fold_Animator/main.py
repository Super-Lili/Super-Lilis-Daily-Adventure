"""Name Fold Animator — An interactive breathing canvas for two names."""
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Name Fold Animator</title>
<style>
  body{background:#f5f0e1;margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,-apple-system,sans-serif}
  .container{text-align:center;max-width:800px;width:100%;padding:20px}
  h1{font-weight:300;color:#333}
  .inputs{display:flex;gap:20px;justify-content:center;margin-bottom:20px}
  .input-group{display:flex;flex-direction:column;align-items:center}
  label{font-size:0.9em;color:#444;margin-bottom:6px}
  input[type="text"]{padding:8px 12px;font-size:1.2em;border:1px solid #ccc;border-radius:8px;width:200px;text-align:center;background:#fff}
  .slider-container{margin:20px 0}
  .slider-container label{display:block;margin-bottom:5px}
  #weight{width:200px}
  canvas{border:1px solid #ccc;border-radius:12px;margin:20px 0}
  #info{margin-top:5px;font-size:0.85em;color:#444}
  #save-btn{padding:10px 20px;font-size:1em;background:#2a9d8f;color:white;border:none;border-radius:8px;cursor:pointer}
  #save-btn:hover{background:#21867a}
</style>
</head>
<body>
<div class="container">
  <h1>Two Names, One Space</h1>
  <div class="inputs">
    <div class="input-group">
      <label for="legal">what the world calls you</label>
      <input type="text" id="legal" placeholder="Legal name" maxlength="40" value="{{ legal }}">
    </div>
    <div class="input-group">
      <label for="chosen">what you call yourself</label>
      <input type="text" id="chosen" placeholder="Chosen name" maxlength="40" value="{{ chosen }}">
    </div>
  </div>
  <div class="slider-container">
    <label for="weight">weight</label>
    <input type="range" id="weight" min="0" max="1" step="0.01" value="{{ weight }}">
  </div>
  <canvas id="canvas" width="700" height="300"></canvas>
  <div id="info"></div>
  <button id="save-btn">save this moment</button>
</div>
<script>
(function() {
  var legalInput = document.getElementById('legal');
  var chosenInput = document.getElementById('chosen');
  var weightSlider = document.getElementById('weight');
  var canvas = document.getElementById('canvas');
  var ctx = canvas.getContext('2d');
  var infoDiv = document.getElementById('info');
  var legalName = '';
  var chosenName = '';
  var weight = parseFloat(weightSlider.value);
  var frictionScore = 0;
  var surplusScore = 0;
  var period = 2;
  var jitterAmp = 0.1;
  var perCharDiffNorm = [];
  var audioCtx = null;
  var osc = null;
  var gainNode = null;
  var audioStarted = false;

  function initAudio() {
    if (audioStarted) return;
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      gainNode = audioCtx.createGain();
      gainNode.gain.value = 0.06;
      osc = audioCtx.createOscillator();
      osc.type = 'sine';
      osc.frequency.value = 200;
      osc.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      osc.start();
      if (audioCtx.state === 'suspended') audioCtx.resume();
      audioStarted = true;
    } catch(e) {}
  }

  function updateParams() {
    legalName = legalInput.value;
    chosenName = chosenInput.value;
    weight = parseFloat(weightSlider.value);
    var maxLen = Math.max(legalName.length, chosenName.length);
    var l = legalName.padEnd(maxLen, ' ');
    var c = chosenName.padEnd(maxLen, ' ');
    var sumDiff = 0;
    perCharDiffNorm = [];
    for (var i = 0; i < maxLen; i++) {
      var dl = l.charCodeAt(i) || 32;
      var dc = c.charCodeAt(i) || 32;
      var diff = Math.abs(dl - dc);
      sumDiff += diff;
      perCharDiffNorm.push(diff / 127);
    }
    frictionScore = maxLen > 0 ? sumDiff / (127 * maxLen) : 0;
    var lenDiff = Math.abs(legalName.length - chosenName.length);
    surplusScore = maxLen > 0 ? lenDiff / maxLen : 0;
    period = 2 + frictionScore * 8;
    jitterAmp = 0.1 + surplusScore * 0.3;
    if (gainNode && osc) {
      osc.frequency.value = 200 * (1 + frictionScore);
    }
    if (!audioStarted) initAudio();
    infoDiv.textContent = 'Friction: ' + frictionScore.toFixed(3) +
      ' | Period: ' + period.toFixed(1) + 's | Jitter: ' + jitterAmp.toFixed(3);
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!legalName && !chosenName) {
      requestAnimationFrame(draw);
      return;
    }
    var t = performance.now() / 1000;
    var fontSize = 48;
    ctx.font = 'bold ' + fontSize + 'px system-ui, -apple-system, sans-serif';
    ctx.textBaseline = 'middle';
    var charWidth = ctx.measureText('M').width;
    var maxLen = Math.max(legalName.length, chosenName.length);
    var startX = (canvas.width - maxLen * charWidth) / 2;
    var y1 = canvas.height / 2 - 30;
    var y2 = canvas.height / 2 + 30;

    for (var i = 0; i < legalName.length; i++) {
      var baseAlpha = 1 - weight;
      var phase = perCharDiffNorm[i] ? perCharDiffNorm[i] * Math.PI * 2 : 0;
      var alpha = baseAlpha + jitterAmp * Math.sin(t * 2 * Math.PI / period + phase);
      alpha = Math.max(0, Math.min(1, alpha));
      var xOff = jitterAmp * 5 * Math.sin(t * 2 * Math.PI / period + phase);
      var yOff = jitterAmp * 3 * Math.cos(t * 2 * Math.PI / period + phase + 1.5);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = '#003049';
      ctx.fillText(legalName[i], startX + i * charWidth + xOff, y1 + yOff);
    }
    for (var i = 0; i < chosenName.length; i++) {
      var baseAlpha = weight;
      var phase = perCharDiffNorm[i] ? perCharDiffNorm[i] * Math.PI * 2 : 0;
      var alpha = baseAlpha + jitterAmp * Math.sin(t * 2 * Math.PI / period + phase);
      alpha = Math.max(0, Math.min(1, alpha));
      var xOff = jitterAmp * 5 * Math.sin(t * 2 * Math.PI / period + phase);
      var yOff = jitterAmp * 3 * Math.cos(t * 2 * Math.PI / period + phase + 1.5);
      ctx.globalAlpha = alpha;
      ctx.fillStyle = '#c1121f';
      ctx.fillText(chosenName[i], startX + i * charWidth + xOff, y2 + yOff);
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  legalInput.addEventListener('input', updateParams);
  chosenInput.addEventListener('input', updateParams);
  weightSlider.addEventListener('input', updateParams);
  document.getElementById('save-btn').addEventListener('click', function() {
    var link = document.createElement('a');
    link.download = 'name-fold-moment.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
  });
  updateParams();
  draw();
})();
</script>
</body>
</html>''')


def process(text: str) -> str:
    """Return an interactive HTML canvas for two name layers breathing together."""
    parts = text.split('|') if '|' in text else ["", ""]
    legal = parts[0].strip()[:40] if parts else ""
    chosen = parts[1].strip()[:40] if len(parts) > 1 else ""
    weight_str = parts[2].strip() if len(parts) > 2 else "0.5"
    try:
        w = float(weight_str)
        w = max(0.0, min(1.0, w))
    except (ValueError, TypeError):
        w = 0.5
    return TEMPLATE.render(legal=legal, chosen=chosen, weight=w)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(process(sys.argv[1]))
    else:
        print(process(""))