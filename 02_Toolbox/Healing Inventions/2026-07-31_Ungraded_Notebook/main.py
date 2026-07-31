"""
requirements:
  - jinja2 (built-in)
  - browser with localStorage, Blob, URL.createObjectURL
  - input: freeform text string (1-500 words), output: full HTML page
  - behavior: interactive notebook, saves entries to localStorage, exports .md
  - algorithmic depth: timestamp on save, markdown export with YAML front-matter
"""

from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ungraded Notebook</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#fefaf3;font-family:Georgia,serif;display:flex;justify-content:center;align-items:center;min-height:100vh;flex-direction:column;}
.container{max-width:640px;width:100%;padding:2rem;}
.notebook{position:relative;}
textarea{width:100%;min-height:200px;padding:2rem;font-family:Georgia,serif;font-size:1.4rem;line-height:1.5;border:none;outline:none;resize:none;background:rgba(255,255,255,0.6);box-shadow:0 2px 12px rgba(0,0,0,0.08);border-radius:4px;transition:box-shadow 0.5s;}
textarea:focus{box-shadow:0 0 20px 5px rgba(210,180,140,0.5);}
textarea::placeholder{color:#b8a99c;}
#logBtn{position:absolute;right:1rem;bottom:1rem;background:#c8a882;border:none;color:#fff;padding:0.4rem 1.2rem;font-size:0.9rem;border-radius:20px;cursor:pointer;transition:opacity 0.3s;display:none;}
#logBtn.show{display:block;}
.checkmark{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) scale(0);font-size:2.5rem;color:#6e8b5e;opacity:0;transition:all 0.4s ease;pointer-events:none;}
.checkmark.flash{opacity:1;transform:translate(-50%,-50%) scale(1);}
.counter{text-align:center;margin-top:1rem;color:#a08c7a;font-size:0.9rem;display:none;}
#seeAllLink{display:none;font-size:0.85rem;text-align:center;margin-top:1rem;color:#b0967c;cursor:pointer;text-decoration:underline;}
#entriesContainer{display:none;margin-top:2rem;border-top:1px solid #e8d9c8;padding-top:1.5rem;}
#exportBtn{background:#c8a882;border:none;color:#fff;padding:0.5rem 1.5rem;font-size:0.9rem;border-radius:20px;cursor:pointer;margin-bottom:1rem;}
.entry-card{background:rgba(255,255,255,0.7);padding:1rem;margin-bottom:0.8rem;box-shadow:0 1px 6px rgba(0,0,0,0.05);border-radius:3px;font-size:0.95rem;transform:rotate(0.5deg);transition:transform 0.2s;}
.entry-card:nth-child(even){transform:rotate(-0.5deg);}
.entry-card:hover{transform:rotate(0);}
.entry-date{font-weight:bold;color:#7b6b5a;margin-bottom:0.4rem;font-size:0.85rem;}
.entry-text{color:#4a3b32;white-space:pre-wrap;overflow:hidden;text-overflow:ellipsis;}
.title{position:fixed;bottom:1.5rem;right:2rem;font-size:0.65rem;color:#cbbeb0;opacity:0.7;}
</style>
</head>
<body>
<div class="container">
  <div class="notebook">
    <textarea id="entry" placeholder="Today, …">{{ initial_text }}</textarea>
    <button id="logBtn">Log</button>
    <div class="checkmark" id="checkmark">&#10003;</div>
    <div class="counter" id="counter">0 moments saved</div>
    <a href="#" id="seeAllLink">see all</a>
  </div>
  <div id="entriesContainer">
    <button id="exportBtn">Export as Markdown</button>
    <div id="entriesList"></div>
  </div>
</div>
<div class="title">Ungraded Notebook</div>
<script>
(function() {
  const STORAGE_KEY = 'ungraded_notebook_entries';
  const entryArea = document.getElementById('entry');
  const logBtn = document.getElementById('logBtn');
  const checkmark = document.getElementById('checkmark');
  const counterDiv = document.getElementById('counter');
  const seeAllLink = document.getElementById('seeAllLink');
  const entriesContainer = document.getElementById('entriesContainer');
  const entriesListDiv = document.getElementById('entriesList');
  const exportBtn = document.getElementById('exportBtn');

  let entries = [];

  function loadEntries() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      entries = raw ? JSON.parse(raw) : [];
    } catch(e) {
      entries = [];
    }
  }

  function saveEntries() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  function updateUI() {
    const count = entries.length;
    if (count > 0) {
      counterDiv.style.display = 'block';
      counterDiv.textContent = count + ' moment' + (count === 1 ? '' : 's') + ' saved';
      seeAllLink.style.display = 'block';
    } else {
      counterDiv.style.display = 'none';
      seeAllLink.style.display = 'none';
      entriesContainer.style.display = 'none';
    }

    if (entryArea.value.trim().length > 0) {
      logBtn.classList.add('show');
    } else {
      logBtn.classList.remove('show');
    }
  }

  function logEntry() {
    const text = entryArea.value.trim();
    if (!text) return;
    const now = new Date();
    const timestamp = now.toISOString();
    const newEntry = { timestamp, text };
    entries.push(newEntry);
    saveEntries();

    // clear & animate
    entryArea.value = '';
    // flash checkmark
    checkmark.classList.add('flash');
    setTimeout(() => checkmark.classList.remove('flash'), 1500);

    updateUI();
    if (entriesContainer.style.display === 'block') {
      renderEntriesList();
    }
  }

  function renderEntriesList() {
    if (entries.length === 0) return;
    // reverse chronological (latest first)
    const sorted = [...entries].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    let html = '';
    sorted.forEach(function(entry) {
      const dateStr = entry.timestamp.split('T')[0] + ' ' + entry.timestamp.split('T')[1].substring(0,5);
      const truncated = entry.text.length > 80 ? entry.text.substring(0,80) + '...' : entry.text;
      html += '<div class="entry-card">' +
              '<div class="entry-date">' + dateStr + '</div>' +
              '<div class="entry-text">' + truncated + '</div>' +
              '</div>';
    });
    entriesListDiv.innerHTML = html;
  }

  function exportMarkdown() {
    if (entries.length === 0) return;
    const sorted = [...entries].sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    const firstDate = sorted[sorted.length-1].timestamp;
    const lastDate = sorted[0].timestamp;
    const frontmatter = '---\ntotal: ' + entries.length + '\nfirst_date: "' + firstDate + '"\nlast_date: "' + lastDate + '"\n---\n\n';
    let md = frontmatter;
    sorted.forEach(function(entry) {
      md += '## ' + entry.timestamp + '\n' + entry.text + '\n\n';
    });
    const blob = new Blob([md], {type: 'text/markdown'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ungraded-notebook-' + new Date().toISOString().slice(0,10) + '.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function toggleEntries() {
    if (entriesContainer.style.display === 'block') {
      entriesContainer.style.display = 'none';
      seeAllLink.textContent = 'see all';
    } else {
      entriesContainer.style.display = 'block';
      seeAllLink.textContent = 'hide all';
      renderEntriesList();
    }
  }

  // Event listeners
  entryArea.addEventListener('input', function() {
    updateUI();
  });

  entryArea.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      logEntry();
    }
  });

  logBtn.addEventListener('click', function(e) {
    e.preventDefault();
    logEntry();
  });

  seeAllLink.addEventListener('click', function(e) {
    e.preventDefault();
    toggleEntries();
  });

  exportBtn.addEventListener('click', function(e) {
    e.preventDefault();
    exportMarkdown();
  });

  // initial load
  loadEntries();
  updateUI();
  // if initial text present, log button shows
  if (entryArea.value.trim().length > 0) {
    logBtn.classList.add('show');
  }

  // auto-resize textarea
  function autoResize() {
    entryArea.style.height = 'auto';
    entryArea.style.height = entryArea.scrollHeight + 'px';
  }
  entryArea.addEventListener('input', autoResize);
  autoResize();

})();
</script>
</body>
</html>''')


def process(text: str) -> str:
    """Return an interactive ungraded notebook HTML page for the given moment."""
    initial_text = text.strip()
    html = TEMPLATE.render(initial_text=initial_text)
    return html


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()