#!/usr/bin/env python3
# Requirements: re, typing; for use in editorial headline analysis
# Tool: Headline Weight Scale
# Category: Office Automation
# Mode: 1 - Text analysis, computed output

import re
from typing import List, Tuple

def process(text: str) -> str:
    """Evaluate a headline draft for agency, consequence distribution, and lexical weight."""
    if not text.strip():
        return "Headline is empty. Please enter a headline to score."

    # Tokenize: lowercase, split on non-alpha
    tokens = re.findall(r'[a-z]+', text.lower())
    if not tokens:
        return "No words detected in headline."

    # Hardcoded word lists
    systemic_agents = ["council","board","officials","government","committee","zoning","policy","vote","decision","authority","mayor","commission"]
    affected_groups = ["residents","families","community","citizens","tenants","homeowners","people","workers","neighborhood"]
    victim_blame_triggers = ["struggle","suffer","face","endure","cope","bear","battle","lack","shortage"]
    systemic_consequences = ["shortage","crisis","lack","deficit","failure","problem","cutback"]
    euphemisms = ["challenges","difficulties","issues"]

    # Count occurrences
    agent_count = sum(1 for w in tokens if w in systemic_agents)
    affected_count = sum(1 for w in tokens if w in affected_groups)
    victim_count = sum(1 for w in tokens if w in victim_blame_triggers)
    consequence_count = sum(1 for w in tokens if w in systemic_consequences)
    euphemism_count = sum(1 for w in tokens if w in euphemisms)

    # Passive voice detection
    passive_pattern = re.compile(r'\b(were|was|been|being)\s+(\w+ed|(?:t|en|own))\b', re.IGNORECASE)
    passive_detected = bool(passive_pattern.search(text))

    # Agency score
    if agent_count > 0:
        agency = 100
    else:
        base_agency = 50 if passive_detected else 0
        add_agent = min(10 * agent_count, 100)  # zero if agent_count == 0
        agency = base_agency + add_agent

    # Consequence distribution score
    if affected_count > 0:
        conseq = 70
    else:
        conseq = 0
    if victim_count > 0 and agent_count == 0:
        conseq -= 20

    # Lexical weight score
    lexical = 50 + 10 * consequence_count - 5 * euphemism_count

    # Clamp all scores
    def clamp(x: int) -> int:
        return max(0, min(100, x))

    agency = clamp(agency)
    conseq = clamp(conseq)
    lexical = clamp(lexical)

    # Overall weighted score
    overall = int(round(0.4 * agency + 0.3 * conseq + 0.3 * lexical))
    overall = clamp(overall)

    # Flagged patterns
    flags = []
    if agent_count == 0:
        flags.append("Missing systemic actor — consider naming the decision-maker.")
    if victim_count > 0 and agent_count == 0:
        flags.append("Victim-blaming syntax: attributes consequence to those affected without naming the cause.")
    if passive_detected:
        flags.append("Passive voice obscures responsibility.")
    if affected_count == 0:
        flags.append("No impacted group identified — consider adding who is affected.")

    # Revision suggestions
    suggestions = []
    if agent_count == 0:
        # Extract the victim/adversarial phrase from original case
        original_words = re.findall(r'[A-Za-z]+', text)
        victim_phrase = "affected people"
        for i, w in enumerate(original_words):
            if w.lower() in affected_groups or w.lower() in victim_blame_triggers:
                victim_phrase = w
                # check if next word also belongs to these lists
                if i + 1 < len(original_words):
                    nw = original_words[i + 1]
                    if nw.lower() in affected_groups or nw.lower() in victim_blame_triggers:
                        victim_phrase += " " + nw
                break
        # Build agent phrase from word list
        agent_phrase = "Zoning board vote"
        verb_phrase = "creates"
        # Use a consequence word if available, else generic
        consequence_word = "shortage"
        for w in original_words:
            if w.lower() in systemic_consequences:
                consequence_word = w.lower()
                break
        actor_example = f"{agent_phrase} {verb_phrase} {consequence_word}"
        suggestions.append(f"Replace '{victim_phrase}' with '{actor_example}'.")
    elif passive_detected:
        suggestions.append("Try converting passive voice to active, e.g., 'The board decided…' instead of 'A decision was made…'.")

    # Build the report
    lines = []
    lines.append("HEADLINE WEIGHT SCORECARD")
    lines.append(f"Overall Score: {overall}/100")
    lines.append(f"Agency Score: {agency}/100")
    lines.append(f"Consequence Distribution Score: {conseq}/100")
    lines.append(f"Lexical Weight Score: {lexical}/100")
    lines.append("")
    lines.append("Flagged Patterns:")
    if flags:
        for i, f in enumerate(flags, 1):
            lines.append(f"  {i}. {f}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Revision Suggestions:")
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            lines.append(f"  {i}. {s}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()  # noqa: F821 - intentionally left for CLI mode if needed