import json
import re
from typing import List, Dict, Any, Tuple

# --- Constants for Brand Voice Analysis ---
INFORMAL_WORDS = {
    "awesome": {"suggestion": "exceptional", "tone": "overly enthusiastic"},
    "cool": {"suggestion": "innovative", "tone": "informal"},
    "super": {"suggestion": "highly", "tone": "informal exaggeration"},
    "amazing": {"suggestion": "remarkable", "tone": "overly enthusiastic"},
    "blow your mind": {"suggestion": "exceed expectations", "tone": "colloquialism"},
    "really excited": {"suggestion": "eager", "tone": "informal intensity"},
    # Add more as needed based on common deviations from a sophisticated tone
}

# Heuristics for tone inference (simplified)
SOPHISTICATED_TONE_WORDS = ["precise", "sophisticated", "authoritative", "meticulous", "strategic", "insightful", "transformative", "pinnacle", "excellence"]

# --- Helper Functions for NLP Simulation ---

def _escape_html(text: str) -> str:
    """Escapes HTML special characters in a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")

def _segment_sentences(text: str) -> List[str]:
    """Segments text into sentences using basic heuristics."""
    # This regex attempts to split sentences while preserving some common exceptions
    # like abbreviations (e.g., Mr. Smith) or decimals (e.g., 3.14).
    # It matches periods, exclamation marks, or question marks that are followed by
    # whitespace and an uppercase letter, or are at the end of the string.
    # For robustness, we handle potential multiple spaces and ensure splits.
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])|\s*(?<=[.!?]$)', text.strip())
    
    # Filter out empty strings and strip whitespace from each sentence
    cleaned_sentences = [s.strip() for s in sentences if s.strip()]
    return cleaned_sentences

def _detect_passive_voice(sentence: str) -> bool:
    """
    A basic heuristic for detecting passive voice.
    Looks for forms of "to be" followed by a past participle.
    This is a simplification and will have false positives/negatives,
    as it doesn't perform full grammatical parsing.
    """
    sentence_lower = sentence.lower()
    
    # Regex for "to be" verb + a word ending in -ed or common irregular past participle patterns
    # We include some common irregular past participles, but it's not exhaustive.
    # This pattern tries to catch "is/was/are/were/been/being + (word ending in -ed or -en or common irregular participle)"
    passive_voice_regex = r'\b(?:is|am|are|was|were|been|being)\b\s+(?:\w+ed|\w+en|done|seen|made|taken|given|bought|caught|found|known|left|sent|told|thought)\b'
    
    if re.search(passive_voice_regex, sentence_lower):
        return True
    return False

def _infer_tone(sentence: str, brand_profile: Dict[str, Any]) -> str:
    """
    Infers the tone of a sentence based on predefined informal words
    and comparison against desired sophisticated tone descriptors.
    Returns 'informal', 'sophisticated', or 'neutral'.
    """
    sentence_lower = sentence.lower()
    
    # Check for informal/prohibited words first
    found_informal = False
    for term in brand_profile.get("prohibited_terms", []):
        if re.search(r'\b' + re.escape(term) + r'\b', sentence_lower):
            found_informal = True
            break
    if not found_informal: # Only check general informal if not already flagged by a prohibited term
        for term in INFORMAL_WORDS:
            if re.search(r'\b' + re.escape(term) + r'\b', sentence_lower):
                found_informal = True
                break
    
    if found_informal:
        return "informal"
            
    # Check for words aligning with desired sophisticated tone
    desired_tones = [t.lower() for t in brand_profile.get("tone_descriptors", [])]
    if any(any(re.search(r'\b' + re.escape(s_word.lower()) + r'\b', sentence_lower) for s_word in SOPHISTICATED_TONE_WORDS) for dt in desired_tones if dt in [s.lower() for s in SOPHISTICATED_TONE_WORDS]):
        return "sophisticated"
    
    # Fallback
    return "neutral"

def _generate_rewrite(original_segment: str, category: str, details: List[str], brand_profile: Dict[str, Any]) -> str:
    """
    Generates a context-aware rewrite for a given segment based on deviation.
    This is a simplified generative step and will not perform deep NLP parsing.
    """
    rewrite = original_segment
    
    # Prioritize prohibited terms for direct replacement
    if category == "Prohibited Terms":
        for term_detail in details: # details might be like ["Uses prohibited term: 'awesome'"]
            match = re.search(r"'([^']+)'", term_detail)
            if match:
                term = match.group(1) # Original casing
                term_lower = term.lower()
                replacement_info = INFORMAL_WORDS.get(term_lower, {})
                replacement = replacement_info.get("suggestion", "[REPHRASE]")
                
                # Use regex to replace whole word, case-insensitively, handling punctuation
                if term_lower == "really excited":
                    rewrite = re.sub(r'\b(?:really)\s+(?:excited)\b', "eager", rewrite, flags=re.IGNORECASE)
                else:
                    rewrite = re.sub(r'\b' + re.escape(term) + r'\b', replacement, rewrite, flags=re.IGNORECASE)

    elif category == "Tone Deviation":
        problematic_words_str = next((d for d in details if "uses words like" in d), "")
        # Extract words from "Tone is informal, uses words like: 'word1', 'word2'"
        problematic_words_matches = re.findall(r"'([^']+)'", problematic_words_str)
        
        temp_rewrite = original_segment
        for word in problematic_words_matches:
            word_lower = word.lower()
            if word_lower in INFORMAL_WORDS:
                replacement = INFORMAL_WORDS[word_lower]["suggestion"]
                temp_rewrite = re.sub(r'\b' + re.escape(word) + r'\b', replacement, temp_rewrite, flags=re.IGNORECASE)
        
        if temp_rewrite != original_segment:
            rewrite = temp_rewrite
        else:
            first_tone = brand_profile.get('tone_descriptors', ['sophisticated'])[0]
            rewrite = f"Consider a more {first_tone} phrasing for: \"{original_segment}\""

    elif category == "Sentence Structure" and "passive voice" in details[0]:
        first_tone = brand_profile.get('tone_descriptors', ['sophisticated'])[0]
        rewrite = f"Rewrite this sentence in active voice to enhance its {first_tone} impact."
    
    elif category == "Sentence Structure" and "long sentence" in details[0]:
        rewrite = f"Consider breaking this sentence into shorter, more impactful statements."
    
    elif category == "Keyword Missing":
        missing_keyword = details[0].split(":")[-1].strip().strip("'") # Extract keyword
        if missing_keyword:
            rewrite = f"Integrate '{missing_keyword}' into your content to reinforce your brand message."

    # If no specific rewrite logic was applied, provide a general prompt
    if rewrite == original_segment:
        rewrite = f"Refine this segment for better alignment with brand voice preferences."

    return rewrite


def process(user_input_json: str) -> str:
    """
    Main function to process user input for Brand Voice Alignment.
    Returns a complete HTML page with analysis and suggestions.
    """
    try:
        input_data = json.loads(user_input_json)
    except json.JSONDecodeError:
        return _render_html_output({"draft_text": "", "brand_profile": {}}, {"error_message": "Invalid JSON input. Please provide a valid JSON object."})

    draft_text = input_data.get("draft_text", "").strip()
    brand_profile = input_data.get("brand_profile", {})

    # Ensure brand_profile fields are lists for easier processing and clean them
    brand_profile["tone_descriptors"] = [s.strip() for s in brand_profile.get("tone_descriptors", []) if s.strip()]
    brand_profile["keywords_to_include"] = [s.strip() for s in brand_profile.get("keywords_to_include", []) if s.strip()]
    brand_profile["prohibited_terms"] = [s.strip() for s in brand_profile.get("prohibited_terms", []) if s.strip()]
    brand_profile["target_emotion"] = [s.strip() for s in brand_profile.get("target_emotion", []) if s.strip()]
    brand_profile["example_phrases"] = [s.strip() for s in brand_profile.get("example_phrases", []) if s.strip()]

    # VALIDATION_FIRST - If input is insufficient, render the input UI with an error.
    if not draft_text or len(draft_text) < 20:
        return _render_html_output(input_data, {"error_message": "Please provide a longer draft text (minimum 20 characters) for analysis."})
    if not brand_profile or not brand_profile.get("name"):
        return _render_html_output(input_data, {"error_message": "Please define or load a complete brand profile with a name."})
    
    # Initialize analysis variables
    overall_consistency_score = 100
    alignment_breakdown: List[Dict[str, Any]] = []
    
    sentences = _segment_sentences(draft_text)
    
    # A temporary structure to hold annotations per sentence and build the final HTML
    # Each item will be (original_sentence_text, html_highlighted_text, list_of_issue_strings)
    sentence_annotations: List[Tuple[str, str, List[str]]] = []

    # --- Analysis Loop ---
    # Process sentences for prohibited terms, tone, structure
    for sentence_original in sentences:
        current_sentence_highlighted = sentence_original
        sentence_issue_details = []
        
        # Flags to prevent redundant score deductions for the same type of issue within one sentence
        has_prohibited_term_issue_in_sentence = False
        has_informal_tone_issue_in_sentence = False
        has_passive_voice_issue_in_sentence = False
        has_long_sentence_issue_in_sentence = False

        # 1. Prohibited Terms
        for term in brand_profile["prohibited_terms"]:
            if re.search(r'\b' + re.escape(term) + r'\b', sentence_original, re.IGNORECASE):
                if not has_prohibited_term_issue_in_sentence:
                    overall_consistency_score -= 10 # High penalty
                    has_prohibited_term_issue_in_sentence = True
                alignment_breakdown.append({
                    "category": "Prohibited Terms",
                    "status": "Deviation",
                    "details": [f"Uses prohibited term: '{term}'"],
                    "original_segments": [sentence_original],
                    "suggested_rewrites": [_generate_rewrite(sentence_original, "Prohibited Terms", [f"Uses prohibited term: '{term}'"], brand_profile)]
                })
                current_sentence_highlighted = re.sub(r'(' + re.escape(term) + r')', r'<span class="highlight-red">\1</span>', current_sentence_highlighted, flags=re.IGNORECASE)
                sentence_issue_details.append(f"Prohibited Term: '{term}'")

        # 2. Tone Deviation (using predefined informal words not in brand_profile.prohibited_terms, or general informal tone)
        inferred_tone = _infer_tone(sentence_original, brand_profile)
        desired_sophisticated_tone = any(t.lower() in [s.lower() for s in SOPHISTICATED_TONE_WORDS] for t in brand_profile["tone_descriptors"])
        
        if inferred_tone == "informal" and desired_sophisticated_tone:
            # Find specific informal words in sentence that are not *also* in the brand_profile's prohibited terms
            problematic_words_for_tone = [
                k for k in INFORMAL_WORDS if re.search(r'\b' + re.escape(k) + r'\b', sentence_original, re.IGNORECASE) and k.lower() not in [pt.lower() for pt in brand_profile["prohibited_terms"]]
            ]

            if problematic_words_for_tone and not has_informal_tone_issue_in_sentence:
                overall_consistency_score -= 5 # Moderate penalty
                has_informal_tone_issue_in_sentence = True
                details_str = f"Tone is informal, uses words like: '{', '.join(problematic_words_for_tone)}'"
                alignment_breakdown.append({
                    "category": "Tone Deviation",
                    "status": "Deviation",
                    "details": [details_str],
                    "original_segments": [sentence_original],
                    "suggested_rewrites": [_generate_rewrite(sentence_original, "Tone Deviation", [details_str], brand_profile)]
                })
                # Highlight in yellow
                for word in problematic_words_for_tone:
                    current_sentence_highlighted = re.sub(r'(' + re.escape(word) + r')', r'<span class="highlight-yellow">\1</span>', current_sentence_highlighted, flags=re.IGNORECASE)
                sentence_issue_details.append(f"Informal Tone: {', '.join(problematic_words_for_tone)}")
            # For general informal tone (not tied to specific words) without highlighting, this is more semantic.
            # We'll stick to highlighting based on detected words for now.

        # 3. Sentence Structure & Voice
        if brand_profile.get("active_passive_voice_preference", "").lower() == "active":
            if _detect_passive_voice(sentence_original):
                if not has_passive_voice_issue_in_sentence:
                    overall_consistency_score -= 3 # Lower penalty
                    has_passive_voice_issue_in_sentence = True
                alignment_breakdown.append({
                    "category": "Sentence Structure",
                    "status": "Deviation",
                    "details": ["Uses passive voice"],
                    "original_segments": [sentence_original],
                    "suggested_rewrites": [_generate_rewrite(sentence_original, "Sentence Structure", ["passive voice"], brand_profile)]
                })
                # Highlight the entire sentence with orange border for passive voice
                current_sentence_highlighted = f'<span class="highlight-orange-sentence">{current_sentence_highlighted}</span>'
                sentence_issue_details.append(f"Passive Voice")
        
        if brand_profile.get("sentence_structure_preference", "").lower() == "concise and impactful":
            word_count = len(re.findall(r'\b\w+\b', sentence_original)) # Robust word count
            if word_count > 20: # Heuristic for potentially long/unconcise sentences
                if not has_long_sentence_issue_in_sentence:
                    overall_consistency_score -= 2
                    has_long_sentence_issue_in_sentence = True
                details_str = f"Sentence is long ({word_count} words), consider conciseness."
                alignment_breakdown.append({
                    "category": "Sentence Structure",
                    "status": "Potential Deviation",
                    "details": [details_str],
                    "original_segments": [sentence_original],
                    "suggested_rewrites": [_generate_rewrite(sentence_original, "Sentence Structure", [details_str], brand_profile)]
                })
                # Apply a light yellow highlight if no other sentence-level highlight is present
                if not has_passive_voice_issue_in_sentence:
                    current_sentence_highlighted = f'<span class="highlight-light-yellow-sentence">{current_sentence_highlighted}</span>'
                sentence_issue_details.append(f"Long Sentence ({word_count} words)")
        
        # Store for final annotated HTML
        sentence_annotations.append((sentence_original, current_sentence_highlighted, sentence_issue_details))

    # 4. Keywords to Include (check overall document presence)
    missing_keywords = []
    for keyword in brand_profile["keywords_to_include"]:
        if not re.search(r'\b' + re.escape(keyword) + r'\b', draft_text, re.IGNORECASE):
            missing_keywords.append(keyword)

    if missing_keywords:
        for keyword in missing_keywords:
            overall_consistency_score -= 7 # Moderate penalty for each missing key term
            details_str = f"Missing key brand keyword: '{keyword}'"
            alignment_breakdown.append({
                "category": "Keyword Missing",
                "status": "Deviation",
                "details": [details_str],
                "original_segments": ["Overall document"], # No specific segment, refers to the whole text
                "suggested_rewrites": [_generate_rewrite(draft_text, "Keyword Missing", [details_str], brand_profile)]
            })

    # Ensure score is within 0-100 range
    overall_consistency_score = max(0, min(100, overall_consistency_score))

    # Build the final annotated HTML text from processed sentence annotations
    final_annotated_parts = []
    for original_text, highlighted_html, details_list in sentence_annotations:
        if details_list:
            # Join details with a specific separator for display in tooltip
            data_issues_attr = _escape_html("; ".join(details_list))
            # Wrap each sentence in a span with the `annotated-segment` class for tooltips
            final_annotated_parts.append(
                f'<span class="annotated-segment" data-original="{_escape_html(original_text)}" data-issues="{data_issues_attr}">{highlighted_html}</span>'
            )
        else:
            final_annotated_parts.append(_escape_html(original_text)) # Clean sentences also get wrapped and escaped
    
    annotated_text_html_content = "<p>" + "</p><p>".join(final_annotated_parts) + "</p>"
    # Clean up any potential empty paragraphs from splitting, and ensure final HTML is correct
    annotated_text_html_content = annotated_text_html_content.replace("<p></p>", "")

    # Summary Recommendation
    summary_recommendation = "Your draft shows strong alignment with your brand voice."
    if overall_consistency_score < 90:
        summary_recommendation = "Your draft has some areas for improvement to better align with your brand voice."
    if overall_consistency_score < 70:
        summary_recommendation = "Significant revisions are recommended to align your draft with your brand voice."
    if overall_consistency_score < 50:
        summary_recommendation = "Your draft requires substantial rephrasing to meet brand voice standards."
    
    # Add specific summary points based on major deviations
    if any(bd["category"] == "Prohibited Terms" for bd in alignment_breakdown):
        summary_recommendation += " Specifically, addressing the use of prohibited terms should be a priority."
    if any(bd["category"] == "Tone Deviation" for bd in alignment_breakdown):
        summary_recommendation += " Focus on refining the tone to be more consistent with your desired style."
    if any(bd["category"] == "Keyword Missing" for bd in alignment_breakdown):
        summary_recommendation += " Consider integrating key brand keywords for stronger messaging."

    output_data = {
        "overall_consistency_score": overall_consistency_score,
        "alignment_breakdown": alignment_breakdown,
        "summary_recommendation": summary_recommendation,
        "annotated_text_html": annotated_text_html_content,
        "error_message": None # No error in this successful path
    }

    return _render_html_output(input_data, output_data)

def _render_html_output(input_data: Dict[str, Any], output_data: Dict[str, Any]) -> str:
    """
    Renders the complete HTML interface with input form, analysis, and results.
    This dynamically switches between Entry/Result states based on `output_data` content.
    """
    draft_text = input_data.get("draft_text", "")
    brand_profile = input_data.get("brand_profile", {})

    # Default brand profile values for the UI if not provided or empty
    bp_name = _escape_html(brand_profile.get("name", "")) # Default to empty for new profile
    bp_tone = _escape_html(", ".join(brand_profile.get("tone_descriptors", ["sophisticated", "precise"])))
    bp_keywords = _escape_html(", ".join(brand_profile.get("keywords_to_include", ["innovation", "excellence"])))
    bp_prohibited = _escape_html(", ".join(brand_profile.get("prohibited_terms", ["awesome", "cool"])))
    bp_sentence_structure = _escape_html(brand_profile.get("sentence_structure_preference", "concise and impactful"))
    bp_voice_preference = _escape_html(brand_profile.get("active_passive_voice_preference", "active"))
    bp_target_emotion = _escape_html(", ".join(brand_profile.get("target_emotion", ["trust", "excitement"])))
    bp_example_phrases = _escape_html("\n".join(brand_profile.get("example_phrases", [""])))

    # If output_data contains an error_message or if no draft_text was provided, show input form with error/initial state.
    error_message = output_data.get("error_message")
    
    if error_message or not draft_text:
        overall_score = 0 # Default score if no analysis happened
        summary_recommendation = ""
        annotated_text_html = ""
        alignment_breakdown = []
        is_initial_load_or_error = True
    else:
        overall_score = output_data["overall_consistency_score"]
        alignment_breakdown = output_data["alignment_breakdown"]
        summary_recommendation = _escape_html(output_data["summary_recommendation"])
        annotated_text_html = output_data["annotated_text_html"]
        is_initial_load_or_error = False

    # Generate breakdown HTML
    breakdown_html_items = ""
    for i, item in enumerate(alignment_breakdown):
        original_segments_str = _escape_html("<br>".join(item["original_segments"]))
        suggested_rewrites_str = _escape_html("<br>".join(item["suggested_rewrites"]))
        details_str = _escape_html("<br>".join(item["details"]))
        breakdown_html_items += f"""
            <div class="breakdown-item">
                <span class="category">{_escape_html(item['category'])}:</span>
                <span class="status {_escape_html(item['status'].lower().replace(' ', '-'))}">{_escape_html(item['status'])}</span>
                <p class="details">{details_str}</p>
                <div class="segment-pair">
                    <div class="original-segment">
                        <h4>Original:</h4>
                        <p>{original_segments_str}</p>
                    </div>
                    <div class="suggested-rewrite">
                        <h4>Suggested Rewrite:</h4>
                        <textarea rows="3" class="rewrite-textarea" data-index="{i}">{suggested_rewrites_str}</textarea>
                    </div>
                </div>
            </div>
        """

    # Dial/Meter HTML and SVG (Rule 16)
    radius = 40
    circumference = 2 * 3.14159 * radius
    arc_length = circumference * 0.75 # Use 270 degrees of the circle
    
    fill_length = (overall_score / 100) * arc_length
    
    # Define colors for score ranges
    if overall_score >= 80:
        score_color = "#28a745" # Green for High
    elif overall_score >= 50:
        score_color = "#ffc107" # Yellow for Medium
    else:
        score_color = "#dc3545" # Red for Low


    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brand Voice Aligner</title>
    <style>
        :root {{
            --primary-brand-color: #6C63FF; /* A sophisticated purple/blue */
            --secondary-brand-color: #E6E0FF; /* Lighter variant */
            --text-color-dark: #2c3e50;
            --text-color-light: #5a6268;
            --background-color-light: #f8f9fa;
            --background-color-dark: #ecf0f1;
            --border-color: #dee2e6;

            --highlight-red: #e74c3c;
            --highlight-yellow: #f1c40f;
            --highlight-orange: #e67e22;
            --highlight-light-yellow: #fef0c9; /* for subtle deviation like long sentences */
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--background-color-light);
            color: var(--text-color-dark);
            line-height: 1.6;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}

        h1, h2, h3, h4 {{
            color: var(--primary-brand-color);
            margin-top: 0;
        }}

        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 2.5em;
            font-weight: 600;
        }}

        /* UI Entry State / Result State toggling */
        .input-section, .result-section {{
            display: none; /* Controlled by JS or Python's initial render */
        }}
        .input-section.active, .result-section.active {{
            display: block;
        }}

        .form-group {{
            margin-bottom: 15px;
        }}

        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: var(--text-color-dark);
        }}

        textarea, input[type="text"] {{
            width: 100%;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-size: 1em;
            box-sizing: border-box;
            background-color: var(--background-color-dark);
            color: var(--text-color-dark);
        }}

        textarea {{
            min-height: 150px;
            resize: vertical;
        }}

        .brand-profile-config {{
            border: 1px solid var(--secondary-brand-color);
            border-radius: 6px;
            padding: 20px;
            margin-top: 20px;
            background-color: #fcfbff;
        }}
        .brand-profile-config.collapsed .config-fields {{
            display: none;
        }}
        .brand-profile-config h3 {{
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text-color-dark);
            font-size: 1.2em;
        }}
        .brand-profile-config h3::after {{
            content: '▲'; /* Up arrow for collapsed */
            font-size: 0.8em;
            transition: transform 0.2s ease;
            transform: rotate(0deg); /* Initial state: pointing up */
        }}
        .brand-profile-config.expanded h3::after {{
            content: '▼'; /* Down arrow for expanded */
            transform: rotate(0deg); /* No rotation needed if content changes */
        }}

        .button-group {{
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 20px;
            align-items: center;
        }}

        button {{
            padding: 12px 25px;
            border: none;
            border-radius: 4px;
            font-size: 1.1em;
            cursor: pointer;
            transition: background-color 0.2s ease, transform 0.1s ease;
        }}

        button.primary {{
            background-color: var(--primary-brand-color);
            color: #fff;
        }}
        button.primary:hover {{
            background-color: #5b54d2;
            transform: translateY(-1px);
        }}
        button.primary:active {{
            transform: translateY(0);
        }}

        button.secondary {{
            background-color: #e0e0e0;
            color: var(--text-color-dark);
        }}
        button.secondary:hover {{
            background-color: #d0d0d0;
            transform: translateY(-1px);
        }}
        button.secondary:active {{
            transform: translateY(0);
        }}

        /* UI Active State (Loading) */
        .loading-spinner {{
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-left-color: var(--primary-brand-color);
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            display: none; /* Hidden by default */
            margin-left: 10px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .loading-spinner.active {{
            display: inline-block;
        }}

        /* UI Result State */
        .result-layout {{
            display: flex;
            flex-wrap: wrap; /* Allows wrapping on smaller screens */
            gap: 20px;
            margin-top: 20px;
        }}

        .text-panel {{
            flex: 1 1 calc(50% - 10px); /* Two columns on wider screens */
            background-color: var(--background-color-dark);
            padding: 20px;
            border-radius: 6px;
            min-width: 300px; /* Minimum width for each panel */
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
            overflow-y: auto;
            max-height: 600px; /* Limit height for scrolling */
        }}

        .text-panel h3 {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 15px;
            color: var(--text-color-dark);
        }}

        .original-text p, .annotated-text p {{
            margin: 0 0 1em 0;
            white-space: pre-wrap; /* Preserves line breaks from input */
        }}
        .original-text p:last-child, .annotated-text p:last-child {{
            margin-bottom: 0;
        }}


        /* Highlighting for annotated text */
        .highlight-red {{ background-color: rgba(231, 76, 60, 0.2); border-bottom: 1px dashed var(--highlight-red); cursor: help; }} /* Prohibited terms */
        .highlight-yellow {{ background-color: rgba(241, 196, 15, 0.2); border-bottom: 1px dashed var(--highlight-yellow); cursor: help; }} /* Tone deviation */
        /* Sentence-level highlights with padding and border for visibility */
        .highlight-orange-sentence {{ background-color: rgba(230, 126, 34, 0.1); border-left: 3px solid var(--highlight-orange); padding-left: 5px; cursor: help; display: block; }} /* Passive voice - whole sentence */
        .highlight-light-yellow-sentence {{ background-color: rgba(254, 240, 201, 0.1); border-left: 3px dotted var(--highlight-yellow); padding-left: 5px; cursor: help; display: block; }} /* Long sentence - whole sentence */

        .tooltip {{
            position: absolute;
            background-color: var(--text-color-dark);
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            z-index: 1000;
            font-size: 0.8em;
            pointer-events: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            white-space: nowrap;
        }}
        .tooltip strong {{ display: block; margin-bottom: 4px; }}
        .tooltip span {{ display: block; line-height: 1.3; }}


        .score-summary {{
            flex: 1 1 100%; /* Full width for score and summary */
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
            border-radius: 6px;
            background-color: var(--background-color-dark);
            margin-top: 20px;
        }}

        .score-dial-container {{
            position: relative;
            width: 120px;
            height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.8em;
            color: var(--text-color-dark);
        }}
        .score-dial-label {{
            font-size: 0.8em;
            color: var(--text-color-light);
            margin-top: 5px;
        }}

        .score-dial-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            transform: rotate(-135deg); /* Start arc at bottom-left */
        }}
        .score-dial-svg circle {{
            transition: stroke-dasharray 1s ease-out;
        }}

        .summary-recommendation {{
            text-align: center;
            font-style: italic;
            color: var(--text-color-light);
            margin-top: 10px;
            max-width: 800px;
        }}

        .breakdown-panel {{
            flex: 1 1 100%; /* Full width below text panels */
            background-color: var(--background-color-dark);
            padding: 20px;
            border-radius: 6px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
            margin-top: 20px;
        }}

        .breakdown-item {{
            margin-bottom: 20px;
            padding: 15px;
            border-bottom: 1px solid var(--border-color);
            background-color: #fff;
            border-radius: 4px;
        }}
        .breakdown-item:last-child {{
            border-bottom: none;
        }}
        .breakdown-item .category {{
            font-weight: bold;
            color: var(--primary-brand-color);
            margin-right: 5px;
        }}
        .breakdown-item .status {{
            font-size: 0.9em;
            padding: 3px 8px;
            border-radius: 3px;
            color: #fff;
        }}
        .breakdown-item .status.deviation {{ background-color: var(--highlight-red); }}
        .breakdown-item .status.potential-deviation {{ background-color: var(--highlight-orange); }}
        .breakdown-item .status.alignment {{ background-color: #28a745; }} /* Not used currently, but good to have */
        .breakdown-item .details {{
            font-style: italic;
            color: var(--text-color-light);
            margin-top: 5px;
        }}
        .breakdown-item h4 {{
            margin-top: 10px;
            margin-bottom: 5px;
            color: var(--text-color-dark);
        }}
        .segment-pair {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }}
        .original-segment, .suggested-rewrite {{
            flex: 1;
            padding: 10px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background-color: var(--background-color-light);
        }}
        .original-segment p, .suggested-rewrite textarea {{
            margin: 0;
            font-size: 0.95em;
        }}
        .suggested-rewrite textarea {{
            width: 100%;
            min-height: 100px; /* Fixed height for consistency */
            resize: vertical;
            border: none;
            background-color: transparent;
            font-family: inherit;
            color: inherit;
        }}
        .action-buttons-result {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }}
        .action-buttons-result button {{
            padding: 10px 20px;
            font-size: 1em;
        }}
        
        .error-message {{
            background-color: #fce4e4;
            color: #c70000;
            border: 1px solid #c70000;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: 500;
            display: block; /* Always block, controlled by JS if empty */
        }}

        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .result-layout {{
                flex-direction: column;
            }}
            .text-panel {{
                flex: 1 1 100%;
            }}
            .segment-pair {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Brand Voice Aligner</h1>
        </div>
        
        <div id="errorMessage" class="error-message" style="display: {{"block" if error_message else "none"}};">
            {_escape_html(error_message) if error_message else ""}
        </div>

        <!-- UI Entry State / Input Form -->
        <div id="inputSection" class="input-section {{"active" if is_initial_load_or_error else ""}}">
            <div class="form-group">
                <label for="draftContent">Paste your draft content here...</label>
                <textarea id="draftContent" placeholder="Our new product launch is going to be totally awesome! It's super sleek and will blow your mind with its cool features. We're really excited for everyone to check it out soon and experience the amazing journey.">{_escape_html(draft_text)}</textarea>
            </div>

            <div id="brandProfileConfig" class="brand-profile-config {{"expanded" if brand_profile and brand_profile.get('name') else "collapsed"}}">
                <h3 onclick="toggleBrandProfileConfig()">Define Your Brand Voice <span id="toggleIcon">▼</span></h3>
                <div class="config-fields">
                    <div class="form-group">
                        <label for="profileName">Profile Name:</label>
                        <input type="text" id="profileName" value="{bp_name}" placeholder="e.g., Lumière Corp - V2">
                    </div>
                    <div class="form-group">
                        <label for="toneDescriptors">Tone Descriptors (comma-separated):</label>
                        <input type="text" id="toneDescriptors" value="{bp_tone}" placeholder="e.g., sophisticated, precise, innovative">
                    </div>
                    <div class="form-group">
                        <label for="keywordsInclude">Keywords to Include (comma-separated):</label>
                        <input type="text" id="keywordsInclude" value="{bp_keywords}" placeholder="e.g., innovation, sustainability, excellence">
                    </div>
                    <div class="form-group">
                        <label for="prohibitedTerms">Prohibited Terms (comma-separated):</label>
                        <input type="text" id="prohibitedTerms" value="{bp_prohibited}" placeholder="e.g., awesome, cool, super, amazing">
                    </div>
                    <div class="form-group">
                        <label for="sentenceStructure">Sentence Structure Preference:</label>
                        <input type="text" id="sentenceStructure" value="{bp_sentence_structure}" placeholder="e.g., concise and impactful, varied">
                    </div>
                    <div class="form-group">
                        <label for="voicePreference">Active/Passive Voice Preference:</label>
                        <input type="text" id="voicePreference" value="{bp_voice_preference}" placeholder="e.g., active, neutral">
                    </div>
                    <div class="form-group">
                        <label for="targetEmotion">Target Emotion (comma-separated):</label>
                        <input type="text" id="targetEmotion" value="{bp_target_emotion}" placeholder="e.g., trust, excitement, admiration">
                    </div>
                    <div class="form-group">
                        <label for="examplePhrases">Example Phrases (one per line):</label>
                        <textarea id="examplePhrases" rows="4" placeholder="Lumière embodies the pinnacle of precision engineering.\nWe forge the future with visionary innovation.">{bp_example_phrases}</textarea>
                    </div>
                </div>
            </div>

            <div class="button-group">
                <button type="button" class="secondary" onclick="loadExampleProfile()">Load Example Profile</button>
                <button type="button" class="primary" id="alignVoiceButton" onclick="submitAnalysis()">
                    Align Voice
                    <span id="loadingSpinner" class="loading-spinner"></span>
                </button>
            </div>
        </div>

        <!-- UI Result State -->
        <div id="resultSection" class="result-section {{"active" if not is_initial_load_or_error else ""}}">
            <div class="score-summary">
                <div class="score-dial-container">
                    <svg class="score-dial-svg" width="100%" height="100%" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="{radius}" fill="none" stroke="#e0e0e0" stroke-width="8" stroke-dasharray="{arc_length}" stroke-dashoffset="{arc_length / 4}" stroke-linecap="round"></circle>
                        <circle cx="50" cy="50" r="{radius}" fill="none" stroke="{score_color}" stroke-width="8" stroke-dasharray="{fill_length} {arc_length - fill_length}" stroke-dashoffset="{arc_length / 4}" stroke-linecap="round"></circle>
                    </svg>
                    <span>{overall_score}</span>
                    <span class="score-dial-label">Alignment Score</span>
                </div>
                <p class="summary-recommendation">{summary_recommendation}</p>
            </div>

            <div class="result-layout">
                <div class="text-panel original-text">
                    <h3>Original Draft</h3>
                    <p>{_escape_html(draft_text)}</p>
                </div>
                <div class="text-panel annotated-text">
                    <h3>Annotated Draft</h3>
                    {annotated_text_html}
                </div>
            </div>

            <div class="breakdown-panel">
                <h3>Alignment Breakdown & Suggestions</h3>
                <div class="breakdown-items-container">
                    {breakdown_html_items}
                </div>
            </div>
            <div class="action-buttons-result">
                <button type="button" class="primary" onclick="copyRewrittenText()">Copy Rewritten Text</button>
                <button type="button" class="secondary" onclick="exportReport()">Export Report</button>
                <button type="button" class="secondary" onclick="resetTool()">Refine Profile / New Analysis</button>
            </div>
        </div>
    </div>

    <script>
        // Store input data for re-running analysis or modifying profile
        // These are initialized by Python, for client-side JS reference.
        let currentDraftText = {_escape_html(json.dumps(draft_text))};
        let currentBrandProfile = {_escape_html(json.dumps(brand_profile))};
        let currentAlignmentBreakdown = {_escape_html(json.dumps(alignment_breakdown))};
        let currentSummaryRecommendation = {_escape_html(json.dumps(summary_recommendation))};
        let currentOverallScore = {_escape_html(json.dumps(overall_score))};

        document.addEventListener('DOMContentLoaded', () => {{
            const inputSection = document.getElementById('inputSection');
            const resultSection = document.getElementById('resultSection');
            const brandProfileConfig = document.getElementById('brandProfileConfig');
            const toggleIcon = document.getElementById('toggleIcon');

            // Set initial state based on Python's rendering logic (is_initial_load_or_error)
            if ({json.dumps(is_initial_load_or_error)}) {{ // True if error or initial empty load
                inputSection.classList.add('active');
                resultSection.classList.remove('active');
            }} else {{ // False means a successful analysis was performed
                inputSection.classList.remove('active');
                resultSection.classList.add('active');
            }}

            // Expand brand profile config if data is pre-filled, or set default arrow
            if (currentBrandProfile && Object.keys(currentBrandProfile).length > 0 && currentBrandProfile.name && currentBrandProfile.name.length > 0) {{
                brandProfileConfig.classList.add('expanded');
                brandProfileConfig.classList.remove('collapsed');
                toggleIcon.textContent = '▼'; // Down arrow for expanded
            }} else {{
                brandProfileConfig.classList.add('collapsed');
                brandProfileConfig.classList.remove('expanded');
                toggleIcon.textContent = '▲'; // Up arrow for collapsed
            }}
            
             // Attach event listeners for highlight tooltips
            document.querySelectorAll('.annotated-segment, .highlight-red, .highlight-yellow, .highlight-orange-sentence, .highlight-light-yellow-sentence').forEach(element => {{
                element.onmouseover = (e) => {{
                    // Prioritize specific word highlights' data-issues if available, falling back to segment-level
                    let issues = e.target.dataset.issues || '';
                    if (!issues && e.target.closest('.annotated-segment')) {{
                        issues = e.target.closest('.annotated-segment').dataset.issues || '';
                    }}

                    if (issues) {{
                        const tooltip = document.createElement('div');
                        tooltip.className = 'tooltip';
                        // Split by '; ' to handle multiple issues per segment
                        // Use _escape_html to prevent XSS if issue details contain user-controlled text
                        tooltip.innerHTML = '<strong>Issues:</strong><br>' + issues.split('; ').map(issue => `<span>${_escape_html(issue)}</span>`).join('');
                        tooltip.style.position = 'absolute';
                        tooltip.style.top = (e.pageY + 15) + 'px';
                        tooltip.style.left = (e.pageX + 15) + 'px';
                        document.body.appendChild(tooltip);
                        e.target.tooltipElement = tooltip; // Store reference to remove later
                    }}
                }};
                element.onmouseout = (e) => {{
                    if (e.target.tooltipElement) {{
                        e.target.tooltipElement.remove();
                        e.target.tooltipElement = null;
                    }}
                }};
                element.onmousemove = (e) => {{
                    if (e.target.tooltipElement) {{
                        tooltip.style.top = (e.pageY + 15) + 'px';
                        tooltip.style.left = (e.pageX + 15) + 'px';
                    }}
                }};
            }});
        }});

        function toggleBrandProfileConfig() {{
            const configDiv = document.getElementById('brandProfileConfig');
            const toggleIcon = document.getElementById('toggleIcon');
            configDiv.classList.toggle('collapsed');
            configDiv.classList.toggle('expanded');
            if (configDiv.classList.contains('expanded')) {{
                toggleIcon.textContent = '▼';
            }} else {{
                toggleIcon.textContent = '▲';
            }}
        }}

        function getBrandProfileFromUI() {{
            return {{
                name: document.getElementById('profileName').value,
                tone_descriptors: document.getElementById('toneDescriptors').value.split(',').map(s => s.trim()).filter(s => s),
                keywords_to_include: document.getElementById('keywordsInclude').value.split(',').map(s => s.trim()).filter(s => s),
                prohibited_terms: document.getElementById('prohibitedTerms').value.split(',').map(s => s.trim()).filter(s => s),
                sentence_structure_preference: document.getElementById('sentenceStructure').value,
                active_passive_voice_preference: document.getElementById('voicePreference').value,
                target_emotion: document.getElementById('targetEmotion').value.split(',').map(s => s.trim()).filter(s => s),
                example_phrases: document.getElementById('examplePhrases').value.split('\\n').map(s => s.trim()).filter(s => s),
            }};
        }}

        function submitAnalysis() {{
            const draftText = document.getElementById('draftContent').value;
            const brandProfile = getBrandProfileFromUI();

            if (!draftText || draftText.trim().length < 20) {{
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Please provide a longer draft text (minimum 20 characters) for analysis.';
                return;
            }}
            if (!brandProfile.name) {{
                const errorDiv = document.getElementById('errorMessage');
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Please define a brand profile name.';
                return;
            }}

            document.getElementById('errorMessage').style.display = 'none'; // Hide any previous error
            document.getElementById('alignVoiceButton').disabled = true;
            document.getElementById('loadingSpinner').classList.add('active');

            // This is a placeholder for actual interaction. In the Lili environment,
            // submitting this form would trigger a re-run of the process() function
            // with the new input, generating a fresh HTML output.
            setTimeout(() => {{
                alert('Analysis request sent. The page will refresh with your results once processing is complete.');
                // In a real browser/server setup, you would typically POST this data:
                // fetch('/process', { method: 'POST', body: JSON.stringify({ draft_text: draftText, brand_profile: brandProfile }) })
                //    .then(response => response.text())
                //    .then(html => document.open('text/html').write(html).close());
                
                // For this challenge, we just reset the button and expect the build system to handle re-rendering on next input.
                document.getElementById('alignVoiceButton').disabled = false;
                document.getElementById('loadingSpinner').classList.remove('active');
            }}, 1500); // Simulate loading time
        }}

        function loadExampleProfile() {{
            document.getElementById('draftContent').value = "Our new product launch is going to be truly exceptional! It's a highly sophisticated device that will exceed expectations with its innovative features. We are eager for everyone to explore its transformative capabilities soon.";
            document.getElementById('profileName').value = "Lumière Corp - V2";
            document.getElementById('toneDescriptors').value = "sophisticated, precise, innovative, inspiring, authoritative";
            document.getElementById('keywordsInclude').value = "innovation, precision, excellence, future-forward, transformative";
            document.getElementById('prohibitedTerms').value = "awesome, cool, super, amazing, blow your mind, really excited";
            document.getElementById('sentenceStructure').value = "concise and impactful";
            document.getElementById('voicePreference').value = "active";
            document.getElementById('targetEmotion').value = "trust, excitement, admiration";
            document.getElementById('examplePhrases').value = "Lumière embodies the pinnacle of precision engineering.\\nWe forge the future with visionary innovation.\\nExperience the transformative power of our latest solution.";
            
            const brandProfileConfig = document.getElementById('brandProfileConfig');
            const toggleIcon = document.getElementById('toggleIcon');
            brandProfileConfig.classList.add('expanded');
            brandProfileConfig.classList.remove('collapsed');
            toggleIcon.textContent = '▼'; // Down arrow for expanded
        }}

        function copyRewrittenText() {{
            let fullRewrittenText = [];
            document.querySelectorAll('.rewrite-textarea').forEach(textarea => {{
                fullRewrittenText.push(textarea.value);
            }});
            navigator.clipboard.writeText(fullRewrittenText.join('\\n\\n')).then(() => {{
                alert('All suggested rewrites copied to clipboard!');
            }}).catch(err => {{
                console.error('Failed to copy text: ', err);
                alert('Failed to copy text. Please try again or copy manually.');
            }});
        }}

        function exportReport() {{
            // Use the Python-generated data for the report, as it's static in this single-HTML context.
            const reportContent = `
Brand Voice Alignment Report
------------------------------------
Overall Consistency Score: ${{currentOverallScore}}

Summary Recommendation:
${{currentSummaryRecommendation}}

Original Draft:
${{currentDraftText}}

--- Alignment Breakdown ---
` + JSON.parse(currentAlignmentBreakdown).map(item => `
Category: ${{item.category}}
Status: ${{item.status}}
Details: ${{item.details.join('; ')}}
Original Segment: ${{item.original_segments.join('\\n')}}
Suggested Rewrite: ${{item.suggested_rewrites.join('\\n')}}
`).join('\\n------------------------------------\n') + `
--- End Report ---
            `;
            const blob = new Blob([reportContent], {{ type: 'text/plain' }});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'BrandVoiceAlignmentReport.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            alert('Report exported as BrandVoiceAlignmentReport.txt!');
        }}

        function resetTool() {{
            // Clear inputs and reset UI to the initial entry state.
            document.getElementById('draftContent').value = '';
            document.getElementById('profileName').value = '';
            document.getElementById('toneDescriptors').value = '';
            document.getElementById('keywordsInclude').value = '';
            document.getElementById('prohibitedTerms').value = '';
            document.getElementById('sentenceStructure').value = '';
            document.getElementById('voicePreference').value = '';
            document.getElementById('targetEmotion').value = '';
            document.getElementById('examplePhrases').value = '';
            
            document.getElementById('inputSection').classList.add('active');
            document.getElementById('resultSection').classList.remove('active');
            document.getElementById('alignVoiceButton').disabled = false;
            document.getElementById('loadingSpinner').classList.remove('active');
            document.getElementById('errorMessage').style.display = 'none';

            const brandProfileConfig = document.getElementById('brandProfileConfig');
            brandProfileConfig.classList.add('collapsed');
            brandProfileConfig.classList.remove('expanded');
            document.getElementById('toggleIcon').textContent = '▲';
            
            alert('Tool reset. You can now define a new brand profile or paste new content.');
        }}
    </script>
</body>
</html>
"""
    return html_content

