import argparse
import sys

# Define the process function for the tool
def process(user_input: str = "") -> str:
    """
    Generates a full-screen HTML clock whose background color shifts through the natural arc of sunlight
    across 24 hours, inspired by Jasper Morrison's minimalist design.

    The clock dynamically interpolates colors:
    - Early morning: gentle golden-pink
    - Midday: bright white-blue
    - Evening: warm orange-red
    - Night: deep indigo-blue

    No input is needed; the tool works immediately upon opening in a browser.

    Example:
    ```python
    # No specific input is required for this ambient tool.
    # The `process` function will return a complete HTML string.
    html_output = process()
    # This HTML can then be saved to a .html file and opened in a browser.
    # The output will start with a DOCTYPE declaration and contain full HTML, CSS, and JavaScript.
    print(html_output[:500]) # Print first 500 chars to show it's HTML
    ```
    """

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sun Light Color Clock</title>
    <style>
        :root {
            --bg-color: rgb(25, 25, 70); /* Default to midnight blue */
            --text-color: rgba(255, 255, 255, 0.8);
        }
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif;
            transition: background-color 1.5s ease-in-out; /* Smooth transition */
            background-color: var(--bg-color);
            display: flex;
            justify-content: center;
            align-items: center;
            color: var(--text-color);
            line-height: 1; /* Ensure no extra line height for clock text */
        }
        #clock {
            font-size: clamp(2rem, 15vw, 10rem); /* Responsive font size */
            font-weight: 200; /* Light font weight for elegance */
            letter-spacing: -0.05em; /* Slightly tighter letter spacing */
            text-shadow: 0 0 15px rgba(0, 0, 0, 0.2); /* Subtle text shadow for depth */
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="clock"></div>

    <script>
        const clockDiv = document.getElementById('clock');
        const root = document.documentElement;

        // Define color points with (hour, minute, r, g, b)
        // These values are chosen to create a natural and calming progression of colors,
        // mimicking the sky's appearance throughout the day.
        const colorPoints = [
            {h: 0, m: 0, r: 25, g: 25, b: 70},   // Midnight: Deep Indigo
            {h: 4, m: 0, r: 40, g: 40, b: 90},   // Pre-dawn: Darker Indigo/Purple
            {h: 6, m: 0, r: 255, g: 190, b: 180},// Sunrise: Gentle Golden-Pink
            {h: 8, m: 0, r: 255, g: 220, b: 190},// Morning: Lighter Golden
            {h: 12, m: 0, r: 170, g: 220, b: 255},// Noon: Bright White-Blue
            {h: 16, m: 0, r: 150, g: 190, b: 230},// Afternoon: Fading Sky Blue
            {h: 18, m: 0, r: 255, g: 100, b: 60}, // Sunset: Vibrant Orange-Red
            {h: 20, m: 0, r: 180, g: 50, b: 100}, // Dusk: Deeper Red/Purple
            {h: 22, m: 0, r: 80, g: 30, b: 120},  // Night: Dark Purple/Indigo
            {h: 24, m: 0, r: 25, g: 25, b: 70}    // Loop back to Midnight (same color as h:0, m:0 for smooth transition)
        ];

        function lerp(a, b, t) {
            return a + (b - a) * t;
        }

        function updateClock() {
            const now = new Date();
            const hours = now.getHours();
            const minutes = now.getMinutes();
            const seconds = now.getSeconds();

            const totalMinutes = hours * 60 + minutes + seconds / 60; // Current total minutes from midnight

            let p1 = colorPoints[0];
            let p2 = colorPoints[1];

            // Find the two control points for interpolation
            // The logic correctly handles totalMinutes from 0 up to 23:59:59.999
            // and the 24:00 point serves as the end of the day segment for interpolation.
            for (let i = 0; i < colorPoints.length - 1; i++) {
                const cp1_total_minutes = colorPoints[i].h * 60 + colorPoints[i].m;
                let cp2_total_minutes = colorPoints[i+1].h * 60 + colorPoints[i+1].m;

                // For the last point defined as h:24, m:0, ensure its time value is correctly 24*60.
                if (colorPoints[i+1].h === 24) {
                    cp2_total_minutes = 24 * 60;
                }

                if (totalMinutes >= cp1_total_minutes && totalMinutes < cp2_total_minutes) {
                    p1 = colorPoints[i];
                    p2 = colorPoints[i+1];
                    break;
                }
            }

            // Calculate interpolation factor (t)
            let t = 0;
            const p1TotalMinutes = p1.h * 60 + p1.m;
            let p2TotalMinutes = p2.h * 60 + p2.m;
            
            // This adjustment handles scenarios where p2's absolute time is conceptually 'next day'
            // (e.g., interpolating from 22:00 to 04:00 if colorPoints didn't wrap with 24:00,
            // but with 24:00 point, it should mostly be handled by the loop above).
            // This block is a robust safeguard.
            if (p2TotalMinutes < p1TotalMinutes) {
                p2TotalMinutes += (24 * 60); // Treat p2 as on the next day for calculation
            }
            
            // Ensure currentInterpolationMinutes is also aligned if it conceptually wrapped.
            let currentInterpolationMinutes = totalMinutes;
            if (currentInterpolationMinutes < p1TotalMinutes && p2TotalMinutes > (24 * 60 - 1)) { // If current time is early morning and p1 is late night
                currentInterpolationMinutes += (24 * 60);
            }
            
            if (p2TotalMinutes === p1TotalMinutes) {
                t = 0; // Avoid division by zero if points are identical (e.g., at midnight, 24:00 vs 0:00)
            } else {
                t = (currentInterpolationMinutes - p1TotalMinutes) / (p2TotalMinutes - p1TotalMinutes);
            }
            
            t = Math.max(0, Math.min(1, t)); // Clamp t between 0 and 1 to prevent overshoot

            const r = lerp(p1.r, p2.r, t);
            const g = lerp(p1.g, p2.g, t);
            const b = lerp(p1.b, p2.b, t);

            root.style.setProperty('--bg-color', `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`);
            
            // Set text color based on perceived luminosity of background for optimal contrast
            const luminosity = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            root.style.setProperty('--text-color', luminosity > 0.6 ? 'rgba(0, 0, 0, 0.7)' : 'rgba(255, 255, 255, 0.8)');


            // Format time as HH:MM:SS (24-hour format)
            const formattedHours = String(hours).padStart(2, '0');
            const formattedMinutes = String(minutes).padStart(2, '0');
            const formattedSeconds = String(seconds).padStart(2, '0');
            clockDiv.textContent = `${formattedHours}:${formattedMinutes}:${formattedSeconds}`;
        }

        // Initial update when the page loads
        updateClock();
        // Update the clock and colors every second for smooth animation
        setInterval(updateClock, 1000);
    </script>
</body>
</html>
    """
    return html_template

# For local testing/CLI, if needed. The primary use is via the browser_input.
def _cli_main():
    """CLI entry point for the tool."""
    # Use argparse to handle command-line arguments, including --help automatically.
    # description is used for the help message.
    parser = argparse.ArgumentParser(
        description="Generates a full-screen HTML clock whose background color dynamically shifts to reflect the natural progression of sunlight throughout the day and night."
    )
    # The tool does not accept any specific runtime arguments for its core function,
    # but argparse provides robust --help handling.
    parser.parse_args() # This will automatically process --help and exit if requested.

    print("This tool generates an HTML file that functions as an ambient clock.")
    print("No command-line input is needed. Please save the output to an .html file and open it in your browser.")
    html_output = process()
    output_filename = "sun_light_color_clock.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"Generated '{output_filename}'. Open this file in a web browser to use the clock.")

# This standard pattern ensures the `process` function is called correctly whether
# the script is executed in a browser environment or via the command line.
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    # When USER_INPUT is provided (e.g., by the platform), print the HTML output directly.
    # Ensure the input to process is always a string.
    print(process(str(_browser_input)))
elif __name__ == "__main__":
    _cli_main()