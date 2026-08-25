# Requirements: jinja2
import math
import re
import json
import sys
from typing import List
from jinja2 import Template

DEFAULT = [0.36, 0.07, 0.19, 0.97]

PRESETS = [
    ("ease", 0.25, 0.1, 0.25, 1.0),
    ("ease-in", 0.42, 0.0, 1.0, 1.0),
    ("ease-out", 0.0, 0.0, 0.58, 1.0),
    ("ease-in-out", 0.42, 0.0, 0.58, 1.0),
    ("power1.in", 0.5, 0.0, 1.0, 1.0),
    ("power1.out", 0.0, 0.0, 0.5, 1.0),
    ("power1.inOut", 0.5, 0.0, 0.5, 1.0),
    ("power2.in", 0.5, 0.0, 0.75, 1.0),
    ("power2.out", 0.25, 0.0, 0.5, 1.0),
    ("power2.inOut", 0.5, 0.0, 0.25, 1.0),
    ("power3.in", 0.66, 0.0, 1.0, 1.0),
    ("power3.out", 0.0, 0.0, 0.33, 1.0),
    ("power3.inOut", 0.66, 0.0, 0.33, 1.0),
    ("power4.in", 0.8, 0.0, 1.0, 1.0),
    ("power4.out", 0.0, 0.0, 0.2, 1.0),
    ("power4.inOut", 0.8, 0.0, 0.2, 1.0),
    ("sine.in", 0.47, 0.0, 0.745, 0.715),
    ("sine.out", 0.39, 0.575, 0.565, 1.0),
    ("sine.inOut", 0.445, 0.05, 0.55, 0.95),
    ("expo.in", 0.95, 0.05, 0.795, 0.035),
    ("expo.out", 0.19, 1.0, 0.22, 1.0),
    ("expo.inOut", 1.0, 0.0, 0.0, 1.0),
    ("circ.in", 0.6, 0.04, 0.98, 0.335),
    ("circ.out", 0.075, 0.82, 0.165, 1.0),
    ("circ.inOut", 0.785, 0.135, 0.15, 0.86),
]

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Easing Curve Rosetta</title>
<style>
:root{font-family:system-ui,Segoe UI,Arial;background:#110f17;color:#f4f0ff}
body{max-width:980px;margin:0 auto;padding:24px}
h1{font-size:26px;margin:0 0 4px}
.sub{color:#a99ec4;margin-bottom:18px}
.wrap{display:grid;grid-template-columns:620px 1fr;gap:18px}
@media(max-width:820px){.wrap{grid-template-columns:1fr}}
canvas{background:#171420;border:1px solid #312a3e;border-radius:14px;cursor:crosshair;width:100%}
input,select{width:100%;padding:10px;font-family:monospace;background:#171420;color:#f4f0ff;border:1px solid #312a3e;border-radius:10px;margin-bottom:10px}
.card{background:#171420;border:1px solid #312a3e;border-radius:12px;padding:12px;margin-bottom:12px}
.card h3{margin:0 0 6px;font-size:14px;color:#c9bde2}
pre{white-space:pre-wrap;word-break:break-all;background:#0c0a11;border:1px solid #2b2338;border-radius:8px;padding:8px;font-family:monospace;font-size:12px;color:#cff5c6;margin:0 0 8px}
button{background:#5b4c8a;border:0;color:white;padding:7px 10px;border-radius:7px;cursor:pointer;font-size:12px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.readout{font-family:monospace;color:#b7f5b0;margin-right:8px}
</style>
</head>
<body>
<h1>Easing Curve Rosetta</h1>
<div class="sub">Convert one easing curve into AE, CSS, GSAP + Webflow.</div>
<div class="wrap">
<div>
<canvas id="cv" width="620" height="400"></canvas>
<input id="inp" value="{{ source_text|e }}" placeholder="cubic-bezier(...) or preset token">
<select id="presetSelect"><option value="">Preset token...</option></select>
<div class="row"><span>Area under curve: <span id="area" class="readout">0</span></span><span>Mid velocity: <span id="vel" class="readout">0</span></span><span>Overshoot samples: <span id="over" class="readout">0</span></span></div>
</div>
<div id="cards">{{ initial_cards|safe }}</div>
</div>
<script>
(function(){
const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
const inp=document.getElementById('inp');
const presetSelect=document.getElementById('presetSelect');
const areaEl=document.getElementById('area');
const velEl=document.getElementById('vel');
const overEl=document.getElementById('over');
const cardsEl=document.getElementById('cards');
const PRESETS={{ presets_json }};
const INITP={{ init_p_json }};
let c=[INITP[0],INITP[1],INITP[2],INITP[3]];
let matched='ease';
const margin=42,w=cv.width-margin*2,h=cv.height-margin*2;
PRESETS.forEach(function(pr){var opt=document.createElement('option');opt.value=pr[0];opt.textContent=pr[0];presetSelect.appendChild(opt);});
function fmt(v){return Math.round(v*100)/100;}
function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v));}
function clamp4(p){return [clamp(p[0],0,1),clamp(p[1],-0.5,1.5),clamp(p[2],0,1),clamp(p[3],-0.5,1.5)];}
function bez(t){var mt=1-t;return [3*mt*mt*t*c[0]+3*mt*t*t*c[2]+t*t*t,3*mt*mt*t*c[1]+3*mt*t*t*c[3]+t*t*t];}
function dxdt(t){var mt=1-t;return 3*mt*mt*c[0]+6*mt*t*(c[2]-c[0])+3*t*t*(1-c[2]);}
function solveX(x){var t=x;for(var i=0;i<5;i++){var mt=1-t;var cx=3*mt*mt*t*c[0]+3*mt*t*t*c[2]+t*t*t;if(Math.abs(cx-x)<1e-6)break;var d=dxdt(t);if(Math.abs(d)<1e-9)break;t-=(cx-x)/d;}return clamp(t,0,1);}
function sample(n){var ys=[];for(var i=0;i<=n;i++){ys.push(bez(solveX(i/n))[1]);}return ys;}
function area(ys){var a=0;for(var i=0;i<ys.length-1;i++){a+=(ys[i]+ys[i+1])/2*(1/(ys.length-1));}return a;}
function midVel(ys){var m=Math.floor(ys.length/2);return (ys[m+1]-ys[m])/(1/(ys.length-1));}
function overCount(ys){var n=0;for(var i=0;i<ys.length;i++){if(ys[i]>1||ys[i]<0)n++;}return n;}
function matchCurve(){var ys=sample(100);var best='ease';var bestM=1e9;for(var i=0;i<PRESETS.length;i++){var pr=PRESETS[i];var old=c.slice();c=[pr[1],pr[2],pr[3],pr[4]];var py=sample(100);c=old;var m=0;for(var j=0;j<ys.length;j++){var d=ys[j]-py[j];m+=d*d;}m/=ys.length;if(m<bestM){bestM=m;best=pr[0];}}return best;}
function webflowPreset(nm){if(nm.indexOf('inOut')>=0||nm.indexOf('in-out')>=0)return 'Ease In Out';if(nm.indexOf('in')>=0)return 'Ease In';if(nm.indexOf('out')>=0)return 'Ease Out';return 'Ease In Out';}
function parseInputText(txt){txt=(txt||'').trim();if(!txt)return null;var m=txt.match(/cubic-bezier\(\s*([^)]*)\)/i);if(m){var nums=(m[1].match(/-?\d+(?:\.\d+)?/g)||[]).map(Number);if(nums.length>=4)return clamp4([nums[0],nums[1],nums[2],nums[3]]);}for(var i=0;i<PRESETS.length;i++){if(txt.toLowerCase()===PRESETS[i][0].toLowerCase())return [PRESETS[i][1],PRESETS[i][2],PRESETS[i][3],PRESETS[i][4]];}m=txt.match(/\bout\s*=\s*(\d+)%\s*\/\s*in\s*=\s*(\d+)%\b/i);if(m){var out=parseFloat(m[1])/100;var inn=parseFloat(m[2])/100;return clamp4([out,0,1-inn,1]);}var nums=(txt.match(/-?\d+(?:\.\d+)?/g)||[]).map(Number);if(nums.length>=4)return clamp4([nums[0],nums[1],nums[2],nums[3]]);return null;}
function artifacts(){var ys=sample(200);var ar=area(ys),mv=midVel(ys),ov=overCount(ys);matched=matchCurve();var css='cubic-bezier('+fmt(c[0])+', '+fmt(c[1])+', '+fmt(c[2])+', '+fmt(c[3])+')';var gsapCustom='M0,0 C'+fmt(c[0])+','+fmt(c[1])+' '+fmt(c[2])+','+fmt(c[3])+' 1,1';var embed='.ease-rosetta{animation:rosetta 1s cubic-bezier('+fmt(c[0])+','+fmt(c[1])+','+fmt(c[2])+','+fmt(c[3])+') both}.ease-rosetta > *{animation-delay:calc(var(--i)*0.08s)}';var ae={outInfluence:Math.round(c[0]*100),inInfluence:Math.round((1-c[2])*100)};var handoff='CSS: '+css+'\nGSAP CustomEase: '+gsapCustom+'\nGSAP Named: '+matched+'\nWebflow Preset: '+webflowPreset(matched)+'\nWebflow Embed: '+embed+'\nAE: out='+ae.outInfluence+'%/in='+ae.inInfluence+'%\nMatched Preset Rationale: closest sampled curve is '+matched+'.';return {css:css,gsapCustom:gsapCustom,gsapNamed:matched,webflowPreset:webflowPreset(matched),webflowEmbed:embed,ae:ae,area:ar,midV:mv,over:ov,handoff:handoff};}
function copyText(code){if(navigator.clipboard&&navigator.clipboard.writeText){try{navigator.clipboard.writeText(code).catch(function(){});}catch(e){}}else{var ta=document.createElement('textarea');ta.value=code;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);}}
function renderCards(a){var card='';card+='<div class="card"><h3>CSS cubic-bezier</h3><pre>'+a.css+'</pre><button data-copy="css">Copy CSS</button></div>';card+='<div class="card"><h3>GSAP CustomEase</h3><pre>'+a.gsapCustom+'</pre><button data-copy="gsap">Copy GSAP</button></div>';card+='<div class="card"><h3>GSAP Named</h3><pre>'+a.gsapNamed+'</pre></div>';card+='<div class="card"><h3>Webflow Preset</h3><pre>'+a.webflowPreset+'</pre></div>';card+='<div class="card"><h3>AE Influence</h3><pre>out='+a.ae.outInfluence+'%/in='+a.ae.inInfluence+'%</pre><button data-copy="ae">Copy AE</button></div>';card+='<div class="card"><h3>Webflow Embed</h3><pre>'+a.webflowEmbed+'</pre><button data-copy="embed">Copy Embed</button></div>';card+='<div class="card"><h3>Handoff block</h3><pre>'+a.handoff+'</pre><button data-copy="handoff" aria-label="copy handoff block">Copy handoff block</button></div>';cardsEl.innerHTML=card;document.querySelectorAll('[data-copy]').forEach(function(b){b.onclick=function(){var key=b.getAttribute('data-copy'),code=a.handoff;if(key==='css')code=a.css;if(key==='gsap')code=a.gsapCustom;if(key==='ae')code='out='+a.ae.outInfluence+'%/in='+a.ae.inInfluence+'%';if(key==='embed')code=a.webflowEmbed;copyText(code);};});}
function draw(){if(!ctx)return;ctx.clearRect(0,0,cv.width,cv.height);ctx.strokeStyle='#2b2338';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(margin,margin);ctx.lineTo(margin+w,margin);ctx.lineTo(margin+w,margin+h);ctx.lineTo(margin,margin+h);ctx.closePath();ctx.stroke();ctx.strokeStyle='#3a3149';ctx.beginPath();ctx.moveTo(margin,margin+h);ctx.lineTo(margin+w,margin);ctx.stroke();ctx.strokeStyle='#b7f5b0';ctx.lineWidth=2;ctx.beginPath();for(var i=0;i<=200;i++){var t=i/200;var p=bez(t);var x=margin+p[0]*w;var y=margin+(1-p[1])*h;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();ctx.strokeStyle='#8b7fb8';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(margin,margin+h);ctx.lineTo(margin+c[0]*w,margin+(1-c[1])*h);ctx.moveTo(margin+w,margin);ctx.lineTo(margin+c[2]*w,margin+(1-c[3])*h);ctx.stroke();}
function refresh(){var a=artifacts();areaEl.textContent=fmt(a.area);velEl.textContent=fmt(a.midV);overEl.textContent=a.over;renderCards(a);if(presetSelect){for(var i=0;i<presetSelect.options.length;i++){if(presetSelect.options[i].value===matched)presetSelect.selectedIndex=i;}}draw();}
inp.addEventListener('input', function(){var p=parseInputText(inp.value);if(p){c=p;refresh();}});
inp.addEventListener('change', function(){var p=parseInputText(inp.value);if(p){c=p;refresh();}});
presetSelect.addEventListener('change', function(){var p=parseInputText(presetSelect.value);if(p){inp.value=presetSelect.value;c=p;refresh();}});
refresh();
})();
</script>
</body>
</html>''')


def clamp_val(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_bezier(text: str) -> List[float]:
    text = text.strip()
    if not text:
        return list(DEFAULT)

    m = re.search(r'out\s*=\s*(\d+)%\s*/\s*in\s*=\s*(\d+)%', text, re.IGNORECASE)
    if m:
        out = float(m.group(1)) / 100.0
        inn = float(m.group(2)) / 100.0
        p1x = clamp_val(out, 0.0, 1.0)
        p1y = 0.0
        p2x = clamp_val(1.0 - inn, 0.0, 1.0)
        p2y = 1.0
        return [p1x, p1y, p2x, p2y]

    m = re.search(r'cubic-bezier\(\s*([^)]*)\)', text, re.IGNORECASE)
    if m:
        nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', m.group(1))]
        if len(nums) >= 4:
            return [
                clamp_val(nums[0], 0.0, 1.0),
                clamp_val(nums[1], -0.5, 1.5),
                clamp_val(nums[2], 0.0, 1.0),
                clamp_val(nums[3], -0.5, 1.5),
            ]

    for name, x1, y1, x2, y2 in PRESETS:
        if text.lower() == name.lower():
            return [x1, y1, x2, y2]

    nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]
    if len(nums) >= 4:
        return [
            clamp_val(nums[0], 0.0, 1.0),
            clamp_val(nums[1], -0.5, 1.5),
            clamp_val(nums[2], 0.0, 1.0),
            clamp_val(nums[3], -0.5, 1.5),
        ]

    return list(DEFAULT)


def _round_js(x: float) -> float:
    if math.isnan(x) or math.isinf(x):
        return x
    if x < 0:
        return math.ceil(x - 0.5)
    return math.floor(x + 0.5)


def _fmt(v: float) -> str:
    r = _round_js(v * 100.0) / 100.0
    if r == 0:
        return "0"
    if abs(r - round(r)) < 1e-12:
        return str(int(round(r)))
    return str(r)


def _bez_y(p: List[float], t: float) -> float:
    mt = 1.0 - t
    return 3.0 * mt * mt * t * p[1] + 3.0 * mt * t * t * p[3] + t * t * t


def _dxdt(p: List[float], t: float) -> float:
    mt = 1.0 - t
    return 3.0 * mt * mt * p[0] + 6.0 * mt * t * (p[2] - p[0]) + 3.0 * t * t * (1.0 - p[2])


def _solve_x(p: List[float], x: float) -> float:
    t = x
    for _ in range(5):
        mt = 1.0 - t
        cx = 3.0 * mt * mt * t * p[0] + 3.0 * mt * t * t * p[2] + t * t * t
        if abs(cx - x) < 1e-6:
            break
        d = _dxdt(p, t)
        if abs(d) < 1e-9:
            break
        t -= (cx - x) / d
    return max(0.0, min(1.0, t))


def _sample(p: List[float], n: int = 100) -> List[float]:
    return [_bez_y(p, _solve_x(p, i / n)) for i in range(n + 1)]


def _classify(p: List[float]) -> str:
    ys = _sample(p, 100)
    best = "ease"
    best_m = 1e9
    for name, x1, y1, x2, y2 in PRESETS:
        py = _sample([x1, y1, x2, y2], 100)
        m = sum((a - b) * (a - b) for a, b in zip(ys, py)) / len(ys)
        if m < best_m:
            best_m = m
            best = name
    return best


def _webflow_preset(name: str) -> str:
    if 'inOut' in name or 'in-out' in name:
        return 'Ease In Out'
    if 'in' in name:
        return 'Ease In'
    if 'out' in name:
        return 'Ease Out'
    return 'Ease In Out'


def _build_initial_cards(p: List[float]) -> str:
    matched = _classify(p)
    css = 'cubic-bezier(' + _fmt(p[0]) + ', ' + _fmt(p[1]) + ', ' + _fmt(p[2]) + ', ' + _fmt(p[3]) + ')'
    gsap_custom = 'M0,0 C' + _fmt(p[0]) + ',' + _fmt(p[1]) + ' ' + _fmt(p[2]) + ',' + _fmt(p[3]) + ' 1,1'
    embed = '.ease-rosetta{animation:rosetta 1s cubic-bezier(' + _fmt(p[0]) + ',' + _fmt(p[1]) + ',' + _fmt(p[2]) + ',' + _fmt(p[3]) + ') both}.ease-rosetta > *{animation-delay:calc(var(--i)*0.08s)}'
    ae_out = int(_round_js(p[0] * 100.0))
    ae_in = int(_round_js((1.0 - p[2]) * 100.0))
    handoff = 'CSS: ' + css + '\nGSAP CustomEase: ' + gsap_custom + '\nGSAP Named: ' + matched + '\nWebflow Preset: ' + _webflow_preset(matched) + '\nWebflow Embed: ' + embed + '\nAE: out=' + str(ae_out) + '%/in=' + str(ae_in) + '%\nMatched Preset Rationale: closest sampled curve is ' + matched + '.'
    cards = ''
    cards += '<div class="card"><h3>CSS cubic-bezier</h3><pre>' + css + '</pre><button data-copy="css">Copy CSS</button></div>'
    cards += '<div class="card"><h3>GSAP CustomEase</h3><pre>' + gsap_custom + '</pre><button data-copy="gsap">Copy GSAP</button></div>'
    cards += '<div class="card"><h3>GSAP Named</h3><pre>' + matched + '</pre></div>'
    cards += '<div class="card"><h3>Webflow Preset</h3><pre>' + _webflow_preset(matched) + '</pre></div>'
    cards += '<div class="card"><h3>AE Influence</h3><pre>out=' + str(ae_out) + '%/in=' + str(ae_in) + '%</pre><button data-copy="ae">Copy AE</button></div>'
    cards += '<div class="card"><h3>Webflow Embed</h3><pre>' + embed + '</pre><button data-copy="embed">Copy Embed</button></div>'
    cards += '<div class="card"><h3>Handoff block</h3><pre>' + handoff + '</pre><button data-copy="handoff" aria-label="copy handoff block">Copy handoff block</button></div>'
    return cards


def _cli_main() -> None:
    text = sys.stdin.read().strip()
    if not text:
        text = 'cubic-bezier(0.36, 0.07, 0.19, 0.97)'
    print(process(text))


def process(text: str) -> str:
    """Convert an easing token into an interactive multi-format Rosetta HTML artifact."""
    if not text.strip():
        return "[Easing Curve Rosetta] Paste a cubic-bezier value, a GSAP named ease, or an AE out/in pair."

    p = parse_bezier(text)
    html = TEMPLATE.render(
        source_text=text,
        presets_json=json.dumps([[n, a, b, c, d] for n, a, b, c, d in PRESETS]),
        init_p_json=json.dumps(p),
        initial_cards=_build_initial_cards(p),
    )
    return html


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
