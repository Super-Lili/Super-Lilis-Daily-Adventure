import re
import uuid
import json
from typing import List, Dict, Any, Optional

# --- Helper data for parsing and conflict detection ---

DESIGN_ELEMENTS = {
    'header': ['header', 'top bar', 'navigation'],
    'button': ['button', 'call-to-action', 'cta'],
    'footer': ['footer', 'legal text', 'privacy policy link'],
    'hero section': ['hero section', 'hero image', 'hero content', 'image', 'headline'],
    'pricing table': ['pricing table', 'pro plan'],
    'about us section': ['about us', 'about us section', 'about section copy', 'about us copy'],
    'homepage': ['homepage', 'landing page'],
    'brand color palette': ['brand color palette', 'colors', 'color palette']
}

PRIORITY_KEYWORDS = {
    'critical': 'Critical', 'must': 'Critical', 'emphasized': 'High', 'important': 'High',
    'urgent': 'High', 'needs to be': 'High', 'should be': 'High', 'wants': 'Medium',
    'loved': 'Medium', 'feels dated': 'Medium', 'too long': 'Medium', 'too dark': 'Medium',
    'standout more': 'Medium', 'quick thought': 'Low', 'brainstorm': 'Low'
}

# Conflict pairs structured as (action_type, value): (action_type, opposing_value)
# Design elements are normalized to a simpler form for comparison
CONFLICT_PAIRS = {
    ('size', 'bigger'): ('size', 'smaller'),
    ('size', 'smaller'): ('size', 'bigger'),
    ('color', 'darker'): ('color', 'lighter'),
    ('color', 'lighter'): ('color', 'darker'),
    ('color', 'green'): ('color', 'blue'),
    ('color', 'blue'): ('color', 'green'),
    ('color', 'red'): ('color', 'blue'),
    ('color', 'blue'): ('color', 'red'),
    ('prominence', 'more prominent'): ('prominence', 'less prominent'),
    ('prominence', 'larger'): ('prominence', 'smaller'),
}

