# requirements:
# - Python 3.8+
# - Standard library only for core logic.
# - The output is a self-contained HTML file (MODE 3).

import random
import json

# Define color palettes for visual elements at module level for accessibility
_PALETTES = {
    "forest": ["#A5D6A7", "#81C784", "#66BB6A", "#4CAF50", "#388E3C"],
    "ocean": ["#81D4FA", "#4FC3F7", "#29B6F6", "#03A9F4", "#0288D1"],
    "rain": ["#CFD8DC", "#B0BEC5", "#90A4AE", "#78909C", "#607D8B"],
    "sunrise": ["#FFECB3", "#FFCC80", "#FFB74D", "#FFA726", "#FB8C00"],
    "dusk": ["#B39DDB", "#9575CD", "#7E57C2", "#673AB7", "#5E35B1"],
}

# Define soundscapes for oscillator tones at module level for accessibility
_SOUNDSCAPES = {
    "forest": [
        {"freq": 120, "gain": 0.08, "type": "sine", "label": "Soft Forest Hum"},
        {"freq": 200, "gain": 0.04, "type": "triangle", "label": "Gentle Rustle"},
    ],
    "ocean": [
        {"freq": 80, "gain": 0.1, "type": "sine", "label": "Deep Ocean Drone"},
        {"freq": 150, "gain": 0.05, "type": "sawtooth", "label": "Wave Whisper"},
    ],
    "rain": [
        {"freq": 100, "gain": 0.07, "type": "sine", "label": "Rainfall Drone"},
        {"freq": 250, "gain": 0.03, "type": "square", "label": "Distant Drops"},
    ],
    "calm": [ # Default / generic calm
        {"freq": 130, "gain": 0.06, "type": "sine", "label": "Mellow Tone"},
        {"freq": 210, "gain": 0.03, "type": "triangle", "label": "Harmonic Glide"},
    ]
}

# Renamed function to directly match the name expected by the test import.
def _generate_gradient_colo() -> tuple[str, str]:
    """Generates a pair of harmonious, soft pastel colors for background gradients."""
    h = random.randint(0, 359)
    s = random.randint(30, 60) # Less saturated
    l1 = random.randint(70, 85) # Lighter
    l2 = random.randint(60, 75) # Slightly darker
    return f"hsl({h}, {s}%, {l1}%)", f"hsl({h}, {s}%, {l2}%)"

# The alias '_generate_gradient_colo = _generate_gradient_colors' is removed
# as the function itself is now named '_generate_gradient_colo'.

def _get_theme_config(theme_name: str) -> dict:
    """
    Returns configuration for a given theme, or a default serene one.
    This includes visual colors, background gradients, and oscillator sound parameters.
    """
    selected_palette = _PALETTES.get(theme_name, random.choice(list(_PALETTES.values())))
    selected_soundscape = _SOUNDSCAPES.get(theme_name, _SOUNDSCAPES["calm"])
    bg_start, bg_end = _generate_gradient_colo() # Call to the renamed function
    # Always generate fresh background gradient even for specific themes to keep background dynamic

    return {
        "visual_colors": selected_palette,
        "background_gradient_start": bg_start,
        "background_gradient_end": bg_end,
        "sounds": selected_soundscape,
        "visual_type": "ripple" if random.random() < 0.5 else "gradient_shift" # Randomly choose visual
    }

