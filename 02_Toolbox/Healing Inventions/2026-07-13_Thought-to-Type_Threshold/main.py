#!/usr/bin/env python3
"""
Thought-to-Type Threshold – Interactive HTML tool.
Real-time typing interface with configurable delay per character.
Author: spec-driven
Date: 2026-07-13
"""

from jinja2 import Template

# ------------------------------------------------------------------
# MANDATORY REQUIREMENTS (keep at top)
# - [x] 220+ lines (including template string)
# - [x] Every step of Algorithmic depth implemented literally
# - [x] No hardcoded lookup tables; compute from input
# - [x] No invented entries, graceful degradation
# - [x] Mode 3: return full HTML via Jinja2 raw template
# ------------------------------------------------------------------

_TEMPLATE_STRING = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Thought → Type Threshold</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:monospace;background:#f5f5f5;}
.container{width:90vw;max-width:720px;text-align:center;}
h1{margin-bottom:20px;color:#333;font-size:1.6rem;}
.controls{display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:15px;}
.controls label{font-size:0.95rem;}
#typing-area{border:2px solid #aaa;border-radius:4px;min-height:150px;padding:15px;background:#fff;text-align:left;position:relative;overflow:hidden;outline:none;font-size:1.1rem;line-height:1.7;white-space:pre-wrap;word-wrap:break-word;}
#typing-area:focus{border-color:#4a90d9;box-shadow:0 0 0 3px rgba(74,144,217,0.2);}
.placeholder{color:#aaa;position:absolute;left:15px;top:15px;}
.char.black{color:#000;}
.char.grey{color:#ccc;}
.caret{display:inline-block;width:2px;height:1.2em;background:#333;vertical-align:text-bottom;animation:blink 1s step-end infinite;}
@keyframes blink{ 0%,100%{opacity:1} 50%{opacity:0} }
.info{display:flex;justify-content:space-between;align-items:center;margin-top:10px;}
#pending-count{font-size:0.9rem;color:#666;}
.actions button{padding:6px 16px;margin-left:8px;border:none;border-radius:4px;cursor:pointer;font-size:0.9rem;}
#copy-btn{background:#4caf50;color:#fff;opacity:0.6;transition:opacity 0.2s;}
#copy-btn:enabled{opacity:1;}
#clear-btn{background:#e0e0e0;color:#333;}
#delay-value{font-weight:bold;min-width:45px;display:inline-block;text-align:right;}
</style>
</head>
<body>
<div class="container">
<h1>Thought → Type Threshold</h1>
<div class="controls">
<label for="delay-slider">Delay (ms):</label>
<input type="range" id="delay-slider" min="300" max="800" value="500" step="5">
<span id="delay-value">500</span>
</div>
<div id="typing-area" tabindex="0">
<span id="placeholder-text" class="placeholder">Start typing&#8230;</span>
<span id="text-content"></span>
<span id="cursor" class="caret"></span>
</div>
<div class="info">
<span id="pending-count">Pending: 0</span>
<div class="actions">
<button id="copy-btn" disabled>Copy</button>
<button id="clear-btn">Clear</button>
</div>
</div>
</div>
<script>
(function() {
    var initialText = {{ text|tojson }};
    var visibleText = [];
    var pendingQueue = [];
    var delayMs = 500;
    var intervalId = null;

    var slider = document.getElementById('delay-slider');
    var delayValue = document.getElementById('delay-value');
    var typingArea = document.getElementById('typing-area');
    var placeholder = document.getElementById('placeholder-text');
    var textContent = document.getElementById('text-content');
    var cursor = document.getElementById('cursor');
    var pendingCount = document.getElementById('pending-count');
    var copyBtn = document.getElementById('copy-btn');
    var clearBtn = document.getElementById('clear-btn');

    function escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function updateDisplay() {
        var totalChars = visibleText.length + pendingQueue.length;
        // Build visible and pending characters
        var parts = [];
        for (var i = 0; i < visibleText.length; i++) {
            parts.push('<span class="char black">' + escapeHtml(visibleText[i]) + '</span>');
        }
        for (var j = 0; j < pendingQueue.length; j++) {
            parts.push('<span class="char grey">' + escapeHtml(pendingQueue[j].char) + '</span>');
        }
        textContent.innerHTML = parts.join('');
        // Placeholder visibility
        if (totalChars === 0) {
            placeholder.style.display = '';
            cursor.style.display = '';
            // Ensure cursor position after placeholder
            textContent.innerHTML = '';
            // Move cursor after placeholder visually: we have placeholder then cursor span, they are siblings. Works.
        } else {
            placeholder.style.display = 'none';
            cursor.style.display = ''; // always show cursor after textContent
        }
        // Update pending count
        pendingCount.textContent = 'Pending: ' + pendingQueue.length;
        // Enable/disable copy button
        if (pendingQueue.length === 0 && visibleText.length > 0) {
            copyBtn.disabled = false;
        } else {
            copyBtn.disabled = true;
        }
    }

    function processQueue() {
        var now = Date.now();
        var somethingChanged = false;
        while (pendingQueue.length > 0 && (now - pendingQueue[0].timestamp) >= delayMs) {
            var item = pendingQueue.shift();
            visibleText.push(item.char);
            somethingChanged = true;
        }
        if (somethingChanged) {
            updateDisplay();
        }
        if (pendingQueue.length === 0 && intervalId !== null) {
            clearInterval(intervalId);
            intervalId = null;
            updateDisplay();
        }
    }

    function startIntervalIfNeeded() {
        if (intervalId === null) {
            intervalId = setInterval(processQueue, 50);
        }
    }

    // Initialize with given text (if any) – push characters as already visible, no pending
    if (initialText.trim()) {
        visibleText = initialText.split('');
        updateDisplay();
    } else {
        updateDisplay();
    }

    // Slider event
    slider.addEventListener('input', function() {
        delayMs = parseInt(slider.value, 10);
        delayValue.textContent = delayMs;
        // Immediately reprocess: characters still pending will be checked against new delay in the next tick
    });

    // Keydown handler
    typingArea.addEventListener('keydown', function(e) {
        e.preventDefault();
        var key = e.key;
        if (key === 'Backspace') {
            if (pendingQueue.length > 0) {
                pendingQueue.pop();
                updateDisplay();
            } else if (visibleText.length > 0) {
                visibleText.pop();
                updateDisplay();
            }
            // no interval needed for backspace
            return;
        }
        if (key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey) {
            // ignore non-printable
            return;
        }
        // Printable character
        pendingQueue.push({
            char: key,
            timestamp: Date.now()
        });
        updateDisplay();
        startIntervalIfNeeded();
    });

    // Copy button
    copyBtn.addEventListener('click', function() {
        var textToCopy = visibleText.join('');
        navigator.clipboard.writeText(textToCopy).then(function() {
            // optional feedback
        }).catch(function() {
            // fallback if clipboard API fails
        });
    });

    // Clear button
    clearBtn.addEventListener('click', function() {
        visibleText = [];
        pendingQueue = [];
        if (intervalId !== null) {
            clearInterval(intervalId);
            intervalId = null;
        }
        updateDisplay();
    });

    // Focus on typing area on page load
    typingArea.focus();
})();
</script>
</body>
</html>
'''

TEMPLATE = Template(_TEMPLATE_STRING)

def process(text: str) -> str:
    """Return an interactive HTML page implementing the Thought-to-Type Threshold tool.

    The input text (if any) is preloaded as visible text.
    """
    if not text or not text.strip():
        text = ""
    return TEMPLATE.render(text=text)

def _cli_main():
    # For manual CLI testing – prints the HTML for an empty initial text
    print(process(""))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()