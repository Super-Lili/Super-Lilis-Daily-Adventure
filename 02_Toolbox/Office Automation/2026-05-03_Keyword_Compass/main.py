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


def process(text: str = "") -> str:
    """Extract resume-relevant keywords from a job description."""
    if not text.strip():
        return "Paste a job description to extract relevant keywords for your resume."
    return keyword_compass(text)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == '__main__':
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