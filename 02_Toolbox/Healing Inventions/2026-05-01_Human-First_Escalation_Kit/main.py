```python
def human_first_escalation_kit():
    """
    Generates a template for escalating an issue past a customer service chatbot
    to a human representative.
    """
    print("\n--- Human-First Escalation Kit: Get to a Real Person! ---\n")

    company_name = input("Which company's chatbot is giving you grief today? ")
    issue_summary = input("In a few words, what's your core issue? ")
    tried_with_bot = input("What have you already attempted with the bot (e.g., 'asked for human', 'rephrased question', 'read FAQs')? ")

    print("\n--- Your Direct-to-Human Message Template ---\n")
    print(f"Subject: URGENT: Immediate Human Assistance Required - {company_name} - Regarding: {issue_summary}")
    print("\nDear [Company Name Customer Service / Management],")
    print("\nI am writing to formally request immediate assistance from a live human representative. Your AI chatbot has been unable to resolve my issue and has actively prevented me from connecting with human support.")
    print(f"My core concern is: {issue_summary}")
    print(f"I have already spent considerable time trying to resolve this with your bot, attempting the following: {tried_with_bot}. The bot repeatedly failed to understand my request, provided irrelevant information, or looped back to previous responses.")
    print("This experience has been deeply frustrating. I require a direct connection to a human agent who can genuinely understand and address my problem.")
    print("Please provide a phone number, direct email, or connect me to a human representative without further delay.")
    print("\nSincerely frustrated,")
    print("[Your Name]")
    print("\n--- Lili's Extra Tips for Chatbot Battles ---")
    print("When stuck in a chatbot loop, try typing these phrases forcefully:")
    print(" - 'ESCALATE TO HUMAN'")
    print(" - 'COMPLAINT - I DEMAND A MANAGER'")
    print(" - 'I NEED TO SPEAK TO A SUPERVISOR'")
    print(" - 'THIS IS URGENT - HUMAN REQUIRED'")
    print("\nGood luck, fellow human. Don't let the bots win.")

if __name__ == "__main__":
    human_first_escalation_kit()
```