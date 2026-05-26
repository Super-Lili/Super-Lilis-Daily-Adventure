import re


def keyword_compass(job_description):
    """
    Extracts potential keywords from a job description to help tailor a resume.
    Focuses on common technical terms, skills, and action verbs.
    """
    if not isinstance(job_description, str) or not job_description.strip():
        return "Please provide a valid job description (string)."

    stop_words = set([
        "a", "an", "the", "and", "or", "to", "in", "on", "with", "for", "of",
        "is", "are", "be", "has", "have", "you", "we", "our", "your", "this",
        "that", "as", "by", "from", "at", "about", "also", "will", "must",
        "can", "should", "etc", "e.g.", "i.e.", "ability", "experience", "strong",
        "demonstrated", "proven", "excellent", "work", "develop", "manage",
        "create", "build", "implement", "design", "ensure", "perform", "responsibilities",
        "required", "skills", "knowledge", "understanding", "role", "key", "successful",
        "candidate", "team", "project", "systems", "solutions", "environment"
    ])

    words = re.findall(r'\b\w+\b', job_description.lower())

    filtered_words = {word for word in words if word not in stop_words and len(word) > 1}

    sorted_keywords = sorted(list(filtered_words))

    if not sorted_keywords:
        return "No significant keywords found."

    return "Suggested keywords: " + ", ".join(sorted_keywords)


def process(text: str) -> str:
    """
    Extract keywords from a job description.
    Input: the job description text.
    Falls back to a sample job description if empty.
    """
    if not text.strip():
        text = """
        We are seeking a highly motivated Software Engineer with proven experience in Python,
        cloud platforms (AWS, Azure), and database management (SQL, NoSQL).
        The ideal candidate will develop and deploy scalable web applications,
        contribute to architectural design, and collaborate with cross-functional teams.
        Strong problem-solving skills and a solid understanding of agile methodologies are required.
        Experience with Docker and Kubernetes is a plus.
        """
    return keyword_compass(text)


def _cli_main():
    sample_jd = """
    We are seeking a highly motivated Software Engineer with proven experience in Python,
    cloud platforms (AWS, Azure), and database management (SQL, NoSQL).
    The ideal candidate will develop and deploy scalable web applications,
    contribute to architectural design, and collaborate with cross-functional teams.
    Strong problem-solving skills and a solid understanding of agile methodologies are required.
    Experience with Docker and Kubernetes is a plus.
    """

    keywords = keyword_compass(sample_jd)
    print(keywords)

    sample_jd_short = "Develop innovative solutions using machine learning and data science."
    keywords_short = keyword_compass(sample_jd_short)
    print(keywords_short)

    sample_jd_empty = ""
    keywords_empty = keyword_compass(sample_jd_empty)
    print(keywords_empty)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
