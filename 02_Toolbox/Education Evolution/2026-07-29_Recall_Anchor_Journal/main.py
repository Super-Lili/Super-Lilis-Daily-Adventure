#!/usr/bin/env python3
"""Recall Anchor Journal – interactive spaced-repetition schedule from unprompted recalls."""
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Recall Anchor Journal</title>
<style>
body{font-family:Arial,sans-serif;max-width:800px;margin:20px auto;padding:0 10px}
.pop{background:#f0f0f0;padding:10px;margin:10px 0;border-radius:5px}
.label{font-weight:bold}
.btn{padding:10px 20px;background:#4CAF50;color:white;border:none;cursor:pointer;border-radius:4px}
.btn:hover{background:#45a049}
.concept-item{background:#e9f7ef;border-left:4px solid #4CAF50;padding:10px;margin:10px 0}
.timeline{display:flex;gap:4px;align-items:center;margin-top:5px}
.tl-bar{width:18px;height:14px;border-radius:2px;background:#ddd;border:1px solid #999}
.tl-bar.recall{background:#2196F3;border-color:#1565C0}
.tl-bar.today{border:3px solid #ff9800;box-shadow:0 0 4px #ff9800}
.queue-item{background:#fff3e0;border-left:4px solid #ff9800;padding:10px;margin:5px 0}
.modal{display:none;position:fixed;z-index:1000;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,0.5)}
.modal-content{background:#fff;margin:15% auto;padding:20px;width:300px;border-radius:8px;text-align:center}
.close{float:right;font-size:24px;cursor:pointer}
</style>
</head>
<body>
<h2>Recall Anchor Journal</h2>
<div class="pop">
<label class="label">Enter concept you just recalled without prompting:</label>
<input type="text" id="conceptInput" style="padding:8px;width:60%;">
<button class="btn" id="logBtn">Log Recall</button>
</div>
<div>Total recalls: <span id="totalRecalls">0</span> | Distinct concepts: <span id="distinctCount">0</span></div>
<div id="todayQueue"><p id="queueMsg">No concepts due. Log your first recall!</p></div>
<div id="conceptsList"></div>
<div id="reviewModal" class="modal">
<div class="modal-content">
<span class="close">&times;</span>
<h3 id="modalConcept"></h3>
</div>
</div>
<script>
var STORAGE_KEY = 'recallEvents';
function loadEvents() {
  var raw = localStorage.getItem(STORAGE_KEY);
  if (raw) { try { return JSON.parse(raw); } catch(e) {} }
  return [];
}
function saveEvents(e) { localStorage.setItem(STORAGE_KEY, JSON.stringify(e)); }
function logRecall() {
  var inp = document.getElementById('conceptInput');
  var c = inp.value.trim();
  if (!c) return;
  var events = loadEvents();
  var now = new Date().toISOString();
  events.push([c, now]);
  saveEvents(events);
  inp.value = '';
  updateUI();
}
function getTodayStart() {
  var d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}
function dateStr(iso) { return iso.substring(0, 10); }
function computeInterval(count) {
  var raw = Math.pow(2, count - 1);
  if (raw > 30) raw = 30;
  return raw;
}
function buildData() {
  var events = loadEvents();
  var groups = {};
  for (var i = 0; i < events.length; i++) {
    var e = events[i];
    var concept = e[0];
    var iso = e[1];
    if (!groups[concept]) groups[concept] = [];
    groups[concept].push(iso);
  }
  var today = getTodayStart();
  var todayStr = today.toISOString().substring(0, 10);
  var days = [];
  for (var d = 6; d >= 0; d--) {
    var day = new Date(today);
    day.setDate(day.getDate() - d);
    days.push(day.toISOString().substring(0, 10));
  }
  var conceptsData = [];
  for (var c in groups) {
    if (!groups.hasOwnProperty(c)) continue;
    var stamps = groups[c].sort();
    var count = stamps.length;
    var lastIso = stamps[stamps.length - 1];
    var interval = computeInterval(count);
    var lastDate = new Date(lastIso);
    var nextReview = new Date(lastDate);
    nextReview.setDate(nextReview.getDate() + interval);
    nextReview.setHours(0, 0, 0, 0);
    var due = nextReview.getTime() <= today.getTime();
    var timeline = [];
    for (var t = 0; t < days.length; t++) {
      var dayKey = days[t];
      var hasEv = false;
      for (var s = 0; s < stamps.length; s++) {
        if (dateStr(stamps[s]) === dayKey) { hasEv = true; break; }
      }
      timeline.push(hasEv ? 1 : 0);
    }
    conceptsData.push([c, count, lastIso, nextReview.toISOString().substring(0, 10), due, timeline, interval]);
  }
  var totalRecalls = events.length;
  var distinct = Object.keys(groups).length;
  var queue = [];
  for (var i = 0; i < conceptsData.length; i++) {
    if (conceptsData[i][4]) queue.push(conceptsData[i]);
  }
  queue.sort(function(a, b) {
    if (a[3] < b[3]) return -1;
    if (a[3] > b[3]) return 1;
    return 0;
  });
  return {
    totalRecalls: totalRecalls,
    distinct: distinct,
    days: days,
    todayStr: todayStr,
    conceptsData: conceptsData,
    queue: queue
  };
}
function updateUI() {
  var data = buildData();
  document.getElementById('totalRecalls').textContent = data.totalRecalls;
  document.getElementById('distinctCount').textContent = data.distinct;
  var qDiv = document.getElementById('todayQueue');
  var msg = document.getElementById('queueMsg');
  var html = '';
  if (data.queue.length === 0) {
    msg.style.display = 'block';
    qDiv.innerHTML = msg.outerHTML;
  } else {
    msg.style.display = 'none';
    html += '<h3>Today\'s Queue</h3>';
    for (var i = 0; i < data.queue.length; i++) {
      var q = data.queue[i];
      html += '<div class="queue-item"><strong>' + q[0] + '</strong> - due: ' + q[3];
      html += ' <button class="btn" onclick="reviewNow(\'' + q[0] + '\')">Review Now</button></div>';
    }
    qDiv.innerHTML = html;
  }
  var listDiv = document.getElementById('conceptsList');
  var listHtml = '<h3>All Concepts</h3>';
  for (var i = 0; i < data.conceptsData.length; i++) {
    var cd = data.conceptsData[i];
    var name = cd[0], count = cd[1], last = cd[2], next = cd[3], due = cd[4], timeline = cd[5], iv = cd[6];
    listHtml += '<div class="concept-item"><span style="color:green;font-size:24px;">&#10003;</span>';
    listHtml += ' <strong>' + name + '</strong> - last recall: ' + last;
    listHtml += '<br> Count: ' + count + ' | Next review: ' + next + ' (interval: ' + iv + ' days)';
    listHtml += '<div class="timeline">';
    for (var d = 0; d < timeline.length; d++) {
      var cls = 'tl-bar';
      if (timeline[d] === 1) cls += ' recall';
      if (data.days[d] === data.todayStr) cls += ' today';
      listHtml += '<div class="' + cls + '"></div>';
    }
    listHtml += '</div>';
    if (due) {
      listHtml += ' <button class="btn" onclick="reviewNow(\'' + name + '\')" style="margin-top:5px;">Review Now</button>';
    }
    listHtml += '</div>';
  }
  listDiv.innerHTML = listHtml;
}
function reviewNow(concept) {
  document.getElementById('modalConcept').textContent = concept;
  document.getElementById('reviewModal').style.display = 'block';
}
window.onload = function() {
  updateUI();
  document.getElementById('logBtn').addEventListener('click', logRecall);
  var closeBtn = document.querySelector('#reviewModal .close');
  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      document.getElementById('reviewModal').style.display = 'none';
    });
  }
  window.addEventListener('click', function(event) {
    if (event.target === document.getElementById('reviewModal')) {
      document.getElementById('reviewModal').style.display = 'none';
    }
  });
};
</script>
</body>
</html>''')


def process(text: str) -> str:
    """Return the interactive recall journal HTML page. Input text is ignored but accepted for API compatibility."""
    return TEMPLATE.render()


def _cli_main():
    print(process(""))


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()