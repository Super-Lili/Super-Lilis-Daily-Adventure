"""
Requirements:
- Python 3.8+
- No external dependencies (standard library only: xml.etree.ElementTree, xml.dom.minidom, sys, argparse)
"""
import argparse
import sys
import xml.etree.ElementTree as ET
import xml.dom.minidom
from typing import Dict

# Target attribute-value pairs to remove from <g> elements
TARGET_ATTRS: Dict[str, str] = {
    'fill': 'none',
    'stroke': 'none',
    'opacity': '0',
    'visibility': 'hidden',
    'display': 'none'
}

def _pretty_svg(svg_string: str) -> str:
    """Reformat SVG string to multiple lines using minidom, stripping XML declaration."""
    if not svg_string.strip():
        return ""
    dom = xml.dom.minidom.parseString(svg_string)
    raw = dom.toprettyxml(indent="  ")
    # Remove the XML declaration line if present
    if raw.startswith('<?xml'):
        parts = raw.split('\n', 1)
        return parts[1] if len(parts) > 1 else raw
    return raw

def process(text: str) -> str:
    """Remove problematic fill/stroke/opacity/visibility/display attributes from <g> tags only."""
    if not text.strip():
        return ""  # empty input -> empty output

    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"Invalid SVG XML: {e}")

    # Iterate over <g> elements only (step 3 of spec)
    for elem in root.iter('g'):
        for attr, target_val in TARGET_ATTRS.items():
            current_val = elem.attrib.get(attr)
            if current_val is not None and current_val.lower() == target_val.lower():
                del elem.attrib[attr]

    # Serialize to string (step 5)
    cleaned_flat = ET.tostring(root, encoding='unicode')
    # Pretty-print to ensure multi-line output (required for structured output)
    pretty = _pretty_svg(cleaned_flat)
    return pretty

def _cli_main() -> None:
    parser = argparse.ArgumentParser(
        description="SVG Path Purifier – Remove animation-hostile attributes from <g> elements."
    )
    parser.add_argument(
        'input',
        help="Input SVG file (use '-' to read from stdin)"
    )
    parser.add_argument(
        '-o', '--output', dest='output', default=None,
        help="Output SVG file (writes to stdout if omitted)"
    )
    args = parser.parse_args()

    # Read input
    if args.input == '-':
        raw_svg = sys.stdin.read()
    else:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                raw_svg = f.read()
        except FileNotFoundError:
            sys.stderr.write(f"Error: File not found: {args.input}\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write(f"Error reading {args.input}: {e}\n")
            sys.exit(1)

    # Process
    try:
        result = process(raw_svg)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        sys.exit(1)

    # Write output
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            sys.stderr.write(f"Output written to {args.output}\n")
        except Exception as e:
            sys.stderr.write(f"Error writing {args.output}: {e}\n")
            sys.exit(1)
    else:
        sys.stdout.write(result)

# In-browser execution hook + normal CLI guard
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()