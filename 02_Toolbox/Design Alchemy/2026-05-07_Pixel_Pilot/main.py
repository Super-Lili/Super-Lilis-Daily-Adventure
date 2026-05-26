import os


def pixel_pilot_local(file_path, max_size_mb=10, allowed_formats=None):
    """
    Diagnoses a local image file for common web upload issues like excessive size or unsupported format.
    Requires Pillow (PIL) to be installed.
    """
    if allowed_formats is None:
        allowed_formats = ['jpeg', 'png', 'gif', 'webp']

    from PIL import Image

    results = {
        'file_exists': False,
        'size_ok': False,
        'format_ok': False,
        'diagnostics': []
    }

    if not os.path.exists(file_path):
        results['diagnostics'].append(f"Error: File '{file_path}' does not exist. Please check the file path.")
        return results
    results['file_exists'] = True

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb <= max_size_mb:
        results['size_ok'] = True
        results['diagnostics'].append(f"File size ({file_size_mb:.2f} MB) is within the {max_size_mb} MB limit.")
    else:
        results['diagnostics'].append(f"Warning: File size ({file_size_mb:.2f} MB) exceeds the {max_size_mb} MB limit. Consider compressing or resizing the image.")

    try:
        with Image.open(file_path) as img:
            image_format = img.format.lower()
            if image_format in allowed_formats:
                results['format_ok'] = True
                results['diagnostics'].append(f"Image format ({image_format}) is among the common allowed formats: {', '.join(allowed_formats)}.")
            else:
                results['diagnostics'].append(f"Warning: Image format ({image_format}) is not in the recommended list: {', '.join(allowed_formats)}. Consider converting to a more common format.")
            results['diagnostics'].append(f"Image dimensions: {img.width}x{img.height} pixels.")
    except Exception as e:
        results['diagnostics'].append(f"Error: Could not read image format or dimensions. Ensure '{file_path}' is a valid image file. Details: {e}")

    return results


def process(text: str) -> str:
    """Browser mode: Pixel Pilot needs a local image file and cannot run in the browser."""
    return "This tool processes image files — use it locally with: python3 main.py --help"


def _cli_main():
    # To use this skill, ensure you have the Pillow library installed: pip install Pillow
    # Example usage:
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py <image_path> [max_size_mb]")
        print("Example: python main.py photo.jpg 5")
        return

    file_path = sys.argv[1]
    max_size_mb = float(sys.argv[2]) if len(sys.argv) > 2 else 10

    diagnostic_report = pixel_pilot_local(file_path, max_size_mb=max_size_mb)
    for line in diagnostic_report['diagnostics']:
        print(line)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
