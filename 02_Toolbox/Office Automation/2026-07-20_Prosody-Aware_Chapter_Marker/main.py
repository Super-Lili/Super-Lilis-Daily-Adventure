"""Prosody-Aware Chapter Marker - Interactive HTML with Web Audio API"""
import json
from jinja2 import Template

def process(text: str) -> str:
    """Return HTML page that analyzes audio/transcript for chapter markers."""
    if not text.strip():
        return "<html><body><p>Paste a transcript or upload audio.</p></body></html>"
    initial_text = json.dumps(text)

    tpl = Template(
        r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Prosody-Aware Chapter Marker</title><style>
*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:#f4f4f9;color:#222;display:flex;flex-direction:column;align-items:center;padding:1rem}
h1{font-size:1.8rem;margin:.5rem 0}.instruction{color:#555;margin-bottom:1.5rem;text-align:center}
#dropzone{border:3px dashed #aaa;border-radius:12px;padding:2rem;text-align:center;cursor:pointer;background:#fafafa;transition:.2s;margin-bottom:1rem;width:100%;max-width:800px}
#dropzone.dragover{background:#e0f0ff;border-color:#36c}
textarea{width:100%;max-width:800px;height:200px;padding:.75rem;font-size:.9rem;resize:vertical;margin-bottom:1rem;border:1px solid #ccc;border-radius:8px}
#wavecontainer{width:100%;max-width:800px;height:120px;margin:.5rem 0;border:1px solid #ddd;border-radius:8px;position:relative;overflow:hidden;background:#fff}
#wavecanvas{width:100%;height:100%}
#sidebar{width:100%;max-width:800px;margin:1rem 0;display:flex;gap:.5rem;flex-wrap:wrap}
.chaptercard{flex:1 1 240px;background:#fff;border-radius:8px;padding:.75rem;box-shadow:0 2px 6px rgba(0,0,0,.08);cursor:pointer;position:relative;border-left:4px solid #36c}
.chaptercard.active{border-left-color:#e69500;background:#fffbf0}
.time{font-family:monospace;font-size:.9rem;color:#666}.title{display:block;width:100%;border:none;background:transparent;font-size:.95rem;font-weight:bold;margin:.25rem 0}.title:focus{outline:none;border-bottom:2px solid #36c}.delete-btn{position:absolute;top:.25rem;right:.5rem;background:none;border:none;color:#c00;font-size:1.3rem;cursor:pointer}
#exportbtn{margin:.75rem;padding:.6rem 2rem;font-size:1rem;border-radius:8px;border:none;background:#36c;color:#fff;cursor:pointer}#exportbtn:hover{background:#258}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);align-items:center;justify-content:center;z-index:1000}
.modal.active{display:flex}.modalbox{background:#fff;padding:1.5rem;border-radius:12px;max-width:600px;width:90%;max-height:80vh;overflow:auto}
.exporttabs{display:flex;gap:.25rem;margin-bottom:1rem}.exporttab{padding:.4rem 1rem;border:1px solid #ccc;background:#eee;cursor:pointer;border-radius:6px 6px 0 0}.exporttab.active{background:#fff;border-bottom:1px solid #fff}
.exportcontent{white-space:pre-wrap;background:#f5f5f5;padding:1rem;border-radius:0 0 8px 8px;font-family:monospace;max-height:300px;overflow:auto}
.copybtn{margin-top:.5rem;padding:.4rem 1rem;background:#222;color:#fff;border:none;border-radius:6px;cursor:pointer}
.resetbtn{background:#999;color:#fff;border:none;border-radius:8px;padding:.5rem 1.2rem;cursor:pointer;margin-bottom:1rem}
</style></head><body>
<h1>Prosody-Aware Chapter Marker</h1>
<p class="instruction">Upload your podcast audio or paste the transcript. We'll detect chapter boundaries based on natural speech rhythm.</p>
<div id="dropzone">Drop audio file (MP3/WAV) here or click to browse<br><small>or paste transcript below</small></div>
<textarea id="transcriptArea" placeholder="Paste transcript with speaker labels (optional timestamps)..."></textarea>
<div id="wavecontainer" style="display:none;"><canvas id="wavecanvas"></canvas></div>
<div id="sidebar"></div>
<button id="exportbtn" style="display:none;">Export Chapters</button>
<button class="resetbtn" id="resetbtn">Reset</button>
<div class="modal" id="exportmodal"><div class="modalbox"><h3>Export Chapters</h3><div class="exporttabs"><button class="exporttab active" data-format="youtube">YouTube</button><button class="exporttab" data-format="csv">CSV</button><button class="exporttab" data-format="markdown">Markdown</button></div><pre class="exportcontent" id="exporttext"></pre><button class="copybtn" id="copybtn">Copy to clipboard</button><button class="copybtn" style="margin-left:.5rem;background:#888" id="closemodal">Close</button></div></div>
<script>
var transcriptText = {{ initial_text }};
document.getElementById('transcriptArea').value = transcriptText;
(function(){
var audioCtx=null, audioBuf=null, chapters=[], sampleRate=0, markers=[];
var dropzone=document.getElementById('dropzone');
var textarea=document.getElementById('transcriptArea');
var wavecont=document.getElementById('wavecontainer');
var canvas=document.getElementById('wavecanvas');
var ctx=canvas.getContext('2d');
var sidebar=document.getElementById('sidebar');
var exportbtn=document.getElementById('exportbtn');
var resetbtn=document.getElementById('resetbtn');
var exportmodal=document.getElementById('exportmodal');
var exporttext=document.getElementById('exporttext');
var copybtn=document.getElementById('copybtn');
var closemodal=document.getElementById('closemodal');
var tabs=document.querySelectorAll('.exporttab');
var activeFormat='youtube';
var dragIdx=-1, isDragging=false;
var globalSentences=[], globalVecs=[];
var stopWords=new Set(['i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','yourselves','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are','was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an','the','and','but','if','or','because','as','until','while','of','at','by','for','with','about','against','between','into','through','during','before','after','above','below','to','from','up','down','in','out','on','off','over','under','again','further','then','once','here','there','when','where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor','not','only','own','same','so','than','too','very','s','t','can','will','just','don','should','now']);
dropzone.addEventListener('dragover',function(e){e.preventDefault();dropzone.classList.add('dragover');});
dropzone.addEventListener('dragleave',function(){dropzone.classList.remove('dragover');});
dropzone.addEventListener('drop',function(e){e.preventDefault();dropzone.classList.remove('dragover');handleFiles(e.dataTransfer.files);});
dropzone.addEventListener('click',function(){var i=document.createElement('input');i.type='file';i.accept='audio/*';i.onchange=function(){handleFiles(i.files)};i.click();});
textarea.addEventListener('input',function(){processTranscript();});
resetbtn.addEventListener('click',function(){chapters=[];markers=[];audioBuf=null;closeAudio();wavecont.style.display='none';exportbtn.style.display='none';sidebar.innerHTML='';globalSentences=[];globalVecs=[];if(textarea.value.trim())processTranscript();});
exportbtn.addEventListener('click',function(){openExport();});
closemodal.addEventListener('click',function(){exportmodal.classList.remove('active');});
copybtn.addEventListener('click',function(){navigator.clipboard.writeText(exporttext.textContent);});
tabs.forEach(function(tab){tab.addEventListener('click',function(){tabs.forEach(t=>t.classList.remove('active'));tab.classList.add('active');activeFormat=tab.dataset.format;renderExport();});});
function handleFiles(files){if(!files||!files.length)return;var f=files[0];if(!f.type.startsWith('audio/')){alert('Please upload an audio file.');return}var reader=new FileReader();reader.onload=function(ev){audioCtx=new(window.AudioContext||window.webkitAudioContext)();audioCtx.decodeAudioData(ev.target.result,function(buffer){audioBuf=buffer;sampleRate=buffer.sampleRate;drawWaveform();analyzeAudioBuffer();},function(){alert('Could not decode audio.');});};reader.readAsArrayBuffer(f);}
function drawWaveform(){
wavecont.style.display='block';var w=canvas.parentElement.clientWidth;canvas.width=w;canvas.height=120;
var ch=audioBuf.getChannelData(0);var step=Math.floor(ch.length/w);var amp=canvas.height/2;
ctx.clearRect(0,0,w,canvas.height);ctx.beginPath();ctx.strokeStyle='#36c';ctx.lineWidth=1;
for(var i=0;i<w;i++){var min=1.0,max=-1.0;for(var j=0;j<step;j++){var idx=i*step+j;if(idx<ch.length){var v=ch[idx];if(v<min)min=v;if(v>max)max=v;}}var y1=amp+min*amp;var y2=amp+max*amp;ctx.moveTo(i+0.5,y1);ctx.lineTo(i+0.5,y2);}
ctx.stroke();drawMarkersOnCanvas();}
function drawMarkersOnCanvas(){
if(!audioBuf)return;var dur=audioBuf.duration;ctx.clearRect(0,0,canvas.width,canvas.height);drawWaveformLines();
markers.forEach(function(m,i){var x=m.time/dur*canvas.width;ctx.beginPath();ctx.strokeStyle=i===dragIdx?'#e69500':'#c00';ctx.lineWidth=2;ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke();ctx.fillStyle='#c00';ctx.font='10px monospace';ctx.fillText(m.time.toFixed(0)+'s',x+4,12);});}
function drawWaveformLines(){var ch=audioBuf.getChannelData(0);var w=canvas.width;var step=Math.floor(ch.length/w);var amp=canvas.height/2;ctx.beginPath();ctx.strokeStyle='#ddd';ctx.lineWidth=1;for(var i=0;i<w;i++){var min=1.0,max=-1.0;for(var j=0;j<step;j++){var idx=i*step+j;if(idx<ch.length){var v=ch[idx];if(v<min)min=v;if(v>max)max=v;}}var y1=amp+min*amp;var y2=amp+max*amp;ctx.moveTo(i+0.5,y1);ctx.lineTo(i+0.5,y2);}ctx.stroke();}
function analyzeAudioBuffer(){
if(!audioBuf)return;
var ch=audioBuf.getChannelData(0);var dur=audioBuf.duration;
var frameLen=Math.floor(sampleRate*0.05);var nFrames=Math.floor(ch.length/frameLen);
var rms=new Float32Array(nFrames);
for(var i=0;i<nFrames;i++){var start=i*frameLen;var sum=0;for(var j=0;j<frameLen;j++)sum+=ch[start+j]*ch[start+j];rms[i]=Math.sqrt(sum/frameLen);}
var alpha=0.15; var smoothed=new Float32Array(nFrames);smoothed[0]=rms[0];for(var i=1;i<nFrames;i++)smoothed[i]=alpha*rms[i]+(1-alpha)*smoothed[i-1];
var troughScore=new Float32Array(nFrames);var maxTrough=0;
for(var i=1;i<nFrames-1;i++){if(smoothed[i]<=smoothed[i-1]&&smoothed[i]<=smoothed[i+1]){var d=Math.max(smoothed[i-1],smoothed[i+1])-smoothed[i];troughScore[i]=d;maxTrough=Math.max(maxTrough,d);}else troughScore[i]=0;}
if(maxTrough===0)maxTrough=1e-9;
var minLag=Math.floor(sampleRate/400),maxLag=Math.floor(sampleRate/80);
var pitch=new Float32Array(nFrames);
for(var i=0;i<nFrames;i++){var start=i*frameLen;if(start+maxLag>=ch.length)break;var bestCorr=-1,bestLag=0;for(var lag=minLag;lag<maxLag;lag++){if(start+lag+frameLen>=ch.length)break;var corr=0;for(var j=0;j<frameLen;j++)corr+=ch[start+j]*ch[start+j+lag];if(corr>bestCorr){bestCorr=corr;bestLag=lag;}}pitch[i]=sampleRate/bestLag;}
var pitchRate=new Float32Array(nFrames-1);
for(var i=0;i<nFrames-1;i++)pitchRate[i]=Math.abs(pitch[i+1]-pitch[i]);
var inflectionScore=new Float32Array(nFrames-1);var maxInf=0;
for(var i=1;i<nFrames-2;i++){if(pitchRate[i]>pitchRate[i-1]&&pitchRate[i]>pitchRate[i+1]){inflectionScore[i]=pitchRate[i];maxInf=Math.max(maxInf,pitchRate[i]);}else inflectionScore[i]=0;}
if(maxInf===0)maxInf=1e-9;
var combined=new Float32Array(nFrames);
for(var i=0;i<nFrames;i++){var ts=i<nFrames?troughScore[i]/maxTrough:0;var ins=i<inflectionScore.length?inflectionScore[i]/maxInf:0;combined[i]=0.6*ts+0.4*ins;}
var numChap=Math.max(2,Math.floor(dur/300)+1);
var rawPeaks=[];for(var i=1;i<combined.length-1;i++)if(combined[i]>combined[i-1]&&combined[i]>combined[i+1])rawPeaks.push({idx:i,val:combined[i]});
rawPeaks.sort(function(a,b){return b.val-a.val;});
var minDist=2*sampleRate/frameLen; var selected=[];
for(var i=0;i<rawPeaks.length;i++){var ok=true;for(var j=0;j<selected.length;j++){if(Math.abs(rawPeaks[i].idx-selected[j])<minDist){ok=false;break;}}if(ok){selected.push(rawPeaks[i].idx);if(selected.length>=numChap)break;}}
selected.sort(function(a,b){return a-b;});
markers=selected.map(function(idx){return {time:idx*frameLen/sampleRate};});
rebuildChaptersFromMarkers();
}
function rebuildChaptersFromMarkers(){
markers.sort(function(a,b){return a.time-b.time});
var dur=audioBuf.duration;
var times=[0].concat(markers.map(function(m){return m.time;})).concat([dur]);
chapters=[];for(var i=0;i<times.length-1;i++){chapters.push({start:secToMMSS(times[i]),end:secToMMSS(times[i+1]),startSec:times[i],endSec:times[i+1],title:'Chapter '+(i+1)});}
if(transcriptText.trim()) try{
  var sentences=parseTimestampedSentences(transcriptText);
  for(var i=0;i<chapters.length;i++){
    var segWords=[];for(var j=0;j<sentences.length;j++){var s=sentences[j];if(s.time>=chapters[i].startSec&&s.time<chapters[i].endSec){var tokens=tokenize(s.text).filter(function(w){return w.length>1&&!stopWords.has(w)});segWords=segWords.concat(tokens);}}
    if(segWords.length>0){var tf={};segWords.forEach(function(w){tf[w]=(tf[w]||0)+1;});
      var entries=Object.entries(tf).sort(function(a,b){return b[1]-a[1];}).slice(0,3);
      chapters[i].title=entries.map(function(e){return e[0];}).join(' ')||'Chapter '+(i+1);
    }
  }
}catch(e){}
renderChapters();exportbtn.style.display='inline-block';}
function parseTimestampedSentences(txt){
var lines=txt.split('\n');var sents=[];var curTime=0;
lines.forEach(function(line){
var m=line.match(/\((\d+):(\d+)\)/);if(m){curTime=parseInt(m[1])*60+parseInt(m[2]);}
var parts=line.split(/(?<=[\.!?])\s+/);parts.forEach(function(p){if(p.trim())sents.push({text:p.trim(),time:curTime});});
});
return sents;
}
function secToMMSS(sec){var m=Math.floor(sec/60);var s=Math.floor(sec%60);return m+':'+(s<10?'0':'')+s;}
function processTranscript(){
var txt=textarea.value;if(!txt.trim()){sidebar.innerHTML='';exportbtn.style.display='none';return;}
var lines=txt.split('\n');var sentences=[];var speaker='', time=0;
lines.forEach(function(line,i){
var t=line.trim();if(!t)return;
var sp=t.match(/^(\w[\w\s]*?):/);if(sp){speaker=sp[1];t=t.substring(sp[0].length);}
var tm=t.match(/\((\d+):(\d+)\)$/);if(tm){time=parseInt(tm[1])*60+parseInt(tm[2]);t=t.replace(/\(\d+:\d+\)$/,'').trim();}
var parts=t.split(/(?<=[\.!?])\s+/);parts.forEach(function(p){if(p.trim())sentences.push({text:p,speaker:speaker,time:time,lineIdx:i});});
});
var boundaries=[];
for(var i=0;i<sentences.length-1;i++){
var s1=sentences[i],s2=sentences[i+1];
if(s1.speaker!==s2.speaker){boundaries.push(i+1);continue;}
var t1=s1.text,t2=s2.text;
if(/[*]{2}pause[*]{2}|\.\.\.|\u2014|\u2013|\u2026+/.test(t1)||/[*]{2}pause[*]{2}|\.\.\.|\u2014|\u2013|\u2026+/.test(t2)){boundaries.push(i+1);continue;}
if(/[!?]/.test(t1)&&!/[!?]/.test(t2)){boundaries.push(i+1);continue;}
}
var allVecs=computeTFIDF(sentences);globalSentences=sentences;globalVecs=allVecs;
for(var i=0;i<sentences.length-1;i++){if(boundaries.indexOf(i+1)>-1)continue;var sim=cosSim(allVecs[i],allVecs[i+1]);if(sim<0.3)boundaries.push(i+1);}
boundaries=Array.from(new Set(boundaries)).sort(function(a,b){return a-b;});
var segments=[];var start=0;boundaries.forEach(function(b){segments.push(sentences.slice(start,b));start=b;});segments.push(sentences.slice(start));
var merged=mergeSegments(segments,allVecs);chapters=[];
merged.forEach(function(seg,idx){var fi=seg[0].time||0;var title=generateTitle(seg);chapters.push({start:secToMMSS(fi),title:title,startSec:fi,endSec:fi+30});});
renderChapters();exportbtn.style.display='inline-block';}
function computeTFIDF(sents){var df={},n=sents.length;sents.forEach(function(s){var ws=tokenize(s.text);var uq=new Set(ws);uq.forEach(function(w){df[w]=(df[w]||0)+1;});});
var vecs=[];sents.forEach(function(s){var ws=tokenize(s.text);var tf={};ws.forEach(function(w){tf[w]=(tf[w]||0)+1;});var vec={};var total=ws.length||1;
Object.keys(tf).forEach(function(w){if(!stopWords.has(w)){var idf=Math.log(n/(1+(df[w]||0)));vec[w]=tf[w]/total*idf;}});vecs.push(vec);});return vecs;}
function tokenize(t){return t.toLowerCase().replace(/[^a-z0-9\s]/g,'').split(/\s+/).filter(Boolean);}
function cosSim(v1,v2){var dot=0,n1=0,n2=0;var keys=new Set(Object.keys(v1).concat(Object.keys(v2)));keys.forEach(function(k){var a=v1[k]||0,b=v2[k]||0;dot+=a*b;n1+=a*a;n2+=b*b;});if(n1===0||n2===0)return 0;return dot/(Math.sqrt(n1)*Math.sqrt(n2));}
function mergeSegments(segs,vecs){
var merged=[segs[0]];for(var i=1;i<segs.length;i++){var last=merged[merged.length-1];var cur=segs[i];var idx1=globalSentences.indexOf(last[0]),idx2=globalSentences.indexOf(cur[0]);
var v1=combineVecs(last),v2=combineVecs(cur);if(cosSim(v1,v2)>0.35){merged[merged.length-1]=last.concat(cur);}else merged.push(cur);}return merged;}
function combineVecs(seg){if(!globalSentences.length)return{};var c={};seg.forEach(function(s){var idx=globalSentences.indexOf(s);if(idx>-1){var v=globalVecs[idx];Object.keys(v).forEach(function(k){c[k]=(c[k]||0)+v[k];});}});return c;}
function generateTitle(seg){var freq={};seg.forEach(function(s){var ws=tokenize(s.text);ws.forEach(function(w){if(!stopWords.has(w))freq[w]=(freq[w]||0)+1;});});var entries=Object.entries(freq).sort(function(a,b){return b[1]-a[1];}).slice(0,3);return entries.map(function(e){return e[0];}).join(' ')||'Chapter';}
function renderChapters(){
sidebar.innerHTML='';chapters.forEach(function(ch,i){
var card=document.createElement('div');card.className='chaptercard';card.dataset.idx=i;
card.innerHTML='<div class="time">'+ch.start+'</div><input type="text" class="title" value="'+escapeHtml(ch.title)+'" data-idx="'+i+'"><button class="delete-btn" data-idx="'+i+'">&times;</button>';
sidebar.appendChild(card);
card.querySelector('.title').addEventListener('input',function(e){var idx=e.target.dataset.idx;chapters[idx].title=e.target.value;});
card.querySelector('.delete-btn').addEventListener('click',function(e){e.stopPropagation();var idx=e.target.dataset.idx;chapters.splice(idx,1);renderChapters();if(audioBuf)rebuildChaptersFromMarkers();});
card.addEventListener('click',function(){if(audioBuf)playSeg(ch.startSec,chapters[i+1]?chapters[i+1].startSec:audioBuf.duration);});});}
function escapeHtml(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function playSeg(s,e){if(!audioBuf)return;var src=audioCtx.createBufferSource();src.buffer=audioBuf;src.connect(audioCtx.destination);src.start(0,s,e-s);}
function closeAudio(){if(audioCtx&&audioCtx.state!=='closed')audioCtx.close();audioCtx=null;audioBuf=null;}
function openExport(){exportmodal.classList.add('active');renderExport();}
function renderExport(){var out='';if(activeFormat==='youtube'){chapters.forEach(function(ch){out+=ch.start+' '+ch.title+'\n';});}
else if(activeFormat==='csv'){out='Timestamp,Title\n';chapters.forEach(function(ch){out+=ch.start+',"'+ch.title+'"\n';});}
else if(activeFormat==='markdown'){out='| Timestamp | Title |\n|---|---|\n';chapters.forEach(function(ch){out+='| '+ch.start+' | '+ch.title+' |\n';});}
exporttext.textContent=out;}
canvas.addEventListener('mousedown',function(e){if(!audioBuf||!markers.length)return;var rect=canvas.getBoundingClientRect();var x=e.clientX-rect.left;var dur=audioBuf.duration;var t=x/canvas.width*dur;var closest=0,minDist=Infinity;markers.forEach(function(m,i){var d=Math.abs(m.time-t);if(d<minDist){minDist=d;closest=i;}});if(minDist*dur/canvas.width<0.5){dragIdx=closest;isDragging=true;}});
canvas.addEventListener('mousemove',function(e){if(!isDragging||dragIdx===-1)return;var rect=canvas.getBoundingClientRect();var x=e.clientX-rect.left;x=Math.max(0,Math.min(x,canvas.width));var t=x/canvas.width*audioBuf.duration;markers[dragIdx].time=t;rebuildChaptersFromMarkers();drawWaveform();});
canvas.addEventListener('mouseup',function(){isDragging=false;dragIdx=-1;});
canvas.addEventListener('mouseleave',function(){isDragging=false;dragIdx=-1;});
processTranscript();
})();
</script></body></html>"""
    )
    return tpl.render(initial_text=initial_text)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()