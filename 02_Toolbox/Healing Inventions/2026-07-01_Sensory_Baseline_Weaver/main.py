import sys
import re
import math
from typing import Dict, Any

def parse_input(text: str) -> Dict[str, Any]:
    """
    Parses user input to extract session duration and infer initial sensory
    intensities (visual and auditory) from descriptive keywords.
    """
    duration_match = re.search(r'(\d+)\s*(minutes?|min)', text, re.IGNORECASE)
    duration_minutes = int(duration_match.group(1)) if duration_match else 15 # Default to 15 minutes

    visual_keywords = ['bright', 'vibrant', 'colorful', 'screens', 'visuals', 'cmyk', 'high contrast', 'glare', 'graphics', 'design', 'interfaces', 'palettes', 'hues', 'luminance']
    auditory_keywords = ['pings', 'alerts', 'noise', 'barrage', 'calls', 'chatter', 'loud', 'drones', 'beeps', 'ringing', 'speaking', 'blips', 'static']

    visual_intensity = 0
    auditory_intensity = 0

    lower_text = text.lower()

    for keyword in visual_keywords:
        if keyword in lower_text:
            visual_intensity += 10 # Simple additive score for keyword presence

    for keyword in auditory_keywords:
        if keyword in lower_text:
            auditory_intensity += 10 # Simple additive score

    # Scale intensity to a 0-100 range.
    # A base intensity of 10% is set if any keyword is found, to ensure progression.
    # This prevents a '0%' intensity from having no change.
    visual_intensity = min(100, max(10, visual_intensity * 5)) if visual_intensity > 0 else 10
    auditory_intensity = min(100, max(10, auditory_intensity * 5)) if auditory_intensity > 0 else 10

    return {
        'duration_minutes': duration_minutes,
        'visual_intensity': visual_intensity,
        'auditory_intensity': auditory_intensity
    }

