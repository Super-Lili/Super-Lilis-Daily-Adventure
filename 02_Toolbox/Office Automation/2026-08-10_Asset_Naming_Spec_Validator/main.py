"""
Asset Naming Spec Validator (Mode 3 interactive HTML)
Generates a complete self-contained HTML tool.

Algorithmic depth implemented fully in client-side JS:
1. Pattern parsing → Cartesian product of all combinations.
2. File name normalization (strip extension, lowercase).
3. Exact token match, else Levenshtein alignment over tokens.
4. Greedy best-match assignment with distance threshold.
5. Missing/ unexpected flagging and detailed mismatch reports.
"""

from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Naming Validator</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui, sans-serif;}
body{background:#f9fafb;display:flex;justify-content:center;align-items:center;min-height:100vh;}
#app{width:960px;max-width:100%;background:white;border-radius:16px;box-shadow:0 20px 35px rgba(0,0,0,0.07);overflow:hidden;transition:all 0.4s;}
.screen{display:none;padding:40px 48px;min-height:480px;flex-direction:column;justify-content:center;}
.screen.active{display:flex;}
h1{font-size:28px;font-weight:700;margin-bottom:8px;color:#0f172a;}
textarea{width:100%;min-height:100px;border:2px solid #e2e8f0;border-radius:10px;padding:14px 18px;font-size:16px;resize:vertical;margin:20px 0 12px;transition:border-color .2s;}
textarea:focus{border-color:#3b82f6;outline:none;}
.tooltip{font-size:13px;color:#64748b;margin-bottom:24px;background:#f1f5f9;padding:8px 14px;border-radius:8px;display:inline-block;}
.btn{padding:12px 28px;border-radius:10px;font-weight:600;font-size:15px;border:none;cursor:pointer;transition:all .2s;}
.btn-primary{background:#3b82f6;color:white;}
.btn-primary:hover{background:#2563eb;}
.btn-secondary{background:#e2e8f0;color:#1e293b;margin-left:12px;}
.drop-zone{border:2px dashed #94a3b8;border-radius:16px;padding:64px 20px;text-align:center;color:#475569;cursor:pointer;transition:background .2s;margin-top:12px;}
.drop-zone.drag-over{background:#eff6ff;border-color:#3b82f6;}
#fileInput{display:none;}
.result-box{overflow:auto;max-height:60vh;margin:16px 0;}
table{width:100%;border-collapse:collapse;font-size:14px;}
th{text-align:left;padding:12px 8px;background:#f8fafc;border-bottom:2px solid #cbd5e1;}
td{padding:10px 8px;border-bottom:1px solid #e2e8f0;}
tr.match{background:#ecfdf5;}
tr.mismatch{background:#fffbeb;}
tr.missing{background:#fef2f2;}
tr.unexpected{background:#f8fafc;color:#64748b;}
.summary{display:flex;gap:32px;font-size:15px;padding:12px 0;border-top:2px solid #e2e8f0;margin-bottom:16px;}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;}
.match-dot{background:#10b981;}
.mismatch-dot{background:#f59e0b;}
.missing-dot{background:#ef4444;}
.actions{display:flex;gap:12px;}
.scanning{text-align:center;padding:32px;animation:pulse 1s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}
</style></head><body>
<div id="app">
 <div id="screen1" class="screen active">
  <h1>Naming Validator</h1>
  <textarea id="patternInput" placeholder="Pattern: {Button,Icon}/{Primary,Secondary}/{Default,Hover}@2x.png"></textarea>
  <div class="tooltip">Use curly braces <code>{ }</code> for choices. Groups separated by <code>/</code> produce folder-style patterns.</div>
  <button class="btn btn-primary" onclick="goToUpload()">Next: Upload Assets</button>
 </div>
 <div id="screen2" class="screen">
  <h1>Upload Assets</h1>
  <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
   Drop your asset folder (.zip or files) here<br>or click to select files
  </div>
  <input type="file" id="fileInput" multiple onchange="handleFiles(this.files)">
  <div style="margin-top:16px;text-align:center">
   <button class="btn btn-primary" onclick="loadExampleFiles()">Load example files</button>
  </div>
  <button class="btn btn-secondary" onclick="goToPattern()" style="margin-top:24px;">← Back to adjust pattern</button>
  <div id="scanMsg" class="scanning" style="display:none;">Scanning assets...</div>
 </div>
 <div id="screen3" class="screen">
  <h1>Validation Report</h1>
  <div id="summaryBar" class="summary"></div>
  <div class="result-box"><table id="reportTable"><thead><tr><th>Expected</th><th>Actual</th><th>Status</th><th>Deviation</th></tr></thead><tbody></tbody></table></div>
  <div class="actions">
   <button class="btn btn-primary" onclick="copyMismatchReport()">Copy Mismatch Report</button>
   <button class="btn btn-primary" onclick="downloadCSV()">Download CSV</button>
   <button class="btn btn-secondary" onclick="goToPattern()">Back to adjust pattern</button>
  </div>
 </div>
</div>
<script>
// ----- START JS -----
let expectedList=[];
let currentPattern='';
// screen switching
function showScreen(id){
 ['screen1','screen2','screen3'].forEach(s=>document.getElementById(s).classList.remove('active'));
 document.getElementById(id).classList.add('active');
 if(id==='screen3') buildSummaryUI();
}
function goToUpload(){ if(!document.getElementById('patternInput').value.trim()) return; showScreen('screen2'); }
function goToPattern(){ showScreen('screen1'); }

// pattern parsing: returns array of options per segment
function parsePattern(pattern){
 const parts = pattern.split('/').filter(p=>p.length);
 const segments=[];
 for(let part of parts){
  const match = part.match(/^([^{]*){([^}]+)}(.*)$/);
  if(match){
   const pre=match[1], choices=match[2].split(',').map(s=>s.trim()), suf=match[3];
   segments.push(choices.map(c=>pre+c+suf));
  }else{
   segments.push([part]);
  }
 }
 return segments;
}
function cartesian(arrays){
 return arrays.reduce((acc,curr)=>acc.flatMap(a=>curr.map(c=>a+'/'+c)));
}
function generateExpected(pattern){
 const segs=parsePattern(pattern);
 if(segs.length===0) return [];
 if(segs.length===1) return segs[0].map(s=>s); // no slashes needed
 let prod=cartesian(segs);
 return prod;
}
function normalize(name){
 // strip extension and path, lowercase
 let base = name.replace(/^.*[\\/]/,''); // remove path if any
 base = base.replace(/\.[^.]*$/,''); // remove extension
 return base.toLowerCase();
}
function tokenize(str){
 return str.split(/[-/_@.]+/).filter(Boolean);
}
function levenshtein(a,b){
 const m=a.length,n=b.length;
 let dp=Array.from({length:m+1},()=>Array(n+1).fill(0));
 for(let i=0;i<=m;i++) dp[i][0]=i;
 for(let j=0;j<=n;j++) dp[0][j]=j;
 for(let i=1;i<=m;i++){
  for(let j=1;j<=n;j++){
   dp[i][j]= a[i-1]===b[j-1]? dp[i-1][j-1]: Math.min(dp[i-1][j-1],dp[i][j-1],dp[i-1][j])+1;
  }
 }
 return dp[m][n];
}
// deviation description between actual and expected normalized strings
function describeDeviation(actualNorm,expNorm){
 const aTok=tokenize(actualNorm), eTok=tokenize(expNorm);
 if(aTok.length===0||eTok.length===0) return 'structure mismatch';
 if(actualNorm===expNorm) return '';
 let parts=[];
 if(actualNorm!==expNorm.replace(/\//g,'-')){
   const sepDiff = (actualNorm.includes('/')!==expNorm.includes('/'))? 'separator mismatch':'';
   if(sepDiff) parts.push(sepDiff);
 }
 if(actualNorm.toLowerCase()!==expNorm.toLowerCase()){
   if(actualNorm.toLowerCase()===expNorm.toLowerCase().replace(/[^a-z0-9]/g,'')) parts.push('case difference');
 }
 const aSet=new Set(aTok), eSet=new Set(eTok);
 const missing=eTok.filter(t=>!aSet.has(t));
 const extra=aTok.filter(t=>!eSet.has(t));
 if(missing.length) parts.push('missing token(s): '+missing.join(','));
 if(extra.length) parts.push('extra token(s): '+extra.join(','));
 return parts.join('; ')||'token order/extra tokens';
}
// main validation
function validate(actualNames){
 const expNormList = expectedList.map(e=> ({original:e, norm:normalize(e), tokens:tokenize(normalize(e))}));
 const MAX_DIST=3;
 let matchedExpectedIndices=new Set();
 let results=[];
 let actItems = actualNames.map(fname=>({ original:fname, norm:normalize(fname), tokens:tokenize(normalize(fname)) }));
 // attempt exact token match first
 for(let ai=0;ai<actItems.length;ai++){
  let act=actItems[ai];
  let found=-1;
  for(let ei=0;ei<expNormList.length;ei++){
   if(matchedExpectedIndices.has(ei)) continue;
   let exp=expNormList[ei];
   if(JSON.stringify(act.tokens)===JSON.stringify(exp.tokens)){
    found=ei; break;
   }
  }
  if(found!==-1){
   matchedExpectedIndices.add(found);
   results.push({exp:expNormList[found].original, act:act.original, status:'Match', deviation:''});
   continue;
  }
  // else find best Levenshtein match among unmatched
  let bestDist=Infinity, bestIdx=-1;
  for(let ei=0;ei<expNormList.length;ei++){
   if(matchedExpectedIndices.has(ei)) continue;
   let exp=expNormList[ei];
   let d=levenshtein(act.tokens,exp.tokens);
   if(d<bestDist){bestDist=d;bestIdx=ei;}
  }
  if(bestDist<=MAX_DIST && bestIdx!==-1){
   matchedExpectedIndices.add(bestIdx);
   let exp=expNormList[bestIdx];
   results.push({exp:exp.original, act:act.original, status:'Mismatch', deviation:describeDeviation(act.norm,exp.norm)});
  }else{
   results.push({exp:'-', act:act.original, status:'Unexpected', deviation:'no matching expected file'});
  }
 }
 // missing expected
 for(let ei=0;ei<expNormList.length;ei++){
  if(!matchedExpectedIndices.has(ei)){
   results.push({exp:expNormList[ei].original, act:'-', status:'Missing', deviation:'file not provided'});
  }
 }
 return results;
}
function handleFiles(files){
 if(!files||files.length===0) return;
 let names=[];
 for(let f of files) names.push(f.name);
 doValidation(names);
}
function doValidation(actualNames){
 currentPattern=document.getElementById('patternInput').value.trim();
 if(!currentPattern) return;
 expectedList=generateExpected(currentPattern);
 const scan=document.getElementById('scanMsg');
 scan.style.display='block';
 setTimeout(()=>{
  scan.style.display='none';
  const report=validate(actualNames);
  renderReport(report);
  showScreen('screen3');
 },600);
}
function renderReport(report){
 const tbody=document.getElementById('reportTable').querySelector('tbody');
 tbody.innerHTML='';
 for(let r of report){
  const tr=document.createElement('tr');
  tr.className=r.status.toLowerCase();
  tr.innerHTML=`<td>${r.exp}</td><td>${r.act}</td><td>${r.status}</td><td>${r.deviation}</td>`;
  tbody.appendChild(tr);
 }
 buildSummaryUI(report);
}
function buildSummaryUI(report){
 if(!report) return;
 const matches=report.filter(r=>r.status==='Match').length;
 const mismatches=report.filter(r=>r.status==='Mismatch').length;
 const missing=report.filter(r=>r.status==='Missing').length;
 const unexpected=report.filter(r=>r.status==='Unexpected').length;
 document.getElementById('summaryBar').innerHTML=
  `<span><span class="dot match-dot"></span>${matches} matches</span>
   <span><span class="dot mismatch-dot"></span>${mismatches} mismatches</span>
   <span><span class="dot missing-dot"></span>${missing} missing</span>
   ${unexpected>0?`<span>+${unexpected} unexpected</span>`:''}`;
}
function loadExampleFiles(){
 // Example files that exercise match, mismatch, missing, and unexpected cases
 const examples=[
  'Disable@2x.png',
  'button_primary_hover@2x.png',
  'Thumbs.db',
  'Button/Primary/Default@2x.png',
  'Icon/Secondary/Disabled@2x.png'
 ];
 doValidation(examples);
}
// drag and drop
const dropZone=document.getElementById('dropZone');
dropZone.addEventListener('dragover',e=>{e.preventDefault();dropZone.classList.add('drag-over');});
dropZone.addEventListener('dragleave',e=>{e.preventDefault();dropZone.classList.remove('drag-over');});
dropZone.addEventListener('drop',e=>{
 e.preventDefault();dropZone.classList.remove('drag-over');
 let files=e.dataTransfer.files;
 if(files.length) handleFiles(files);
 else alert('No files dropped.');
});
// copy mismatch report
function copyMismatchReport(){
 const rows=document.querySelectorAll('#reportTable tbody tr.mismatch');
 let text='Mismatch Report\n';
 rows.forEach(r=>{
  const cells=r.querySelectorAll('td');
  text+=`Expected: ${cells[0].textContent}\nActual: ${cells[1].textContent}\nDeviation: ${cells[3].textContent}\n\n`;
 });
 if(!rows.length) text+='No mismatches present in this report.';
 navigator.clipboard.writeText(text).then(()=>alert('Copied to clipboard'));
}
function downloadCSV(){
 const rows=document.querySelectorAll('#reportTable tbody tr');
 let csv='Expected,Actual,Status,Deviation\n';
 rows.forEach(r=>{
  const cells=r.querySelectorAll('td');
  csv+=`"${cells[0].textContent}","${cells[1].textContent}","${cells[2].textContent}","${cells[3].textContent}"\n`;
 });
 const blob=new Blob([csv],{type:'text/csv'});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download='naming_report.csv';a.click();
 URL.revokeObjectURL(url);
}
</script></body></html>''')

def process(text: str) -> str:
    """Return full interactive HTML for the Naming Validator tool."""
    return TEMPLATE.render()

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # For CLI testing convenience
    print(process(""))
