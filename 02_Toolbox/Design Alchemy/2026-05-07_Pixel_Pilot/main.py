import re


def analyze_image_info_text(text: str) -> str:
    """Parse image metadata from text description and give upload advice."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    size_mb = None
    fmt = None
    width = height = None
    allowed_formats = ['jpeg', 'jpg', 'png', 'gif', 'webp']

    for line in lines:
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:mb|megabyte)', line, re.IGNORECASE)
        if m:
            size_mb = float(m.group(1))
        m = re.search(r'\b(jpe?g|png|gif|webp|bmp|tiff?|svg)\b', line, re.IGNORECASE)
        if m:
            fmt = m.group(1).lower()
        m = re.search(r'(\d+)\s*[x×]\s*(\d+)', line, re.IGNORECASE)
        if m:
            width, height = int(m.group(1)), int(m.group(2))

    out = ["## Pixel Pilot Diagnostic Report", ""]
    if size_mb is not None:
        if size_mb <= 10:
            out.append(f"- File size: {size_mb:.2f} MB — within the 10 MB limit.")
        else:
            out.append(f"- File size: {size_mb:.2f} MB — EXCEEDS 10 MB limit. Consider compressing or resizing.")
    else:
        out.append("- File size: not detected in input.")
    if fmt:
        if fmt in allowed_formats:
            out.append(f"- Format: {fmt} — allowed for web upload.")
        else:
            out.append(f"- Format: {fmt} — not in recommended list ({', '.join(allowed_formats)}). Consider converting.")
    else:
        out.append("- Format: not detected in input.")
    if width and height:
        mp = (width * height) / 1_000_000
        out.append(f"- Dimensions: {width}x{height} px ({mp:.1f} megapixels).")
        if width > 4000 or height > 4000:
            out.append("  Warning: very large dimensions — resize for faster uploads.")
    else:
        out.append("- Dimensions: not detected in input.")
    out += ["", "Tip: For web use, JPEG/PNG under 2 MB at 1920px wide is ideal."]
    return "\n".join(out)


def process(text: str = "") -> str:
    """Analyze image metadata from text description for web upload readiness."""
    if not text.strip():
        return (
            "Paste image info (filename, size in MB, format, dimensions) to get upload advice.\n\n"
            "Example:\n  photo.jpg, 3.2 MB, JPEG, 4000x3000"
        )
    return analyze_image_info_text(text)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(process("portrait.png, 12.5 MB, PNG, 6000x4000"))