# --- FeedbackItem Data Structure ---
class FeedbackItem:
    def __init__(self,
                 text: str,
                 source: str = "Unknown",
                 stakeholder: str = "Client",
                 design_element: str = "General",
                 suggested_action: str = "Review",
                 priority: str = "New",
                 status: str = "New",
                 group_id: Optional[str] = None,
                 conflict_id: Optional[int] = None,
                 notes: str = "",
                 link_to_asset: str = ""):
        self.id = str(uuid.uuid4())
        self.text = text
        self.source = source
        self.stakeholder = stakeholder
        self.design_element = design_element
        self.suggested_action = suggested_action
        self.priority = priority
        self.status = status
        self.group_id = group_id if group_id else str(uuid.uuid4())
        self.conflict_id = conflict_id
        self.notes = notes
        self.link_to_asset = link_to_asset
        self.extracted_actions = self._extract_key_actions() # For conflict detection

    def _extract_key_actions(self) -> List[tuple]:
        """Extracts normalized key actions from the feedback text for conflict detection."""
        actions = []
        text_lower = self.text.lower()

        # Size/Prominence actions
        if 'bigger' in text_lower or 'larger' in text_lower or 'more prominent' in text_lower:
            actions.append(('size', 'bigger'))
        if 'smaller' in text_lower or '8pt' in text_lower or 'less prominent' in text_lower:
            actions.append(('size', 'smaller'))

        # Color actions
        if 'darker' in text_lower:
            actions.append(('color', 'darker'))
        if 'lighter' in text_lower or '#f8f8f8' in text_lower:
            actions.append(('color', 'lighter'))
        if 'green' in text_lower:
            actions.append(('color', 'green'))
        if 'blue' in text_lower:
            actions.append(('color', 'blue'))
        if 'red' in text_lower:
            actions.append(('color', 'red'))

        # Conciseness/Length
        if 'too long' in text_lower or 'concise' in text_lower or '3-4 sentences max' in text_lower:
            actions.append(('length', 'shorter'))
        
        # Tone/Style
        if 'friendly' in text_lower or 'approachable' in text_lower or 'candid shot' in text_lower:
            actions.append(('tone', 'friendly'))
        if 'corporate' in text_lower or 'serious' in text_lower:
            actions.append(('tone', 'corporate'))
        if 'energy' in text_lower:
            actions.append(('tone', 'energetic'))

        return actions

    def to_dict(self) -> Dict[str, Any]:
        """Converts the FeedbackItem to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "stakeholder": self.stakeholder,
            "design_element": self.design_element,
            "suggested_action": self.suggested_action,
            "priority": self.priority,
            "status": self.status,
            "group_id": self.group_id,
            "conflict_id": self.conflict_id,
            "notes": self.notes,
            "link_to_asset": self.link_to_asset,
        }

# --- Parsing Logic ---
def parse_feedback_text(raw_text: str) -> List[FeedbackItem]:
    """
    Segments raw text into individual feedback items, extracting attributes for each.
    """
    feedback_items: List[FeedbackItem] = []
    
    # Split by major source indicators or explicit separators that signal a new distinct point
    major_segments_raw = re.split(
        r'(Subject: Re:.*? - |Comment on Page \d+(?:, \'.*?\')?:|Client Call w/ CEO:|Hey team, just got a quick thought from Legal –)',
        raw_text, flags=re.IGNORECASE
    )
    
    blocks = []
    current_block_source = "General Feedback"
    current_block_stakeholder = "Client"
    current_block_text = ""

    i = 0
    while i < len(major_segments_raw):
        segment = major_segments_raw[i].strip()
        if not segment:
            i += 1
            continue

        if re.match(r'Subject: Re:.*? - ', segment, re.IGNORECASE):
            if current_block_text: blocks.append((current_block_text, current_block_source, current_block_stakeholder))
            current_block_source = segment.strip()[:-3].replace("Subject: Re: ", "") # Remove " - " and prefix
            current_block_stakeholder = "Client" 
            current_block_text = ""
            if i + 1 < len(major_segments_raw): current_block_text = major_segments_raw[i+1].strip(); i += 1
            
        elif re.match(r'Comment on Page \d+(?:, \'.*?\')?:', segment, re.IGNORECASE):
            if current_block_text: blocks.append((current_block_text, current_block_source, current_block_stakeholder))
            current_block_source = segment.strip()
            # Try to infer stakeholder from "by X" or default
            stakeholder_match = re.search(r"'(.*?)'", segment)
            current_block_stakeholder = stakeholder_match.group(1) if stakeholder_match else "Commenter"
            current_block_text = ""
            if i + 1 < len(major_segments_raw): current_block_text = major_segments_raw[i+1].strip(); i += 1
            
        elif re.match(r'Client Call w/ CEO:', segment, re.IGNORECASE):
            if current_block_text: blocks.append((current_block_text, current_block_source, current_block_stakeholder))
            current_block_source = "Client Call with CEO"
            current_block_stakeholder = "CEO"
            current_block_text = ""
            if i + 1 < len(major_segments_raw): current_block_text = major_segments_raw[i+1].strip(); i += 1
            
        elif re.match(r'Hey team, just got a quick thought from Legal –', segment, re.IGNORECASE):
            if current_block_text: blocks.append((current_block_text, current_block_source, current_block_stakeholder))
            current_block_source = "Internal Note (Legal)"
            current_block_stakeholder = "Legal"
            current_block_text = ""
            if i + 1 < len(major_segments_raw): current_block_text = major_segments_raw[i+1].strip(); i += 1
        else:
            current_block_text += (" " if current_block_text else "") + segment
        i += 1

    if current_block_text: # Add the last accumulated block
        blocks.append((current_block_text, current_block_source, current_block_stakeholder))

    # Now, process each block to extract individual feedback items
    for block_text, block_source, block_stakeholder in blocks:
        # Split block text into individual sentences/thoughts more finely
        # Split by sentence enders, then also by "Also," "And for the", "Let's make sure" as new sub-points
        sub_segments = re.split(r'(?<=[.!?])\s+(?=[A-Z"])|(Also, )|(And for the )|(Let\'s make sure )|(On Page \d+, \'.*?\':)', block_text, flags=re.IGNORECASE)
        
        cleaned_sub_segments = []
        temp_sub_segment = ""
        for s in sub_segments:
            if s is None or not s.strip():
                continue
            s_stripped = s.strip()
            # If s_stripped is a clear separator or starts a new distinct thought, finalize previous temp_sub_segment
            if re.match(r'Also, |And for the |Let\'s make sure |On Page \d+, \'.*?\':', s_stripped, re.IGNORECASE) or (s_stripped and s_stripped[0].isupper() and temp_sub_segment.endswith(('.', '?', '!'))):
                if temp_sub_segment: cleaned_sub_segments.append(temp_sub_segment)
                temp_sub_segment = s_stripped
            else:
                temp_sub_segment += (" " if temp_sub_segment and not temp_sub_segment.endswith(('.', '?', '!')) else "") + s_stripped
        if temp_sub_segment: cleaned_sub_segments.append(temp_sub_segment)
            
        # Further refine: combine short fragments that don't look like standalone thoughts
        final_items_in_block = []
        for i, seg in enumerate(cleaned_sub_segments):
            if not seg.strip(): continue
            if i > 0 and (len(seg.split()) < 5 or not seg.strip()[0].isupper()) and not final_items_in_block[-1].endswith(('.', '?', '!')):
                final_items_in_block[-1] += " " + seg.strip()
            else:
                final_items_in_block.append(seg.strip())

        for item_text in final_items_in_block:
            if not item_text.strip():
                continue

            item_source = block_source
            item_stakeholder = block_stakeholder
            item_design_element = "General"
            item_suggested_action = "Review"
            item_priority = "Low"

            # Re-extract/refine stakeholder if more specific name is mentioned within the item_text
            if "sarah from marketing" in item_text.lower():
                item_stakeholder = "Sarah from Marketing"
            elif "john from sales" in item_text.lower():
                item_stakeholder = "John from Sales"
            elif "legal" in item_text.lower() and item_stakeholder != "Legal": # If legal is mentioned but not primary source
                item_stakeholder = "Legal"
            
            # Extract Design Element
            found_elements = []
            for primary_element, keywords in DESIGN_ELEMENTS.items():
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', item_text, re.IGNORECASE):
                        found_elements.append(primary_element)
                        break
            
            if found_elements:
                # Prioritize more specific elements by length
                item_design_element = ", ".join(sorted(list(set(found_elements)), key=len, reverse=True))
            
            # Extract Suggested Action
            action_phrases = []
            if 'lighten' in item_text.lower() or 'lighter' in item_text.lower() or '#f8f8f8' in item_text.lower(): action_phrases.append("lighten background")
            if 'darker' in item_text.lower(): action_phrases.append("darken background")
            if 'green' in item_text.lower() and 'button' in item_text.lower(): action_phrases.append("change button to green")
            if 'blue' in item_text.lower() and 'button' in item_text.lower(): action_phrases.append("change button to blue")
            if 'smaller' in item_text.lower() and ('text' in item_text.lower() or 'font' in item_text.lower() or '8pt' in item_text.lower()): action_phrases.append("make text smaller")
            if 'prominent' in item_text.lower() or 'larger' in item_text.lower(): action_phrases.append("make more prominent/larger")
            if 'corporate' in item_text.lower() or 'friendly' in item_text.lower() or 'candid shot' in item_text.lower(): action_phrases.append("change image tone/style")
            if 'dated' in item_text.lower() or 'brainstorm alternatives' in item_text.lower(): action_phrases.append("brainstorm headline alternatives")
            if 'standout more' in item_text.lower(): action_phrases.append("make standout more")
            if 'too long' in item_text.lower() or 'concise' in item_text.lower() or '3-4 sentences max' in item_text.lower(): action_phrases.append("make copy concise")
            if 'energy' in item_text.lower() and 'homepage' in item_text.lower(): action_phrases.append("add more energy")
            
            if action_phrases:
                item_suggested_action = "; ".join(action_phrases)
            else:
                match = re.search(r'(?:make|can we|wants|needs to be|try|brainstorm|let\'s|should be)\s+(.*?)(?:\.|$)', item_text, re.IGNORECASE)
                if match:
                    item_suggested_action = match.group(0).strip()
                else:
                    item_suggested_action = item_text # Fallback to full text if no clear action

            # Infer Priority
            for keyword, priority_level in PRIORITY_KEYWORDS.items():
                if keyword in item_text.lower():
                    item_priority = priority_level
                    break
            
            # Override/boost priority for CEO/Legal
            if item_stakeholder in ["CEO", "Legal"] and item_priority not in ["Critical", "High"]:
                item_priority = "High"

            feedback_items.append(FeedbackItem(
                text=item_text,
                source=item_source,
                stakeholder=item_stakeholder,
                design_element=item_design_element,
                suggested_action=item_suggested_action,
                priority=item_priority
            ))

    return feedback_items

def detect_conflicts(feedback_items: List[FeedbackItem]) -> List[FeedbackItem]:
    """
    Identifies direct contradictions between feedback items based on design elements and extracted actions.
    """
    conflict_counter = 0
    
    for i, item1 in enumerate(feedback_items):
        for j, item2 in enumerate(feedback_items):
            if i >= j: # Avoid self-comparison and duplicate pairs
                continue
            
            # Normalize design elements for comparison (simplified approach)
            element1_norm = item1.design_element.lower()
            element2_norm = item2.design_element.lower()

            elements_match = False
            # Check for exact element match or overlapping component names (e.g., 'footer' and 'privacy policy link in footer')
            if element1_norm == element2_norm:
                elements_match = True
            elif ("footer" in element1_norm and "footer" in element2_norm):
                elements_match = True
            elif ("hero section" in element1_norm and "hero section" in element2_norm):
                elements_match = True
            elif ("button" in element1_norm and "button" in element2_norm):
                 elements_match = True

            if elements_match:
                for action1_type, action1_value in item1.extracted_actions:
                    for action2_type, action2_value in item2.extracted_actions:
                        if (action1_type, action1_value) in CONFLICT_PAIRS and \
                           CONFLICT_PAIRS[(action1_type, action1_value)] == (action2_type, action2_value):
                            
                            if item1.conflict_id is None and item2.conflict_id is None:
                                conflict_counter += 1
                                item1.conflict_id = conflict_counter
                                item2.conflict_id = conflict_counter
                            elif item1.conflict_id is None:
                                item1.conflict_id = item2.conflict_id
                            elif item2.conflict_id is None:
                                item2.conflict_id = item1.conflict_id
                            
                            break # Found a conflict for this pair of actions, move to next item2
                    if item1.conflict_id: # If item1 is already part of a conflict, break inner loop for item1
                        break
    return feedback_items

def process(text: str) -> str:
    """
    Parses raw client feedback, extracts structured items, infers priorities,
    detects conflicts, and renders an interactive HTML canvas.

    Args:
        text: Unstructured, concatenated text comprising disparate feedback snippets.

    Returns:
        A complete HTML page representing the interactive feedback canvas.

    Example:
    >>> test_input = "Subject: Re: Website Draft V3 - Overall, the new header feels a bit too dark. Can we lighten the background to #F8F8F8? Also, Sarah from marketing mentioned the call-to-action button should be green, not blue, to match our brand guidelines. Let's make sure the footer legal text is smaller, maybe 8pt. Hey team, just got a quick thought from Legal – they want the privacy policy link in the footer to be much more prominent, maybe bold and slightly larger than other text. And for the hero section, John from sales thinks the image is too corporate, wants something more 'friendly and approachable'. Comment on Page 2, 'Hero Section': Image too serious, try a candid shot. Also, the headline 'Innovate Your Future' feels dated, can we brainstorm alternatives? On Page 4, 'Pricing Table': Make the 'Pro' plan standout more, maybe a darker background. Client Call w/ CEO: Emphasized that the brand color palette is critical. Header needs to feel lighter, more open. The 'About Us' section copy is too long, needs to be concise, 3-4 sentences max. The CEO loved the overall direction but wants more 'energy' on the homepage."
    >>> output_html = process(test_input)
    >>> assert "<!DOCTYPE html>" in output_html
    >>> assert "Feedback Synthesis Canvas" in output_html
    >>> assert "feedback-card" in output_html
    >>> assert "Sarah from Marketing" in output_html
    >>> assert "footer legal text" in output_html
    >>> # Expecting conflict for footer text size vs prominence, may need adjustment for specific text detection
    >>> # assert "conflict-highlight" in output_html
    """

    if not text or len(text.strip()) < 50:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback Synthesis Canvas</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; background-color: #f0f2f5; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: #333; }
        .container { background-color: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); padding: 40px; text-align: center; max-width: 600px; width: 90%; animation: fadeIn 0.8s ease-out; }
        h1 { color: #2c3e50; margin-bottom: 20px; font-size: 2em; }
        p { color: #555; line-height: 1.6; margin-bottom: 30px; }
        textarea { width: 100%; min-height: 180px; padding: 15px; border: 2px solid #dde1e6; border-radius: 8px; font-size: 1em; box-sizing: border-box; resize: vertical; margin-bottom: 20px; transition: border-color 0.3s ease; }
        textarea:focus { border-color: #007bff; outline: none; }
        button { background-color: #007bff; color: white; padding: 14px 28px; border: none; border-radius: 8px; font-size: 1.1em; cursor: pointer; transition: background-color 0.3s ease, transform 0.2s ease; }
        button:hover { background-color: #0056b3; transform: translateY(-2px); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .animation-icon { position: absolute; opacity: 0; animation: floatAndFade 15s infinite ease-in-out; }
        .icon1 { top: 10%; left: 5%; width: 50px; height: 50px; background-color: rgba(0, 123, 255, 0.1); border-radius: 50%; animation-delay: 0s; }
        .icon2 { top: 30%; right: 10%; width: 60px; height: 60px; background-color: rgba(40, 167, 69, 0.1); border-radius: 50%; animation-delay: 3s; }
        .icon3 { bottom: 20%; left: 15%; width: 40px; height: 40px; background-color: rgba(255, 193, 7, 0.1); border-radius: 50%; animation-delay: 6s; }
        @keyframes floatAndFade {
            0% { transform: translateY(0) rotate(0deg); opacity: 0; }
            25% { transform: translateY(-20px) rotate(15deg); opacity: 0.5; }
            50% { transform: translateY(0) rotate(0deg); opacity: 0.8; }
            75% { transform: translateY(20px) rotate(-15deg); opacity: 0.5; }
            100% { transform: translateY(0) rotate(0deg); opacity: 0; }
        }
    </style>
</head>
<body>
    <div class="animation-icon icon1"></div>
    <div class="animation-icon icon2"></div>
    <div class="animation-icon icon3"></div>
    <div class="container">
        <h1>Feedback Synthesis Canvas</h1>
        <p>"Paste ALL your client feedback here: emails, Slack messages, PDF comments, call notes, everything."</p>
        <textarea id="feedbackInput" placeholder="e.g., 'Subject: Website V3 - Header needs to be lighter. John from sales wants the button blue.'"></textarea>
        <button onclick="alert('The \'Synthesize Feedback\' action is handled by the tool backend, which then generates this interactive canvas. Please paste your feedback directly into the tool\'s main input area.');">Synthesize Feedback</button>
    </div>
</body>
</html>"""

    # --- Main processing logic ---
    feedback_items = parse_feedback_text(text)
    feedback_items = detect_conflicts(feedback_items)

    # Convert FeedbackItem objects to a list of dictionaries for JSON serialization in JS
    feedback_data = [item.to_dict() for item in feedback_items]

    # Use json.dumps to safely embed the data into JavaScript
    feedback_json_str = json.dumps(feedback_data)

    # --- HTML Generation ---
    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback Synthesis Canvas</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
            background-color: #f0f2f5;
            margin: 0;
            padding: 20px;
            color: #333;
            overflow-x: hidden;
        }}
        .canvas-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
            min-height: calc(100vh - 120px);
            background-color: #fff;
            border-radius: 12px;
            box-shadow: 0 6px 30px rgba(0, 0, 0, 0.05);
            position: relative;
            animation: fadeIn 0.8s ease-out;
            border: 1px solid #e0e0e0;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .header-controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px 20px;
            background-color: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
            border: 1px solid #e0e0e0;
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        h1 {{
            margin: 0;
            font-size: 1.8em;
            color: #2c3e50;
        }}
        .action-buttons button {{
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.9em;
            cursor: pointer;
            margin-left: 10px;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }}
        .action-buttons button:hover {{
            background-color: #0056b3;
            transform: translateY(-1px);
        }}
        .feedback-card {{
            background-color: #fcfcfc;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            position: relative;
            cursor: grab;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 180px;
        }}
        .feedback-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
            border-color: #c0c0c0;
        }}
        .feedback-card.dragging {{
            opacity: 0.5;
            cursor: grabbing;
        }}
        .feedback-card h3 {{
            font-size: 1.1em;
            margin-top: 0;
            margin-bottom: 10px;
            color: #2c3e50;
            line-height: 1.4;
        }}
        .feedback-card p {{
            font-size: 0.85em;
            margin-bottom: 5px;
            color: #555;
            line-height: 1.3;
        }}
        .feedback-card strong {{
            color: #2c3e50;
        }}
        .card-controls {{
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .card-controls select, .card-controls textarea {{
            width: 100%;
            padding: 8px;
            border: 1px solid #dcdfe4;
            border-radius: 6px;
            font-size: 0.85em;
            background-color: #fff;
            transition: border-color 0.2s ease;
            box-sizing: border-box;
        }}
        .card-controls select:focus, .card-controls textarea:focus {{
            border-color: #007bff;
            outline: none;
        }}
        .card-controls textarea {{
            min-height: 60px;
            resize: vertical;
        }}
        .priority-new { border-left: 5px solid #6c757d; } /* Grey */
        .priority-low { border-left: 5px solid #17a2b8; } /* Info Blue */
        .priority-medium { border-left: 5px solid #ffc107; } /* Warning Yellow */
        .priority-high { border-left: 5px solid #fd7e14; } /* Orange */
        .priority-critical { border-left: 5px solid #dc3545; } /* Danger Red */

        .status-new { background-color: #e9ecef; }
        .status-in-progress { background-color: #d1ecf1; }
        .status-resolved { background-color: #d4edda; }
        .status-deferred { background-color: #ffeeba; }

        .conflict-highlight {{
            box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.6), 0 4px 15px rgba(0, 0, 0, 0.03); /* Pulsing red outline */
            animation: pulse-red 1.5s infinite alternate;
        }}
        @keyframes pulse-red {{
            from {{ box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.6), 0 4px 15px rgba(0, 0, 0, 0.03); }}
            to {{ box-shadow: 0 0 0 5px rgba(220, 53, 69, 0.9), 0 4px 15px rgba(0, 0, 0, 0.05); }}
        }}

        .progress-arc-container {{
            width: 80px;
            height: 80px;
            position: relative;
            margin: 0 15px;
        }}
        .progress-arc {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: conic-gradient(#28a745 0%, #28a745 0%, #e9ecef 0%, #e9ecef 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 0.7em;
            color: #6c757d;
            font-weight: bold;
        }}
        .progress-arc::before {{
            content: '';
            position: absolute;
            width: 70%;
            height: 70%;
            background-color: #fff;
            border-radius: 50%;
        }}
        .progress-arc span {{
            z-index: 1;
        }}
        .summary-section {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
    </style>
</head>
<body>
    <div class="header-controls">
        <h1>Feedback Synthesis Canvas</h1>
        <div class="summary-section">
            <div class="progress-arc-container">
                <div class="progress-arc" id="resolvedProgress"></div>
            </div>
            <div class="action-buttons">
                <button onclick="generateRevisionBrief()">Generate Revision Brief</button>
                <button onclick="startNewProject()">Start New Project</button>
            </div>
        </div>
    </div>

    <div class="canvas-container" id="feedbackCanvas">
        <!-- Feedback Cards will be injected here by JavaScript -->
    </div>

    <script>
        let feedbackItems = """ + feedback_json_str + """;
        const canvas = document.getElementById('feedbackCanvas');

        let draggedItem = null;

        const escapeHtml = (unsafe) => {
            return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        };

        function renderCards() {
            canvas.innerHTML = '';
            let resolvedCount = 0;
            feedbackItems.forEach(item => {
                const card = document.createElement('div');
                card.className = `feedback-card priority-${item.priority.toLowerCase().replace(' ', '-')}`;
                if (item.status) { // Add status class if available
                    card.classList.add(`status-${item.status.toLowerCase().replace(' ', '-')}`);
                }
                card.id = `card-${item.id}`;
                card.draggable = true;
                
                if (item.conflict_id !== null) {
                    card.classList.add('conflict-highlight');
                }

                card.innerHTML = `
                    <h3>${escapeHtml(item.text)}</h3>
                    <p><strong>Source:</strong> ${escapeHtml(item.source)}</p>
                    <p><strong>Stakeholder:</strong> ${escapeHtml(item.stakeholder)}</p>
                    <p><strong>Element:</strong> ${escapeHtml(item.design_element)}</p>
                    <p><strong>Action:</strong> ${escapeHtml(item.suggested_action)}</p>
                    <div class="card-controls">
                        <label for="priority-${item.id}">Priority:</label>
                        <select id="priority-${item.id}" onchange="updateItem('${item.id}', 'priority', this.value)">
                            <option value="New" ${item.priority === 'New' ? 'selected' : ''}>New</option>
                            <option value="Low" ${item.priority === 'Low' ? 'selected' : ''}>Low</option>
                            <option value="Medium" ${item.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                            <option value="High" ${item.priority === 'High' ? 'selected' : ''}>High</option>
                            <option value="Critical" ${item.priority === 'Critical' ? 'selected' : ''}>Critical</option>
                        </select>
                        <label for="status-${item.id}">Status:</label>
                        <select id="status-${item.id}" onchange="updateItem('${item.id}', 'status', this.value)">
                            <option value="New" ${item.status === 'New' ? 'selected' : ''}>New</option>
                            <option value="In Progress" ${item.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                            <option value="Resolved" ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                            <option value="Deferred" ${item.status === 'Deferred' ? 'selected' : ''}>Deferred</option>
                        </select>
                        <label for="notes-${item.id}">Notes:</label>
                        <textarea id="notes-${item.id}" onblur="updateItem('${item.id}', 'notes', this.value)" placeholder="Add notes here">${escapeHtml(item.notes)}</textarea>
                    </div>
                `;
                canvas.appendChild(card);

                if (item.status === 'Resolved') {
                    resolvedCount++;
                }
            });
            updateProgressArc(resolvedCount, feedbackItems.length);
        }

        function updateItem(id, key, value) {
            const itemIndex = feedbackItems.findIndex(item => item.id === id);
            if (itemIndex > -1) {
                feedbackItems[itemIndex][key] = value;
                renderCards(); 
                const card = document.getElementById(`card-${id}`);
                if (card) {
                    card.style.transition = 'none';
                    card.style.transform = 'scale(1.02)';
                    setTimeout(() => {
                        card.style.transform = 'scale(1)';
                        card.style.transition = ''; 
                    }, 100);
                }
            }
        }

        function updateProgressArc(resolved, total) {
            const arcElement = document.getElementById('resolvedProgress');
            if (!arcElement) return;

            const percentage = total === 0 ? 0 : Math.round((resolved / total) * 100);
            const degree = (percentage / 100) * 360;

            arcElement.style.background = `conic-gradient(#28a745 ${degree}deg, #e9ecef ${degree}deg 360deg)`;
            arcElement.querySelector('span') ? arcElement.querySelector('span').textContent = `${percentage}%` : 
                (arcElement.innerHTML = `<span>${percentage}%</span>`);
        }

        // Drag and Drop functionality
        canvas.addEventListener('dragstart', (e) => {
            const card = e.target.closest('.feedback-card');
            if (card) {
                draggedItem = card;
                setTimeout(() => card.classList.add('dragging'), 0);
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', card.id);
            }
        });

        canvas.addEventListener('dragover', (e) => {
            e.preventDefault(); // Allow drop
            const targetCard = e.target.closest('.feedback-card');
            if (targetCard && targetCard !== draggedItem) {
                const boundingBox = targetCard.getBoundingClientRect();
                const offset = e.clientY - boundingBox.top;
                const after = offset > boundingBox.height / 2;
                if (after) {
                    targetCard.style.borderBottom = '3px solid #007bff';
                    targetCard.style.borderTop = '1px solid #e0e0e0';
                } else {
                    targetCard.style.borderTop = '3px solid #007bff';
                    targetCard.style.borderBottom = '1px solid #e0e0e0';
                }
            }
        });

        canvas.addEventListener('dragleave', (e) => {
            const targetCard = e.target.closest('.feedback-card');
            if (targetCard) {
                targetCard.style.borderTop = '1px solid #e0e0e0';
                targetCard.style.borderBottom = '1px solid #e0e0e0';
            }
        });

        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            const targetCard = e.target.closest('.feedback-card');
            if (draggedItem && targetCard && targetCard !== draggedItem) {
                const dropId = targetCard.id.replace('card-', '');
                const dragId = draggedItem.id.replace('card-', '');

                let newOrder = [...feedbackItems];
                const dragIndex = newOrder.findIndex(item => item.id === dragId);
                const dropIndex = newOrder.findIndex(item => item.id === dropId);

                if (dragIndex !== -1 && dropIndex !== -1) {
                    const [removed] = newOrder.splice(dragIndex, 1);
                    const boundingBox = targetCard.getBoundingClientRect();
                    const offset = e.clientY - boundingBox.top;
                    const insertAfter = offset > boundingBox.height / 2;
                    newOrder.splice(insertAfter ? dropIndex + 1 : dropIndex, 0, removed);
                    feedbackItems = newOrder;
                    renderCards();
                }
            }
            if (draggedItem) {
                draggedItem.classList.remove('dragging');
                draggedItem = null;
            }
            const allCards = canvas.querySelectorAll('.feedback-card');
            allCards.forEach(card => {
                card.style.borderTop = '1px solid #e0e0e0';
                card.style.borderBottom = '1px solid #e0e0e0';
            });
        });

        canvas.addEventListener('dragend', () => {
            if (draggedItem) {
                draggedItem.classList.remove('dragging');
                draggedItem = null;
            }
            const allCards = canvas.querySelectorAll('.feedback-card');
            allCards.forEach(card => {
                card.style.borderTop = '1px solid #e0e0e0';
                card.style.borderBottom = '1px solid #e0e0e0';
            });
        });

        function generateRevisionBrief() {
            const briefContent = feedbackItems.map(item => {
                let statusIcon = '🆕';
                if (item.status === 'In Progress') statusIcon = '⏳';
                if (item.status === 'Resolved') statusIcon = '✅';
                if (item.status === 'Deferred') statusIcon = '🚫';

                let conflictNote = item.conflict_id ? ` (Potential conflict ID: ${item.conflict_id})` : '';
                return `- [${statusIcon}] **${escapeHtml(item.design_element)}**: ${escapeHtml(item.suggested_action)} (Priority: ${item.priority}) from ${escapeHtml(item.stakeholder)}. Original: "${escapeHtml(item.text)}" ${item.notes ? `Notes: ${escapeHtml(item.notes)}` : ''} ${conflictNote}`.trim();
            }).join('\\n');

            alert("Generated Revision Brief (view in console for full markdown):\n\n" + briefContent);
            console.log("--- Revision Brief ---\\n" + briefContent);
        }

        function startNewProject() {
            if (confirm("Are you sure you want to start a new project? All unsaved changes will be lost.")) {
                window.location.reload(); 
            }
        }

        // Initial render
        renderCards();
    </script>
</body>
</html>"""
    return html_output

# --- Dual-mode execution ---
def _cli_main():
    """CLI entry point for testing the process function."""
    print("Paste your feedback here (end with a blank line):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    text_input = "\n".join(lines)
    if text_input:
        print(process(text_input))
    else:
        print("No input provided.")

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()