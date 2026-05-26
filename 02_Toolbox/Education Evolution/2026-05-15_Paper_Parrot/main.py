import argparse
import re
import os
import csv
from typing import List, Dict

# Requirements:
# pip install PyPDF2


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A string containing all text from the PDF, or an empty string if an error occurs.
    """
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_path}'. Please check the path.")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF '{pdf_path}': {e}")
        return ""


def identify_key_points(text: str) -> List[Dict[str, str]]:
    """
    Identifies potential key points (arguments, methods, findings) from the text
    and suggests questions and prompts for active recall.

    Args:
        text: The full text of the paper.

    Returns:
        A list of dictionaries, each containing a 'question', 'answer_prompt',
        'original_snippet', and 'type'.
    """
    key_points = []

    patterns = {
        "argument": r"(?:this paper|we)\s+(?:propose|argue|demonstrate|show|present|suggest|contend)\s+([\w\s,-]+(?:\s+that|\s+how|\s+the)?(?:[^.!?\n]{10,150}[.!?]))",
        "methodology": r"(?:our approach|the method|we utilized|we employed|the experimental design involved)\s+([\w\s,-]+(?:[^.!?\n]{10,150}[.!?]))",
        "finding": r"(?:our results|we found|the study revealed|the data indicate|it was observed)\s+([\w\s,-]+(?:[^.!?\n]{10,150}[.!?]))"
    }

    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    for para_idx, paragraph in enumerate(paragraphs):
        for key_type, pattern in patterns.items():
            for match in re.finditer(pattern, paragraph, re.IGNORECASE):
                snippet = match.group(0).strip()
                extracted_content = match.group(1).strip()

                question = ""
                answer_prompt = ""

                if key_type == "argument":
                    question = "What is the main argument or proposal of this section?"
                    answer_prompt = f"Summarize the argument presented: '{extracted_content}'"
                elif key_type == "methodology":
                    question = "Describe the key methodology or approach used here."
                    answer_prompt = f"Explain the method highlighted: '{extracted_content}'"
                elif key_type == "finding":
                    question = "What are the main findings or results reported in this section?"
                    answer_prompt = f"Detail the findings: '{extracted_content}'"

                if question and answer_prompt:
                    key_points.append({
                        "Type": key_type.capitalize(),
                        "Question": question,
                        "Answer Prompt": answer_prompt,
                        "Original Snippet": snippet,
                        "Source Paragraph": para_idx + 1
                    })
    return key_points


def save_insights_to_csv(insights: List[Dict[str, str]], output_path: str):
    """
    Saves the extracted insights to a CSV file without using pandas.

    Args:
        insights: A list of dictionaries containing the extracted key points.
        output_path: The path where the CSV file will be saved.
    """
    if not insights:
        print("No insights to save.")
        return

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(insights[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in insights:
                writer.writerow(row)
        print(f"Insights successfully saved to '{output_path}'")
    except Exception as e:
        print(f"Error saving insights to CSV '{output_path}': {e}")


def process(text: str) -> str:
    """
    Extract key points from plain text (academic paper content).
    In browser mode, accepts raw text instead of a PDF file.
    """
    if not text.strip():
        return "This tool needs academic paper text as input. Paste the text of a paper to extract key points."

    insights = identify_key_points(text)

    if not insights:
        return "Paper Parrot couldn't find any prominent arguments, methodologies, or findings in this text. Try pasting a section with phrases like 'we propose', 'our results', 'we found', etc."

    lines = ["Paper Parrot: Active Recall Insights", "=" * 40, ""]
    for i, insight in enumerate(insights, 1):
        lines.append(f"[{i}] Type: {insight['Type']}")
        lines.append(f"    Question: {insight['Question']}")
        lines.append(f"    Prompt:   {insight['Answer Prompt']}")
        lines.append("")

    lines.append(f"Found {len(insights)} insight(s). Time to engage with your new knowledge!")
    return "\n".join(lines)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Paper Parrot: Extracts key points from academic PDFs and generates active recall prompts."
    )
    parser.add_argument("--input_pdf", type=str, required=True,
                        help="Path to the input PDF academic paper.")
    parser.add_argument("--output_csv", type=str, default="paper_parrot_insights.csv",
                        help="Path to the output CSV file where insights will be saved.")

    parsed_args = parser.parse_args(args)

    print(f"Flapping wings for Paper Parrot to process '{parsed_args.input_pdf}'...")

    paper_text = extract_text_from_pdf(parsed_args.input_pdf)
    if not paper_text:
        print("Exiting due to empty or unreadable PDF text.")
        return

    insights = identify_key_points(paper_text)

    if not insights:
        print("Hmm, Paper Parrot couldn't find any prominent arguments, methodologies, or findings in this paper.")
        return

    save_insights_to_csv(insights, parsed_args.output_csv)
    print("\nPaper Parrot finished its squawk! Time to engage with your new insights.")


def _cli_main():
    demo_pdf_content = """
    A Novel Approach to Cognitive Load Reduction in Online Learning Environments

    Abstract
    Online learning has gained significant traction, yet students often face high cognitive load, impacting retention. This paper proposes a novel algorithm, called 'Adaptive Content Chunking' (ACC), designed to dynamically adjust content presentation based on learner performance metrics. Our methodology involved a randomized controlled trial with 200 university students across various disciplines. We utilized eye-tracking data and post-lecture quizzes to assess cognitive load and comprehension. The experimental design involved three groups: control (standard presentation), static chunking, and ACC.

    Introduction
    Cognitive overload is a pervasive challenge in digital education. Existing solutions often simplify content uniformly, which may not cater to individual learning paces. This research aims to address this adaptive challenge. We argue that dynamic content delivery can significantly enhance learning outcomes.

    Methodology
    Our approach employed a custom-built learning platform integrating advanced eye-tracking hardware and a real-time quiz engine. Participants completed modules on introductory physics. The study revealed that students in the ACC group demonstrated a 15% improvement in quiz scores and reported lower perceived cognitive load compared to the control group. Data indicate that early intervention with smaller content chunks was crucial. We found a strong correlation between reduced gaze duration on distracting elements and improved retention.

    Results
    The primary finding was the significant reduction in cognitive load for students using the ACC algorithm. Specifically, ANOVA tests showed a statistically significant difference (p < 0.01) in quiz performance. We observed that the ACC group required fewer repetitions to achieve mastery.

    Conclusion
    This study demonstrates the efficacy of the Adaptive Content Chunking algorithm in mitigating cognitive load and improving learning outcomes in online environments. We suggest future work could explore personalized chunking strategies for different subject matters.
    """

    demo_pdf_path = "demo_paper.pdf"
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(demo_pdf_path, pagesize=letter)
        textobject = c.beginText()
        textobject.setTextOrigin(50, 750)
        textobject.setFont("Helvetica", 12)

        for line in demo_pdf_content.split('\n'):
            textobject.textLine(line)

        c.drawText(textobject)
        c.save()
        print(f"Created dummy PDF: '{demo_pdf_path}'")

        main(args=["--input_pdf", demo_pdf_path, "--output_csv", "demo_paper_insights.csv"])

        if os.path.exists(demo_pdf_path):
            os.remove(demo_pdf_path)
            print(f"Cleaned up dummy PDF: '{demo_pdf_path}'")

    except ImportError:
        print("reportlab not installed — running with simulated text for demo.")
        insights_for_demo = identify_key_points(demo_pdf_content)
        save_insights_to_csv(insights_for_demo, "demo_paper_insights_simulated.csv")
    except Exception as e:
        print(f"Error during demo: {e}")
        print("Proceeding with simulated text for demo.")
        paper_text_for_demo = demo_pdf_content
        insights_for_demo = identify_key_points(paper_text_for_demo)
        save_insights_to_csv(insights_for_demo, "demo_paper_insights_simulated.csv")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
