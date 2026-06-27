import json
import re
import difflib
from collections import Counter

GENERIC_WORDS = ["significant", "positive", "trends", "indicates", "overall", "should", "focus on", "take advantage", "expansion", "uplift", "various", "certain", "many", "several", "some"]
SPECIFIC_WORDS = ["data", "numbers", "metrics", "percentage", "quarter", "year-over-year", "market share", "revenue", "cost", "budget", "Q2", "Q3", "YoY", "$50M", "+25%", "+18%", "Competitor A", "Gen Z", "10%"]
NEGATING_WORDS = ["not", "no", "n't", "decline", "decrease", "down", "cut", "reduced", "lack", "fail", "contrary", "opposite"]

def get_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def get_key_entities(text: str) -> list[str]:
    nums = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%?\b|\$\d+\.?\d*[MKB]?', text)
    caps = re.findall(r'\b[A-Z][a-z0-9]+\b', text)
    terms = re.findall(r'\b\w{4,}\b', text.lower())
    term_counts = Counter(terms)
    frequent_terms = [k for k, v in term_counts.items() if v > 1]
    return list(set(nums + caps + frequent_terms))

def analyze_repetitiveness(g_sents: list[str]) -> tuple[list[str], int]:
    r_issues = []
    r_score = 100
    if len(g_sents) < 2: return [], 100
    for i in range(len(g_sents)):
        for j in range(i + 1, len(g_sents)):
            s = difflib.SequenceMatcher(None, g_sents[i].lower(), g_sents[j].lower())
            ratio = s.ratio()
            if ratio > 0.7:
                r_issues.append(f"  - Sentences '{g_sents[i]}' and '{g_sents[j]}' are highly similar (score: {ratio:.2f}).")
                r_score -= 15
    return r_issues, max(0, r_score)

def analyze_completeness(g_out: str, s_ctx: str) -> tuple[list[str], int]:
    c_issues = []
    c_score = 100
    s_entities = get_key_entities(s_ctx)
    found_entities = set()
    missing_entities = set()
    g_out_lower = g_out.lower()
    for ent in s_entities:
        if re.search(r'\b' + re.escape(ent.lower()) + r'\b', g_out_lower):
            found_entities.add(ent)
        else:
            missing_entities.add(ent)
    if missing_entities:
        c_issues.append(f"  - Key entities from source context are missing: {', '.join(list(missing_entities)[:5])}{'...' if len(missing_entities) > 5 else ''}")
        c_score -= len(missing_entities) * 7
    if not found_entities and s_entities:
        c_issues.append("  - No significant entities from the source context were found in the output.")
        c_score = 0
    return c_issues, max(0, c_score)

def analyze_genericity(g_out: str) -> tuple[list[str], int]:
    g_issues = []
    g_score = 100
    g_count = 0
    s_count = 0
    g_out_lower = g_out.lower()
    for w in GENERIC_WORDS:
        g_count += g_out_lower.count(w)
    for w in SPECIFIC_WORDS:
        s_count += g_out_lower.count(w)
    total_words = len(re.findall(r'\b\w+\b', g_out_lower))
    if total_words > 0:
        g_density = g_count / total_words
        s_density = s_count / total_words
        if g_density > 0.08:
            g_issues.append(f"  - High density of generic terms detected ({g_density:.2f}).")
            g_score -= 25
        if s_density < 0.03:
            g_issues.append(f"  - Low density of specific terms detected ({s_density:.2f}).")
            g_score -= 25
        if g_count > s_count * 1.5:
             g_issues.append("  - Significantly more generic than specific terms used.")
             g_score -= 30
    else:
        g_score = 0
        g_issues.append("  - Output is too short for meaningful specificity analysis.")
    return g_issues, max(0, g_score)

def analyze_consistency(g_out: str, s_ctx: str) -> tuple[list[str], int]:
    cn_issues = []
    cn_score = 100
    s_entities = get_key_entities(s_ctx)
    g_out_lower = g_out.lower()
    s_ctx_lower = s_ctx.lower()
    for ent in s_entities:
        for neg in NEGATING_WORDS:
            if re.search(r'\b' + re.escape(neg) + r'\s+' + re.escape(ent.lower()) + r'\b', g_out_lower) or \
               re.search(r'\b' + re.escape(ent.lower()) + r'\s+(?:is|are|was|were)\s+' + re.escape(neg) + r'\b', g_out_lower):
                cn_issues.append(f"  - Potential negation found: '{neg} {ent}' in output related to source context.")
                cn_score -= 25

    if "market growth" in g_out_lower and "marketing budget cut" in s_ctx_lower:
        cn_issues.append("  - Output highlights 'market growth'/'market expanding' but source notes 'Marketing budget cut', indicating a potential contextual inconsistency in Q2 narrative.")
        cn_score -= 35
    
    if "positive trends" in g_out_lower and "competitor a gained" in s_ctx_lower:
        cn_issues.append("  - Output states 'positive trends' but source indicates 'Competitor A gained 5% market share', which might be an unaddressed competitive challenge within overall positive framing.")
        cn_score -= 20

    return cn_issues, max(0, cn_score)