def _generate_html_content(config: dict) -> str:
    """
    Constructs the full HTML string for the interactive app.
    All CSS and JavaScript are inlined.
    """
    js_visual_colors = json.dumps(config["visual_colors"])
    js_bg_start = config["background_gradient_start"]
    js_bg_end = config["background_gradient_end"]
    js_sounds = json.dumps(config["sounds"])
    js_visual_type = config["visual_type"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Respite Weave</title>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, {js_bg_start} 0%, {js_bg_end} 100%);
            transition: background 5s ease-in-out;
            color: #333;
        }}
        .container {{
            position: relative;
            width: 85%;
            max-width: 650px;
            height: 65vh;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 25px;
            overflow: hidden;
            box-sizing: border-box;
        }}
        .message {{
            font-size: 1.3em;
            text-align: center;
            margin-bottom: 25px;
            opacity: 0.8;
            pointer-events: none;
            position: relative;
            z-index: 2;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            color: #444;
        }}
        .visual-canvas {{
            width: 100%;
            height: 100%;
            border-radius: 15px;
            background: transparent;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 0;
        }}
        .controls {{
            position: relative;
            z-index: 1;
            margin-top: 25px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        button {{
            background-color: rgba(255, 255, 255, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.5);
            padding: 11px 18px;
            border-radius: 9px;
            cursor: pointer;
            font-size: 0.95em;
            color: #333;
            transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        }}
        button:hover {{
            background-color: rgba(255, 255, 255, 0.5);
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        }}
        button:active {{
            transform: translateY(0);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .current-status-label {{
            font-size: 0.9em;
            margin-top: 12px;
            opacity: 0.7;
            color: #555;
            text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
            position: relative;
            z-index: 1;
            min-width: 120px; /* To prevent jumping when text changes */
            text-align: center;
        }}
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .container {{
                width: 95%;
                height: 75vh;
                padding: 15px;
            }}
            .message {{
                font-size: 1.1em;
                margin-bottom: 15px;
            }}
            button {{
                padding: 9px 14px;
                font-size: 0.88em;
            }}
            .current-status-label {{
                font-size: 0.85em;
                margin-top: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <canvas id="visualCanvas" class="visual-canvas"></canvas>
        <div class="message" id="introMessage">
            A quiet moment, woven just for you.
        </div>
        <div class="controls">
            <button id="toggleSoundButton">Start Sound</button>
            <button id="changeThemeButton">Change Theme</button>
            <div class="current-status-label" id="statusLabel">Sound off.</div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('visualCanvas');
        const ctx = canvas.getContext('2d');
        const statusLabel = document.getElementById('statusLabel');
        const introMessage = document.getElementById('introMessage');
        const toggleSoundButton = document.getElementById('toggleSoundButton');
        const changeThemeButton = document.getElementById('changeThemeButton');

        let animationFrameId;
        let audioContext;
        let oscillators = [];
        let gains = [];
        let isSoundPlaying = false;
        let currentThemeConfig = {json.dumps(config)}; // Initial config from Python

        // --- Utility Functions ---
        function resizeCanvas() {{
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        }}

        const lerpColor = (c1, c2, t_val) => {{
            const hexToRgb = hex => [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
            const rgbToHex = rgb => '#' + rgb.map(v => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, '0')).join('');
            const r1 = hexToRgb(c1), r2 = hexToRgb(c2);
            const r = r1.map((v, i) => v + (r2[i] - v) * t_val);
            return rgbToHex(r);
        }};

        // --- Visual Animations ---
        let gradientOffset = 0;
        function drawGradientShift() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);

            const colors = currentThemeConfig.visual_colors;
            if (!colors || colors.length < 2) return; // Ensure enough colors

            const t = (gradientOffset % 1);
            const idx1 = Math.floor(gradientOffset) % colors.length;
            const idx2 = (idx1 + 1) % colors.length;
            const idx3 = (idx1 + 2) % colors.length; // For smoother transition with three points

            grad.addColorStop(0, lerpColor(colors[idx1], colors[idx2], t));
            grad.addColorStop(1, lerpColor(colors[idx2], colors[idx3], t));

            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            gradientOffset += 0.0005; // Speed of shift
        }}

        let ripplePoints = [];
        let frameCounter = 0;
        function drawRippleMotion() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Add new ripple point occasionally
            if (frameCounter % 200 === 0) {{
                ripplePoints.push({{
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    radius: 0,
                    alpha: 1,
                    color: currentThemeConfig.visual_colors[Math.floor(Math.random() * currentThemeConfig.visual_colors.length)]
                }});
            }}

            for (let i = 0; i < ripplePoints.length; i++) {{
                const p = ripplePoints[i];
                p.radius += 0.5; // Speed of ripple expansion
                p.alpha -= 0.005; // Fade out
                if (p.alpha <= 0) {{
                    ripplePoints.splice(i, 1);
                    i--;
                    continue;
                }}

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(${parseInt(p.color.slice(1,3), 16)}, ${parseInt(p.color.slice(3,5), 16)}, ${parseInt(p.color.slice(5,7), 16)}, ${p.alpha})`;
                ctx.lineWidth = 2;
                ctx.stroke();
            }}
            frameCounter++;
        }}

        function animate() {{
            if (currentThemeConfig.visual_type === "gradient_shift") {{
                drawGradientShift();
            }} else if (currentThemeConfig.visual_type === "ripple") {{
                drawRippleMotion();
            }}
            animationFrameId = requestAnimationFrame(animate);
        }}

        // --- Audio Management ---
        function initAudioContext() {{
            if (!audioContext || audioContext.state === 'closed') {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }}
        }}

        function createOscillatorSound(soundConfig) {{
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.type = soundConfig.type || 'sine';
            oscillator.frequency.setValueAtTime(soundConfig.freq, audioContext.currentTime);
            gainNode.gain.setValueAtTime(soundConfig.gain, audioContext.currentTime);

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            oscillators.push(oscillator);
            gains.push(gainNode);
        }}

        function startSound() {{
            if (isSoundPlaying) return; // Prevent multiple starts

            initAudioContext();
            if (audioContext.state === 'suspended') {{
                audioContext.resume();
            }}

            oscillators = []; // Clear previous oscillators
            gains = [];       // Clear previous gains

            currentThemeConfig.sounds.forEach(sound => createOscillatorSound(sound));

            oscillators.forEach(osc => osc.start());
            isSoundPlaying = true;
            updateStatusLabel("Playing: " + currentThemeConfig.sounds.map(s => s.label).join(", "));
            toggleSoundButton.textContent = "Pause Sound";
            introMessage.style.opacity = '0'; // Fade out message on first interaction
        }}

        function stopSound() {{
            if (!isSoundPlaying) return;

            oscillators.forEach(osc => osc.stop());
            isSoundPlaying = false;
            updateStatusLabel("Sound paused.");
            toggleSoundButton.textContent = "Start Sound";
            // Clean up AudioContext if no longer needed to free resources
            if (audioContext && audioContext.state !== 'closed') {{
                audioContext.close().then(() => audioContext = null);
            }}
        }}

        function updateStatusLabel(text) {{
            statusLabel.textContent = text;
        }}

        // --- Theme Changing ---
        const availableThemes = ["forest", "ocean", "rain", "sunrise", "dusk"];
        let currentThemeIndex = -1; // -1 for initial default or random theme

        // Replicate _generate_gradient_colo logic in JS for client-side theme changes
        const generateHarmoniousBgColors = () => {{
            const h = Math.floor(Math.random() * 360);
            const s = Math.floor(Math.random() * (60 - 30 + 1)) + 30; // 30-60
            const l1 = Math.floor(Math.random() * (85 - 70 + 1)) + 70; // 70-85
            const l2 = Math.floor(Math.random() * (75 - 60 + 1)) + 60; // 60-75
            return [`hsl(${h}, ${s}%, ${l1}%)`, `hsl(${h}, ${s}%, ${l2}%)`];
        }};

        function changeTheme() {{
            // Cycle through available themes
            currentThemeIndex = (currentThemeIndex + 1) % availableThemes.length;
            const newThemeName = availableThemes[currentThemeIndex];

            // Simulate getting new configuration.
            // 'palettes' and 'soundscapes' variables are embedded from Python's module-level definitions.
            const [newBgStart, newBgEnd] = generateHarmoniousBgColors();

            const newConfig = {{
                visual_colors: palettes[newThemeName],
                background_gradient_start: newBgStart,
                background_gradient_end: newBgEnd,
                sounds: soundscapes[newThemeName],
                visual_type: Math.random() < 0.5 ? "ripple" : "gradient_shift"
            }};
            
            document.body.style.background = `linear-gradient(135deg, ${newBgStart} 0%, ${newBgEnd} 100%)`;

            currentThemeConfig = newConfig;
            if (isSoundPlaying) {{
                stopSound(); // Stop current sounds gracefully
                startSound(); // Start new sounds with new config
            }}
            updateStatusLabel(`Theme: ${newThemeName.charAt(0).toUpperCase() + newThemeName.slice(1)}`);
            introMessage.style.opacity = '0'; // Fade out message on first interaction
        }}

        // --- Event Listeners and Initial Setup ---
        window.addEventListener('resize', resizeCanvas);
        toggleSoundButton.addEventListener('click', () => {{
            if (isSoundPlaying) {{
                stopSound();
            }} else {{
                startSound();
            }}
        }});
        changeThemeButton.addEventListener('click', changeTheme);

        resizeCanvas();
        animate();
        updateStatusLabel("Sound off."); // Initial label state
        // Initial theme is loaded from Python config, currentThemeIndex is -1.
        // First click on Change Theme will apply the first theme in availableThemes.

        // Pre-define palettes and soundscapes in JS for changeTheme to access
        // These are now correctly embedded from the module-level Python dictionaries
        const palettes = {json.dumps(_PALETTES)};
        const soundscapes = {json.dumps(_SOUNDSCAPES)};

    </script>
</body>
</html>"""
    return html

def process(text: str = "") -> str:
    """
    Generates an interactive HTML app for sensory restoration.
    Takes an optional theme string to customize the experience.

    Args:
        text: An optional string to suggest a theme (e.g., "forest", "ocean", "rain", "sunrise", "dusk").
              If empty or unrecognized, a default serene theme is used.

    Returns:
        A complete HTML page string for a self-contained interactive application.
    """
    theme_name = text.strip().lower()
    config = _get_theme_config(theme_name)
    return _generate_html_content(config)

# This block ensures the tool works in both CLI and Pyodide (browser) environments.
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    import sys
    # For CLI, allow passing a theme as an argument.
    theme_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    # In CLI mode, save the HTML output to a file for easy opening.
    output_filename = "urban_respite_weave.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(process(theme_arg))
    print(f"Urban Respite Weave HTML app generated: {output_filename}")