def generate_escalation_template(company_name: str, issue_summary: str, tried_with_bot: str) -> str:
    """Generates a human escalation message template."""
    lines = [
        f"Subject: URGENT: Immediate Human Assistance Required - {company_name} - Regarding: {issue_summary}",
        "",
        "Dear [Company Name Customer Service / Management],",
        "",
        "I am writing to formally request immediate assistance from a live human representative. "
        "Your AI chatbot has been unable to resolve my issue and has actively prevented me from connecting with human support.",
        f"My core concern is: {issue_summary}",
        f"I have already spent considerable time trying to resolve this with your bot, attempting the following: {tried_with_bot}. "
        "The bot repeatedly failed to understand my request, provided irrelevant information, or looped back to previous responses.",
        "This experience has been deeply frustrating. I require a direct connection to a human agent who can genuinely understand and address my problem.",
        "Please provide a phone number, direct email, or connect me to a human representative without further delay.",
        "",
        "Sincerely frustrated,",
        "[Your Name]",
        "",
        "--- Lili's Extra Tips for Chatbot Battles ---",
        "When stuck in a chatbot loop, try typing these phrases forcefully:",
        " - 'ESCALATE TO HUMAN'",
        " - 'COMPLAINT - I DEMAND A MANAGER'",
        " - 'I NEED TO SPEAK TO A SUPERVISOR'",
        " - 'THIS IS URGENT - HUMAN REQUIRED'",
        "",
        "Good luck, fellow human. Don't let the bots win.",
    ]
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Generate a human-first escalation message from company/issue info."""
    if not text.strip():
        return generate_escalation_template(
            "[Company Name]",
            "[Describe your issue here]",
            "asked for human, rephrased question, read FAQs"
        )
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    company = lines[0] if len(lines) > 0 else "[Company Name]"
    issue = lines[1] if len(lines) > 1 else lines[0] if lines else "[Your issue]"
    tried = lines[2] if len(lines) > 2 else "asked for human, rephrased question, read FAQs"
    return generate_escalation_template(company, issue, tried)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(process("Example Corp\nRefund not processed\nasked for human, tried FAQ, rephrased 3 times"))