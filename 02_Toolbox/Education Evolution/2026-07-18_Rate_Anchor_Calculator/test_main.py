from main import process

def test_process_with_data():
    input1 = "SaaS Dashboard UX audit|B2B startup|Heuristic eval, wireframes, 3 revision rounds|30|135|Extra discovery call with CTO (2h unpaid), explained design system to junior dev|10% discount for first engagement\nLanding page content strategy|Fintech|Copy audit, tone guide, 5 pages|15|150|Wrote microcopy for 3 error states not in original scope|None\nMobile app UX writing|Healthtech|User flow copy, 2 rounds stakeholder review|25|140|Unpaid stakeholder alignment meeting (1.5h)|Equity in lieu of partial payment\nNEW PROJECT:"
    output1 = process(input1)
    assert len(output1) > 100, "Output should be substantial"
    assert "RATE SUMMARY" in output1
    assert "HIDDEN LABOR ANALYSIS" in output1
    assert "CONCESSION PATTERNS" in output1
    assert "ANCHORED RATE RECOMMENDATION" in output1

def test_process_empty():
    output_empty = process("")
    assert "Please paste your project log" in output_empty

def test_process_different_inputs():
    out_a = process("Project A|Client X|Scope A|10|100|no extra|none\nNEW PROJECT:")
    out_b = process("Project B|Client Y|Scope B|5|200|unpaid training|discount\nNEW PROJECT:")
    assert out_a != out_b, "Different inputs should yield different outputs"