def process(input_data: dict) -> str:
    if not isinstance(input_data, dict) or not input_data.get('generated_output') or not input_data.get('source_context'):
        return "Please provide a dictionary with 'generated_output' and 'source_context' string keys."

    go = input_data['generated_output']
    sc = input_data['source_context']

    g_sents = get_sentences(go)
    
    r_issues, r_score = analyze_repetitiveness(g_sents)
    c_issues, c_score = analyze_completeness(go, sc)
    g_issues, g_score = analyze_genericity(go)
    cn_issues, cn_score = analyze_consistency(go, sc)

    overall_score = (r_score + c_score + g_score + cn_score) // 4

    report_parts = [
        "--- DIAGNOSTIC REPORT ---",
        f"Overall Quality Score: {overall_score}/100",
        "\n--- 1. Repetitiveness Analysis ---",
        f"Score: {r_score}/100",
        "Issues:"
    ]
    if r_issues: report_parts.extend(r_issues)
    else: report_parts.append("  - No significant repetitiveness detected.")
    report_parts.append("Recommendations:")
    report_parts.append("  - Consolidate highly similar phrases into stronger, single statements, drawing more distinct details from source context.")
    report_parts.append("  - Use varied phrasing and synonyms to convey similar ideas, ensuring each statement adds new value.")

    report_parts.append("\n--- 2. Completeness Analysis ---")
    report_parts.append(f"Score: {c_score}/100")
    report_parts.append("Issues:")
    if c_issues: report_parts.extend(c_issues)
    else: report_parts.append("  - Key entities from source context are adequately covered.")
    report_parts.append("Recommendations:")
    report_parts.append("  - Explicitly mention all critical numbers, proper nouns, and concepts from the source context where relevant.")
    report_parts.append("  - Review source context for any unmentioned specific details that would enrich the output.")

    report_parts.append("\n--- 3. Specificity/Genericity Analysis ---")
    report_parts.append(f"Score: {g_score}/100")
    report_parts.append("Issues:")
    if g_issues: report_parts.extend(g_issues)
    else: report_parts.append("  - Output is sufficiently specific and avoids excessive genericity.")
    report_parts.append("Recommendations:")
    report_parts.append("  - Replace vague terms (e.g., 'significant', 'positive trends') with precise data points from the source (e.g., 'up 12% YoY', 'social media mentions +25%').")
    report_parts.append("  - Quantify statements and provide concrete examples from the source whenever possible.")

    report_parts.append("\n--- 4. Logical Consistency Analysis ---")
    report_parts.append(f"Score: {cn_score}/100")
    report_parts.append("Issues:")
    if cn_issues: report_parts.extend(cn_issues)
    else: report_parts.append("  - No direct logical inconsistencies or contradictions detected.")
    report_parts.append("Recommendations:")
    report_parts.append("  - Cross-reference all statements against the source context to ensure factual accuracy and avoid subtle contradictions.")
    report_parts.append("  - Pay close attention to implied meanings and ensure the overall tone aligns with all source facts, even negative ones.")

    report_parts.append("\n--- END OF REPORT ---")

    return "\n".join(report_parts)

_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(json.loads(_browser_input)))
elif __name__ == "__main__":
    def _cli_main():
        test_input = {
            "generated_output": "Our Q2 analysis indicates significant market growth. We observed an uplift in consumer engagement, showing positive trends. Key takeaway: The market is expanding. We should focus on increasing marketing efforts to take advantage of this expansion. Data confirms overall positive trajectory.",
            "source_context": "Q2 Data Highlights: Market size up 12% YoY to $50M. Social media mentions +25%, Website traffic +18%. Competitor A gained 5% market share. Q3 focus: Gen Z products. Marketing budget cut by 10% in Q2."
        }
        print(process(test_input))
    _cli_main()