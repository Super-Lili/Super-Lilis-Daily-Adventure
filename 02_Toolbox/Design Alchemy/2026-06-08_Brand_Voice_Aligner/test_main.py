from main import process
import json

def test_process_valid_input():
    test_input = {
        "draft_text": "Our new product launch is going to be totally awesome! It's super sleek and will blow your mind with its cool features. We're really excited for everyone to check it out soon and experience the amazing journey.",
        "brand_profile": {
            "name": "Lumière Corp - V2",
            "tone_descriptors": ["sophisticated", "precise", "innovative", "inspiring", "authoritative"],
            "keywords_to_include": ["innovation", "precision", "excellence", "future-forward", "transformative"],
            "prohibited_terms": ["awesome", "cool", "super", "amazing", "blow your mind", "really excited"],
            "sentence_structure_preference": "concise and impactful",
            "active_passive_voice_preference": "active",
            "target_emotion": ["trust", "excitement", "admiration"],
            "example_phrases": ["Lumière embodies the pinnacle of precision engineering.", "We forge the future with visionary innovation.", "Experience the transformative power of our latest solution."]
        }
    }
    
    html_output = process(json.dumps(test_input))
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "Brand Voice Aligner" in html_output
    
    # Check for presence of key output elements in the HTML (indirectly verifies logic)
    assert "Overall Consistency Score:" in html_output # Check for summary area presence
    assert "Alignment Breakdown & Suggestions" in html_output # Breakdown panel title
    assert "Prohibited Terms" in html_output # Category in breakdown
    assert "Tone Deviation" in html_output # Category in breakdown
    assert "Keyword Missing" in html_output # Category in breakdown
    assert "highlight-red" in html_output # Visual highlights
    assert "highlight-yellow" in html_output # Visual highlights
    assert "alignVoiceButton" in html_output # UI buttons

    # Further checks using regex to parse out specific values if needed, but not strictly required by problem.
    # For example, to check the score:
    score_match = re.search(r'<span>(\d+)</span>\s*<span class="score-dial-label">Alignment Score</span>', html_output)
    assert score_match is not None, "Overall score not found in HTML output."
    overall_score = int(score_match.group(1))
    assert 0 <= overall_score <= 100

    # Ensure rewrites are present
    assert "Rewrite this sentence in active voice" in html_output
    assert "Integrate 'innovation' into your content" in html_output
    assert "exceptional" in html_output # A specific rewrite suggestion for 'awesome'

def test_process_empty_draft_text():
    test_input = {
        "draft_text": "",
        "brand_profile": { "name": "Test Profile" }
    }
    html_output = process(json.dumps(test_input))
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "Please provide a longer draft text" in html_output
    assert 'inputSection" class="input-section active' in html_output # Should show input form

def test_process_invalid_json():
    invalid_json = "{'draft_text': 'test', 'brand_profile': 'invalid'"
    html_output = process(invalid_json)
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "Invalid JSON input" in html_output
    assert 'inputSection" class="input-section active' in html_output # Should show input form
    
def test_process_missing_brand_profile_name():
    test_input = {
        "draft_text": "This is some draft text.",
        "brand_profile": { "tone_descriptors": ["formal"] }
    }
    html_output = process(json.dumps(test_input))
    assert isinstance(html_output, str)
    assert html_output.startswith("<!DOCTYPE html>")
    assert "Please define or load a complete brand profile with a name" in html_output
    assert 'inputSection" class="input-section active' in html_output # Should show input form

def test_process_no_deviations():
    test_input = {
        "draft_text": "Lumière embodies the pinnacle of precision engineering. We forge the future with visionary innovation. Experience the transformative power of our latest solution.",
        "brand_profile": {
            "name": "Lumière Corp - V2",
            "tone_descriptors": ["sophisticated", "precise", "innovative", "inspiring", "authoritative"],
            "keywords_to_include": ["innovation", "precision", "excellence", "future-forward", "transformative"],
            "prohibited_terms": ["awesome", "cool", "super", "amazing", "blow your mind", "really excited"],
            "sentence_structure_preference": "concise and impactful",
            "active_passive_voice_preference": "active",
            "target_emotion": ["trust", "excitement", "admiration"],
            "example_phrases": ["Lumière embodies the pinnacle of precision engineering.", "We forge the future with visionary innovation.", "Experience the transformative power of our latest solution."]
        }
    }
    html_output = process(json.dumps(test_input))
    assert isinstance(html_output, str)
    score_match = re.search(r'<span>(\d+)</span>\s*<span class="score-dial-label">Alignment Score</span>', html_output)
    assert score_match is not None
    overall_score = int(score_match.group(1))
    assert overall_score > 90 # Should be very high, possibly 100 if no subtle issues caught
    assert "strong alignment" in html_output
    assert "Alignment Breakdown" not in html_output or "breakdown-item" not in html_output # Should have very few or no breakdown items
    
    # Check if the result section is active
    assert 'resultSection" class="result-section active' in html_output