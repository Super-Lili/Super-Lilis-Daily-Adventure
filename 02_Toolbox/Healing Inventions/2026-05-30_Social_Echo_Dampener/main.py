import os
import argparse
import json # Import json for safe JavaScript string escaping

def process(user_input: str = "") -> str:
    """
    Generates an interactive HTML application that guides the user through a series of
    gentle prompts and subtle sensory shifts to help process and release residual mental
    "social static" after demanding interactions. The user_input provides context
    for the initial prompt, making the experience more personalized.

    The tool functions as a sequence of meditative, non-demanding steps to aid in mental
    decompression. It uses simple visual cues and sound to create a calming environment.
    """

    # Requirements: HTML, CSS, JavaScript inline. No external resources.
    # Uses Web Audio API for subtle sound cues.

    # Determine the initial prompt based on user_input
    if user_input:
        # Truncate user_input for a concise initial display, focusing on the core scenario.
        # It's an ambient tool, so brevity and a gentle acknowledgement are key.
        # Take the first sentence or up to 100 characters.
        initial_context_segment = user_input.split('.')[0].strip()
        if len(initial_context_segment) > 100:
            initial_context_segment = initial_context_segment[:97] + "..."
        elif not initial_context_segment and len(user_input) > 0: # If first sentence is empty but user_input exists
            initial_context_segment = user_input[:100].strip()
            if len(user_input) > 100: initial_context_segment += "..."

        if initial_context_segment:
            initial_prompt_content = f"Acknowledging the echoes from: '{initial_context_segment}'"
        else:
            initial_prompt_content = "Acknowledging the day's lingering echoes."
    else:
        initial_prompt_content = "Acknowledging the day's lingering echoes."

    # The existing core prompts
    core_prompts = [
        "Notice them without judgment.",
        "Where do these echoes reside in your mind or body?",
        "Imagine them as gentle ripples, slowly softening.",
        "Breathe, and release a little more with each exhale.",
        "Feel the quiet space returning.",
        "You are here, in this moment, complete.",
        "The echoes are fading, leaving clarity.",
        "Rest now. The day's demands have passed."
    ]

    # Combine into a single list, with the dynamic initial prompt first
    all_prompts_list = [initial_prompt_content] + core_prompts
    
    # Use json.dumps for proper JavaScript string escaping when embedding Python list into JS array
    js_prompts_array_string = ',\n            '.join([json.dumps(p) for p in all_prompts_list])

    # Fix: Escape all literal curly braces {{ and }} within the f-string.
    # This prevents Python from interpreting them as f-string expressions.
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Echo Dampener</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f0f4f8; /* Soft, light blue-grey */
            color: #4a5568; /* Muted dark grey */
            transition: background-color 2s ease-in-out, color 2s ease-in-out;
            cursor: pointer; /* Indicate interactivity */
            user-select: none; /* Prevent text selection distractions */
            line-height: 1.6;
        }}
        .container {{
            text-align: center;
            max-width: 600px;
            padding: 2rem;
        }}
        .prompt {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 1.5s ease-out, transform 1.5s ease-out;
        }}
        .instruction {{
            font-size: 1rem;
            color: #718096; /* Lighter grey */
            opacity: 0;
            transition: opacity 2s ease-out;
        }}
        @media (max-width: 768px) {{
            .prompt {{
                font-size: 1.4rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container" id="app">
        <div id="prompt-text" class="prompt"></div>
        <div id="instruction-text" class="instruction">Tap anywhere to begin.</div>
    </div>

    <script>
        const app = document.getElementById('app');
        const promptText = document.getElementById('prompt-text');
        const instructionText = document.getElementById('instruction-text');

        let audioContext;
        let oscillator;
        let gainNode;

        const prompts = [
            {js_prompts_array_string}
        ];

        const backgroundColors = [
            '#f0f4f8', // Initial light blue-grey
            '#e8eef2',
            '#e0e8ec',
            '#d8e2e6',
            '#d0dce0',
            '#c8d6da',
            '#c0d0d4',
            '#b8cacd',
            '#b0c4c7'  // Deeper calming blue-grey
        ];

        const textColors = [
            '#4a5568', // Initial muted dark grey
            '#5a6578',
            '#6a7588',
            '#7a8598',
            '#8a95a8',
            '#9aa5b8',
            '#aab5c8',
            '#bbc5d8',
            '#ccd5e8'  // Lighter, more serene text
        ];

        let currentStep = -1;
        let debounce = false;

        function initAudio() {{
            if (!audioContext) {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                gainNode = audioContext.createGain();
                gainNode.gain.value = 0; // Start muted
                gainNode.connect(audioContext.destination);
            }}
        }}

        function playSoftTone(frequency, duration, volume) {{
            if (!audioContext) initAudio();
            if (oscillator) {{
                oscillator.stop();
            }}
            oscillator = audioContext.createOscillator();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);

            const now = audioContext.currentTime;
            gainNode.gain.cancelScheduledValues(now);
            gainNode.gain.setValueAtTime(0, now);
            gainNode.gain.linearRampToValueAtTime(volume, now + 0.1); // Fade in
            gainNode.gain.linearRampToValueAtTime(0, now + duration - 0.1); // Fade out

            oscillator.connect(gainNode);
            oscillator.start(now);
            oscillator.stop(now + duration);
        }}

        function updateContent() {{
            if (debounce) return;
            debounce = true;

            currentStep++;

            if (currentStep < prompts.length) {{
                promptText.style.opacity = '0';
                promptText.style.transform = 'translateY(20px)';
                instructionText.style.opacity = '0';

                setTimeout(() => {{
                    promptText.textContent = prompts[currentStep];
                    document.body.style.backgroundColor = backgroundColors[currentStep % backgroundColors.length];
                    document.body.style.color = textColors[currentStep % textColors.length];

                    promptText.style.opacity = '1';
                    promptText.style.transform = 'translateY(0)';
                    playSoftTone(220 + (currentStep * 10), 2, 0.05); // Gentle rising tone

                    instructionText.textContent = currentStep === prompts.length - 1 ? "Breathe, and enjoy the calm." : "Tap to continue.";
                    instructionText.style.opacity = '1';
                    debounce = false;
                }}, 1000); // Wait for fade out, then update and fade in
            }} else {{
                promptText.textContent = "Deep calm. You are reset.";
                instructionText.textContent = "Close this window when you're ready.";
                instructionText.style.opacity = '1';
                debounce = false;
            }}
        }}

        app.addEventListener('click', () => {{
            if (currentStep === -1) {{
                instructionText.style.opacity = '0';
                setTimeout(updateContent, 500); // Start the first prompt
            }} else {{
                updateContent();
            }}
        }});

        // Initial state on load
        window.addEventListener('load', () => {{
            // No action on load, wait for user click.
            // This prevents unexpected audio playback without user interaction.
        }});

    </script>
</body>
</html>
    """
    return html_content.strip()

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # For CLI, the input is just a placeholder to trigger the ambient app.
    # The app itself is interactive within the browser, not driven by CLI arguments.
    parser = argparse.ArgumentParser(
        description="Launch an ambient HTML app to help dampen social echoes.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--context",
        type=str,
        required=True, # FIXED: Removed default and made argument required
        help=(
            "REQUIRED: Provide a short context string (e.g., 'after a long meeting').\n"
            "This input is used to personalize the initial prompt of the interactive app.\n\n"
            "Example: python main.py --context 'after a demanding client pitch'"
        )
    )
    args = parser.parse_args()
    print(process(args.context))