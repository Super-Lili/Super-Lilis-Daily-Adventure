"""
Batch Episode Renamer - Interactive HTML tool to rename podcast audio filenames.
Paste filenames, optionally with configuration lines (episode, guest mapping, target pattern).
Default source pattern is Zoom; target default: "{date}_{guest}_Episode{episode}.{ext}".
"""
import json
import re
from jinja2 import Template

ZOOM_RE = re.compile(
    r'^Zoom_Recording_(?P<date>\d{4}-\d{2}-\d{2})_(?P<time>\d{2}\.\d{2}\.\d{2})'
    r'_Participant_(?P<participant>\d+)\.(?P<ext>[^.]+)$'
)
AUDIO_EXT_RE = re.compile(r'\.(mp3|wav|m4a|ogg|flac|aac|wma)$', re.IGNORECASE)

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Batch Episode Renamer</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f0f2f5;color:#333;margin:0;padding:2rem 1rem;display:flex;justify-content:center}
.container{max-width:900px;width:100%;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);padding:2rem}
h1{font-size:1.5rem;margin:0 0 1.5rem;font-weight:600}
textarea,input,select{font-family:inherit;font-size:0.95rem;width:100%;padding:0.6rem 0.8rem;border:1px solid #d1d5db;border-radius:8px;box-sizing:border-box;margin-bottom:1rem;outline:none}
textarea:focus,input:focus,select:focus{border-color:#4f46e5;box-shadow:0 0 0 3px rgba(79,70,229,0.1)}
label{font-weight:600;display:block;margin-bottom:0.3rem;color:#4b5563}
.pills{display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.6rem;font-size:0.8rem}
.pill{background:#e0e7ff;color:#3730a3;padding:0.2rem 0.6rem;border-radius:999px}
.hint{font-size:0.8rem;color:#6b7280;margin-top:-0.5rem;margin-bottom:1rem}
#guestMapping{height:4rem}
#customRegex{display:none}
table{width:100%;border-collapse:collapse;margin-top:1.5rem}
th,td{text-align:left;padding:0.5rem 0.75rem;border-bottom:1px solid #e5e7eb;font-size:0.9rem}
th{background:#f9fafb;font-weight:600;color:#4b5563}
td.error{background:#fef2f2;color:#b91c1c}
.copy-btn{background:none;border:none;cursor:pointer;font-size:1rem;color:#6b7280;padding:0.2rem;border-radius:4px;transition:all 0.2s}
.copy-btn:hover{color:#4f46e5;background:#eef2ff}
.copy-success{color:#059669!important;background:#d1fae5!important}
.actions{margin-top:1.5rem;display:flex;gap:0.5rem;flex-wrap:wrap}
.btn{background:#4f46e5;color:#fff;border:none;padding:0.6rem 1.2rem;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.9rem;transition:background 0.2s}
.btn:hover{background:#4338ca}
.btn.secondary{background:#e5e7eb;color:#374151}
.btn.secondary:hover{background:#d1d5db}
#downloadAnchor{display:none}
</style>
</head>
<body>
<div class="container">
<h1>Batch Episode Renamer</h1>
<label for="filenames">Paste filenames here (one per line)</label>
<textarea id="filenames" rows="5" placeholder="e.g. Zoom_Recording_2026-08-05_14.30.45_Participant_1234567890.mp3"></textarea>

<label for="sourcePattern">Source pattern</label>
<select id="sourcePattern">
<option value="zoom">Zoom (date_time_participant)</option>
<option value="riverside">Riverside (date_time_guest)</option>
<option value="custom">Custom regex</option>
</select>
<input type="text" id="customRegex" placeholder="Enter regex with named groups, e.g. (?<date>...)_(?<participant>...)">

<label for="targetPattern">Target pattern</label>
<div class="pills">
<span class="pill">{date}</span><span class="pill">{date:format}</span>
<span class="pill">{time}</span><span class="pill">{time:format}</span>
<span class="pill">{participant}</span><span class="pill">{guest}</span>
<span class="pill">{episode}</span><span class="pill">{ext}</span>
</div>
<input type="text" id="targetPattern" value="{{ default_target_pattern }}">

<label for="episode">Episode number</label>
<input type="text" id="episode" value="{{ default_episode }}">

<label for="guestMapping">Guest name mapping (participantID=Guest Name, one per line)</label>
<textarea id="guestMapping" rows="3" placeholder="1234567890=Jane Doe&#10;9876543210=John Smith">{{ guest_mapping }}</textarea>

<div class="actions">
<button id="previewBtn" class="btn">Preview</button>
<button id="copyAllBtn" class="btn secondary">Copy all new names</button>
<button id="downloadBtn" class="btn secondary">Download rename script</button>
</div>

<table>
<thead><tr><th>Source filename</th><th>New filename</th><th></th></tr></thead>
<tbody id="resultsBody">
{% for r in initial_results %}
<tr{% if r.error %} class="error"{% endif %}>
<td>{{ r.old }}</td><td>{{ r.new }}</td><td><button class="copy-btn" title="Copy new name">&#128203;</button></td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
<script>
const INITIAL_FILENAMES = {{ initial_filenames_json }};
document.getElementById('filenames').value = INITIAL_FILENAMES.join('\n');

const presets = {
zoom: /^Zoom_Recording_(?<date>\d{4}-\d{2}-\d{2})_(?<time>\d{2}\.\d{2}\.\d{2})_Participant_(?<participant>\d+)\.(?<ext>[^.]+)$/,
riverside: /^Riverside_(?<date>\d{4}-\d{2}-\d{2})_(?<time>\d{2}-\d{2}-\d{2})_(?<guest>\S+)\.(?<ext>[^.]+)$/
};

const els = {
filenames: document.getElementById('filenames'),
source: document.getElementById('sourcePattern'),
customRegex: document.getElementById('customRegex'),
target: document.getElementById('targetPattern'),
episode: document.getElementById('episode'),
guestMapping: document.getElementById('guestMapping'),
tbody: document.getElementById('resultsBody'),
preview: document.getElementById('previewBtn'),
copyAll: document.getElementById('copyAllBtn'),
download: document.getElementById('downloadBtn')
};

function parseDate(str) {
let m = str.match(/^(\d{4})[-.](\d{2})[-.](\d{2})$/);
return m ? {y:m[1], m:m[2], d:m[3]} : null;
}
function parseTime(str) {
let m = str.match(/^(\d{2})[.:](\d{2})[.:](\d{2})$/);
return m ? {h:m[1], min:m[2], s:m[3]} : null;
}
function pad(n){return String(n).padStart(2,'0');}
function formatDate(d, fmt) {
if(!d) return '';
f = fmt || 'YYYY-MM-DD';
return f.replace('YYYY',d.y).replace('YY',d.y.slice(-2)).replace('MM',pad(d.m)).replace('DD',pad(d.d)).replace('M',d.m).replace('D',d.d);
}
function formatTime(t, fmt) {
if(!t) return '';
f = fmt || 'HH.mm.ss';
return f.replace('HH',pad(t.h)).replace('H',t.h).replace('mm',pad(t.min)).replace('m',t.min).replace('ss',pad(t.s)).replace('s',t.s);
}

function getGuestMapping() {
const lines = els.guestMapping.value.split('\n');
const map = {};
lines.forEach(line => {
const [id, ...nameParts] = line.split('=');
const name = nameParts.join('=').trim();
if(id && name) map[id.trim()] = name;
});
return map;
}

function processAll() {
const filenames = els.filenames.value.split('\n').filter(l=>l.trim());
const sourceType = els.source.value;
let regex;
if(sourceType === 'zoom') regex = presets.zoom;
else if(sourceType === 'riverside') regex = presets.riverside;
else {
try{ regex = new RegExp(els.customRegex.value, 'i'); } catch(e){ return []; }
}
const episode = els.episode.value.trim();
const guestMap = getGuestMapping();
const targetPattern = els.target.value;
const results = [];
filenames.forEach(f => {
const match = f.match(regex);
if(!match) { results.push({old:f, new:'[No Match]', error:true}); return; }
const g = match.groups || {};
let guest = g.guest || '';
if(g.participant) guest = guestMap[g.participant] || g.participant;
let dateObj = null, timeObj = null;
if(g.date) dateObj = parseDate(g.date);
if(g.time) timeObj = parseTime(g.time);
let newName = targetPattern;
newName = newName.replace(/\{date(?::([^}]+))?\}/g, (_, fmt) => dateObj ? formatDate(dateObj, fmt) : (g.date||''));
newName = newName.replace(/\{time(?::([^}]+))?\}/g, (_, fmt) => timeObj ? formatTime(timeObj, fmt) : (g.time||''));
newName = newName.replace(/\{participant\}/g, g.participant || '');
newName = newName.replace(/\{guest\}/g, guest);
newName = newName.replace(/\{episode\}/g, episode);
newName = newName.replace(/\{ext\}/g, g.ext || '');
results.push({old:f, new:newName, error:false});
});
return results;
}

function render(results) {
const tbody = els.tbody;
tbody.innerHTML = '';
results.forEach(r => {
const tr = document.createElement('tr');
if(r.error) tr.className = 'error';
tr.innerHTML = `<td>${escapeHtml(r.old)}</td><td>${escapeHtml(r.new)}</td><td><button class="copy-btn" title="Copy new name">&#128203;</button></td>`;
const btn = tr.querySelector('.copy-btn');
btn.addEventListener('click', () => {
navigator.clipboard.writeText(r.new).then(() => {
btn.classList.add('copy-success');
setTimeout(() => btn.classList.remove('copy-success'), 1200);
});
});
tbody.appendChild(tr);
});
}

function escapeHtml(text) {
const d = document.createElement('div');
d.textContent = text;
return d.innerHTML;
}

function update() {
const results = processAll();
render(results);
updateDownloadState(results);
}

function updateDownloadState(results) {
const valid = results.filter(r=>!r.error);
els.copyAll.disabled = valid.length === 0;
els.download.disabled = valid.length === 0;
}

els.preview.addEventListener('click', update);

els.copyAll.addEventListener('click', () => {
const results = processAll();
const names = results.filter(r=>!r.error).map(r=>r.new).join('\n');
navigator.clipboard.writeText(names).then(() => {
els.copyAll.textContent = 'Copied!';
setTimeout(() => { els.copyAll.textContent = 'Copy all new names'; }, 1500);
});
});

els.download.addEventListener('click', () => {
const results = processAll();
const valid = results.filter(r=>!r.error);
const script = '#!/bin/bash\n' + valid.map(r => `mv "${r.old.replace(/"/g,'\\"')}" "${r.new.replace(/"/g,'\\"')}"`).join('\n');
const blob = new Blob([script], {type: 'application/x-sh'});
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'rename_episodes.sh';
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
});

els.source.addEventListener('change', () => {
els.customRegex.style.display = els.source.value === 'custom' ? 'block' : 'none';
update();
});
['input','change'].forEach(ev => {
els.filenames.addEventListener(ev, update);
els.target.addEventListener(ev, update);
els.episode.addEventListener(ev, update);
els.guestMapping.addEventListener(ev, update);
els.customRegex.addEventListener(ev, update);
});

update();
</script>
</body>
</html>''')


def compute_initial_results(filenames, target_pattern, episode, guest_map):
    """Server‑side pre‑computation of the rename table using the Zoom preset."""
    results = []
    for f in filenames:
        m = ZOOM_RE.match(f)
        if not m:
            results.append({"old": f, "new": "[No Match]", "error": True})
            continue
        date_str = m.group("date")
        participant = m.group("participant")
        ext = m.group("ext")
        guest = guest_map.get(participant, participant)
        new_name = target_pattern
        new_name = new_name.replace("{date}", date_str)
        new_name = new_name.replace("{guest}", guest)
        new_name = new_name.replace("{episode}", episode)
        new_name = new_name.replace("{ext}", ext)
        results.append({"old": f, "new": new_name, "error": False})
    return results


def process(text: str) -> str:
    """Interactive batch episode renamer – returns a self‑contained HTML page."""
    if not text.strip():
        return TEMPLATE.render(
            initial_filenames_json='[]',
            default_target_pattern="{date}_{guest}_Episode{episode}.{ext}",
            default_episode="1",
            guest_mapping="",
            initial_results=[]
        )

    filenames = []
    config_tokens = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for token in stripped.split():
            if AUDIO_EXT_RE.search(token):
                filenames.append(token)
            elif ('=' in token and not AUDIO_EXT_RE.search(token)) or \
                 ('{' in token and not AUDIO_EXT_RE.search(token)) or \
                 token.isdigit():
                config_tokens.append(token)

    # Defaults
    episode = "1"
    guest_map = {}
    target_pattern = "{date}_{guest}_Episode{episode}.{ext}"

    for tok in config_tokens:
        if tok.isdigit():
            episode = tok
        elif '=' in tok:
            parts = tok.split('=', 1)
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                if key and val:
                    guest_map[key] = val
        elif '{' in tok:
            target_pattern = tok

    guest_mapping_lines = "\n".join(f"{k}={v}" for k, v in guest_map.items())

    initial_results = compute_initial_results(filenames, target_pattern, episode, guest_map)

    return TEMPLATE.render(
        initial_filenames_json=json.dumps(filenames),
        default_target_pattern=target_pattern,
        default_episode=episode,
        guest_mapping=guest_mapping_lines,
        initial_results=initial_results
    )


_browser_input = globals().get("USER_INPUT", None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    data = sys.stdin.read() if not sys.stdin.isatty() else (
        "Zoom_Recording_2026-08-05_14.30.45_Participant_1234567890.mp3 "
        "Zoom_Recording_2026-08-05_14.32.12_Participant_9876543210.mp3\n"
        "023\n1234567890=Alice\n9876543210=Bob\n"
        "Episode_{episode}_{date}_Guest_{guest}.{ext}"
    )
    print(process(data))