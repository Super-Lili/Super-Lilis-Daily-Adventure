"""Bumble Cursor - Mode 3 interactive pollen-map tool."""
from html import escape
from jinja2 import Template

TEMPLATE = Template(r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bumble Cursor</title>
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#FBF4E6;cursor:none;font-family:Georgia,'Times New Roman',serif}
#field{position:fixed;inset:0;width:100%;height:100%;z-index:0}
#ui{position:fixed;inset:0;z-index:2;pointer-events:none;display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:2rem}
h1{font-size:clamp(2rem,5vw,4.5rem);font-weight:400;letter-spacing:.2em;color:#4a3a28;margin:0;text-shadow:1px 1px 0 #eee3cd}
.sub{font-style:italic;color:#7a6848;margin-top:.4rem}
#bee{position:fixed;z-index:3;width:40px;height:40px;pointer-events:none;will-change:transform}
#dial,#save,#clearBtn,#copyBtn{pointer-events:auto;cursor:none;font-family:inherit}
#dial{width:110px;height:110px;border-radius:50%;border:2px solid #b08d57;background:radial-gradient(circle at 35% 30%,#e7c98d,#b08d57);color:#3c2f1c;font-size:1rem;box-shadow:0 4px 14px rgba(0,0,0,.2)}
#save{border:2px solid #b08d57;background:transparent;color:#4a3a28;padding:.75rem 1.5rem;border-radius:2rem;font-size:1rem}
#clearBtn,#copyBtn{border:1px solid #b08d57;background:transparent;color:#4a3a28;padding:.5rem 1rem;border-radius:1.5rem}
#sheet{position:fixed;left:0;right:0;bottom:0;z-index:4;background:#FBF4E6;border-top:1px solid #d9c7a1;box-shadow:0 -8px 30px rgba(0,0,0,.08);padding:1rem;max-height:70vh;overflow:auto;transform:translateY(100%);transition:transform .4s ease}
#sheet.show{transform:translateY(0)}
#preview{max-width:100%;height:220px;border:1px solid #d9c7a1;border-radius:8px;overflow:auto;background:#FBF4E6}
#diary{white-space:pre-line;font-size:.95rem;color:#4a3a28;margin-top:.5rem}
</style>
</head>
<body>
<canvas id="field"></canvas>
<div id="bee" data-flutter="buzzy"><svg width="40" height="40" viewBox="0 0 40 40"><g><ellipse id="wingL" cx="14" cy="10" rx="9" ry="4" fill="rgba(200,220,255,.7)" stroke="#8899aa"/><ellipse id="wingR" cx="26" cy="10" rx="9" ry="4" fill="rgba(200,220,255,.7)" stroke="#8899aa"/></g><ellipse cx="20" cy="22" rx="8" ry="12" fill="#2b2b2b"/><rect x="18" y="28" width="12" height="2" fill="#2b2b2b"/><circle cx="16" cy="18" r="1.5" fill="#f6d365"/></svg></div>
<div id="ui"><header style="text-align:center"><h1>Bumble Cursor</h1><div class="sub">your pointer just grew wings</div></header><div style="display:flex;gap:1rem;align-items:center;justify-content:center;margin-bottom:2rem;"><button id="dial" aria-label="Flutter: Buzzy">Flutter: Buzzy</button><button id="save">Save Pollen Path</button></div></div>
<div id="sheet"><h2>Pollen Map</h2><div id="preview"></div><div id="diary"></div><div style="display:flex;gap:.75rem;margin-top:.75rem;"><button id="copyBtn">Copy diary</button><button id="clearBtn">Clear field</button></div></div>
<div id="user-note" hidden>{{ note }}</div>
<script>
(() => {
const canvas=document.getElementById('field'),ctx=canvas.getContext('2d');
const beeEl=document.getElementById('bee'),dial=document.getElementById('dial'),saveBtn=document.getElementById('save'),clearBtn=document.getElementById('clearBtn'),copyBtn=document.getElementById('copyBtn');
const sheet=document.getElementById('sheet'),preview=document.getElementById('preview'),diary=document.getElementById('diary');
const wingL=document.getElementById('wingL'),wingR=document.getElementById('wingR');
const modes=['gentle','buzzy','frantic'],rates={gentle:6,buzzy:12,frantic:20},amps={gentle:1,buzzy:3,frantic:6};
let mode='buzzy',start=null,lastMove=performance.now(),lastSampleT=null,lastRecordT=0;
let pointer={x:innerWidth/2,y:innerHeight/2},bee={x:pointer.x,y:pointer.y},lastPointer={x:pointer.x,y:pointer.y},lastPollen={x:pointer.x,y:pointer.y};
let samples=[],pollen=[],velocities=[],grid=new Array(1024).fill(0),phase=0,lastFrame=performance.now();
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function record(x,y,t){
    if(!start)start=t;
    if(lastSampleT!==null){
        const dt=(t-lastSampleT)/1000;
        if(dt>0){
            const dx=x-lastPointer.x,dy=y-lastPointer.y,v=Math.hypot(dx,dy)/dt;
            velocities.push(v);if(velocities.length>5000)velocities.shift();
            samples.push({x:x,y:y,t:t});if(samples.length>5000)samples.shift();
            const dp=Math.hypot(x-lastPollen.x,y-lastPollen.y);
            if(dp>=6){
                const r=clamp(2.5+v/600,2.5,7.5);
                const alpha=Math.min(0.6,0.22+v/3000);
                pollen.push({x:x,y:y,r:r,alpha:alpha,t:t});
                if(pollen.length>900)pollen.shift();
                lastPollen={x:x,y:y};
            }
            const gx=clamp(Math.floor(x/innerWidth*32),0,31);
            const gy=clamp(Math.floor(y/innerHeight*32),0,31);
            grid[gy*32+gx]+=1;
        }
    }else{
        samples.push({x:x,y:y,t:t});if(samples.length>5000)samples.shift();
    }
    lastPointer={x:x,y:y};lastSampleT=t;lastMove=t;
}
function onMove(e){
    const t=performance.now();
    const ev=e.touches&&e.touches[0]?e.touches[0]:e;
    if(!ev)return;
    const x=ev.clientX,y=ev.clientY;
    if(typeof x!=='number'||typeof y!=='number')return;
    pointer={x:x,y:y};
    if(t-lastRecordT>=16){lastRecordT=t;record(x,y,t);}
}
window.addEventListener('pointermove',onMove,{passive:true});
window.addEventListener('touchmove',onMove,{passive:true});
function focusTo(e){
    const r=e.target.getBoundingClientRect();
    pointer={x:r.left+r.width/2,y:r.top+r.height/2};
    record(pointer.x,pointer.y,performance.now());
}
dial.addEventListener('focusin',focusTo);saveBtn.addEventListener('focusin',focusTo);
function draw(now){
    canvas.width=innerWidth;canvas.height=innerHeight;
    ctx.clearRect(0,0,innerWidth,innerHeight);
    pollen=pollen.filter(p=>now-p.t<=45000);
    for(let i=0;i<pollen.length;i++){
        const p=pollen[i],age=(now-p.t)/1000,a=p.alpha*Math.max(0,1-age/45);
        ctx.beginPath();ctx.fillStyle='rgba(198,150,45,'+a+')';ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();
    }
    if(now-lastMove>3000){
        ctx.beginPath();ctx.strokeStyle='rgba(180,140,60,.25)';ctx.lineWidth=1;
        ctx.arc(pointer.x,pointer.y-14,12+Math.sin(phase*2)*3,0,Math.PI*2);ctx.stroke();
    }
}
function frame(now){
    const dt=(now-lastFrame)/1000;lastFrame=now;
    const k=Math.min(1,dt*8);
    bee.x+=(pointer.x-bee.x)*k;bee.y+=(pointer.y-bee.y)*k;
    phase+=dt*rates[mode];
    const amp=amps[mode];
    const bob=(now-lastMove>3000)?Math.sin(phase*0.8)*1.5:0;
    const wingRot=Math.sin(phase)*38;
    const bx=bee.x+Math.sin(phase*2.1)*amp*0.5;
    const by=bee.y+Math.cos(phase*3.7)*amp*0.5+bob;
    beeEl.style.transform='translate('+(bx-20)+'px,'+(by-20-14)+'px)';
    wingL.setAttribute('transform','rotate('+wingRot+' 14 10)');
    wingR.setAttribute('transform','rotate('+(-wingRot)+' 26 10)');
    draw(now);requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
function downsample(arr,max){
    if(arr.length<=max)return arr;
    const step=Math.ceil(arr.length/max);
    return arr.filter((_,i)=>i%step===0).slice(0,max);
}
function stats(){
    const ln=samples.length;
    const duration=ln?((samples[ln-1].t-(start||0))/1000):0;
    let totalDistance=0,activeSeconds=0;
    for(let i=1;i<ln;i++){
        const dx=samples[i].x-samples[i-1].x,dy=samples[i].y-samples[i-1].y,d=Math.hypot(dx,dy);
        totalDistance+=d;
        const dt=(samples[i].t-samples[i-1].t)/1000;
        if(dt>0&&d/dt>20)activeSeconds+=dt;
    }
    const active=Math.min(duration,activeSeconds||0);
    const wingbeats=Math.round(rates[mode]*active);
    const beeLengths=Math.round(totalDistance/22);
    const zones=new Array(9).fill(0);
    for(let gx=0;gx<32;gx++)for(let gy=0;gy<32;gy++){
        const zx=Math.min(2,Math.floor(gx/(32/3))),zy=Math.min(2,Math.floor(gy/(32/3)));
        zones[zy*3+zx]+=grid[gy*32+gx];
    }
    const zoneNames=['top-left corner','top-center','top-right corner','middle-left','center','middle-right','bottom-left corner','bottom-center','bottom-right corner'];
    let favorite='center',maxZone=-1;
    zones.forEach((v,i)=>{if(v>maxZone){maxZone=v;favorite=zoneNames[i];}});
    const vs=velocities.slice().sort((a,b)=>a-b);
    const median=vs.length?(vs.length%2?vs[(vs.length-1)/2]:(vs[vs.length/2-1]+vs[vs.length/2])/2):0;
    const mean=velocities.length?velocities.reduce((a,b)=>a+b,0)/velocities.length:0;
    const stdev=velocities.length>1?Math.sqrt(velocities.reduce((a,b)=>a+Math.pow(b-mean,2),0)/(velocities.length-1)):0;
    let mood=median<100?'a slow, sunny drift':median<350?'an even, purposeful buzz':'a wild pollination spree';
    if(mean>0&&stdev/mean>1.5)mood+=' with sudden starts';
    return {duration:duration,totalDistance:totalDistance,pollenCount:pollen.length,wingbeats:wingbeats,beeLengths:beeLengths,favorite:favorite,mood:mood};
}
function buildSvg(){
    const W=innerWidth,H=innerHeight,date=new Date().toISOString().slice(0,10);
    if(samples.length<5){return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'"><rect width="100%" height="100%" fill="#FBF4E6"/><text x="50%" y="50%" font-family="Georgia" font-size="20" fill="#4a3a28" text-anchor="middle">The bee is still waiting for its first flight.</text></svg>';}
    const sd=downsample(samples,1800),pd=downsample(pollen,1500);
    const points=sd.map(s=>s.x+','+s.y).join(' ');
    let gridLines='';
    for(let i=1;i<3;i++){
        const y=H*i/3,x=W*i/3;
        gridLines+='<line x1="0" y1="'+y+'" x2="'+W+'" y2="'+y+'" stroke="#d9c7a1" stroke-width="1" opacity=".4"/>';
        gridLines+='<line x1="'+x+'" y1="0" x2="'+x+'" y2="'+H+'" stroke="#d9c7a1" stroke-width="1" opacity=".4"/>';
    }
    const pc=pd.slice().sort((a,b)=>a.t-b.t).map(p=>{
        const age=(performance.now()-p.t)/1000,a=p.alpha*Math.max(0,1-age/45);
        return '<circle cx="'+p.x+'" cy="'+p.y+'" r="'+p.r+'" fill="rgba(198,150,45,'+a+')"/>';
    }).join('');
    const last=samples[samples.length-1];
    const bee='<g transform="translate('+last.x+','+last.y+')"><ellipse cx="-6" cy="-12" rx="9" ry="4" fill="rgba(200,220,255,.7)" stroke="#8899aa"/><ellipse cx="6" cy="-12" rx="9" ry="4" fill="rgba(200,220,255,.7)" stroke="#8899aa"/><ellipse cx="0" cy="0" rx="8" ry="12" fill="#2b2b2b"/><rect x="-2" y="6" width="12" height="2" fill="#2b2b2b"/><circle cx="-4" cy="-4" r="1.5" fill="#f6d365"/></g>';
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'"><rect width="100%" height="100%" fill="#FBF4E6"/>'+gridLines+'<polyline points="'+points+'" fill="none" stroke="#b08d57" stroke-width="2" stroke-dasharray="6 6" opacity=".7"/>'+pc+bee+'<text x="'+(W/2)+'" y="'+(H-16)+'" font-family="Georgia" font-size="14" fill="#4a3a28" text-anchor="middle">Bumble Cursor · '+date+' · '+mode+' flutter</text></svg>';
}
function diaryText(){
    const s=stats();
    return 'Field Diary\nTime in the field: '+s.duration.toFixed(1)+'s\nDistance flown: '+Math.round(s.totalDistance)+'px ('+s.beeLengths+' bee-lengths)\nPollen drops: '+s.pollenCount+'\nWingbeats: '+s.wingbeats+'\nFavorite corner: '+s.favorite+'\nMood: '+s.mood;
}
function fallbackCopy(text){
    const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();
    try{document.execCommand('copy');}catch(e){}ta.remove();
}
dial.addEventListener('click',()=>{
    const idx=(modes.indexOf(mode)+1)%modes.length;mode=modes[idx];
    const cap=mode.charAt(0).toUpperCase()+mode.slice(1);
    dial.textContent='Flutter: '+cap;dial.setAttribute('aria-label','Flutter: '+cap);beeEl.dataset.flutter=mode;
    try{
        const ac=new (window.AudioContext||window.webkitAudioContext)();
        const o=ac.createOscillator(),g=ac.createGain();
        o.frequency.setValueAtTime(180,ac.currentTime);
        o.frequency.exponentialRampToValueAtTime(130,ac.currentTime+0.12);
        g.gain.value=0.06;o.connect(g);g.connect(ac.destination);
        o.start();o.stop(ac.currentTime+0.12);
    }catch(e){}
});
saveBtn.addEventListener('click',()=>{
    const svg=buildSvg();
    const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
    const a=document.createElement('a');a.href=url;a.download='bumble-pollen-path-'+new Date().toISOString().slice(0,10)+'.svg';
    document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    preview.innerHTML=svg;diary.textContent=diaryText();sheet.classList.add('show');
});
copyBtn.addEventListener('click',()=>{
    const text=diary.textContent;if(!text)return;
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).catch(()=>fallbackCopy(text));}
    else{fallbackCopy(text);}
});
clearBtn.addEventListener('click',()=>{
    start=null;samples=[];pollen=[];velocities=[];grid=new Array(1024).fill(0);lastSampleT=null;lastRecordT=0;
    lastMove=performance.now();lastPollen=pointer;diary.textContent='';preview.innerHTML='';sheet.classList.remove('show');
});
})();
</script>
</body>
</html>''')


def process(text: str) -> str:
    """Return the Bumble Cursor interactive HTML page."""
    note = escape(text.strip()[:200]) if text.strip() else ""
    return TEMPLATE.render(note=note)


def _cli_main() -> None:
    print(process(""))


_browser_input = globals().get("USER_INPUT", None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()