"""
Medication Merge - Portal-Bag-Post-It Merger
Collects hospital discharge, pharmacy leaflet, and nurse note transcriptions,
reconciles medication information, detects contradictions, and produces a
printable morning checklist.
"""
import re
from jinja2 import Template

def split_sources(text):
    """Split the input text into three source sections, removing headers."""
    sections = {'discharge': '', 'pharmacy': '', 'nurse': ''}
    
    # Find positions
    disc_match = re.search(r'DISCHARGE\s*SUMMARY\s*[:.-]?\s*', text, re.IGNORECASE)
    pharm_match = re.search(r'PHARMACY\s*LEAFLET\s*[:.-]?\s*', text, re.IGNORECASE)
    nurse_match = re.search(r'NURSE\s*NOTE\s*[:.-]?\s*', text, re.IGNORECASE)
    
    boundaries = []
    if disc_match:
        boundaries.append((disc_match.start(), disc_match.end(), 'discharge'))
    if pharm_match:
        boundaries.append((pharm_match.start(), pharm_match.end(), 'pharmacy'))
    if nurse_match:
        boundaries.append((nurse_match.start(), nurse_match.end(), 'nurse'))
    
    boundaries.sort()
    
    for i, (start, end, name) in enumerate(boundaries):
        if i + 1 < len(boundaries):
            next_start = boundaries[i+1][0]
            sections[name] = text[end:next_start].strip()
        else:
            sections[name] = text[end:].strip()
    
    return sections['discharge'], sections['pharmacy'], sections['nurse']

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Medication Merge</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
.step-indicator { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.step { flex: 1; text-align: center; border-bottom: 3px solid #ccc; padding-bottom: 0.5rem; font-weight: bold; }
.step.active { border-color: #007bff; color: #007bff; }
.step.completed { border-color: #28a745; color: #28a745; }
button { padding: 0.6rem 1.2rem; margin: 0.3rem; cursor: pointer; }
textarea { width: 100%; height: 150px; font-family: monospace; margin-bottom: 1rem; }
.hidden { display: none; }
table { width: 100%; border-collapse: collapse; margin: 1.5rem 0; }
th, td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
.contradiction { background-color: #fdd; }
.warning { color: #b00; font-size: 0.9rem; }
.morning-checklist { border: 1px solid #ddd; padding: 1rem; margin: 1rem 0; }
.morning-checklist ul { list-style: none; padding-left: 0; }
.checkbox-item { display: flex; align-items: center; gap: 0.5rem; }
.checkbox-item input[type=checkbox] { transform: scale(1.3); }
.print-button { background: #007bff; color: white; border: none; padding: 0.8rem 1.2rem; }
</style>
</head>
<body>
<h1>Medication Merge</h1>
<p>Paste your discharge, pharmacy, and nurse notes to get a safe, contradiction-checked schedule.</p>
<div id="wizard">
  <div class="step-indicator">
    <div class="step active" id="step1-ind">1 of 3</div>
    <div class="step" id="step2-ind">2 of 3</div>
    <div class="step" id="step3-ind">3 of 3</div>
  </div>
  <div id="step1">
    <p><strong>Hospital Discharge Summary</strong></p>
    <textarea id="src0" placeholder="Paste the hospital discharge medication list here">{{ discharge }}</textarea>
    <p>Medications detected so far: <span id="count0">0</span></p>
    <button onclick="nextStep(1)">Next</button>
  </div>
  <div id="step2" class="hidden">
    <p><strong>Pharmacy Leaflet</strong></p>
    <textarea id="src1" placeholder="Paste the pharmacy leaflet content here">{{ pharmacy }}</textarea>
    <p>Medications detected so far: <span id="count1">0</span></p>
    <button onclick="prevStep(2)">Back</button>
    <button onclick="nextStep(2)">Next</button>
  </div>
  <div id="step3" class="hidden">
    <p><strong>Nurse's Handwritten Note Transcription</strong></p>
    <textarea id="src2" placeholder="Paste the nurse's note here">{{ nurse }}</textarea>
    <p>Medications detected so far: <span id="count2">0</span></p>
    <button onclick="prevStep(3)">Back</button>
    <button onclick="finish()">Generate Schedule</button>
  </div>
</div>
<div id="result" class="hidden"></div>
<script>
// Levenshtein distance
function levenshtein(a,b){
  const m=a.length,n=b.length,dp=Array.from({length:m+1},()=>Array(n+1).fill(0));
  for(let i=0;i<=m;i++)dp[i][0]=i;
  for(let j=0;j<=n;j++)dp[0][j]=j;
  for(let i=1;i<=m;i++){for(let j=1;j<=n;j++){if(a[i-1]===b[j-1])dp[i][j]=dp[i-1][j-1];else dp[i][j]=1+Math.min(dp[i-1][j],dp[i][j-1],dp[i-1][j-1]);}}
  return dp[m][n];
}
function hasCommonSubstring(a,b,len){
  for(let i=0;i<=a.length-len;i++){let sub=a.slice(i,i+len); if(b.includes(sub))return true;}
  return false;
}
function canonicalName(raw){
  let name=raw.trim().toLowerCase().split(/[\(]/)[0].trim();
  return name || raw.trim().toLowerCase();
}
function extractFeatures(stmt){
  let doseMatch=stmt.match(/(\d+\s*(?:mg|mcg|g|mL|unit|tab(?:let)?s?))/i);
  let dose=doseMatch?doseMatch[1]:'';
  let timing=[];
  let food='UNSPECIFIED';
  let admin='';
  if(/morning|A\.?M\.?|breakfast|8[:.]?[ ]?[0]?[0-9]?\s*(?:AM|am)/i.test(stmt)) timing.push('MORNING');
  if(/noon|12[:.]?[ ]?[0]?[0-9]?\s*(?:PM|pm)/i.test(stmt)) timing.push('NOON');
  if(/evening|dinner|(?:[5-9]|1[0-9]|20)[:.]?[0-9]{2}\s*(?:PM|pm)/i.test(stmt)) timing.push('EVENING');
  if(/bedtime|night|before bed|(?:2[1-3]|0[0-5])[:.]?[0-9]{2}\s*(?:AM|am)/i.test(stmt)) timing.push('BEDTIME');
  if(/twice daily|two times a day|BID/i.test(stmt) && timing.length===0) timing.push('MORNING','EVENING');
  if(/once daily|once a day|daily/i.test(stmt) && timing.length===0) timing.push('MORNING');
  if(/with food|take with meal|with meals|with a small snack/i.test(stmt)) food='WITH_FOOD';
  if(/on empty stomach|without food|take before meal|before breakfast/i.test(stmt)) food='WITHOUT_FOOD';
  if(/with or without food/i.test(stmt)) food='UNSPECIFIED';
  if(/orally|capsule|tablet|take/i.test(stmt)) admin='ORAL';
  else if(/injection|inject/i.test(stmt)) admin='INJECTION';
  else if(/apply|topical/i.test(stmt)) admin='TOPICAL';
  return {dose,timing,food,admin};
}
function extractMedications(txt){
  let statements=txt.split(/[.;\n]+/).filter(s=>s.trim());
  let meds=[];
  for(let st of statements){
    let matches=st.match(/([A-Z][a-zA-Z\-]*\s*(?:\([^)]*\)\s*)?)\s*(\d+\s*(?:mg|mcg|g|mL|unit|tab(?:let)?s?)?)/gi);
    if(matches){
      for(let m of matches){
        let nameFull=m.split(/\s*\d/)[0].trim();
        let feats=extractFeatures(st);
        meds.push({raw:st, nameFull, dose:feats.dose, timing:feats.timing, food:feats.food, admin:feats.admin, canonical:canonicalName(nameFull), originalName:nameFull});
      }
    }
  }
  return meds;
}
let sourcesData=[];
function nextStep(from){
  let srcId=from-1;
  let ta=document.getElementById('src'+srcId);
  let meds=extractMedications(ta.value);
  document.getElementById('count'+srcId).textContent=meds.length;
  sourcesData[srcId]=meds;
  document.getElementById('step'+from).classList.add('hidden');
  document.getElementById('step'+from+'-ind').classList.remove('active');
  document.getElementById('step'+from+'-ind').classList.add('completed');
  let next=from+1;
  document.getElementById('step'+next).classList.remove('hidden');
  document.getElementById('step'+next+'-ind').classList.add('active');
}
function prevStep(from){
  document.getElementById('step'+from).classList.add('hidden');
  document.getElementById('step'+from+'-ind').classList.remove('active');
  let prev=from-1;
  document.getElementById('step'+prev).classList.remove('hidden');
  document.getElementById('step'+prev+'-ind').classList.add('active');
}
function finish(){
  let src2=document.getElementById('src2');
  let meds=extractMedications(src2.value);
  document.getElementById('count2').textContent=meds.length;
  sourcesData[2]=meds;
  let allEntries=[];
  for(let si=0;si<sourcesData.length;si++){
    for(let m of sourcesData[si]){
      allEntries.push({med:m, source:si});
    }
  }
  let clusters=[];
  let used=new Set();
  for(let i=0;i<allEntries.length;i++){
    if(used.has(i)) continue;
    let cluster=[allEntries[i]];
    used.add(i);
    for(let j=i+1;j<allEntries.length;j++){
      if(used.has(j)) continue;
      let a=allEntries[i].med.canonical, b=allEntries[j].med.canonical;
      let dist=levenshtein(a,b);
      let minLen=Math.min(a.length,b.length);
      if(dist<=2 && minLen>=4 && hasCommonSubstring(a,b,4)){
        cluster.push(allEntries[j]);
        used.add(j);
      }
    }
    clusters.push(cluster);
  }
  let rows=[];
  let morningMeds=[];
  for(let cl of clusters){
    let timingSet=new Map();
    let foodMap=new Map();
    let adminMap=new Map();
    let names=[];
    let doses=[];
    for(let e of cl){
      for(let t of e.med.timing){ if(!timingSet.has(t)) timingSet.set(t,new Set()); timingSet.get(t).add(e.source); }
      if(e.med.food!=='UNSPECIFIED'){ if(!foodMap.has(e.med.food)) foodMap.set(e.med.food,new Set()); foodMap.get(e.med.food).add(e.source); }
      if(e.med.admin){ if(!adminMap.has(e.med.admin)) adminMap.set(e.med.admin,new Set()); adminMap.get(e.med.admin).add(e.source); }
      names.push(e.med.originalName);
      if(e.med.dose) doses.push(e.med.dose);
    }
    function selectBest(map){
      let bestVal=null;
      let bestPriority=Infinity;
      for(let [val,sources] of map){
        for(let src of sources){
          let priority= src===0?0: src===2?1:2;
          if(priority<bestPriority){
            bestPriority=priority;
            bestVal=val;
          }
        }
      }
      return bestVal;
    }
    let finalTiming=Array.from(timingSet.keys());
    let timingContradiction=false;
    let allSourceTimings=[];
    for(let e of cl){
      allSourceTimings.push({src:e.source, slots:e.med.timing.slice()});
    }
    for(let i=0;i<allSourceTimings.length;i++){
      for(let j=i+1;j<allSourceTimings.length;j++){
        let a=allSourceTimings[i].slots.sort().join(',');
        let b=allSourceTimings[j].slots.sort().join(',');
        if(a!==b && a!=='' && b!=='') timingContradiction=true;
      }
    }
    let finalFood=foodMap.size>0?selectBest(foodMap):'UNSPECIFIED';
    let foodContradiction=false;
    if(foodMap.size>1) foodContradiction=true;
    let finalAdmin=adminMap.size>0?selectBest(adminMap):'';
    let uniqueNames=[...new Set(names)];
    let uniqueDoses=[...new Set(doses)];
    let row={
      name:uniqueNames.join(', '),
      dose:uniqueDoses.join(', '),
      timing:finalTiming,
      food:finalFood,
      admin:finalAdmin,
      contradiction: timingContradiction || foodContradiction,
      notes: (timingContradiction?'Timing conflict among sources. ':'') + (foodContradiction?'Food instruction conflict. ':''),
      morning: finalTiming.includes('MORNING')
    };
    rows.push(row);
    if(row.morning) morningMeds.push(row);
  }
  let html='<h2>Reconciled Medication Schedule</h2>';
  html+='<table><thead><tr><th>Medication</th><th>Dosage</th><th>Timing</th><th>Food</th><th>Administration</th><th>Warnings</th></tr></thead><tbody>';
  for(let r of rows){
    let cls=r.contradiction?' class="contradiction"':'';
    let warning=r.contradiction?`<span class="warning">⚠ ${r.notes}</span>`:'';
    // Format timing for display
    let timingDisplay=r.timing.map(t=>{
      if(t==='MORNING') return '8:00 AM';
      if(t==='EVENING') return 'Evening';
      if(t==='BEDTIME') return 'Bedtime';
      if(t==='NOON') return 'Noon';
      return t;
    }).join(', ');
    // Format food for display
    let foodDisplay=r.food;
    if(foodDisplay==='WITH_FOOD') foodDisplay='with food';
    if(foodDisplay==='WITHOUT_FOOD') foodDisplay='Without food';
    let conflictTag=r.contradiction?' CONFLICT':'';
    html+=`<tr${cls}><td>${r.name}</td><td>${r.dose}</td><td>${timingDisplay}</td><td>${foodDisplay}</td><td>${r.admin}</td><td>${warning}${conflictTag}</td></tr>`;
  }
  html+='</tbody></table>';
  if(morningMeds.length){
    html+='<div class="morning-checklist" id="morning"><h3>Morning Checklist</h3><ul>';
    for(let r of morningMeds){
      let fd=r.food;
      if(fd==='WITH_FOOD') fd='with food';
      if(fd==='WITHOUT_FOOD') fd='Without food';
      html+=`<li class="checkbox-item"><input type="checkbox" id="chk_${r.name.replace(/\s/g,'_')}"><label>${r.name} ${r.dose} (${fd})</label></li>`;
    }
    html+='</ul></div>';
  }
  html+='<button class="print-button" onclick="window.print()">Print Morning Schedule</button> ';
  html+='<button onclick="copyText()">Copy as Text</button>';
  html+='<div class="hidden" id="plaintext"></div>';
  document.getElementById('result').innerHTML=html;
  document.getElementById('step3').classList.add('hidden');
  document.getElementById('step3-ind').classList.remove('active');
  document.getElementById('step3-ind').classList.add('completed');
  document.getElementById('result').classList.remove('hidden');
  let plain='Medication Schedule\n'+rows.map(r=>`${r.name} | ${r.dose} | ${r.timing.join('/')} | ${r.food} | ${r.admin} | ${r.contradiction?'WARNING: '+r.notes:''}`).join('\n');
  if(morningMeds.length){
    plain+='\n\nMorning Checklist:\n'+morningMeds.map(r=>`[ ] ${r.name} ${r.dose} (${r.food})`).join('\n');
  }
  document.getElementById('plaintext').textContent=plain;
}
function copyText(){
  let t=document.getElementById('plaintext');
  t.classList.remove('hidden');
  t.focus();
  t.select();
  document.execCommand('copy');
  t.classList.add('hidden');
  alert('Copied to clipboard');
}
// Auto-advance through all steps and generate schedule
(function autoProcess(){
  // Process step 1
  let meds0=extractMedications(document.getElementById('src0').value);
  document.getElementById('count0').textContent=meds0.length;
  sourcesData[0]=meds0;
  // Process step 2
  let meds1=extractMedications(document.getElementById('src1').value);
  document.getElementById('count1').textContent=meds1.length;
  sourcesData[1]=meds1;
  // Process step 3
  let meds2=extractMedications(document.getElementById('src2').value);
  document.getElementById('count2').textContent=meds2.length;
  sourcesData[2]=meds2;
  // Call finish logic
  finish();
})();
</script>
</body>
</html>''')

def process(text: str) -> str:
    """Generate Medication Merge wizard HTML with pre-filled, pre-processed sections."""
    if not text.strip():
        text = ""
    discharge, pharmacy, nurse = split_sources(text)
    return TEMPLATE.render(discharge=discharge, pharmacy=pharmacy, nurse=nurse)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            print(process(f.read()))
    else:
        print(process(""))