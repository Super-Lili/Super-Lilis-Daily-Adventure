def generate_escalation_message(company_name: str, issue_summary: str, tried_with_bot: str) -> str:
    """
    Generates a template for escalating an issue past a customer service chatbot
    to a human representative.
    """
    lines = [
        f"Subject: URGENT: Immediate Human Assistance Required - {company_name} - Regarding: {issue_summary}",
        "",
        "Dear [Company Name Customer Service / Management],",
        "",
        "I am writing to formally request immediate assistance from a live human representative. Your AI chatbot has been unable to resolve my issue and has actively prevented me from connecting with human support.",
        f"My core concern is: {issue_summary}",
        f"I have already spent considerable time trying to resolve this with your bot, attempting the following: {tried_with_bot}. The bot repeatedly failed to understand my request, provided irrelevant information, or looped back to previous responses.",
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


def process(text: str) -> str:
    """
    Generate an escalation message template.
    Input format: 'company | issue summary | what you tried'
    Or just provide a company name for a generic template.
    Falls back to a demo if empty.
    """
    parts = [p.strip() for p in text.split('|')]

    if len(parts) >= 3:
        company_name = parts[0] or "the company"
        issue_summary = parts[1] or "unresolved issue"
        tried_with_bot = parts[2] or "asked for human multiple times"
    elif len(parts) == 2:
        company_name = parts[0] or "the company"
        issue_summary = parts[1] or "unresolved issue"
        tried_with_bot = "asked for human multiple times, rephrased questions, read FAQs"
    elif len(parts) == 1 and parts[0]:
        company_name = parts[0]
        issue_summary = "[describe your issue here]"
        tried_with_bot = "[list what you tried with the chatbot]"
    else:
        company_name = "TechCorp"
        issue_summary = "account locked out and unable to access my data"
        tried_with_bot = "asked for human 5 times, used reset password link, rephrased question repeatedly"

    return generate_escalation_message(company_name, issue_summary, tried_with_bot)


def human_first_escalation_kit():
    """
    Interactive version: Generates a template for escalating an issue past a customer service chatbot.
    """
    print("\n--- Human-First Escalation Kit: Get to a Real Person! ---\n")

    company_name = input("Which company's chatbot is giving you grief today? ")
    issue_summary = input("In a few words, what's your core issue? ")
    tried_with_bot = input("What have you already attempted with the bot? ")

    print("\n--- Your Direct-to-Human Message Template ---\n")
    print(generate_escalation_message(company_name, issue_summary, tried_with_bot))


def _cli_main():
    human_first_escalation_kit()


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
