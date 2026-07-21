# Requirements: python-dateutil, jinja2
import csv
import io
import json
import re
from dateutil import parser as dtparser
from jinja2 import Template
from collections import OrderedDict

TEMPLATE_HTML = r'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Headline Resonance Ledger</title>
<style>
*{box-sizing:border-box;font-family:system-ui,sans-serif}
body{margin:0;padding:20px;background:#f5f5f5}
#controls{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-bottom:15px;background:white;padding:12px 16px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
#controls label{font-size:14px;display:flex;align-items:center;gap:4px}
#controls select{padding:4px 8px;border-radius:4px;border:1px solid #ccc}
button{padding:6px 14px;border:none;border-radius:4px;cursor:pointer;background:#4d90fe;color:white;font-weight:500}
button:hover{background:#357ae8}
#range-slider{position:relative;width:200px;height:24px;margin:0 8px}
#range-slider input[type=range]{position:absolute;width:100%;pointer-events:none;appearance:none;height:6px;background:transparent;top:9px;left:0}
#range-slider input[type=range]::-webkit-slider-thumb{pointer-events:auto;width:14px;height:14px;border-radius:50%;background:#4d90fe;cursor:pointer;appearance:none;margin-top:-4px}
#range-slider input[type=range]::-moz-range-thumb{pointer-events:auto;width:14px;height:14px;border-radius:50%;background:#4d90fe;cursor:pointer}
#range-slider::before{content:'';position:absolute;top:9px;left:0;width:100%;height:6px;background:#ccc;border-radius:3px;z-index:0}
#timeline-container{width:100%;height:75vh;overflow-y:auto;overflow-x:auto;background:white;border-radius:8px;padding:10px;box-shadow:0 2px 4px rgba(0,0,0,0.1);position:relative}
#timeline-svg{display:block;min-width:600px}
#tooltip{position:fixed;background:white;border:1px solid #aaa;padding:6px 10px;border-radius:4px;font-size:14px;max-width:300px;word-wrap:break-word;box-shadow:0 2px 6px rgba(0,0,0,0.15);pointer-events:none;z-index:1000;transition:opacity 0.15s}
#export-modal{display:none;position:fixed;top:20%;left:10%;width:80%;max-height:70vh;background:white;border:2px solid #aaa;border-radius:8px;z-index:2000;padding:16px;flex-direction:column}
#export-modal textarea{width:100%;height:200px;margin-top:8px;font-family:monospace}
#export-modal button{margin-top:8px;align-self:flex-end}
</style></head><body>
<div id="controls">
  <label>Group by: <select id="groupBy"><option value="mood">Mood</option><option value="campaign">Campaign</option></select></label>
  <label>Mood: <select id="filterMood"><option value="all">All</option></select></label>
  <label>Campaign: <select id="filterCampaign"><option value="all">All</option></select></label>
  <label>Date: <div id="range-slider"><input type="range" id="rangeMin" min="0" max="100" value="0" step="1"><input type="range" id="rangeMax" min="0" max="100" value="100" step="1"></div></label>
  <button id="resetBtn">Reset</button>
  <button id="exportBtn">Export visible</button>
</div>
<div id="timeline-container"><svg id="timeline-svg"></svg></div>
<div id="tooltip" style="opacity:0"></div>
<div id="export-modal"><h3>Visible headlines</h3><textarea readonly></textarea><button id="closeExport">Close</button></div>
<script>
const ENTRIES = {{ data|safe }};
const COLORS = ["#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#a65628","#f781bf","#999999","#66c2a5","#8dd3c7"];
let minDate, maxDate, totalWidth, groupField = 'mood';
let moodColorMap = {};
function initData(){
  if(ENTRIES.length===0) return;
  const dates = ENTRIES.map(e=>new Date(e.date));
  minDate = new Date(Math.min(...dates));
  maxDate = new Date(Math.max(...dates));
  if(maxDate - minDate === 0){maxDate = new Date(minDate.getTime()+86400000);}
  const daysDiff = (maxDate - minDate)/86400000;
  totalWidth = Math.max(800, daysDiff*6 + 200);
  // assign colors to moods
  const moods = [...new Set(ENTRIES.map(e=>e.mood))];
  moods.forEach((m,i)=>moodColorMap[m]=COLORS[i%COLORS.length]);
  populateDropdowns();
  buildTimeline();
}
function populateDropdowns(){
  const moods = [...new Set(ENTRIES.map(e=>e.mood))];
  const campaigns = [...new Set(ENTRIES.map(e=>e.campaign))];
  const moodSel = document.getElementById('filterMood');
  const campSel = document.getElementById('filterCampaign');
  [moodSel, campSel].forEach(s=>{while(s.options.length>1)s.remove(1);});
  moods.forEach(m=>{const o=document.createElement('option');o.value=m;o.text=m;moodSel.add(o);});
  campaigns.forEach(c=>{const o=document.createElement('option');o.value=c;o.text=c;campSel.add(o);});
}
function getFilteredEntries(){
  const moodFilter = document.getElementById('filterMood').value;
  const campFilter = document.getElementById('filterCampaign').value;
  const minP = parseInt(document.getElementById('rangeMin').value);
  const maxP = parseInt(document.getElementById('rangeMax').value);
  const totalMs = maxDate - minDate;
  return ENTRIES.filter(e=>{
    if(moodFilter!=='all' && e.mood!==moodFilter) return false;
    if(campFilter!=='all' && e.campaign!==campFilter) return false;
    const d = new Date(e.date);
    const p = totalMs>0 ? (d-minDate)/totalMs*100 : 50;
    return p>=minP && p<=maxP;
  });
}
function buildTimeline(){
  const svg = document.getElementById('timeline-svg');
  const container = document.getElementById('timeline-container');
  groupField = document.getElementById('groupBy').value;
  const filtered = getFilteredEntries();
  if(filtered.length===0){
    svg.innerHTML='<text x="20" y="30" font-size="14">No headlines match filters.</text>';
    svg.setAttribute('width',400);
    svg.setAttribute('height',80);
    return;
  }
  const groups = {};
  filtered.forEach(e=>{
    const key = e[groupField] || 'undefined';
    if(!groups[key]) groups[key]=[];
    groups[key].push(e);
  });
  const groupKeys = Object.keys(groups).sort();
  const groupHeight = 50;
  const paddingTop = 30;
  const svgHeight = groupKeys.length * groupHeight + paddingTop + 20;
  svg.setAttribute('width', totalWidth);
  svg.setAttribute('height', svgHeight);
  let html = '<g>';
  // y-axis labels, group bands
  groupKeys.forEach((key, i)=>{
    const y = paddingTop + i*groupHeight + groupHeight/2;
    html += `<text x="10" y="${y}" alignment-baseline="middle" font-size="12" fill="#333">${key}</text>`;
    html += `<line x1="80" y1="${y+6}" x2="${totalWidth}" y2="${y+6}" stroke="#eee" stroke-dasharray="4"/>`;
  });
  // draw circles
  filtered.forEach(e=>{
    const key = e[groupField]||'undefined';
    const i = groupKeys.indexOf(key);
    if(i<0) return;
    const y = paddingTop + i*groupHeight + groupHeight/2 + 6;
    const d = new Date(e.date);
    const totalMs = maxDate - minDate;
    const x = totalMs>0 ? ((d-minDate)/totalMs * totalWidth) : totalWidth/2;
    const color = moodColorMap[e.mood] || '#ccc';
    const title = e.headline.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    html += `<circle cx="${x}" cy="${y}" r="6" fill="${color}" stroke="#fff" stroke-width="1" data-headline="${title}" data-campaign="${e.campaign}" data-date="${e.date}" data-mood="${e.mood}" class="dot" style="cursor:pointer"/>`;
  });
  html += '</g>';
  // axis
  const axisY = svgHeight - 15;
  html += `<line x1="80" y1="${axisY}" x2="${totalWidth}" y2="${axisY}" stroke="#999"/>`;
  // date ticks
  const tickCount = Math.min(10, Math.floor(totalWidth/100));
  for(let i=0;i<=tickCount;i++){
    const fraction = i/tickCount;
    const x = 80 + (totalWidth-80)*fraction;
    const t = new Date(minDate.getTime() + fraction*(maxDate-minDate));
    const label = t.toISOString().slice(0,10);
    html += `<line x1="${x}" y1="${axisY-4}" x2="${x}" y2="${axisY+4}" stroke="#999"/><text x="${x}" y="${axisY+14}" text-anchor="middle" font-size="10">${label}</text>`;
  }
  svg.innerHTML = html;
  attachTooltips();
}
function attachTooltips(){
  const tooltip = document.getElementById('tooltip');
  document.querySelectorAll('#timeline-svg .dot').forEach(circle=>{
    circle.addEventListener('mouseenter',(e)=>{
      const headline = circle.getAttribute('data-headline');
      tooltip.textContent = headline;
      tooltip.style.opacity='1';
    });
    circle.addEventListener('mousemove',(e)=>{
      tooltip.style.left=(e.clientX+12)+'px';
      tooltip.style.top=(e.clientY-30)+'px';
    });
    circle.addEventListener('mouseleave',()=>{tooltip.style.opacity='0';});
  });
}
function exportVisible(){
  const filtered = getFilteredEntries();
  const text = filtered.map(e=>`${e.date} | ${e.campaign} | ${e.mood} | ${e.headline}`).join('\n');
  const modal = document.getElementById('export-modal');
  modal.querySelector('textarea').value = text;
  modal.style.display='flex';
}
document.getElementById('resetBtn').addEventListener('click',()=>{
  document.getElementById('filterMood').value='all';
  document.getElementById('filterCampaign').value='all';
  document.getElementById('rangeMin').value=0;
  document.getElementById('rangeMax').value=100;
  buildTimeline();
});
document.getElementById('exportBtn').addEventListener('click',exportVisible);
document.getElementById('closeExport').addEventListener('click',()=>{
  document.getElementById('export-modal').style.display='none';
});
document.getElementById('filterMood').addEventListener('change',buildTimeline);
document.getElementById('filterCampaign').addEventListener('change',buildTimeline);
document.getElementById('groupBy').addEventListener('change',buildTimeline);
document.getElementById('rangeMin').addEventListener('input',function(){
  if(parseInt(this.value)>parseInt(document.getElementById('rangeMax').value))
    this.value = document.getElementById('rangeMax').value;
  buildTimeline();
});
document.getElementById('rangeMax').addEventListener('input',function(){
  if(parseInt(this.value)<parseInt(document.getElementById('rangeMin').value))
    this.value = document.getElementById('rangeMin').value;
  buildTimeline();
});
window.addEventListener('load',initData);
</script></body></html>'''

def parse_csv(text: str):
    """Parse CSV with columns: date, headline, campaign, mood (any order)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 2:
        return []
    header = lines[0].split(',')
    idx = [h.strip().lower() for h in header]
    date_idx = next((i for i, h in enumerate(idx) if 'date' in h), None)
    headline_idx = next((i for i, h in enumerate(idx) if 'headline' in h), None)
    campaign_idx = next((i for i, h in enumerate(idx) if 'campaign' in h), None)
    mood_idx = next((i for i, h in enumerate(idx) if 'mood' in h), None)
    # fallback positions
    if date_idx is None:
        date_idx = 0
    if headline_idx is None:
        headline_idx = 1
    if campaign_idx is None:
        campaign_idx = 2 if len(idx) > 2 else None
    if mood_idx is None:
        mood_idx = 3 if len(idx) > 3 else None
    entries = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) <= max(filter(None, [date_idx, headline_idx])):  # type: ignore
            continue
        date_str = parts[date_idx]
        headline = parts[headline_idx]
        campaign = parts[campaign_idx] if campaign_idx is not None else ''
        mood = parts[mood_idx] if mood_idx is not None else ''
        try:
            date = dtparser.parse(date_str).strftime('%Y-%m-%d')
        except Exception:
            continue
        entries.append({'date': date, 'headline': headline, 'campaign': campaign, 'mood': mood})
    return entries

def parse_piped(text: str):
    """Parse pipe-delimited lines: date | campaign | mood | headline."""
    entries = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) != 4:
            continue
        date_str, campaign, mood, headline = parts
        try:
            date = dtparser.parse(date_str).strftime('%Y-%m-%d')
        except Exception:
            continue
        entries.append({'date': date, 'headline': headline, 'campaign': campaign, 'mood': mood})
    return entries

def parse_input(text: str):
    """Detect format and parse into list of dicts."""
    if not text.strip():
        return []
    first_line = text.strip().split('\n')[0].strip()
    if ',' in first_line and (re.search(r'\bdate\b', first_line, re.IGNORECASE) or re.search(r'\bheadline\b', first_line, re.IGNORECASE)):
        return parse_csv(text)
    else:
        return parse_piped(text)

def process(text: str) -> str:
    """Build an interactive timeline HTML from headline data."""
    if not text.strip():
        return "<html><body><p style='padding:20px'>No data provided. Please paste your headline drafts.</p></body></html>"
    entries = parse_input(text)
    entries.sort(key=lambda e: e['date'])
    data_json = json.dumps(entries)
    template = Template(TEMPLATE_HTML)
    return template.render(data=data_json)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    txt = sys.stdin.read()
    print(process(txt))