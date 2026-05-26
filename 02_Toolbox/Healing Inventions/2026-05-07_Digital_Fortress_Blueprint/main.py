import random
import string


def generate_strong_password():
    """Generates a suggestion for a strong password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(16))
    return password


def get_security_advice() -> str:
    """Returns essential digital security advice as a string."""
    lines = [
        "## Digital Fortress Blueprint",
        "",
        "1. Use unique, strong passwords for every account. Consider a password manager.",
        f"   Example strong password: `{generate_strong_password()}`",
        "2. Enable Two-Factor Authentication (2FA) wherever possible, but understand its limits.",
        "3. Be wary of phishing attempts and suspicious links.",
        "4. Regularly review your account activity and connected apps.",
        "5. Demand better security and support from platforms that host your digital life.",
        "",
        "Remember: Your digital security is a shared responsibility, but ultimately, your vigilance is key.",
    ]
    return "\n".join(lines)


def process(text: str = "") -> str:
    """Return digital security advice, with a freshly generated example password."""
    return get_security_advice()


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    print(get_security_advice())