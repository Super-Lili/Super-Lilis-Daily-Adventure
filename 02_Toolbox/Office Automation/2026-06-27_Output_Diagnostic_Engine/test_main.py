from main import process
import json

def test_process_valid_input():
    input_data = {
        "generated_output": "Our Q2 analysis indicates significant market growth. We observed an uplift in consumer engagement, showing positive trends. Key takeaway: The market is expanding. We should focus on increasing marketing efforts to take advantage of this expansion. Data confirms overall positive trajectory.",
        "source_context": "Q2 Data Highlights: Market size up 12% YoY to $50M. Social media mentions +25%, Website traffic +18%. Competitor A gained 5% market share. Q3 focus: Gen Z products. Marketing budget cut by 10% in Q2."
    }
    result = process(input_data)
    assert isinstance(result, str)
    assert len(result) > 500
    assert "Repetitiveness Analysis" in result
    assert "Completeness Analysis" in result
    assert "Specificity/Genericity Analysis" in result
    assert "Logical Consistency Analysis" in result
    assert "Overall Quality Score:" in result

def test_process_empty_input():
    input_data = {"generated_output": "", "source_context": ""}
    result = process(input_data)
    assert "Please provide" in result

def test_process_different_input():
    input_data = {
        "generated_output": "The project is on track. We are moving forward with the plan. All tasks are progressing well. The team is dedicated and making good progress. We anticipate a successful completion.",
        "source_context": "Project status: Task A (80% complete), Task B (20% complete, blocked by vendor), Task C (not started). Deadline: next week. Budget: 10% over."
    }
    result = process(input_data)
    assert isinstance(result, str)
    assert "Repetitiveness" in result
    assert "missing: Task B" in result or "missing: Task C" in result or "missing: vendor" in result
    assert "High density of generic terms" in result
    assert "potential contextual inconsistency" in result or "Potential negation found" in result