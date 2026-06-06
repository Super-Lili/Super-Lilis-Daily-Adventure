from main import process, FeedbackItem, parse_feedback_text, detect_conflicts

def test_parse_feedback_text_basic():
    input_text = "The header feels too dark. Can we lighten it? Also, make the button green. Client Call w/ CEO: Important - privacy link needs to be bigger."
    items = parse_feedback_text(input_text)
    assert len(items) >= 3, f"Expected at least 3 items, got {len(items)}"
    
    # Check for header item
    header_item = next((item for item in items if "header" in item.design_element.lower()), None)
    assert header_item is not None, "Did not find header item"
    assert "dark" in header_item.text.lower()
    assert "lighten" in header_item.suggested_action.lower()

    # Check for button item
    button_item = next((item for item in items if "button" in item.design_element.lower()), None)
    assert button_item is not None, "Did not find button item"
    assert "green" in button_item.suggested_action.lower()

    # Check for CEO/privacy item
    ceo_item = next((item for item in items if "ceo" in item.stakeholder.lower() or "privacy" in item.design_element.lower()), None)
    assert ceo_item is not None, "Did not find CEO/privacy item"
    assert "ceo" in ceo_item.stakeholder.lower()
    assert ceo_item.priority == "High" or ceo_item.priority == "Critical"
    assert "bigger" in ceo_item.suggested_action.lower()

def test_detect_conflicts():
    item1 = FeedbackItem(
        text="Make the header darker.",
        design_element="Header",
        suggested_action="darken",
        extracted_actions=[('color', 'darker')]
    )
    item2 = FeedbackItem(
        text="The header needs to be lighter.",
        design_element="Header",
        suggested_action="lighten",
        extracted_actions=[('color', 'lighter')]
    )
    item3 = FeedbackItem(
        text="The footer text is smaller.",
        design_element="Footer",
        suggested_action="make smaller",
        extracted_actions=[('size', 'smaller')]
    )
    item4 = FeedbackItem(
        text="Privacy link in footer must be much larger.",
        design_element="Footer", # Should normalize to 'footer' for conflict detection
        suggested_action="make larger",
        extracted_actions=[('size', 'bigger')]
    )
    item5 = FeedbackItem(
        text="The button should be green.",
        design_element="Button",
        suggested_action="change to green",
        extracted_actions=[('color', 'green')]
    )
    item6 = FeedbackItem(
        text="The CTA button must be blue.",
        design_element="Button",
        suggested_action="change to blue",
        extracted_actions=[('color', 'blue')]
    )

    items = [item1, item2, item3, item4, item5, item6]
    conflicted_items = detect_conflicts(items)

    assert conflicted_items[0].conflict_id is not None, "Header dark/light conflict not detected"
    assert conflicted_items[0].conflict_id == conflicted_items[1].conflict_id, "Header dark/light conflict IDs do not match"

    assert conflicted_items[2].conflict_id is not None, "Footer size conflict not detected"
    assert conflicted_items[2].conflict_id == conflicted_items[3].conflict_id, "Footer size conflict IDs do not match"
    assert conflicted_items[2].conflict_id != conflicted_items[0].conflict_id, "Conflict IDs should be distinct for different conflicts"

    assert conflicted_items[4].conflict_id is not None, "Button color conflict not detected"
    assert conflicted_items[4].conflict_id == conflicted_items[5].conflict_id, "Button color conflict IDs do not match"
    assert conflicted_items[4].conflict_id != conflicted_items[0].conflict_id, "Conflict IDs should be distinct for different conflicts"

def test_process_full_input():
    test_input = "Subject: Re: Website Draft V3 - Overall, the new header feels a bit too dark. Can we lighten the background to #F8F8F8? Also, Sarah from marketing mentioned the call-to-action button should be green, not blue, to match our brand guidelines. Let's make sure the footer legal text is smaller, maybe 8pt. Hey team, just got a quick thought from Legal – they want the privacy policy link in the footer to be much more prominent, maybe bold and slightly larger than other text. And for the hero section, John from sales thinks the image is too corporate, wants something more 'friendly and approachable'. Comment on Page 2, 'Hero Section': Image too serious, try a candid shot. Also, the headline 'Innovate Your Future' feels dated, can we brainstorm alternatives? On Page 4, 'Pricing Table': Make the 'Pro' plan standout more, maybe a darker background. Client Call w/ CEO: Emphasized that the brand color palette is critical. Header needs to feel lighter, more open. The 'About Us' section copy is too long, needs to be concise, 3-4 sentences max. The CEO loved the overall direction but wants more 'energy' on the homepage."
    output_html = process(test_input)

    assert "<!DOCTYPE html>" in output_html
    assert "Feedback Synthesis Canvas" in output_html
    assert "feedback-card" in output_html
    assert "Sarah from Marketing" in output_html
    assert "footer legal text" in output_html
    assert "CEO" in output_html

    # Check for specific conflicts expected in the test input
    # 1. Header dark/light (Item 1 vs Item 9)
    # 2. Button green/blue (Item 2) - need a conflicting item to trigger
    # 3. Footer legal text smaller vs privacy link larger (Item 3 vs Item 4)
    
    # Conflict for footer size should be present
    # This checks for the HTML class which indicates a conflict
    assert 'conflict-highlight' in output_html, "Expected conflict highlight class in HTML output"
    
    # Verify JSON data embedding
    start_idx = output_html.find("let feedbackItems = ") + len("let feedbackItems = ")
    end_idx = output_html.find(";", start_idx)
    json_data_str = output_html[start_idx:end_idx]
    
    # Try to parse the embedded JSON
    try:
        data = json.loads(json_data_str)
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(item.get("stakeholder") == "Sarah from Marketing" for item in data)
        assert any(item.get("design_element") == "footer" and item.get("conflict_id") is not None for item in data)
        
        # Verify specific conflict detection for footer elements
        footer_smaller_item = next((item for item in data if "footer" in item.get("design_element", "").lower() and "smaller" in item.get("suggested_action", "").lower()), None)
        footer_larger_item = next((item for item in data if "footer" in item.get("design_element", "").lower() and ("prominent" in item.get("suggested_action", "").lower() or "larger" in item.get("suggested_action", "").lower())), None)
        
        assert footer_smaller_item is not None, "Did not find 'footer smaller' item in embedded data"
        assert footer_larger_item is not None, "Did not find 'footer larger' item in embedded data"
        assert footer_smaller_item["conflict_id"] is not None
        assert footer_larger_item["conflict_id"] is not None
        assert footer_smaller_item["conflict_id"] == footer_larger_item["conflict_id"]

    except json.JSONDecodeError as e:
        assert False, f"Embedded JSON data is invalid: {e}"

def test_empty_input():
    output_html = process("")
    assert "Paste ALL your client feedback here" in output_html
    assert "textarea" in output_html
    assert "Synthesize Feedback" in output_html
    assert "feedback-card" not in output_html # Should not render canvas on empty input

def test_short_input():
    output_html = process("Just a short sentence.")
    assert "Paste ALL your client feedback here" in output_html
    assert "textarea" in output_html
    assert "Synthesize Feedback" in output_html
    assert "feedback-card" not in output_html # Should not render canvas on short input


# Manual execution of tests
# test_parse_feedback_text_basic()
# test_detect_conflicts()
# test_process_full_input()
# test_empty_input()
# test_short_input()
# print("All tests passed!")