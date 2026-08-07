"""Flyer Mosaic Finder - Interactive HTML page that transforms noisy filenames into an organized visual mosaic."""
from jinja2 import Template

TEMPLATE = Template(r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flyer Mosaic Finder</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 2rem; }
  .app { max-width: 900px; margin: 0 auto; }
  .input-area { margin-bottom: 2rem; }
  textarea { width: 100%; height: 160px; font-size: 1rem; padding: 1rem; border: 2px solid #ccc; border-radius: 8px; resize: vertical; outline: none; }
  textarea:focus { border-color: #6c5ce7; }
  .example { font-size: 0.85rem; color: #888; margin-top: 0.5rem; white-space: pre-line; line-height: 1.5; }
  .project { margin-bottom: 1.5rem; }
  .project-header { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; user-select: none; padding: 0.5rem 0; border-bottom: 2px solid #ddd; }
  .project-header h3 { font-size: 1.2rem; margin: 0; color: #333; }
  .project-header .toggle { font-size: 1.2rem; width: 24px; text-align: center; transition: transform 0.2s; }
  .project-header.collapsed .toggle { transform: rotate(-90deg); }
  .tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.8rem; padding: 0.5rem 0; }
  .project.collapsed .tiles { display: none; }
  .tile { background: #fff; border-radius: 8px; padding: 0.8rem; display: flex; align-items: center; gap: 0.6rem; box-shadow: 0 1px 4px rgba(0,0,0,0.1); transition: box-shadow 0.2s; position: relative; cursor: pointer; }
  .tile:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
  .tile.highlight { box-shadow: 0 0 0 3px #6c5ce7; }
  .color-block { width: 32px; height: 32px; border-radius: 4px; flex-shrink: 0; }
  .tile-label { font-size: 0.9rem; color: #222; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .copy-btn { background: none; border: 1px solid #ccc; border-radius: 4px; font-size: 0.7rem; padding: 2px 6px; cursor: pointer; color: #555; white-space: nowrap; }
  .copy-btn:hover { background: #eee; border-color: #999; }
  .tooltip { display: none; position: absolute; bottom: 110%; left: 10px; background: #333; color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; white-space: nowrap; pointer-events: none; }
  .tile:hover .tooltip { display: block; }
</style>
</head>
<body>
<div class="app">
  <div class="input-area">
    <textarea id="fileInput" placeholder="Paste your file names (one per line)…"></textarea>
    <div class="example">
      Example: Downloads/charity_bake_sale_poster_2026.jpg<br>
      School_Sports_Day_Banner.png<br>
      PTA_Meeting_Flyer.png
    </div>
  </div>
  <div id="mosaicContainer"></div>
</div>
<script>
(function() {
  const textarea = document.getElementById('fileInput');
  const container = document.getElementById('mosaicContainer');
  let updatePending = false;

  textarea.addEventListener('input', scheduleUpdate);
  if (textarea.value.trim()) scheduleUpdate();

  function scheduleUpdate() {
    if (updatePending) return;
    updatePending = true;
    requestAnimationFrame(() => {
      updatePending = false;
      buildMosaic(textarea.value);
    });
  }

  function escapeHTML(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function cleanBasename(raw) {
    const lastSlash = raw.lastIndexOf('/');
    const basename = lastSlash >= 0 ? raw.substring(lastSlash + 1) : raw;
    const lastDot = basename.lastIndexOf('.');
    const name = lastDot >= 0 ? basename.substring(0, lastDot) : basename;
    const ext = lastDot >= 0 ? basename.substring(lastDot) : '';
    let cleaned = name;
    // normalize separators to spaces
    cleaned = cleaned.replace(/[_\-]+/g, ' ');
    // remove noise tokens
    const patterns = [
      /\bfinal\b/gi,
      /\bdraft\b/gi,
      /\bv\d+\b/gi,
      /_\d{2,4}-\d{2}-\d{2}/g
    ];
    patterns.forEach(p => { cleaned = cleaned.replace(p, ''); });
    // collapse spaces and trim
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    return cleaned + ext;
  }

  function getWords(name) {
    const idx = name.lastIndexOf('.');
    const base = idx >= 0 ? name.substring(0, idx) : name;
    return base.toLowerCase().split(/\s+/).filter(w => w);
  }

  function jaccard(setA, setB) {
    const intersection = new Set([...setA].filter(x => setB.has(x)));
    const union = new Set([...setA, ...setB]);
    if (union.size === 0) return 1;
    return intersection.size / union.size;
  }

  function extractVersion(basename) {
    const m = basename.match(/\bv(\d+)\b/i);
    return m ? parseInt(m[1], 10) : 0;
  }

  function buildMosaic(text) {
    container.innerHTML = '';
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    if (!lines.length) {
      container.innerHTML = '<p style="color:#999;text-align:center;padding:2rem;">Your mosaic will appear here</p>';
      return;
    }

    const files = lines.map(line => {
      const lastSlash = line.lastIndexOf('/');
      const original = lastSlash >= 0 ? line.substring(lastSlash + 1) : line;
      const cleaned = cleanBasename(line);
      const words = getWords(cleaned);
      const version = extractVersion(original);
      return { original, cleaned, words: new Set(words), version };
    });

    // Group by word-set similarity (threshold 0.5)
    const groups = [];
    for (const file of files) {
      let assigned = false;
      for (const group of groups) {
        for (const member of group) {
          if (jaccard(file.words, member.words) >= 0.5) {
            group.push(file);
            assigned = true;
            break;
          }
        }
        if (assigned) break;
      }
      if (!assigned) groups.push([file]);
    }

    // For each group, compute project name = longest common word prefix
    groups.forEach(group => {
      let prefixWords = [];
      if (group.length) {
        const wordArrs = group.map(f => getWords(f.cleaned));
        const minLen = Math.min(...wordArrs.map(w => w.length));
        for (let i = 0; i < minLen; i++) {
          const w = wordArrs[0][i];
          if (wordArrs.every(arr => arr[i] === w)) {
            prefixWords.push(w);
          } else {
            break;
          }
        }
      }
      group._projectName = prefixWords.length ?
        prefixWords.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') :
        group[0].cleaned;
      // hue from project name
      const sum = [...group._projectName].reduce((s, ch) => s + ch.charCodeAt(0), 0);
      group._hue = sum % 360;
    });

    // Sort groups by project name
    groups.sort((a, b) => a._projectName.localeCompare(b._projectName));

    // Sort each group's files by version, then cleaned name
    groups.forEach(group => {
      group.sort((a, b) => {
        if (a.version !== b.version) return a.version - b.version;
        return a.cleaned.localeCompare(b.cleaned);
      });
    });

    // Render
    groups.forEach(group => {
      const projectDiv = document.createElement('div');
      projectDiv.className = 'project';
      const header = document.createElement('div');
      header.className = 'project-header';
      header.innerHTML = '<span class="toggle">\u25B6</span><h3>' + escapeHTML(group._projectName) + '</h3>';
      const tilesDiv = document.createElement('div');
      tilesDiv.className = 'tiles';

      header.addEventListener('click', () => {
        projectDiv.classList.toggle('collapsed');
        header.classList.toggle('collapsed');
      });

      group.forEach(file => {
        const tile = document.createElement('div');
        tile.className = 'tile';
        const colorBlock = document.createElement('div');
        colorBlock.className = 'color-block';
        colorBlock.style.backgroundColor = 'hsl(' + group._hue + ', 60%, 80%)';
        const label = document.createElement('span');
        label.className = 'tile-label';
        label.textContent = file.cleaned;
        const tooltip = document.createElement('span');
        tooltip.className = 'tooltip';
        tooltip.textContent = file.original;
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy original';

        tile.appendChild(colorBlock);
        tile.appendChild(label);
        tile.appendChild(tooltip);
        tile.appendChild(copyBtn);
        tilesDiv.appendChild(tile);

        tile.addEventListener('click', (e) => {
          if (e.target === copyBtn) return;
          navigator.clipboard.writeText(file.cleaned).then(() => {
            tile.classList.add('highlight');
            setTimeout(() => tile.classList.remove('highlight'), 800);
          });
        });

        copyBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(file.original);
        });
      });

      projectDiv.appendChild(header);
      projectDiv.appendChild(tilesDiv);
      container.appendChild(projectDiv);
    });
  }
})();
</script>
</body>
</html>''')

def process(text: str) -> str:
    """Return an interactive HTML page that organizes file names into a visual mosaic."""
    return TEMPLATE.render()

import sys
def _cli_main() -> None:
    text = sys.stdin.read()
    print(process(text))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()