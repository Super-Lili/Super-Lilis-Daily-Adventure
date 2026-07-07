from main import process

def test_process():
    inputs = [
        "the way the steam curled off my tea this morning",
        "the weight of a heavy novel in my hands",
        "tasting the salt on my lips after a walk by the pier"
    ]
    results = [process(t) for t in inputs]
    for r in results:
        assert r and isinstance(r, str), "output must be a non-empty string"
        assert "anchor" in r.lower(), "output must reference anchors"
    # The page is identical for every input (static) but must still be returned
    assert len(set(results)) == 1, "static page should be returned consistently"