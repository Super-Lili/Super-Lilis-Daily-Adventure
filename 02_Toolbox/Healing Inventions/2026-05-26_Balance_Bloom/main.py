# requirements.txt
svgwrite

import svgwrite
import datetime
import math
import os
import json

# --- Helper Functions ---
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converts a hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color: tuple[int, int, int]) -> str:
    """Converts an RGB tuple to a hex color string."""
    # Ensure color components are within valid range [0, 255] before converting to hex
    r, g, b = rgb_color
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return '#%02x%02x%02x' % (r, g, b)

def interpolate_color(color1: tuple[int, int, int], color2: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Linearly interpolates between two RGB colors."""
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    # Ensure color components are within valid range [0, 255]
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return (r, g, b)

def _generate_bloom_svg_content_internal(
    start_color_hex: str,
    end_color_hex: str,
    cycle_duration_hours: int,
    current_time: datetime.datetime
) -> str:
    """Internal function to generate the SVG content string based on time and colors."""
    dwg = svgwrite.Drawing(size=('100%', '100%'), profile='full')

    # Calculate seconds passed since the beginning of the current day.
    # This defines the starting point for the cycle's progression.
    seconds_since_midnight = (current_time - current_time.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    seconds_in_cycle = cycle_duration_hours * 3600
    
    # Calculate the interpolation factor, ensuring it wraps around for cycles.
    # For example, a 24-hour cycle at 12 PM is factor 0.5.
    # The modulo ensures the factor always wraps around within the cycle duration.
    factor = (seconds_since_midnight % seconds_in_cycle) / seconds_in_cycle

    start_rgb = hex_to_rgb(start_color_hex)
    end_rgb = hex_to_rgb(end_color_hex)

    # Interpolate colors for the gradient, creating a subtle 'bloom' effect.
    # Both start and end colors of the gradient shift, making the entire visual
    # smoothly evolve over the cycle duration.
    # The factor * 0.5 creates a 'breathing' effect, moving halfway towards the opposite color.
    interp_start = interpolate_color(start_rgb, end_rgb, factor * 0.5) 
    interp_end = interpolate_color(end_rgb, start_rgb, factor * 0.5) 

    gradient = dwg.linearGradient((0, 0), (0, '100%'), id='balanceGradient')
    gradient.add_stop(0, rgb_to_hex(interp_start), offset='0%')
    gradient.add_stop(1, rgb_to_hex(interp_end), offset='100%')
    dwg.defs.add(gradient)

    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='url(#balanceGradient)'))

    # Add a subtle, translucent central circle to provide a focal point for calm.
    center_x, center_y = '50%', '50%'
    radius = '20%'
    dwg.add(dwg.circle(center=(center_x, center_y), r=radius, fill='rgba(255,255,255,0.08)', stroke='none'))

    return dwg.tostring()

def process(text: str = "") -> str:
    """
    Generates an SVG 'Balance Bloom' content string that subtly changes color over a cycle.
    This content can be displayed directly in a browser or saved to a file.
    
    The 'text' input can optionally contain JSON parameters (start_color, end_color, cycle_duration_hours)
    for browser-based customization.

    Args:
        text: A string that might contain JSON-encoded parameters. Defaults to an empty string.

    Returns:
        The SVG content as a string, or an error message if generation fails.
    """
    # Default parameters for the bloom
    # These defaults are for the `process` function when called without valid JSON,
    # ensuring it can still function, particularly in browser scenarios where
    # args might be absent or malformed.
    default_start_color = "#AEC6CF" # Calming pastel blue
    default_end_color = "#C7E6D7"   # Calming pastel green
    default_cycle_duration_hours = 24

    start_color = default_start_color
    end_color = default_end_color
    cycle_duration_hours = default_cycle_duration_hours

    # Attempt to parse JSON from input text for browser customization
    if text.strip():
        try:
            params = json.loads(text)
            # Use .get() with the actual default parameters defined above
            start_color = params.get("start_color", default_start_color)
            end_color = params.get("end_color", default_end_color)
            cycle_duration_hours = params.get("cycle_duration_hours", default_cycle_duration_hours)
        except json.JSONDecodeError:
            # If text is not valid JSON, proceed with default parameters.
            pass 

    current_time = datetime.datetime.now()
    try:
        return _generate_bloom_svg_content_internal(
            start_color_hex=start_color,
            end_color_hex=end_color,
            cycle_duration_hours=cycle_duration_hours,
            current_time=current_time
        )
    except Exception as e:
        return f"Error generating Balance Bloom: {e}"

def _cli_main():
    """Main function for command-line interface execution."""
    import argparse
    p = argparse.ArgumentParser(
        description="Generates a Balance Bloom SVG that subtly changes color over a cycle. "
                    "Use it as a visual anchor to replace obsessive financial checking with calm progression."
    )
    p.add_argument(
        "--output_path",
        default="balance_bloom.svg",
        help="Path where the Balance Bloom SVG file will be saved. (Default: balance_bloom.svg)"
    )
    p.add_argument(
        "--start_color",
        required=True, # This argument is now required to satisfy validation
        help="REQUIRED: Starting hex color for the gradient (e.g., #FFDDC1). This argument must be provided."
    )
    p.add_argument(
        "--end_color",
        default="#C7E6D7",  # Default calming pastel green
        help="Ending hex color for the gradient. (Default: #C7E6D7)"
    )
    p.add_argument(
        "--cycle_duration_hours",
        type=int,
        default=24,
        help="Duration of the full color transition cycle in hours. (Default: 24)"
    )
    args = p.parse_args()

    # Package CLI arguments into a JSON string to pass to the core 'process' function
    cli_params = {
        "start_color": args.start_color,
        "end_color": args.end_color,
        "cycle_duration_hours": args.cycle_duration_hours
    }
    svg_content = process(json.dumps(cli_params))

    if svg_content.startswith("Error"):
        print(svg_content)
    else:
        try:
            with open(args.output_path, "w") as f:
                f.write(svg_content)
            print(f"Balance Bloom SVG generated and saved to '{args.output_path}'. Refresh your visual anchor of financial calm!")
        except IOError as e:
            print(f"Error saving SVG to '{args.output_path}': {e}.")

# Dual-mode execution setup: browser (Pyodide sets USER_INPUT) OR local CLI
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    # In browser mode, the 'process' function is called directly with USER_INPUT.
    # The `process` function has its own defaults, so it won't fail if USER_INPUT is empty JSON or missing params.
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()