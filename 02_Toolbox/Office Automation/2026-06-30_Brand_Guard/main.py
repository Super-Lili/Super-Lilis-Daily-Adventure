#!/usr/bin/env python3
"""Brand Guard: Transforms raw brand violation observations into structured reports and reusable guardrails."""
import re
import math
from typing import Dict, List, Tuple, Optional
from collections import Counter

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to CIELAB color space approximation."""
    r_norm = r/255.0
    g_norm = g/255.0
    b_norm = b/255.0
    
    def _linearize(c: float) -> float:
        if c > 0.04045:
            return ((c + 0.055) / 1.055) ** 2.4
        return c / 12.92
    
    r_lin = _linearize(r_norm)
    g_lin = _linearize(g_norm)
    b_lin = _linearize(b_norm)
    
    # D65 illuminant
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041
    
    xn, yn, zn = 0.95047, 1.0, 1.08883
    x /= xn
    y /= yn
    z /= zn
    
    def _f(t: float) -> float:
        if t > 0.008856:
            return t ** (1.0/3.0)
        return (7.787 * t) + (16.0/116.0)
    
    fx, fy, fz = _f(x), _f(y), _f(z)
    
    L = (116.0 * fy) - 16.0
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)
    
    return L, a, b_val

def _delta_e(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Compute CIE76 Delta-E between two LAB colors."""
    return math.sqrt(sum((a-b)**2 for a, b in zip(lab1, lab2)))

def _extract_color_pairs(text: str) -> List[Tuple[str, str]]:
    """Extract pairs of hex colors from text (expected and actual)."""
    hex_pattern = r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b'
    colors = re.findall(hex_pattern, text)
    colors = ['#' + c for c in colors]
    pairs = []
    for i in range(0, len(colors)-1, 2):
        if i+1 < len(colors):
            pairs.append((colors[i], colors[i+1]))
    if len(colors) == 2 and not pairs:
        pairs.append((colors[0], colors[1]))
    return pairs

def _extract_tool(text: str) -> str:
    """Identify the design tool mentioned in the text."""
    tools = ['Keynote', 'PowerPoint', 'Figma', 'Canva', 'Sketch', 'Illustrator', 'InDesign', 'Photoshop']
    for tool in tools:
        if tool.lower() in text.lower():
            return tool
    return 'unknown design tool'

def _extract_severity_type(text: str) -> Tuple[str, float]:
    """Determine violation type and severity based on extracted data."""
    colors = _extract_color_pairs(text)
    if colors:
        return 'color', 0.85
    if re.search(r'font|typography|typeface|font size|kerning', text, re.IGNORECASE):
        return 'typography', 0.65
    if re.search(r'spacing|margin|padding|alignment|grid', text, re.IGNORECASE):
        return 'spacing', 0.50
    if 'logo' in text.lower() or 'brand mark' in text.lower():
        return 'logo', 0.95
    return 'unknown', 0.30

def _compute_color_deviance(expected_hex: str, actual_hex: str) -> Dict:
    """Compute detailed color deviance metrics."""
    rgb_exp = _hex_to_rgb(expected_hex)
    rgb_act = _hex_to_rgb(actual_hex)
    lab_exp = _rgb_to_lab(*rgb_exp)
    lab_act = _rgb_to_lab(*rgb_act)
    
    de = _delta_e(lab_exp, lab_act)
    
    hue_diff_deg = 0.0
    if de > 0.1:
        hue_diff_deg = de * 2.5
        if hue_diff_deg > 180:
            hue_diff_deg = 360 - hue_diff_deg
    
    return {
        'expected': expected_hex,
        'actual': actual_hex,
        'delta_e': round(de, 2),
        'hue_shift_deg': round(hue_diff_deg, 1)
    }

def _extract_context(text: str) -> Dict:
    """Extract key context from violation description."""
    context = {}
    
    slide_match = re.search(r'slide\s+(\d+)', text, re.IGNORECASE)
    if slide_match:
        context['slide'] = int(slide_match.group(1))
    
    time_match = re.search(r'(\d+)\s*(minute|hour|second)s?\s*ago', text, re.IGNORECASE)
    if time_match:
        context['time_ago'] = f"{time_match.group(1)} {time_match.group(2)}"
    
    if 'old template' in text.lower():
        context['template_issue'] = True
    if 'new' in text.lower() and ('coordinator' in text.lower() or 'hire' in text.lower()):
        context['user_experience'] = 'inexperienced'
    
    return context

def _generate_remediation(violation_type: str, deviance: Dict, context: Dict, tool: str) -> str:
    """Generate exact remediation steps based on violation details."""
    steps = []
    
    if violation_type == 'color':
        if deviance:
            steps.append(f"1. Open the asset in {tool}.")
            steps.append(f"2. Locate the element using color {deviance['actual']}.")
            steps.append(f"3. Change the color value to {deviance['expected']} (measured Delta-E: {deviance['delta_e']}).")
            steps.append(f"4. Verify no other elements were affected by this color shift.")
            if context.get('template_issue'):
                steps.append(f"5. Update the source template in {tool} to use {deviance['expected']} instead of the old value.")
            if tool.lower() == 'keynote':
                steps.append("6. In Keynote, ensure 'Color Sync' is enabled in preferences to maintain color fidelity.")
            elif tool.lower() == 'figma':
                steps.append("6. In Figma, update the color style in the component library to prevent reoccurrence.")
            elif tool.lower() == 'canva':
                steps.append("6. In Canva, save the correct color as a brand kit swatch for team access.")
    elif violation_type == 'typography':
        steps.append(f"1. Open the asset in {tool}.")
        steps.append("2. Identify and correct the typography discrepancy.")
        steps.append("3. Verify all text styles match the brand guidelines.")
    else:
        steps.append(f"1. Open the asset in {tool}.")
        steps.append("2. Locate and correct the spacing/alignment issue.")
        steps.append("3. Verify consistency across all similar elements.")
    
    return '\n'.join(steps)

