"""
Variable Font Warm-Up Wheel - Live canvas with wheel-driven axis exploration.
Requires: jinja2.
"""
import re
from jinja2 import Template

HTML_TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Variable Font Warm-Up Wheel</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght,wdth,slnt@14..32,100..900,75..125,-10..0&display=swap" rel="stylesheet">
<style>
body{margin:0;background:#f5f0e6;display:flex;justify-content:center;align-items:center;height:100vh;font-family:'Inter Variable',sans-serif;}
.container{text-align:center;}
canvas{display:block;margin:0 auto;cursor:pointer;}
#sampleText{font-size:64px;margin:20px 0;word-break:break-word;}
.axis-indicator{font-size:14px;margin-bottom:5px;}
.controls{margin-top:10px;}
.controls select,.controls input,.controls button{margin:5px;}
</style>
</head>
<body>
<div class="container">
  <canvas id="wheelCanvas" width="300" height="300"></canvas>
  <div id="sampleText">{{ sample_word }}</div>
  <div class="axis-indicator" id="axisVals"></div>
  <div class="controls">
    <select id="axis1Sel"></select>
    <select id="axis2Sel"></select>
    <br>
    <label>Speed <input type="range" id="speedSlider" min="0.1" max="3" step="0.1" value="0.5"></label>
    <select id="easingSelect">
      <option value="linear">linear</option>
      <option value="easeIn" selected>easeIn</option>
      <option value="easeOut">easeOut</option>
      <option value="easeInOut">easeInOut</option>
      <option value="sine">sine</option>
    </select>
    <button id="sweepBtn">Start Sweep</button>
    <button id="copyBtn">Copy Axes</button>
    <button id="exportBtn" style="display:none">Export CSV</button>
  </div>
</div>
<script>
(function(){
  const AXES = [
    {tag:"wght",min:300,max:900,def:450},
    {tag:"wdth",min:75,max:125,def:100},
    {tag:"slnt",min:-10,max:0,def:-5},
    {tag:"ital",min:0,max:1,def:0},
    {tag:"opsz",min:14,max:32,def:16}
  ];

  const canvas=document.getElementById('wheelCanvas');
  const ctx=canvas.getContext('2d');
  const sampleText=document.getElementById('sampleText');
  const axisVals=document.getElementById('axisVals');
  const axis1Sel=document.getElementById('axis1Sel');
  const axis2Sel=document.getElementById('axis2Sel');
  const speedSlider=document.getElementById('speedSlider');
  const easingSelect=document.getElementById('easingSelect');
  const sweepBtn=document.getElementById('sweepBtn');
  const copyBtn=document.getElementById('copyBtn');
  const exportBtn=document.getElementById('exportBtn');

  let selectedAxis1=AXES[0];
  let selectedAxis2=AXES[1];
  let isDragging=false;
  let isSweeping=false;
  let sweepRecords=[];
  let sweepStartTime=0;
  let lastFrameTime=0;
  let wheelAngle=0;
  let angularVelocity=0;
  let lastMouseAngle=0;
  let lastMouseTime=0;
  let sweepSpeed=0;

  function populateAxes() {
    [axis1Sel, axis2Sel].forEach((sel, idx) => {
      sel.innerHTML='';
      AXES.forEach(a => {
        let opt=document.createElement('option');
        opt.value=a.tag;
        opt.textContent=a.tag;
        sel.appendChild(opt);
      });
      sel.value=idx===0? selectedAxis1.tag : selectedAxis2.tag;
    });
    axis1Sel.onchange=() => {
      selectedAxis1=AXES.find(a=>a.tag===axis1Sel.value);
      if(axis1Sel.value===axis2Sel.value){
        let other = AXES.find(a=>a.tag!==axis2Sel.value)||AXES[0];
        axis2Sel.value=other.tag;
        selectedAxis2=other;
      }
      updateAll();
    };
    axis2Sel.onchange=() => {
      selectedAxis2=AXES.find(a=>a.tag===axis2Sel.value);
      if(axis2Sel.value===axis1Sel.value){
        let other = AXES.find(a=>a.tag!==axis1Sel.value)||AXES[0];
        axis1Sel.value=other.tag;
        selectedAxis1=other;
      }
      updateAll();
    };
  }
  populateAxes();

  const easings={
    linear:t=>t,
    easeIn:t=>t*t,
    easeOut:t=>1-(1-t)*(1-t),
    easeInOut:t=>t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
    sine:t=>Math.sin(t*Math.PI/2)
  };

  function getAxisValues(angle){
    let t=((angle%360+360)%360)/360;
    let easingType=easingSelect.value;
    let easeFn=easings[easingType]||easings.linear;
    let easedT=easeFn(t);
    let angleRad=easedT*2*Math.PI;
    let range1=selectedAxis1.max-selectedAxis1.min;
    let range2=selectedAxis2.max-selectedAxis2.min;
    let val1=selectedAxis1.min+range1*(0.5+0.5*Math.cos(angleRad));
    let val2=selectedAxis2.min+range2*(0.5+0.5*Math.sin(angleRad));
    // Derivative of axis values w.r.t angle (degrees)
    let dEasedT = easings[easingType]? ((easings[easingType](t+0.0001)-easings[easingType](t-0.0001))/0.0002) : 1;
    let dAngleRad=dEasedT*2*Math.PI/360;
    let dVal1=range1*0.5*(-Math.sin(angleRad))*dAngleRad;
    let dVal2=range2*0.5*Math.cos(angleRad)*dAngleRad;
    let derivMag=Math.sqrt(dVal1*dVal1+dVal2*dVal2);
    let score=Math.min(1,derivMag*8);
    return {val1,val2,score};
  }

  function updateSampleText(){
    let {val1,val2}=getAxisValues(wheelAngle%360);
    sampleText.style.fontVariationSettings=
      "'" + selectedAxis1.tag + "' " + Math.round(val1) + ", '" + selectedAxis2.tag + "' " + Math.round(val2);
    axisVals.textContent=
      selectedAxis1.tag+": "+Math.round(val1)+", "+selectedAxis2.tag+": "+Math.round(val2);
  }

  function drawWheel(){
    let {score}=getAxisValues(wheelAngle%360);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    let cx=150,cy=150,r=140;
    let hue=score*120;
    let grad=ctx.createRadialGradient(cx,cy,0,cx,cy,r);
    grad.addColorStop(0,"hsl("+hue+",100%,50%)");
    grad.addColorStop(1,"hsl("+hue+",100%,80%)");
    ctx.beginPath();
    ctx.arc(cx,cy,r,0,Math.PI*2);
    ctx.fillStyle=grad;
    ctx.fill();
    ctx.strokeStyle='#333';
    ctx.lineWidth=2;
    ctx.stroke();
    for(let a=0;a<360;a+=15){
      let rad=a*Math.PI/180;
      ctx.beginPath();
      ctx.moveTo(cx+Math.cos(rad)*(r-10),cy+Math.sin(rad)*(r-10));
      ctx.lineTo(cx+Math.cos(rad)*(r-2),cy+Math.sin(rad)*(r-2));
      ctx.strokeStyle='#fff';
      ctx.lineWidth=1;
      ctx.stroke();
    }
    let curAng=(wheelAngle%360)*Math.PI/180;
    let px=cx+Math.cos(curAng)*(r-15);
    let py=cy+Math.sin(curAng)*(r-15);
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.lineTo(px,py);
    ctx.strokeStyle='#000';
    ctx.lineWidth=3;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(px,py,4,0,2*Math.PI);
    ctx.fillStyle='#000';
    ctx.fill();
    if(isSweeping){
      let progress=((wheelAngle%360)/360);
      ctx.beginPath();
      ctx.moveTo(cx,cy);
      ctx.arc(cx,cy,r-5,-Math.PI/2,-Math.PI/2+progress*Math.PI*2);
      ctx.closePath();
      ctx.fillStyle='rgba(0,0,0,0.12)';
      ctx.fill();
    }
  }

  function updateAll(){
    updateSampleText();
    drawWheel();
    let {val1,val2}=getAxisValues(wheelAngle%360);
    copyBtn.dataset.css='font-variation-settings: "'+selectedAxis1.tag+'" '+Math.round(val1)+', "'+selectedAxis2.tag+'" '+Math.round(val2)+';';
    copyBtn.dataset.ae='['+Math.round(val1)+', '+Math.round(val2)+']';
  }

  copyBtn.addEventListener('click',()=>{
    let str=copyBtn.dataset.css+'\n'+copyBtn.dataset.ae;
    navigator.clipboard.writeText(str).catch(()=>alert('Copy failed'));
  });

  function getMouseAngle(e){
    let rect=canvas.getBoundingClientRect();
    return Math.atan2(e.clientY-(rect.top+rect.height/2),e.clientX-(rect.left+rect.width/2))*180/Math.PI;
  }
  canvas.addEventListener('mousedown',e=>{
    isDragging=true;
    lastMouseAngle=getMouseAngle(e);
    lastMouseTime=performance.now();
    e.preventDefault();
  });
  window.addEventListener('mouseup',()=>{isDragging=false;});
  window.addEventListener('mousemove',e=>{
    if(!isDragging)return;
    let now=performance.now();
    let curMouse=getMouseAngle(e);
    let delta=curMouse-lastMouseAngle;
    if(delta>180)delta-=360;
    if(delta<-180)delta+=360;
    wheelAngle+=delta;
    let dt=(now-lastMouseTime)/1000;
    if(dt>0)angularVelocity=delta/dt;
    lastMouseAngle=curMouse;
    lastMouseTime=now;
  });
  canvas.addEventListener('touchstart',e=>{
    isDragging=true;
    let touch=e.touches[0];
    let rect=canvas.getBoundingClientRect();
    lastMouseAngle=Math.atan2(touch.clientY-(rect.top+rect.height/2),touch.clientX-(rect.left+rect.width/2))*180/Math.PI;
    lastMouseTime=performance.now();
    e.preventDefault();
  });
  canvas.addEventListener('touchend',()=>{isDragging=false;});
  canvas.addEventListener('touchmove',e=>{
    if(!isDragging)return;
    e.preventDefault();
    let touch=e.touches[0];
    let rect=canvas.getBoundingClientRect();
    let curMouse=Math.atan2(touch.clientY-(rect.top+rect.height/2),touch.clientX-(rect.left+rect.width/2))*180/Math.PI;
    let now=performance.now();
    let delta=curMouse-lastMouseAngle;
    if(delta>180)delta-=360;
    if(delta<-180)delta+=360;
    wheelAngle+=delta;
    let dt=(now-lastMouseTime)/1000;
    if(dt>0)angularVelocity=delta/dt;
    lastMouseAngle=curMouse;
    lastMouseTime=now;
  });

  sweepBtn.addEventListener('click',()=>{
    isSweeping=!isSweeping;
    if(isSweeping){
      sweepBtn.textContent='Stop Sweep';
      sweepRecords=[];
      sweepStartTime=performance.now();
      sweepSpeed=parseFloat(speedSlider.value)*180;
    } else {
      sweepBtn.textContent='Start Sweep';
      if(sweepRecords.length>0)exportBtn.style.display='inline-block';
    }
  });

  exportBtn.addEventListener('click',()=>{
    let header="time,"+selectedAxis1.tag+","+selectedAxis2.tag;
    let rows=sweepRecords.map(r=>r.time.toFixed(3)+","+r.val1.toFixed(1)+","+r.val2.toFixed(1));
    let csv=header+"\n"+rows.join("\n");
    let blob=new Blob([csv],{type:'text/csv'});
    let url=URL.createObjectURL(blob);
    let a=document.createElement('a');
    a.href=url;a.download='font_axis_sweep.csv';a.click();
    URL.revokeObjectURL(url);
  });

  const FRICTION=0.97;
  function animate(now){
    let deltaSec=lastFrameTime?(now-lastFrameTime)/1000:0;
    lastFrameTime=now;
    if(isSweeping){
      wheelAngle+=sweepSpeed*deltaSec;
      angularVelocity=sweepSpeed;
      let {val1,val2}=getAxisValues(wheelAngle%360);
      sweepRecords.push({time:(now-sweepStartTime)/1000,val1,val2});
    } else if(!isDragging){
      if(Math.abs(angularVelocity)>0.5){
        wheelAngle+=angularVelocity*deltaSec;
        angularVelocity*=FRICTION;
      } else {
        angularVelocity=0;
      }
    }
    updateAll();
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
  updateAll();
})();
</script>
</body>
</html>''')

def extract_sample_word(text: str) -> str:
    """Extract a sample word from user input, falling back to whole cleaned text."""
    cleaned = text.strip()
    if not cleaned:
        return "Motion"
    # explicit patterns: "sample word X" or "word X"
    m = re.search(r'sample\s+word\s+"?(\w[\w\s]*?\w)"?', cleaned, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'word\s+"?(\w[\w\s]*?\w)"?', cleaned, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # No explicit pattern: use the entire input as sample text (up to 30 chars to avoid overflow)
    if len(cleaned) > 30:
        return cleaned[:30] + '...'
    return cleaned

def process(text: str) -> str:
    """Live variable font warm-up wheel – returns interactive HTML."""
    if not text.strip():
        return "<html><body><p>Enter a sample word to explore variable font axes.</p></body></html>"
    sample_word = extract_sample_word(text)
    return HTML_TEMPLATE.render(sample_word=sample_word)

def _cli_main():
    import sys
    if len(sys.argv) > 1:
        print(process(sys.argv[1]))
    else:
        print(process('User selects wght and wdth sample word Kinetic'))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()