def _cli_main():
    """
    Command-line interface entry point for testing or direct execution.
    For Mode 3 tools, this is primarily for development and testing.
    """
    import sys
    
    # Use the test input from the spec by default for CLI
    default_test_input = """
        { "draft_text": "Our new product launch is going to be totally awesome! It's super sleek and will blow your mind with its cool features. We're really excited for everyone to check it out soon and experience the amazing journey.", "brand_profile": { "name": "Lumière Corp - V2", "tone_descriptors": ["sophisticated", "precise", "innovative", "inspiring", "authoritative"], "keywords_to_include": ["innovation", "precision", "excellence", "future-forward", "transformative"], "prohibited_terms": ["awesome", "cool", "super", "amazing", "blow your mind", "really excited"], "sentence_structure_preference": "concise and impactful", "active_passive_voice_preference": "active", "target_emotion": ["trust", "excitement", "admiration"], "example_phrases": ["Lumière embodies the pinnacle of precision engineering.", "We forge the future with visionary innovation.", "Experience the transformative power of our latest solution."] } }
    """
    
    if len(sys.argv) > 1:
        user_input_arg = sys.argv[1]
    else:
        user_input_arg = default_test_input
        # print("Using default test input for CLI. Provide JSON as argument for custom input.")

    # In a real CLI scenario, you might print the raw JSON output or open the HTML in a browser.
    # For this exercise, we just print the HTML, as per Mode 3 requirement.
    print(process(user_input_arg))

# DUAL-MODE PATTERN
_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()