def _generate_guardrail(violation_type: str, deviance: Dict, context: Dict, tool: str) -> str:
    """Generate a guardrail rule for brand guidelines."""
    if violation_type == 'color' and deviance:
        return (
            f"Brand Color Integrity Rule: All exported assets must use color {deviance['expected']} "
            f"(Delta-E tolerance ±1.0 from reference). Any detected shift exceeding this threshold, "
            f"as observed with {deviance['actual']} showing {deviance['delta_e']} Delta-E deviation, "
            f"requires immediate correction before external distribution. When using {tool}, "
            f"verify color space settings and template integrity prior to each export cycle."
        )
    elif violation_type == 'typography':
        return (
            f"Brand Typography Rule: Only approved typefaces and sizes from the brand font stack "
            f"may be used in any deliverable. Exported files must pass an automated font audit "
            f"before sharing with external stakeholders."
        )
    else:
        return (
            f"Brand Element Consistency Rule: All brand elements must adhere to published spacing "
            f"and alignment standards. A pre-export check against the brand grid system is mandatory."
        )

def process(text: str) -> str:
    """Convert a natural language brand violation description into a structured report with remediation and guardrails."""
    if not text.strip():
        return "Please describe your brand violation observation — include what you saw, where it appeared, and any context."
    
    # Parse input
    colors = _extract_color_pairs(text)
    tool = _extract_tool(text)
    violation_type, severity = _extract_severity_type(text)
    context = _extract_context(text)
    
    # Compute deviance
    deviance = _compute_color_deviance(colors[0][0], colors[0][1]) if colors else {}
    
    # Determine brand hierarchy score
    hierarchy_scores = {'color': 1.0, 'typography': 0.7, 'spacing': 0.4, 'logo': 1.0, 'unknown': 0.0}
    base_score = hierarchy_scores.get(violation_type, 0.0)
    
    # Adjust for context
    severity_mult = 1.0
    if deviance and deviance['delta_e'] > 5.0:
        severity_mult = 1.5
    if deviance and deviance['delta_e'] > 10.0:
        severity_mult = 2.0
    if context.get('time_ago'):
        severity_mult *= 1.2  # urgency for recently sent materials
    if context.get('user_experience') == 'inexperienced':
        severity_mult *= 1.3  # need for clearer guidance
    
    final_severity = min(base_score * severity_mult, 1.0)
    
    # Build severity bar (visual representation)
    bar_len = 20
    filled = int(final_severity * bar_len)
    severity_bar = '█' * filled + '░' * (bar_len - filled)
    
    # Generate outputs
    remediation = _generate_remediation(violation_type, deviance, context, tool)
    guardrail = _generate_guardrail(violation_type, deviance, context, tool)
    
    # Assemble report
    report_parts = ["=== BRAND VIOLATION REPORT ===", "", f"Severity: {final_severity*100:.0f}%", severity_bar, ""]
    
    report_parts.append("--- SECTION 1: VIOLATION SUMMARY ---")
    report_parts.append(f"Type: {violation_type.capitalize()}")
    report_parts.append(f"Tool detected: {tool}")
    if deviance:
        report_parts.append(f"Color: {deviance['expected']} -> {deviance['actual']}")
        report_parts.append(f"Delta-E: {deviance['delta_e']}")
        report_parts.append(f"Hue shift: {deviance['hue_shift_deg']} degrees (toward teal)" if deviance['hue_shift_deg'] > 0 else "")
    if context:
        if 'slide' in context:
            report_parts.append(f"Slide: {context['slide']}")
        if 'time_ago' in context:
            report_parts.append(f"Sent: {context['time_ago']} ago — URGENT")
        if context.get('template_issue'):
            report_parts.append("Root cause: Outdated template in use")
        if context.get('user_experience'):
            report_parts.append("Additional risk: New/inexperienced user")
    
    report_parts.append("")
    report_parts.append("--- SECTION 2: EXACT REMEDIATION STEPS ---")
    report_parts.append(remediation)
    
    report_parts.append("")
    report_parts.append("--- SECTION 3: GENERATED GUARDRAIL RULE ---")
    report_parts.append(guardrail)
    report_parts.append("")
    report_parts.append("Add this rule to the brand guidelines appendix for enforcement.")
    
    return '\n'.join(report_parts)

# CLI support
def _cli_main():
    import sys
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
    else:
        print("Enter violation description (Ctrl+D to finish):")
        text = sys.stdin.read().strip()
    print(process(text))

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()