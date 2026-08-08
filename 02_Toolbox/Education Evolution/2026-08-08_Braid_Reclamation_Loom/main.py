"""
Braid Reclamation Loom - Education Evolution (Mode 3)
Interactive HTML page for braiding career moments into narrative scaffold.
"""
import json
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Braid Reclamation Loom</title>
<style>
body{background:#fdf6e3;font-family:Georgia,serif;margin:20px;color:#333;}
#entry{max-width:600px;margin:40px auto;text-align:center;}
#entry textarea{width:100%;height:200px;padding:10px;font-size:14px;border:1px solid #ccc;border-radius:4px;resize:vertical;}
#entry button{margin-top:10px;padding:8px 20px;font-size:16px;background:#5a8f6a;color:white;border:none;border-radius:4px;cursor:pointer;}
#active{display:none;max-width:1200px;margin:20px auto;}
.staging,.wells,.timeline,.scaffold{margin:20px 0;}
.card{display:inline-block;background:white;border:1px solid #ddd;padding:8px 12px;margin:5px;border-radius:6px;cursor:pointer;transition:all 0.3s;}
.card.past{border-left:5px solid #bbdefb;}
.card.pivot{border-left:5px solid #e1bee7;}
.card.emerging{border-left:5px solid #c8e6c9;}
.tag{font-size:11px;margin-left:8px;padding:2px 6px;border-radius:10px;}
.pastTag{background:#bbdefb;}
.pivotTag{background:#e1bee7;}
.emergingTag{background:#c8e6c9;}
.well{border:1px solid #ccc;padding:10px;min-height:40px;background:white;border-radius:4px;margin:5px;display:inline-block;width:30%;vertical-align:top;box-sizing:border-box;}
.well h3{margin:0 0 5px;font-size:14px;}
.wellCard{background:#fafafa;padding:4px 8px;margin:3px 0;border-radius:3px;font-size:13px;}
.timelineItem{display:inline-flex;align-items:center;margin:2px 5px;font-size:13px;}
.timelineTag{width:10px;height:10px;border-radius:50%;margin-right:4px;display:inline-block;}
.scaffoldOutput{white-space:pre-wrap;background:white;border:1px solid #ccc;padding:15px;border-radius:4px;font-size:14px;max-height:400px;overflow-y:auto;}
#throughline{font-style:italic;margin-top:10px;}
.throughlineInput{margin:10px 0;}
.throughlineInput input{padding:5px;width:200px;}
</style>
</head>
<body>
<div id="entry">
<h2>Braid Reclamation Loom</h2>
<p>Paste the moments — one per line</p>
<textarea id="momentsInput" placeholder="2006 — Broke the city hall story...&#10;2011 — Won a national award..."></textarea>
<button id="setLoomBtn">Set the Loom</button>
</div>

<div id="active">
<div class="staging"><h3>Staging Lane</h3><div id="stagingCards"></div></div>
<div class="wells">
  <div class="well" id="wellPast"><h3>Past</h3></div>
  <div class="well" id="wellPivot"><h3>Pivot</h3></div>
  <div class="well" id="wellEmerging"><h3>Emerging</h3></div>
</div>
<div class="timeline"><h3>Braided Timeline</h3><div id="timelineOutput"></div></div>
<div class="scaffold"><h3>Braided Thread Scaffold</h3><div id="scaffoldOutput" class="scaffoldOutput"></div>
<div class="throughlineInput"><label>Theme word: </label><input type="text" id="themeWordInput" placeholder="e.g. resilience"></div>
<div id="throughline"></div>
<button id="copyBraidBtn">Copy Braid</button>
<button id="resetBtn">Re-set Loom</button>
</div>
</div>

<script>
function escapeHtml(s){return s.replace(/[&<>"']/g,function(m){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m];});}
function parseInput(txt){
    return txt.split(/\r?\n/).map(function(l){
        return l.replace(/^[\s]*([\u2022\-*>\d]+[.)]?)?\s*/, '').trim();
    }).filter(function(l){return l.length>=3;});
}
function extractYear(str){var m=str.match(/\b(19|20)\d{2}\b/);return m?parseInt(m[0],10):null;}
var moments=[];
var entryDiv, activeDiv, textarea, themeInput, stagingCards, wellPast, wellPivot, wellEmerging, timelineOutput, scaffoldOutput, throughlineDiv;

function computeMoments(lines){
    var raw=lines.map(function(t,i){return{text:t,year:extractYear(t),origIdx:i};});
    var hasYear=raw.filter(function(a){return a.year!==null;}).length>=2;
    if(hasYear){
        raw.sort(function(a,b){
            var ay=a.year||0, by=b.year||0;
            if(ay!==by) return ay-by;
            return a.origIdx-b.origIdx;
        });
    }
    var n=raw.length;
    var t1=Math.ceil(n/3), t2=Math.ceil(2*n/3);
    var pivotRe=/laid off|fired|resign|quit|walked away|ended|collapsed|fail|lost|rejected|no longer|stopped|pivot|turn|abrupt|instead/i;
    var emergRe=/now|currently|today|teach|mentor|apply|building|beginning|write about myself|own story/i;
    var pastRe=/reported|covered|edited|investigat|wrote|broke|worked|spent|learned|ran|team|award|published/i;
    return raw.map(function(item,i){
        var text=item.text, year=item.year;
        var baseline=i<t1?'Past':(i<t2?'Pivot':'Emerging');
        var scores={Past:0,Pivot:0,Emerging:0};
        if(baseline==='Past') scores.Past=1;
        else if(baseline==='Pivot') scores.Pivot=1;
        else scores.Emerging=1;
        if(pivotRe.test(text)) scores.Pivot+=2;
        if(emergRe.test(text)) scores.Emerging+=2;
        if(pastRe.test(text)) scores.Past+=2;
        var best='Past', bestScore=scores.Past;
        if(scores.Pivot>bestScore||(scores.Pivot===bestScore&&baseline==='Pivot')){best='Pivot';bestScore=scores.Pivot;}
        if(scores.Emerging>bestScore||(scores.Emerging===bestScore&&baseline==='Emerging')){best='Emerging';bestScore=scores.Emerging;}
        return{text:text,year:year,thread:best};
    });
}

function throughlineSentence(){
    var first=moments.length?moments[0].text:'';
    var last=moments.length?moments[moments.length-1].text:'';
    var tw=themeInput.value.trim()||'self';
    return 'From '+(first?'"'+first+'"':'the beginning')+' to '+(last?'"'+last+'"':'now')+', the thread I am pulling is '+tw+'.';
}

function renderAll(){
    stagingCards.innerHTML=moments.map(function(m,i){
        return '<div class="card '+m.thread.toLowerCase()+'" data-index="'+i+'"><span class="cardText">'+escapeHtml(m.text)+'</span><span class="tag '+m.thread.toLowerCase()+'Tag">'+m.thread+'</span></div>';
    }).join('')||'<p>No moments yet.</p>';
    wellPast.innerHTML='<h3>Past</h3>'+moments.filter(function(m){return m.thread==='Past';}).map(function(m){return'<div class="wellCard">'+escapeHtml(m.text)+'</div>';}).join('');
    wellPivot.innerHTML='<h3>Pivot</h3>'+moments.filter(function(m){return m.thread==='Pivot';}).map(function(m){return'<div class="wellCard">'+escapeHtml(m.text)+'</div>';}).join('');
    wellEmerging.innerHTML='<h3>Emerging</h3>'+moments.filter(function(m){return m.thread==='Emerging';}).map(function(m){return'<div class="wellCard">'+escapeHtml(m.text)+'</div>';}).join('');
    timelineOutput.innerHTML=moments.map(function(m){
        return'<span class="timelineItem"><span class="timelineTag" style="background:'+(m.thread==='Past'?'#bbdefb':m.thread==='Pivot'?'#e1bee7':'#c8e6c9')+'"></span>'+escapeHtml(m.text)+'</span>';
    }).join(' &rarr; ')||'&nbsp;';
    var pastLines=moments.filter(function(m){return m.thread==='Past';}).map(function(m){return'\u2022 '+m.text;}).join('\n');
    var pivotLines=moments.filter(function(m){return m.thread==='Pivot';}).map(function(m){return'\u2022 '+m.text;}).join('\n');
    var emergLines=moments.filter(function(m){return m.thread==='Emerging';}).map(function(m){return'\u2022 '+m.text;}).join('\n');
    var scaffold='The years when the work spoke louder than I did:\n'+pastLines+'\n\nThen the story turned and made me its subject:\n'+pivotLines+'\n\nThe narrator I am now is the one who:\n'+emergLines+'\n\n'+throughlineSentence();
    scaffoldOutput.textContent=scaffold;
    throughlineDiv.textContent=throughlineSentence();
}

function setLoom(){
    var lines=parseInput(textarea.value);
    if(lines.length===0){alert('Please enter at least one moment.');return;}
    moments=computeMoments(lines);
    entryDiv.style.display='none';
    activeDiv.style.display='block';
    renderAll();
}

function resetLoom(){
    moments=[];
    entryDiv.style.display='block';
    activeDiv.style.display='none';
    textarea.value='';
    themeInput.value='';
    stagingCards.innerHTML='';
    wellPast.innerHTML='<h3>Past</h3>';
    wellPivot.innerHTML='<h3>Pivot</h3>';
    wellEmerging.innerHTML='<h3>Emerging</h3>';
    timelineOutput.innerHTML='';
    scaffoldOutput.textContent='';
    throughlineDiv.textContent='';
}

function copyBraid(){
    var text=scaffoldOutput.textContent;
    navigator.clipboard.writeText(text).then(function(){alert('Braid copied!');}).catch(function(){alert('Copy failed');});
}

entryDiv=document.getElementById('entry');
activeDiv=document.getElementById('active');
textarea=document.getElementById('momentsInput');
themeInput=document.getElementById('themeWordInput');
stagingCards=document.getElementById('stagingCards');
wellPast=document.getElementById('wellPast');
wellPivot=document.getElementById('wellPivot');
wellEmerging=document.getElementById('wellEmerging');
timelineOutput=document.getElementById('timelineOutput');
scaffoldOutput=document.getElementById('scaffoldOutput');
throughlineDiv=document.getElementById('throughline');

document.getElementById('setLoomBtn').addEventListener('click',setLoom);
textarea.addEventListener('input',setLoom);
themeInput.addEventListener('input',renderAll);
document.getElementById('copyBraidBtn').addEventListener('click',copyBraid);
document.getElementById('resetBtn').addEventListener('click',resetLoom);

stagingCards.addEventListener('click',function(e){
    var card=e.target.closest('.card');
    if(!card)return;
    var idx=parseInt(card.getAttribute('data-index'),10);
    if(!isNaN(idx)&&idx>=0&&idx<moments.length){
        var m=moments[idx];
        var threads=['Past','Pivot','Emerging'];
        var tIdx=threads.indexOf(m.thread);
        if(tIdx>=0) m.thread=threads[(tIdx+1)%3];
        renderAll();
    }
});

var initText={{ input_text | safe }};
if(initText){textarea.value=initText;setLoom();}
</script>
</body>
</html>''')

def process(text: str) -> str:
    """Generate interactive Braid Reclamation Loom with pasted career moments."""
    if not text.strip():
        return "<html><body><h1>Braid Reclamation Loom</h1><p>Please paste career moments to begin.</p></body></html>"
    safe_text = json.dumps(text)
    return TEMPLATE.render(input_text=safe_text)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    pass