
"""Color System CSS Generator - interactive HTML tool."""
import base64
import re
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Color System CSS Generator</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;padding:20px;transition:background .3s,color .3s;}
#entry,#active{max-width:1000px;margin:0 auto;}
textarea{width:100%;height:200px;font-family:monospace;padding:10px;box-sizing:border-box;}
button{padding:8px 16px;margin:5px;cursor:pointer;}
#split{display:flex;gap:20px;flex-wrap:wrap;}
#swatches{flex:1;min-width:300px;display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;}
.swatch-card{border:1px solid #ccc;padding:10px;border-radius:8px;background:#f9f9f9;}
.swatch-light,.swatch-dark{width:100%;height:40px;border-radius:4px;margin-bottom:5px;}
#code-panel{flex:1;min-width:300px;}
#css-code{background:#f4f4f4;padding:15px;border-radius:8px;overflow:auto;white-space:pre-wrap;font-family:monospace;max-height:400px;}
#toast{display:none;position:fixed;bottom:20px;right:20px;background:#333;color:#fff;padding:10px 20px;border-radius:8px;z-index:1000;}
</style>
</head>
<body>
<div id="entry">
<h2>Paste your color tokens</h2>
<textarea id="input-text" placeholder="token-name #lighthex [#darkhex]"></textarea>
<button id="generate-btn">Generate CSS</button>
</div>
<div id="active" style="display:none">
<div id="split">
<div id="swatches"></div>
<div id="code-panel">
<button id="copy-btn">Copy CSS</button><button id="download-btn">Download CSS</button>
<pre id="css-code">{{ initial_css }}</pre>
</div>
</div>
<button id="toggle-bg">Toggle Preview Background</button>
</div>
<div id="toast">Copied!</div>
<script>
var INITIAL_INPUT = atob('{{ encoded_input }}');
document.getElementById('input-text').value = INITIAL_INPUT;

function hexToRgb(h){var v=parseInt(h.slice(1),16);return[(v>>16)&255,(v>>8)&255,v&255];}
function rgbToHex(r,g,b){return'#'+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1);}
function rgbToHsl(r,g,b){r/=255;g/=255;b/=255;var max=Math.max(r,g,b),min=Math.min(r,g,b),h,s,l=(max+min)/2;if(max===min){h=s=0;}else{var d=max-min;s=l>0.5?d/(2-max-min):d/(max+min);switch(max){case r:h=((g-b)/d+(g<b?6:0))/6;break;case g:h=((b-r)/d+2)/6;break;case b:h=((r-g)/d+4)/6;}}return[h,s,l];}
function hslToRgb(h,s,l){var r,g,b;if(s===0){r=g=b=l;}else{function hue2rgb(p,q,t){if(t<0)t+=1;if(t>1)t-=1;if(t<1/6)return p+(q-p)*6*t;if(t<1/2)return q;if(t<2/3)return p+(q-p)*(2/3-t)*6;return p;}var q=l<0.5?l*(1+s):l+s-l*s,p=2*l-q;r=hue2rgb(p,q,h+1/3);g=hue2rgb(p,q,h);b=hue2rgb(p,q,h-1/3);}return[Math.round(r*255),Math.round(g*255),Math.round(b*255)];}
function generateDark(hex){var rgb=hexToRgb(hex);var hsl=rgbToHsl(rgb[0],rgb[1],rgb[2]);var newL=Math.max(0,Math.min(1,hsl[2]-0.3));var nrgb=hslToRgb(hsl[0],hsl[1],newL);return rgbToHex(nrgb[0],nrgb[1],nrgb[2]);}
function isHex(s){return /^#[0-9a-fA-F]{6}$/.test(s);}

function parseAndGenerate(text){
  var parts=[];
  var lines=text.split('\n');
  for(var i=0;i<lines.length;i++){
    var line=lines[i].trim();
    if(!line) continue;
    var lp=line.split(/[,\t ]+/);
    for(var j=0;j<lp.length;j++) parts.push(lp[j]);
  }
  var tokens=[];
  var seen={};
  var idx=0;
  while(idx<parts.length){
    var name=parts[idx];
    if(idx+1>=parts.length) break;
    var light=parts[idx+1];
    if(!isHex(light)){idx+=1;continue;}
    if(idx+2<parts.length&&isHex(parts[idx+2])){
      var dark=parts[idx+2];
      tokens.push({name:name,light:light,dark:dark});
      seen[name]=true;
      idx+=3;
    }else{
      tokens.push({name:name,light:light,dark:generateDark(light)});
      seen[name]=true;
      idx+=2;
    }
  }
  if(!seen['error']) tokens.push({name:'error',light:'#ff0000',dark:'#990000'});
  return {tokens:tokens};
}

document.getElementById('generate-btn').addEventListener('click',function(){
  var text=document.getElementById('input-text').value;
  var result=parseAndGenerate(text);
  var tokens=result.tokens;
  var css='/* Color System */\n:root {\n';
  tokens.forEach(function(t){css+='  --color-'+t.name+': '+t.light+';\n';});
  css+='}\n\n[data-theme="dark"] {\n';
  tokens.forEach(function(t){css+='  --color-'+t.name+': '+t.dark+';\n';});
  css+='}';
  document.getElementById('css-code').textContent=css;
  var sw=document.getElementById('swatches');sw.innerHTML='';
  tokens.forEach(function(t){
    var card=document.createElement('div');card.className='swatch-card';
    card.innerHTML='<div class="swatch-light" style="background:'+t.light+'"></div><div class="swatch-dark" style="background:'+t.dark+'"></div><span>'+t.name+'</span><br><small>'+t.light+' / '+t.dark+'</small>';
    sw.appendChild(card);
  });
  document.getElementById('entry').style.display='none';
  document.getElementById('active').style.display='block';
});

var darkMode=false;
document.getElementById('toggle-bg').addEventListener('click',function(){
  darkMode=!darkMode;
  document.body.style.backgroundColor=darkMode?'#222':'#fff';
  document.body.style.color=darkMode?'#eee':'#333';
});
document.getElementById('copy-btn').addEventListener('click',function(){
  navigator.clipboard.writeText(document.getElementById('css-code').textContent).then(function(){
    var t=document.getElementById('toast');t.style.display='block';setTimeout(function(){t.style.display='none';},2000);
  });
});
document.getElementById('download-btn').addEventListener('click',function(){
  var blob=new Blob([document.getElementById('css-code').textContent],{type:'text/css'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='colors.css';a.click();
});
</script>
</body>
</html>''')

HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

def hex_to_rgb(h):
    v = int(h.lstrip('#'), 16)
    return [(v >> 16) & 255, (v >> 8) & 255, v & 255]

def rgb_to_hex(r, g, b):
    return '#' + ''.join(f'{c:02x}' for c in (r, g, b))

def rgb_to_hsl(r, g, b):
    r, g, b = r/255, g/255, b/255
    mx = max(r, g, b)
    mn = min(r, g, b)
    l = (mx + mn) / 2
    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:
            h = ((g - b) / d + (6 if g < b else 0)) / 6
        elif mx == g:
            h = ((b - r) / d + 2) / 6
        else:
            h = ((r - g) / d + 4) / 6
    return [h, s, l]

def hsl_to_rgb(h, s, l):
    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    return [round(r*255), round(g*255), round(b*255)]

def generate_dark(light_hex):
    r, g, b = hex_to_rgb(light_hex)
    h, s, l = rgb_to_hsl(r, g, b)
    new_l = max(0.0, min(1.0, l - 0.3))
    nr, ng, nb = hsl_to_rgb(h, s, new_l)
    return rgb_to_hex(nr, ng, nb)

DEFAULT_TOKENS = {
    'error': ('#ff0000', '#990000'),
}

def parse_tokens(text):
    """Parse token text and return list of (name, light, dark)."""
    all_parts = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        all_parts.extend(re.split(r'[,\t ]+', line))
    
    tokens = []
    seen = set()
    i = 0
    while i < len(all_parts):
        name = all_parts[i]
        if i + 1 >= len(all_parts):
            break
        light = all_parts[i + 1]
        if not HEX_RE.match(light):
            i += 1
            continue
        
        if i + 2 < len(all_parts) and HEX_RE.match(all_parts[i + 2]):
            dark = all_parts[i + 2]
            tokens.append((name, light, dark))
            seen.add(name)
            i += 3
        else:
            tokens.append((name, light, generate_dark(light)))
            seen.add(name)
            i += 2
    
    # Add default tokens
    for def_name, (def_light, def_dark) in DEFAULT_TOKENS.items():
        if def_name not in seen:
            tokens.append((def_name, def_light, def_dark))
    
    return tokens

def generate_css(tokens):
    css = '/* Color System */\n:root {\n'
    for name, light, dark in tokens:
        css += f'  --color-{name}: {light};\n'
    css += '}\n\n[data-theme="dark"] {\n'
    for name, light, dark in tokens:
        css += f'  --color-{name}: {dark};\n'
    css += '}'
    return css

def process(text: str) -> str:
    """Generate interactive HTML tool for color token to CSS conversion."""
    if not text.strip():
        return '<!DOCTYPE html><html lang="en"><head><title>Color System CSS Generator</title></head><body><h1>Color System CSS Generator</h1><p>No tokens provided. Paste a list of color tokens (name #lighthex #darkhex) to generate CSS.</p></body></html>'
    encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
    tokens = parse_tokens(text)
    initial_css = generate_css(tokens)
    return TEMPLATE.render(encoded_input=encoded, initial_css=initial_css)

def _cli_main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = f.read()
    else:
        data = sys.stdin.read()
    print(process(data))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
