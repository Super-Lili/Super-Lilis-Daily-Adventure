"""Pre-Meeting Intent Memo - interactive HTML wizard (Mode 3)."""
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Pre-Meeting Intent Memo</title>
<style>
body{font-family:system-ui,sans-serif;max-width:700px;margin:2rem auto;padding:0 1rem}
h1{font-size:2rem;color:#1f2937}
textarea{width:100%;min-height:80px}
input[type=text]{width:100%}
.dot{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:4px}
.green{background:#10b981}.orange{background:#f59e0b}
#wizard div{margin:1rem 0}
#preview{background:#f3f4f6;padding:1rem;border-radius:8px;white-space:pre-wrap;font-family:monospace}
button{margin:0.5rem 0.5rem 0 0}
#decWarnings{color:#dc2626;font-weight:600}
.owner-row{display:flex;gap:0.5rem;margin:0.5rem 0}
.owner-row input{flex:1}
</style>
</head>
<body>
<div id="app">
  <h1>Pre-Meeting Intent Memo</h1>
  <div id="titleSection">
    <input type="text" id="meetingTitle" placeholder="Meeting title" required>
    <button id="startBtn">Create Memo</button>
  </div>
  <div id="wizard" style="display:none;">
    <div>
      <h2>Step 1: Purpose &amp; Participants</h2>
      <textarea id="purposeInput" placeholder="Define meeting purpose..."></textarea>
      <p><span id="clarityDot" class="dot orange"></span><span id="clarityText">Clarity: needs action verb</span></p>
      <label>Participants (comma-separated):</label>
      <input type="text" id="participantsInput" placeholder="e.g., eng-lead, design-lead">
    </div>
    <div>
      <h2>Step 2: Required Decisions</h2>
      <textarea id="decisionsInput" placeholder="One decision per line"></textarea>
      <p>Decisions: <span id="decCount">0</span></p>
      <div id="decWarnings"></div>
    </div>
    <div>
      <h2>Step 3: Owner-by-Outcome</h2>
      <div id="ownerContainer"><p>Enter decisions above to assign owners.</p></div>
    </div>
    <button id="generateBtn">Generate Memo</button>
    <h2>Live Preview</h2>
    <div id="preview"></div>
  </div>
  <div id="result" style="display:none;">
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:1rem">
      <h2>Generated Memo</h2>
      <pre id="memoTextOutput"></pre>
      <button id="copyMemo">Copy Memo</button>
      <button id="copyLink">Copy Share Link</button>
      <button id="editBtn">Edit</button>
    </div>
  </div>
</div>
<script>
var VERBS=["align","decide","define","confirm","assign","resolve","prioritize","agree","determine","propose","set","finalize"];
var OUTCOME=["okrs","budget","milestone","kpi","goal","objective","deliverable","outcome","success","metric"];
var TIMEWORDS=["week","month","quarter","q1","q2","q3","q4","deadline","days","year","sprint","timeline","deadline"];
function $(id){return document.getElementById(id);}
function tokenize(t){return t.toLowerCase().match(/\b\w+\b/g)||[];}
function hasVerb(toks){return toks.some(function(t){return VERBS.indexOf(t)!==-1;});}
function hasOutcome(toks){return toks.some(function(t){return OUTCOME.indexOf(t)!==-1;});}
function hasNums(t){return /\d/.test(t);}
function hasTime(toks){return toks.some(function(t){return TIMEWORDS.indexOf(t)!==-1;});}
function parseDecisions(t){return t.split('\n').map(function(l){return l.trim();}).filter(function(l){return l.length>0;});}
function normD(d){return d.toLowerCase().replace(/\s+/g,' ');}
function updateClarity(){
  var p=$('purposeInput').value,toks=tokenize(p),vb=hasVerb(toks),oc=hasOutcome(toks),nm=hasNums(p),tm=hasTime(toks);
  var dot=$('clarityDot'),txt=$('clarityText');
  if(vb&&(oc||nm||tm)){dot.className='dot green';txt.textContent='Clarity: action verb + measurable outcome';}
  else if(vb){dot.className='dot orange';txt.textContent='Action verb found \u2014 add measurable outcome (numbers, deadline, etc.)';}
  else{dot.className='dot orange';txt.textContent='Clarity: needs action verb';}
}
function updateDecisions(){
  var dtext=$('decisionsInput').value,decs=parseDecisions(dtext);
  $('decCount').textContent=decs.length;
  var warnings=[];
  if(decs.length>5)warnings.push('Strong warning: Meeting overloaded (>5 decisions). Consider splitting.');
  else if(decs.length>3)warnings.push('Soft warning: Meeting may be overloaded (>3 decisions).');
  var seen={},dupes=[];
  for(var i=0;i<decs.length;i++){
    var n=normD(decs[i]);
    if(seen.hasOwnProperty(n))dupes.push(decs[i]);else seen[n]=i;
  }
  if(dupes.length)warnings.push('Duplicate decisions detected: '+dupes.join(', '));
  $('decWarnings').innerHTML=warnings.map(function(w){return '<div>'+w+'</div>';}).join('');
  var container=$('ownerContainer');
  if(decs.length===0){container.innerHTML='<p>Enter decisions above to assign owners.</p>';}
  else{
    var html='';
    for(var i=0;i<decs.length;i++){
      var d=decs[i];
      html+='<div class="owner-row"><input class="owner-dec" value="'+d.replace(/"/g,'&quot;')+'" readonly><input class="owner-owner" placeholder="Owner"><input class="owner-next" placeholder="Next Step"></div>';
    }
    container.innerHTML=html;
  }
  updatePreview();
}
function updatePreview(){
  var title=$('meetingTitle').value.trim(),purpose=$('purposeInput').value.trim();
  var parts=$('participantsInput').value.trim(),decs=parseDecisions($('decisionsInput').value);
  var rows=document.querySelectorAll('.owner-row'),memo='';
  if(title)memo+='*Meeting:* '+title+'\n';
  if(parts){
    var plist=parts.split(',').map(function(s){return s.trim();}).filter(function(s){return s.length>0;});
    if(plist.length)memo+='*Participants:* '+plist.join(', ')+'\n';
  }
  if(purpose)memo+='*Purpose:* '+purpose+'\n';
  if(decs.length>0){
    memo+='\n*Required Decisions:*\n';
    decs.forEach(function(d){memo+='  \u2022 '+d+'\n';});
  }
  if(rows.length>0){
    memo+='\n*Owner-by-Outcome:*\n';
    memo+='  Decision | Owner | Next Step\n';
    rows.forEach(function(r){
      var d=r.querySelector('.owner-dec').value||'',o=r.querySelector('.owner-owner').value||'';
      var n=r.querySelector('.owner-next').value||'';
      memo+='  '+d+' | '+o+' | '+n+'\n';
    });
  }
  $('preview').textContent=memo||'Start filling...';
}
function generateMemo(){
  var title=$('meetingTitle').value.trim(),purpose=$('purposeInput').value.trim();
  var parts=$('participantsInput').value.trim(),decs=parseDecisions($('decisionsInput').value);
  var rows=document.querySelectorAll('.owner-row');
  var ownerOut=[];
  rows.forEach(function(r){
    var d=r.querySelector('.owner-dec'),o=r.querySelector('.owner-owner'),n=r.querySelector('.owner-next');
    ownerOut.push({decision:(d?d.value:'').trim(),owner:(o?o.value:'').trim(),next_step:(n?n.value:'').trim()});
  });
  var warnings=[],decNorm=decs.map(normD);
  var matched=ownerOut.map(function(o){return normD(o.decision);});
  for(var i=0;i<decs.length;i++){if(matched.indexOf(decNorm[i])===-1)warnings.push('Missing owner-outcome for: "'+decs[i]+'"');}
  for(var j=0;j<ownerOut.length;j++){if(decNorm.indexOf(normD(ownerOut[j].decision))===-1)warnings.push('Extra owner-outcome not in decisions: "'+ownerOut[j].decision+'"');}
  if(decs.length>5)warnings.push('Strong warning: Meeting overloaded (>5 decisions). Consider splitting.');
  else if(decs.length>3)warnings.push('Soft warning: Meeting may be overloaded (>3 decisions).');
  var dups=[];
  var seen2={};
  for(var i=0;i<decs.length;i++){var n=normD(decs[i]);if(seen2.hasOwnProperty(n))dups.push(decs[i]);else seen2[n]=i;}
  if(dups.length)warnings.push('Duplicate decisions: '+dups.join(', '));
  var toks=tokenize(purpose),vb=hasVerb(toks),oc=hasOutcome(toks),nm=hasNums(purpose),tm=hasTime(toks);
  if(!vb||!(oc||nm||tm))warnings.push('Clarity hint: add an action verb and measurable outcome indicator (e.g., numbers, deadline).');
  var now=new Date(),timestamp=now.toISOString(),id=Math.floor(now.getTime()/1000).toString(16).slice(-8);
  var plist=parts.split(',').map(function(s){return s.trim();}).filter(function(s){return s.length>0;});
  var memo='*Pre-Meeting Intent Memo*\nGenerated: '+timestamp+' | ID: '+id+'\n\n*Meeting Title:* '+title+'\n';
  if(plist.length)memo+='*Participants:* '+plist.join(', ')+'\n';
  memo+='*Purpose:* '+purpose+'\n\n';
  if(decs.length>0){memo+='*Required Decisions:*\n';decs.forEach(function(d,i){memo+=(i+1)+'. '+d+'\n';});}
  memo+='\n*Owner-by-Outcome:*\n';
  if(ownerOut.length>0)memo+=ownerOut.map(function(o){return '  Decision: '+o.decision+' | Owner: '+o.owner+' | Next Step: '+o.next_step;}).join('\n')+'\n';
  else memo+='(none)\n';
  if(warnings.length>0)memo+='\n*Warnings:*\n'+warnings.map(function(w){return '  \u26a0 '+w;}).join('\n');
  $('memoTextOutput').textContent=memo;
  $('wizard').style.display='none';$('result').style.display='block';
  var data={meeting_title:title,purpose:purpose,participants:plist,decisions:decs,owner_outcomes:ownerOut};
  window.location.hash='#memo='+encodeURIComponent(JSON.stringify(data));
}
function copyText(id){var t=$(id).textContent;navigator.clipboard.writeText(t).then(function(){alert('Copied!');});}
function copyLink(){navigator.clipboard.writeText(window.location.href).then(function(){alert('Link copied!');});}
function loadFromHash(){
  var h=window.location.hash;
  if(h.indexOf('#memo=')===0){
    try{
      var data=JSON.parse(decodeURIComponent(h.substring('#memo='.length)));
      if(data.meeting_title)$('meetingTitle').value=data.meeting_title;
      if(data.purpose)$('purposeInput').value=data.purpose;
      if(data.decisions)$('decisionsInput').value=data.decisions.join('\n');
      if(data.participants)$('participantsInput').value=data.participants.join(', ');
      updateDecisions();
      if(data.owner_outcomes){
        setTimeout(function(){
          var rows=document.querySelectorAll('.owner-row');
          for(var i=0;i<rows.length&&i<data.owner_outcomes.length;i++){
            var o=data.owner_outcomes[i];
            if(rows[i]){
              if(rows[i].querySelector('.owner-owner'))rows[i].querySelector('.owner-owner').value=o.owner||'';
              if(rows[i].querySelector('.owner-next'))rows[i].querySelector('.owner-next').value=o.next_step||'';
            }
          }
        },0);
      }
      $('titleSection').style.display='none';$('wizard').style.display='block';
      updateClarity();updatePreview();
    }catch(e){}
  }
}
$('startBtn').addEventListener('click',function(){
  if($('meetingTitle').value.trim()===''){alert('Please enter a meeting title.');return;}
  $('titleSection').style.display='none';$('wizard').style.display='block';
  updateClarity();updatePreview();
});
$('purposeInput').addEventListener('input',function(){updateClarity();updatePreview();});
$('participantsInput').addEventListener('input',updatePreview);
$('decisionsInput').addEventListener('input',updateDecisions);
document.addEventListener('change',function(e){
  if(e.target.matches('.owner-owner,.owner-next')) updatePreview();
});
$('generateBtn').addEventListener('click',generateMemo);
$('copyMemo').addEventListener('click',function(){copyText('memoTextOutput');});
$('copyLink').addEventListener('click',copyLink);
$('editBtn').addEventListener('click',function(){
  $('result').style.display='none';$('wizard').style.display='block';
});
window.addEventListener('load',loadFromHash);
</script>
</body>
</html>''')

def process(text: str = "") -> str:
    """Return the interactive HTML tool."""
    return TEMPLATE.render()

def _cli_main():
    print(process())

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()