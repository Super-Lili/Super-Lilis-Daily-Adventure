"""
The Humming Page – a persistent low‑frequency sonic environment that
responds to typed input in real time.  Mode 3 (HTML page with Web Audio
API and visual feedback).
"""

from jinja2 import Template

_TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Humming Page</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#0f1117;display:flex;justify-content:center;align-items:center;height:100vh;overflow:hidden;font-family:sans-serif;}
.container{position:relative;text-align:center;}
.glow{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:300px;height:300px;background:radial-gradient(circle,rgba(70,130,180,0.3) 0%,rgba(15,17,23,0) 70%);border-radius:50%;filter:blur(40px);z-index:0;}
textarea{position:relative;z-index:1;background:transparent;border:none;outline:none;resize:none;width:500px;height:200px;color:#d0d7e5;font-size:18px;line-height:1.6;padding:20px;caret-color:#a0b4d0;}
textarea::placeholder{color:#4a5260;}
.pulse-circle{position:absolute;bottom:-100px;left:50%;transform:translate(-50%,0) scale(1);width:120px;height:120px;border-radius:50%;background:radial-gradient(circle at 30% 30%,rgba(120,150,200,0.5),rgba(70,130,180,0.15));z-index:0;transition:transform 0.05s linear;}
#status{position:absolute;bottom:-150px;left:50%;transform:translateX(-50%);color:rgba(160,180,210,0.7);font-size:14px;z-index:2;white-space:nowrap;}
</style>
</head>
<body>
<div class="container">
  <div class="glow"></div>
  <textarea id="t" placeholder="type your thoughts…">{{ it|e }}</textarea>
  <div class="pulse-circle" id="circle"></div>
  <span id="status"></span>
</div>
<script>
(function() {
  var ctx, osc, gn, bv=0.3, cp={f:61,d:0.8,r:0.2}, tp={f:61,d:0.8,r:0.2}, tr=null, idle=null, c=document.getElementById('circle'), ta=document.getElementById('t'), status=document.getElementById('status');
  var ts=[], initialised=false;
  function mc(v,i0,i1,o0,o1){var t=Math.max(i0,Math.min(i1,v));return o0+(t-i0)*(o1-o0)/(i1-i0);}
  function gm(){
    var txt=ta.value,ch=txt.length,w=txt.trim().split(/\s+/).filter(function(w){return w.length>0;}),wc=w.length,twc=w.reduce(function(s,w){return s+w.length},0),awl=wc?twc/wc:0;
    return {ch:ch,wc:wc,awl:awl};
  }
  function desc(p){
    var fdesc = p.f < 62 ? 'low' : (p.f > 64 ? 'high' : 'mid');
    var ddesc = p.d < 0.7 ? 'shallow' : (p.d > 1.5 ? 'deep' : 'gentle');
    var rdesc = p.r < 0.15 ? 'slow' : (p.r > 0.25 ? 'fast' : 'steady');
    return 'A ' + fdesc + ', ' + ddesc + ' hum with a ' + rdesc + ' rhythm.';
  }
  function upTarget(){
    var m=gm(),s=0;
    if(ts.length>1){var dur=(ts[ts.length-1]-ts[0])/1000;s=dur>0?(ts.length-1)/dur:0;}
    tp.f=mc(m.wc,0,100,58,65);
    tp.d=mc(s,0,10,2.0,0.5);
    tp.r=mc(m.awl,3,8,0.3,0.1);
    tr=null;
    if(idle){clearTimeout(idle);}
    idle=setTimeout(rampDef,3000);
    status.textContent = desc(tp);
  }
  function rampDef(){
    tr={st:performance.now(),dur:1.5};
    tp.f=61;tp.d=0.8;tp.r=0.2;
    status.textContent = desc(tp);
  }
  function kv(e){
    var now=Date.now();ts.push(now);if(ts.length>10)ts.shift();
    upTarget();
  }
  function interp(cur,tar,t){return cur+(tar-cur)*Math.min(1,t);}
  function update(now){
    requestAnimationFrame(update);
    if(!ctx)return;
    var tnow=performance.now();
    var prog=0;
    if(tr){
      var el=(tnow-tr.st)/tr.dur;
      prog=Math.min(1,el);
      cp.f=interp(cp.f,tp.f,prog);
      cp.d=interp(cp.d,tp.d,prog);
      cp.r=interp(cp.r,tp.r,prog);
      if(prog>=1)tr=null;
    }else{
      cp.f=tp.f;cp.d=tp.d;cp.r=tp.r;
    }
    var time=ctx.currentTime;
    var pulse=cp.d*Math.sin(2*Math.PI*cp.r*time);
    var gain=Math.max(0,Math.min(0.9,bv*(1+pulse)));
    gn.gain.cancelScheduledValues(time);
    gn.gain.setValueAtTime(gain,time);
    osc.frequency.setValueAtTime(cp.f,time);
    var sc=1+cp.d*0.15*Math.sin(2*Math.PI*cp.r*time);
    c.style.transform='translate(-50%,0) scale('+sc+')';
  }
  function applyInitialText(){
    if(initialised)return;
    initialised=true;
    ts.push(Date.now());
    upTarget();
    cp.f=tp.f;cp.d=tp.d;cp.r=tp.r;
  }
  function init(){
    ctx=new (window.AudioContext||window.webkitAudioContext)();
    osc=ctx.createOscillator();
    osc.type='sine';
    osc.frequency.value=61;
    gn=ctx.createGain();
    gn.gain.value=0;
    osc.connect(gn);
    gn.connect(ctx.destination);
    osc.start();
    var st=ctx.state;
    var resumeAndStart=function(){
      gn.gain.cancelScheduledValues(ctx.currentTime);
      gn.gain.setValueAtTime(0,ctx.currentTime);
      gn.gain.linearRampToValueAtTime(bv,ctx.currentTime+1.5);
      requestAnimationFrame(update);
      setTimeout(applyInitialText,2000);
    };
    if(st==='suspended'){
      var resume=function(){
        ctx.resume().then(function(){
          resumeAndStart();
        });
        document.removeEventListener('click',resume);
        document.removeEventListener('keydown',resume);
      };
      document.addEventListener('click',resume);
      document.addEventListener('keydown',resume);
    }else{
      resumeAndStart();
    }
  }
  window.addEventListener('load',function(){
    ta.addEventListener('input',kv);
    ta.addEventListener('keyup',kv);
    init();
  });
})();
</script>
</body>
</html>''')


def process(text: str) -> str:
    """Return the full Humming Page HTML with initial text pre-filled."""
    initial = text.strip()[:500] if text else ""
    return _TEMPLATE.render(it=initial)


def _cli_main() -> None:
    import sys
    text = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    print(process(text))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()