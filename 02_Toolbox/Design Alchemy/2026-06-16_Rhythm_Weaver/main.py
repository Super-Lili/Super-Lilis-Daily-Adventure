import json
import math
from typing import List, Dict, Any, Literal

# --- Configuration Constants ---
# These factors are approximations for a generic sans-serif font like Inter.
# In a real tool, these would come from font metric files or be user-defined presets.
AVG_CHAR_WIDTH_FACTOR = 0.6  # Average character width relative to font_size (e.g., for 'Inter')
DEFAULT_WORD_SPACE_EM = 0.25 # Default space width relative to font_size
MIN_CHARS_FOR_ANALYSIS = 50  # Minimum characters required for meaningful analysis

# --- Analysis Thresholds (can be tuned for sensitivity) ---
RAG_DEVIATION_THRESHOLD_PX = 10 # Pixels of deviation for raggedness to be flagged
VERTICAL_RHYTHM_DEVIATION_THRESHOLD_PX = 2 # Pixels deviation from baseline grid to be flagged
WHITESPACE_RIVER_GAP_FACTOR = 1.8 # Word gap must be this many times the default to be considered for a river
WHITESPACE_RIVER_ALIGNMENT_TOLERANCE_PX = 15 # Max horizontal deviation for gaps to align vertically/diagonally
DENSITY_VARIANCE_THRESHOLD = 0.08 # Max allowed relative standard deviation in character density per line

class TextLayoutSimulator:
    """
    Simulates text layout to determine word positions, line breaks, and spacing.
    This is a simplified model, as precise typographic layout requires a full rendering engine.
    """
    def __init__(self, input_params: Dict[str, Any]):
        self.text_content: str = input_params["text_content"]
        self.font_family: str = input_params["font_family"]
        self.font_size_px: float = input_params["font_size_px"]
        self.line_height_multiplier: float = input_params["line_height_multiplier"]
        self.letter_spacing_em: float = input_params["letter_spacing_em"]
        self.container_width_px: float = input_params["container_width_px"]
        self.text_align: Literal["left", "justify", "center", "right"] = input_params["text_align"]

        # Calculated layout metrics
        self.avg_char_width_px = self.font_size_px * AVG_CHAR_WIDTH_FACTOR
        self.letter_spacing_px = self.font_size_px * self.letter_spacing_em
        self.default_word_space_px = self.font_size_px * DEFAULT_WORD_SPACE_EM
        self.line_height_px = self.font_size_px * self.line_height_multiplier

        self.lines: List[Dict[str, Any]] = [] # Stores detailed data for each laid-out line
        self