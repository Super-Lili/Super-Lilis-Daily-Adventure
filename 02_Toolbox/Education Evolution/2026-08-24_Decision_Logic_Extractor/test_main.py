from main import process

def test_decision_logic_map():
    a = process(
        "Q3 launch: legal wanted a full compliance review and a two-week freeze, but the deadline was immovable, so I pushed back and scoped the review to only the new payment flow; it shipped on time with zero compliance issues.\n\n"
        "In the free tier project, we had only two engineers and the deadline slipped, so I cut the free tier's reporting dashboard and prioritized the core sync instead; retention stayed flat and support tickets did not spike.\n\n"
        "Agency clients kept asking for custom reporting, and we had a fixed quarterly budget, so I said no to one-off requests and built a template library instead; this actually increased upsells because sales had something to sell."
    )
    b = process(
        "We had a tight deadline and only two engineers, so I cut the reporting dashboard; it shipped without a support spike.\n\n"
        "A client kept asking for custom work on a fixed budget, so I said no and built reusable templates; upsells increased."
    )
    assert a and b
    assert a != b
    assert "# Decision Logic Map" in a
    assert "Recurring situations" in a
    assert "Conditional principles" in a
    assert len(a) > 300

def test_usage_hint_for_short_input():
    out = process("Only one story here.")
    assert "at least two decision stories" in out.lower()