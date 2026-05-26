import random
import string


def generate_strong_password(length=16):
    """Generates a suggestion for a strong password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def get_security_advice(password_length=16):
    """Returns essential digital security advice as a string."""
    lines = [
        "--- Digital Fortress Blueprint ---",
        "1. Use unique, strong passwords for every account. Consider a password manager.",
        f"   Example strong password: {generate_strong_password(password_length)}",
        "2. Enable Two-Factor Authentication (2FA) wherever possible, but understand its limits.",
        "3. Be wary of phishing attempts and suspicious links.",
        "4. Regularly review your account activity and connected apps.",
        "5. Demand better security and support from platforms that host your digital life.",
        "",
        "Remember: Your digital security is a shared responsibility, but ultimately, your vigilance is key.",
    ]
    return "\n".join(lines)


def process(text: str) -> str:
    """
    Generate digital security advice and a strong password.
    Optionally accepts a password length as input (e.g. '20').
    """
    length = 16
    try:
        val = int(text.strip())
        if 8 <= val <= 64:
            length = val
    except (ValueError, AttributeError):
        pass

    return get_security_advice(password_length=length)


def _cli_main():
    print(get_security_advice())


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
