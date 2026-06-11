#!/usr/bin/env python3
"""
Handoff Blueprint Generator
Category: Office Automation | Mode: 3 (HTML)
Generates interactive, visually polished HTML design specifications
from semi-structured textual design component descriptions.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import html

REQUIREMENTS = {
    "mode": "3",
    "algorithmic_depth": [
        "semantic_parsing_and_property_extraction",
        "visual_component_rendering",
        "responsive_rule_interpretation_and_visualization"
    ],
    "requires_external_libraries": False
}

def _parse_dimensions(text: str) -> Dict[str, Optional[int]]:
    """Parse dimension strings like '320x48', 'w:320 h:48', 'width 320 height 48'"""
    result = {"width": None, "height": None}
    patterns = [
        (r'(\d+)\s*x\s*(\d+)', lambda m: (int(m.group(1)), int(m.group(2)))),
        (r'(?:w(?:idth)?)[:\s]*(\d+)[,\s]*(?:h(?:eight)?)[:\s]*(\d+)', lambda m: (int(m.group(1)), int(m.group(2)))),
        (r'(\d+)\s*(?:px)?\s*(?:wide|width)[,\s]*(\d+)\s*(?:px)?\s*(?:tall|height)', lambda m: (int(m.group(1)), int(m.group(2)))),
    ]
    for pattern, extractor in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["width"], result["height"] = extractor(match)
            break
    return result

def _parse_typography(text: str) -> Dict[str, Any]:
    """Parse typography like '16px Inter bold, lh 24px' or 'font: Inter 16px/24px bold'"""
    result = {"font_family": None, "font_size": None, "font_weight": None, "line_height": None}
    font_size_match = re.search(r'(\d+)\s*px', text)
    if font_size_match:
        result["font_size"] = int(font_size_match.group(1))
    font_family_match = re.search(r'(Inter|Helvetica|Arial|Georgia|Times|Menlo|Monaco|sans-serif|serif|monospace)', text, re.IGNORECASE)
    if font_family_match:
        result["font_family"] = font_family_match.group(1).lower().capitalize()
    weight_match = re.search(r'(bold|semibold|medium|regular|light|thin|700|600|500|400|300|100)', text, re.IGNORECASE)
    if weight_match:
        w = weight_match.group(1).lower()
        weight_map = {"bold": "700", "semibold": "600", "medium": "500", "regular": "400", "light": "300", "thin": "100"}
        result["font_weight"] = weight_map.get(w, w)
    lh_match = re.search(r'lh[:\s]*(\d+)\s*px', text, re.IGNORECASE)
    if lh_match:
        result["line_height"] = int(lh_match.group(1))
    elif result["font_size"]:
        result["line_height"] = int(result["font_size"] * 1.5)
    return result

def _parse_colors(text: str) -> Dict[str, str]:
    """Parse color specifications"""
    result = {"background": None, "text": None, "border": None, "primary": None}
    hex_pattern = r'#[0-9a-fA-F]{3,8}'
    hex_matches = re.findall(hex_pattern, text)
    color_labels = ["bg", "background", "text", "border", "primary", "accent", "color"]
    for i, label in enumerate(color_labels):
        pattern = rf'{label}[:\s]*({hex_pattern})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["background" if "bg" in label or "background" in label else
                   "text" if "text" in label else
                   "border" if "border" in label else
                   "primary"] = match.group(1)
    if not any(result.values()) and hex_matches:
        for i, hex_val in enumerate(hex_matches):
            keys = ["background", "text", "border", "primary"]
            if i < len(keys):
                result[keys[i]] = hex_val
    return result

def _parse_states(text: str) -> List[str]:
    """Parse state descriptions"""
    states = []
    state_keywords = ["hover", "active", "disabled", "focus", "visited", "pressed"]
    for s in state_keywords:
        if re.search(rf'\b{s}\b', text, re.IGNORECASE):
            states.append(s)
    return states

def _parse_responsive_behavior(text: str) -> List[Dict[str, Any]]:
    """Parse responsive behavior descriptions"""
    behaviors = []
    bp_patterns = [
        (r'(mobile|phone|small)[^.]*?(?:full width|stack|single|column)', "Mobile", "stacked"),
        (r'(tablet|medium)[^.]*?(\d)[-\s]*column', "Tablet", "multi-column"),
        (r'(desktop|large|wide)[^.]*?(\d)[-\s]*column', "Desktop", "multi-column"),
    ]
    for pattern, bp, behavior in bp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            behaviors.append({"breakpoint": bp, "layout": behavior})
    if not behaviors:
        if re.search(r'responsive|adaptive|mobile[- ]?first|breakpoint', text, re.IGNORECASE):
            behaviors = [
                {"breakpoint": "Mobile", "layout": "single column, full width"},
                {"breakpoint": "Tablet", "layout": "2-column grid"},
                {"breakpoint": "Desktop", "layout": "3-column grid"}
            ]
    return behaviors

def _parse_component_block(block: str) -> Dict[str, Any]:
    """Parse a single component block into structured data"""
    component = {
        "name": "Unnamed Component",
        "type": "Generic",
        "dimensions": {"width": None, "height": None},
        "typography": {"font_family": None, "font_size": None, "font_weight": None, "line_height": None},
        "colors": {"background": None, "text": None, "border": None, "primary": None},
        "spacing": {"padding": None, "margin": None},
        "states": [],
        "responsive_behavior": [],
        "content": ""
    }
    
    # Extract name
    name_match = re.search(r'Name[:\s]+([^\n]+)', block, re.IGNORECASE)
    if name_match:
        component["name"] = name_match.group(1).strip()
    
    # Extract type
    type_match = re.search(r'Type[:\s]+([^\n]+)', block, re.IGNORECASE)
    if type_match:
        component["type"] = type_match.group(1).strip()
    
    # Extract content
    content_match = re.search(r'(?:Text|Content|Label)[:\s]+([^\n]+)', block, re.IGNORECASE)
    if content_match:
        component["content"] = content_match.group(1).strip()
    
    # Parse all properties
    component["dimensions"] = _parse_dimensions(block)
    component["typography"] = _parse_typography(block)
    component["colors"] = _parse_colors(block)
    component["states"] = _parse_states(block)
    component["responsive_behavior"] = _parse_responsive_behavior(block)
    
    # Parse spacing
    spacing_match = re.search(r'(?:padding|margin)[:\s]*(\d+)', block, re.IGNORECASE)
    if spacing_match:
        key = "padding" if "padding" in block.lower() else "margin"
        component["spacing"][key] = int(spacing_match.group(1))
    
    return component

def _parse_input(text: str) -> List[Dict[str, Any]]:
    """Parse the full input text into a list of component dictionaries"""
    components = []
    
    # Split by component markers or double newlines
    blocks = re.split(r'(?:^|\n)(?=//\s*Component:|\*\*|##|—)', text, flags=re.MULTILINE)
    
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue
        
        component = _parse_component_block(block)
        if component["dimensions"]["width"] or component["colors"]["background"] or component["typography"]["font_family"]:
            components.append(component)
    
    return components

def _generate_component_html(comp: Dict[str, Any], index: int) -> str:
    """Generate HTML for a single component preview"""
    name_id = f"comp-{index}"
    font_family = comp["typography"].get("font_family") or "-apple-system, sans-serif"
    font_size = comp["typography"].get("font_size") or 14
    font_weight = comp["typography"].get("font_weight") or "400"
    line_height = comp["typography"].get("line_height") or 20
    
    bg_color = comp["colors"].get("background") or "#f8f9fa"
    text_color = comp["colors"].get("text") or "#1a1a1a"
    border_color = comp["colors"].get("border") or "transparent"
    primary_color = comp["colors"].get("primary") or "#0066ff"
    
    width = comp["dimensions"].get("width") or 300
    height = comp["dimensions"].get("height") or 48
    
    padding = comp["spacing"].get("padding") or 12
    content = comp.get("content") or comp["name"]
    
    states_html = ""
    if comp["states"]:
        states_html = '<div class="states-row">\n'
        for state in comp["states"]:
            state_display = state.capitalize()
            states_html += f'<span class="state-badge state-{state}">{state_display}</span>\n'
        states_html += '</div>\n'
    
    responsive_html = ""
    if comp["responsive_behavior"]:
        responsive_html = '<div class="responsive-section">\n'
        responsive_html += '<div class="responsive-header">Responsive Behavior</div>\n'
        responsive_html += '<div class="breakpoint-toggles">\n'
        for bp_idx, bp in enumerate(comp["responsive_behavior"]):
            active = "active" if bp_idx == 0 else ""
            responsive_html += f'<button class="bp-toggle {active}" data-comp="{name_id}" data-bp="{bp_idx}">{bp["breakpoint"]}</button>\n'
        responsive_html += '</div>\n'
        for bp_idx, bp in enumerate(comp["responsive_behavior"]):
            shown = "shown" if bp_idx == 0 else "hidden"
            responsive_html += f'<div class="bp-preview {shown}" data-comp="{name_id}" data-bp="{bp_idx}">\n'
            responsive_html += f'<div class="bp-label">{bp["breakpoint"]} → {bp["layout"]}</div>\n'
            responsive_html += f'<div class="bp-visual" style="width:100%;height:40px;background:{bg_color};border:1px dashed {primary_color};border-radius:4px;"></div>\n'
            responsive_html += '</div>\n'
        responsive_html += '</div>\n'
    
    # Color swatches
    colors_html = '<div class="color-swatches">\n'
    color_keys = {"background": "BG", "text": "Text", "border": "Border", "primary": "Primary"}
    for key, label in color_keys.items():
        val = comp["colors"].get(key)
        if val:
            colors_html += f'<div class="swatch-row"><div class="swatch" style="background:{val};width:20px;height:20px;border-radius:3px;border:1px solid rgba(0,0,0,0.1);flex-shrink:0;"></div><span class="swatch-label">{label}: <code>{val}</code></span></div>\n'
    colors_html += '</div>\n'
    
    # Typography details
    ty_html = '<div class="typo-details">\n'
    if comp["typography"]["font_family"]:
        ty_html += f'<div><span class="detail-label">Font:</span> {comp["typography"]["font_family"]}</div>\n'
    if comp["typography"]["font_size"]:
        ty_html += f'<div><span class="detail-label">Size:</span> {comp["typography"]["font_size"]}px</div>\n'
    if comp["typography"]["font_weight"]:
        ty_html += f'<div><span class="detail-label">Weight:</span> {comp["typography"]["font_weight"]}</div>\n'
    if comp["typography"]["line_height"]:
        ty_html += f'<div><span class="detail-label">Line Height:</span> {comp["typography"]["line_height"]}px</div>\n'
    ty_html += '</div>\n'
    
    dimensions_html = f'<div class="dimensions">{width}×{height} px</div>\n'
    
    return f'''
    <div class="component-card" id="{name_id}" data-index="{index}">
      <div class="card-header">
        <h2 class="component-name">{html.escape(comp["name"])}</h2>
        <span class="component-type">{html.escape(comp["type"])}</span>
      </div>
      <div class="card-body">
        <div class="preview-section">
          <div class="component-preview" style="width:{width}px;height:{height}px;background:{bg_color};color:{text_color};font-family:{font_family};font-size:{font_size}px;font-weight:{font_weight};line-height:{line_height}px;border:1px solid {border_color};border-radius:6px;display:flex;align-items:center;justify-content:center;padding:{padding}px;transition:all 0.3s ease;">
            {html.escape(content[:50])}
          </div>
          {dimensions_html}
        </div>
        <div class="details-section">
          {ty_html}
          {colors_html}
          {states_html}
        </div>
        {responsive_html}
      </div>
    </div>
    '''

def process(text: str) -> str:
    """Main entry point - transforms design notes into interactive HTML blueprint"""
    
    # Validate input
    if not text or len(text.strip()) < 10:
        return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Handoff Blueprint Generator</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,sans-serif; background:#faf9f7; color:#1a1a1a; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.container { max-width:640px; padding:40px 24px; text-align:center; }
h1 { font-size:28px; font-weight:600; margin-bottom:12px; color:#1a1a1a; }
p { font-size:16px; line-height:1.7; color:#666; margin-bottom:24px; }
.example { background:#f0edea; padding:20px 24px; border-radius:8px; text-align:left; font-size:14px; line-height:1.6; margin-top:24px; }
.example code { display:block; white-space:pre-wrap; font-family:Menlo,monospace; font-size:13px; }
</style>
</head>
<body>
<div class="container">
  <h1>Handoff Blueprint Generator</h1>
  <p>Please provide at least 10 characters of component description to generate a design blueprint.</p>
  <div class="example">
    <strong>Example input:</strong>
    <code>// Component: Primary Button
Name: primaryButton
Type: button
Dimensions: 320x48
Typography: 16px Inter bold, lh 24px
Colors: background: #0066ff, text: #ffffff
States: hover, active, disabled
Responsive: full width on mobile, 2-column grid on tablet</code>
  </div>
</div>
</body>
</html>"""
    
    components = _parse_input(text)
    
    if not components:
        return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Handoff Blueprint Generator</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,sans-serif; background:#faf9f7; color:#1a1a1a; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.container { max-width:640px; padding:40px 24px; text-align:center; }
h1 { font-size:28px; font-weight:600; margin-bottom:12px; color:#1a1a1a; }
p { font-size:16px; line-height:1.7; color:#666; }
</style>
</head>
<body>
<div class="container">
  <h1>No Components Found</h1>
  <p>Could not parse any design components from your input. Please