def generate_plan(parsed_data: Dict[str, Any]) -> str:
    """
    Generates a structured plain-text plan outlining the progressive sensory
    reduction, including proposed CSS and Web Audio API parameters.
    """
    duration = parsed_data['duration_minutes']
    vis_int = parsed_data['visual_intensity']
    aud_int = parsed_data['auditory_intensity']

    # --- Visual State Mapping ---
    # Initial visual state parameters (HSL: Hue, Saturation, Lightness)
    # Higher intensity means more saturation, more lightness, and higher filter values.
    base_hue = 220 # A calming base blue/indigo hue
    
    # Calculate initial values based on visual intensity (0-100)
    # These values are designed to scale from a calm baseline (low intensity)
    # to a more saturated/bright state (high intensity).
    initial_saturation = min(100, 15 + int(70 * (vis_int / 100))) # Base 15% + up to 70%
    initial_lightness = min(100, 20 + int(50 * (vis_int / 100)))  # Base 20% + up to 50%
    initial_brightness_filter = min(150, 100 + int(40 * (vis_int / 100))) # Base 100% + up to 40%
    initial_saturate_filter = min(150, 100 + int(40 * (vis_int / 100))) # Base 100% + up to 40%

    # Final visual state (very low luminance, near monochromatic)
    final_hue = 240 # Slightly deeper, more muted indigo hue
    final_saturation = 5 # Extremely low saturation
    final_lightness = 8 # Very low lightness
    final_brightness_filter = 10 # Very dim
    final_saturate_filter = 0 # Fully desaturated

    # --- Auditory State Mapping ---
    # Descriptions for initial auditory environment based on inferred intensity.
    aud_high_freq_presence_desc = "prominent mid-to-high frequency elements (e.g., sharp pings, speech overtones)." if aud_int > 60 else \
                                   "some mid-range frequency presence (e.g., gentle hums, distant murmurs)." if aud_int > 20 else \
                                   "minimal high-frequency presence, mostly low-frequency ambient tones."
    initial_volume_desc = f"Moderate to {'high' if aud_int > 70 else 'medium'} volume with {aud_high_freq_presence_desc}"
    final_volume_desc = "Near-silent with a pure, barely audible low-frequency tone (<100 Hz)."

    plan_parts = []
    plan_parts.append("--- Sensory Baseline Weaver Session Plan ---")
    plan_parts.append(f"\nSession Duration: {duration} minutes")

    plan_parts.append("\n## Initial Sensory Assessment")
    plan_parts.append(f"Based on your input, the session will begin by actively reducing:")
    plan_parts.append(f"- Visual Intensity: {vis_int}% inferred (e.g., bright screens, vibrant colors, glare)")
    plan_parts.append(f"- Auditory Intensity: {aud_int}% inferred (e.g., sharp alerts, constant noise, chatter)")

    plan_parts.append("\n## Session Progression Strategy")
    plan_parts.append(f"Objective: Gently guide your nervous system towards a state of reduced external stimulation over {duration} minutes.")

    plan_parts.append("\n### Visual Transition Plan")
    plan_parts.append(f"Starts: A visually { 'active and stimulating' if vis_int > 50 else 'moderate'} environment.")
    plan_parts.append(f"  Proposed CSS Initial State:")
    plan_parts.append(f"    background-color: hsl({base_hue}, {initial_saturation}%, {initial_lightness}%);")
    plan_parts.append(f"    filter: saturate({initial_saturate_filter}%) brightness({initial_brightness_filter}%);")
    plan_parts.append("  Progression Phases:")
    plan_parts.append(f"    - Phase 1 (0-{duration * 0.2:.0f} min): Initial subtle shift. Gentle desaturation, overall luminance reduction. Focus on softening sharp visual elements and reducing glare.")
    plan_parts.append(f"    - Phase 2 ({duration * 0.2:.0f}-{duration * 0.6:.0f} min): Core transformation. Continued luminance decrease, gradual shift towards cooler, more muted tones (e.g., deep blues, muted indigos, charcoal grays). Saturation significantly drops.")
    plan_parts.append(f"    - Phase 3 ({duration * 0.6:.0f}-{duration * 0.9:.0f} min): Deep calming. Intensive reduction in brightness and saturation, subtle deepening to near-monochromatic states. Visual detail minimizes.")
    plan_parts.append(f"    - Final Phase ({duration * 0.9:.0f}-{duration:.0f} min): Baseline approach. Gradual, final fade to the ultimate minimal visual state.")
    plan_parts.append("  Ends: A near-monochromatic, very low-luminance state, resembling a deep charcoal or muted indigo.")
    plan_parts.append(f"  Proposed CSS Final State:")
    plan_parts.append(f"    background-color: hsl({final_hue}, {final_saturation}%, {final_lightness}%);")
    plan_parts.append(f"    filter: saturate({final_saturate_filter}%) brightness({final_brightness_filter}%);")
    plan_parts.append("  Eased Transition Note: All visual changes should utilize a custom-eased, non-linear progression (e.g., `cubic-bezier(0.25, 0.1, 0.25, 1.0)`) to ensure smoothness and prevent jarring shifts. Apply transitions to background color, filter properties, and potentially overlay opacity for subtle texture shifts.")

    plan_parts.append("\n### Auditory Transition Plan")
    plan_parts.append(f"Starts: {initial_volume_desc}")
    plan_parts.append("  Progression Phases:")
    plan_parts.append(f"    - Phase 1 (0-{duration * 0.2:.0f} min): Initial auditory softening. Subtle attenuation of higher frequencies (e.g., >2kHz), gentle overall volume reduction. Sharp alert-like sounds begin to lose their edge.")
    plan_parts.append(f"    - Phase 2 ({duration * 0.2:.0f}-{duration * 0.6:.0f} min): Soundscape transformation. Introduction of smooth, low-frequency hums and tones (e.g., filtered white noise below 500 Hz). Continued significant volume decrease, further high-frequency filtering (e.g., high-shelf filter cut-off below 1kHz).")
    plan_parts.append(f"    - Phase 3 ({duration * 0.6:.0f}-{duration * 0.9:.0f} min): Deep auditory calming. Dominance of very low-frequency ambient tones, approaching near-silent volume. Vocal range and percussive frequencies largely filtered out.")
    plan_parts.append(f"    - Final Phase ({duration * 0.9:.0f}-{duration:.0f} min): Baseline approach. Gradual, final fade to the ultimate minimal auditory state.")
    plan_parts.append(f"  Ends: {final_volume_desc}")
    plan_parts.append("  Web Audio API Note: This plan requires dynamic gain node manipulation for volume control and BiquadFilterNode adjustments (e.g., lowpass filters with decaying Q, high-shelf filters with increasing attenuation) for frequency shaping. Implement custom audio envelopes to match visual easing, ensuring a synchronized, immersive experience.")

    plan_parts.append("\n## Sensory Baseline Reached - Session Complete")
    plan_parts.append("Upon completion of the session, the environment will stabilize at a minimal state, offering a deep charcoal or muted indigo visual field and an auditory landscape of near-silence or a pure, barely audible low-frequency tone. This state is designed to allow for effortless transition into restorative activities or focused, calm creative work.")

    plan_parts.append("\n## Implementation Guidance for a Creative Technologist")
    plan_parts.append("This plan provides concrete parameters derived from the user's current sensory overload. The inferred initial intensities guide the starting points for CSS (e.g., `background-color`, `filter` properties) and Web Audio API parameters (e.g., `GainNode` for volume, `BiquadFilterNode` for frequency shaping). Emphasize non-linear easing and careful synchronization between visual and auditory transitions for a truly immersive and restorative experience. The goal is a perceptibly seamless reduction, guiding the nervous system rather than shocking it.")

    return "\n".join(plan_parts)

def process(text: str) -> str:
    """
    Transforms user's sensory overload description into a detailed, actionable
    plain-text plan for creating a progressive sensory reduction environment.
    This output serves as a specification for a developer/designer to implement
    the described HTML/CSS/Web Audio API-based environment.
    """
    if not text.strip() or len(text.strip()) < 10:
        return "Error: Please provide a description of your sensory overload and desired session duration. Example: 'My day was full of bright CMYK palettes and constant email pings. I need 20 minutes to reset.'"

    try:
        parsed_data = parse_input(text)
        if parsed_data['duration_minutes'] <= 0:
            return "Error: Please specify a valid duration in minutes (e.g., '20 minutes')."
        
        plan = generate_plan(parsed_data)
        return plan
    except Exception as e:
        # Catch potential parsing errors or other issues
        return f"An error occurred while processing your request: {str(e)}. Please check your input format and try again."

# Test input for local execution
_test_input = "My day was a non-stop barrage of bright client brand guides and video call alerts. I need 25 minutes to feel human again."

def _cli_main():
    """Main function for command-line execution."""
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = _test_input # Use the internal test input if no CLI arguments
    
    result = process(user_input)
    print(result)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()