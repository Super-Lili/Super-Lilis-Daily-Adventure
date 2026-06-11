import argparse
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Using a simulated langextract/LLM for demonstration purposes.
# In a real-world scenario, this would integrate with an actual LLM service
# (e.g., via an API) to perform advanced text analysis and extraction.

def _simulate_langextract_concepts(text: str) -> List[str]:
    """
    Simulates extracting key concepts from text.
    In a real tool, this would use a robust LLM or langextract.
    """
    common_keywords = ['data', 'analysis', 'python', 'tools', 'process',
                       'information', 'knowledge', 'synthesis', 'learning',
                       'connections', 'system', 'flow', 'structure', 'context']
    concepts = [word for word in common_keywords if word in text.lower()]
    # Add some simple heuristic extraction
    sentences = text.split('.')
    for sentence in sentences:
        if 'key concept' in sentence.lower() or 'main idea' in sentence.lower():
            start_index = max(sentence.lower().find('key concept'), sentence.lower().find('main idea'))
            if start_index != -1:
                potential_concept = sentence[start_index:].split(':')[1].strip() if ':' in sentence[start_index:] else sentence[start_index + len('key concept'):].strip()
                if len(potential_concept.split()) < 5 and potential_concept: # simple length check
                    concepts.append(potential_concept.strip('.'))
    return list(set(concepts[:5])) # Limit to a few for demo clarity


def _simulate_langextract_relationships(concept1: str, concept2: str, text: str) -> str:
    """
    Simulates identifying a relationship between two concepts from text.
    In a real tool, this would use a robust LLM or langextract.
    """
    text_lower = text.lower()
    if concept1.lower() in text_lower and concept2.lower() in text_lower:
        if f"{concept1.lower()} relates to {concept2.lower()}" in text_lower:
            return f"relates to {concept2}"
        if f"{concept1.lower()} is a type of {concept2.lower()}" in text_lower:
            return f"is a type of {concept2}"
        if f"{concept1.lower()} enables {concept2.lower()}" in text_lower:
            return f"enables {concept2}"
        return "is connected to"
    return "unclear connection"


def load_learning_material(file_paths: List[Path]) -> str:
    """
    Loads text content from multiple file paths.
    Handles FileNotFoundError and decoding errors.
    """
    combined_text = []
    for f_path in file_paths:
        if not f_path.is_file():
            print(f"Error: File not found at '{f_path}'. Skipping this file.")
            continue
        try:
            with open(f_path, 'r', encoding='utf-8') as f:
                combined_text.append(f.read())
        except UnicodeDecodeError:
            print(f"Error: Could not decode '{f_path}' with UTF-8. Trying Latin-1.")
            try:
                with open(f_path, 'r', encoding='latin-1') as f:
                    combined_text.append(f.read())
            except Exception as e:
                print(f"Error: Could not read '{f_path}' due to encoding issue: {e}. Skipping.")
        except Exception as e:
            print(f"Error: Failed to read '{f_path}': {e}. Skipping.")
    return "\n\n".join(combined_text)


def extract_and_refine_concepts(text: str) -> List[str]:
    """
    Extracts initial concepts and allows user to refine them.
    """
    if not text.strip():
        print("No text provided for concept extraction. Returning empty list.")
        return []

    initial_concepts = _simulate_langextract_concepts(text)
    print("\n--- Initial Concept Extraction ---")
    if not initial_concepts:
        print("No key concepts automatically identified. Let's add some!")
    else:
        print("Here are some concepts I've sparked from your material:")
        for i, concept in enumerate(initial_concepts):
            print(f"  {i+1}. {concept}")

    refined_concepts = []
    while True:
        user_input = input("\nAdd a concept (or type 'done' to finish, 'list' to see current, 'clear' to restart): ").strip()
        if user_input.lower() == 'done':
            break
        elif user_input.lower() == 'list':
            if not refined_concepts:
                print("No concepts added yet.")
            else:
                print("Current concepts:")
                for i, c in enumerate(refined_concepts):
                    print(f"  {i+1}. {c}")
        elif user_input.lower() == 'clear':
            refined_concepts = []
            print("Concepts cleared. Starting fresh!")
        elif user_input:
            refined_concepts.append(user_input)
            print(f"'{user_input}' added.")
        else:
            print("Please enter a valid concept or command.")

    return list(dict.fromkeys(refined_concepts))  # Unique, preserve insertion order


def define_relationships(concepts: List[str], full_text: str) -> Dict[str, Dict[str, str]]:
    """
    Guides the user to define relationships between concepts.
    """
    if len(concepts) < 2:
        print("\nNeed at least two concepts to define relationships. Skipping relationship definition.")
        return {}

    print("\n--- Defining Relationships ---")
    print("Let's connect your concepts. For each pair, describe how they relate.")
    relationships = {} # Format: {concept1: {concept2: "relationship_description"}}

    for i, c1 in enumerate(concepts):
        for j, c2 in enumerate(concepts):
            if i >= j: # Avoid self-relations and duplicate pairs
                continue

            # Suggest an initial relationship based on text (simulated)
            suggested_rel = _simulate_langextract_relationships(c1, c2, full_text)
            print(f"\nHow does '{c1}' relate to '{c2}'? (e.g., 'enables', 'is a type of', '{suggested_rel}')")
            user_rel = input(f"Relationship for '{c1}' and '{c2}': ").strip()

            if user_rel:
                if c1 not in relationships:
                    relationships[c1] = {}
                relationships[c1][c2] = user_rel
                print(f"Relationship recorded: '{c1}' --[{user_rel}]--> '{c2}'")
            else:
                print("No relationship defined for this pair. Moving on.")
    return relationships


def generate_recall_questions(structured_knowledge: Dict[str, Any]) -> List[str]:
    """
    Generates open-ended recall questions from structured knowledge.
    """
    print("\n--- Generating Recall Questions ---")
    questions = []
    concepts = structured_knowledge.get("concepts", [])
    relationships = structured_knowledge.get("relationships", {})

    if not concepts and not relationships:
        questions.append("Based on your learning, what are the most crucial insights you gained?")
        questions.append("Can you explain the main theme of the materials in your own words?")
        return questions

    # Questions based on individual concepts
    for concept in concepts:
        questions.append(f"Explain '{concept}' in your own words, assuming I know nothing about it.")
        questions.append(f"What are the key characteristics or components of '{concept}'?")

    # Questions based on relationships
    for c1, connections in relationships.items():
        for c2, relation in connections.items():
            questions.append(f"How does '{c1}' '{relation}' '{c2}'? Provide a specific example.")
            questions.append(f"Describe the connection between '{c1}' and '{c2}' and why it's important.")

    # General synthesis questions
    if concepts:
        questions.append(f"Considering all the concepts ({', '.join(concepts)}), what is the overarching principle?")
    questions.append("If you had to teach this to someone, what 3 key takeaways would you emphasize?")

    return list(set(questions)) # Remove duplicates


def save_structured_knowledge(structured_data: Dict[str, Any], output_path: Path):
    """
    Saves the structured knowledge to a Markdown file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Synthesis Spark: Your Knowledge Weave\n\n")
            f.write(f"## Date: {structured_data.get('date', 'N/A')}\n\n")

            f.write("## Concepts:\n")
            if structured_data.get("concepts"):
                for concept in structured_data["concepts"]:
                    f.write(f"- {concept}\n")
            else:
                f.write("No concepts defined.\n")

            f.write("\n## Relationships:\n")
            if structured_data.get("relationships"):
                for c1, connections in structured_data["relationships"].items():
                    for c2, relation in connections.items():
                        f.write(f"- **{c1}** {relation} **{c2}**\n")
            else:
                f.write("No relationships defined.\n")

            f.write("\n---\n\n")
            f.write("## Raw Input Snippets (for reference):\n")
            f.write("```\n")
            f.write(structured_data.get("full_text_snippet", "No raw text snippet saved."))
            f.write("\n```\n")

        print(f"\nStructured knowledge saved to '{output_path}'.")
    except Exception as e:
        print(f"Error: Could not save structured knowledge to '{output_path}': {e}.")


def save_recall_questions(questions: List[str], output_path: Path):
    """
    Saves the generated recall questions to a text file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Synthesis Spark: Your Recall Questions\n\n")
            f.write(f"## Date: {Path(output_path).stem.split('_')[0]}\n\n") # Extract date from filename

            if questions:
                for i, q in enumerate(questions):
                    f.write(f"{i+1}. {q}\n\n")
            else:
                f.write("No recall questions generated.\n")

        print(f"Recall questions saved to '{output_path}'.")
    except Exception as e:
        print(f"Error: Could not save recall questions to '{output_path}': {e}.")


def main(args: List[str] = None):
    """
    Main function to parse arguments and run the Synthesis Spark tool.
    """
    parser = argparse.ArgumentParser(
        description="""
        Synthesis Spark: Turn fragmented learning materials into connected knowledge
        and generate recall questions to reinforce your understanding.
        """
    )
    parser.add_argument(
        '--files',
        nargs='+',
        required=True,
        type=Path,
        help="One or more paths to text files containing your learning notes or articles."
    )
    parser.add_argument(
        '--output_prefix',
        type=str,
        default="synthesis_spark",
        help="Prefix for output files (e.g., 'my_topic' will generate 'my_topic_knowledge.md' and 'my_topic_questions.txt')."
    )

    if args is None:
        parsed_args = parser.parse_args()
    else:
        parsed_args = parser.parse_args(args)

    if not parsed_args.files:
        print("Error: No input files provided. Please use --files to specify your learning materials.")
        return

    full_text = load_learning_material(parsed_args.files)
    if not full_text.strip():
        print("No content found in the provided files. Exiting.")
        return

    print(f"\nHello, human! Let's spark some synthesis from your {len(parsed_args.files)} learning file(s).")
    print("This tool will guide you to clarify concepts and connect ideas.")

    concepts = extract_and_refine_concepts(full_text)
    if not concepts:
        print("\nNo concepts defined. Cannot proceed with relationships or questions. Exiting.")
        return

    relationships = define_relationships(concepts, full_text)

    today_date = parsed_args.output_prefix # Using prefix as identifier for simplicity here.
    structured_knowledge = {
        "date": today_date,
        "concepts": concepts,
        "relationships": relationships,
        "full_text_snippet": full_text[:500] + "..." if len(full_text) > 500 else full_text # Store a snippet for context
    }

    questions = generate_recall_questions(structured_knowledge)

    knowledge_output_path = Path(f"{parsed_args.output_prefix}_knowledge.md")
    questions_output_path = Path(f"{parsed_args.output_prefix}_questions.txt")

    save_structured_knowledge(structured_knowledge, knowledge_output_path)
    save_recall_questions(questions, questions_output_path)

    print("\n--- Synthesis Spark Complete! ---")
    print(f"Your synthesized knowledge is in: {knowledge_output_path}")
    print(f"Your recall questions are in: {questions_output_path}")
    print("Go forth and connect those dots!")

def process(text: str = "") -> str:
    """Extract key concepts from learning notes and generate recall questions."""
    if not text.strip():
        return "Paste your learning notes or article text to extract concepts and generate recall questions."
    concepts = _simulate_langextract_concepts(text)
    if not concepts:
        concepts = ["main theme", "key idea"]
    sk = {"concepts": concepts, "relationships": {}}
    questions = generate_recall_questions(sk)
    out = ["## Key Concepts Identified:", ""]
    for c in concepts:
        out.append(f"- {c}")
    out += ["", "## Recall Questions:", ""]
    for i, q in enumerate(questions[:10], 1):
        out.append(f"{i}. {q}")
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Create dummy input files for demonstration
    demo_content_1 = """
    This article introduces the core concept of 'Data Flow Diagrams'.
    A key concept is that DFDs illustrate how data moves through a system.
    They are not about process logic, but rather the information path.
    Another key concept is 'External Entities', which are sources or sinks of data.
    DFDs often relate to 'Process Modeling' in software engineering.
    """
    demo_content_2 = """
    Understanding 'System Analysis' requires grasping several tools.
    'Use Case Diagrams' are another important tool, showing user interactions.
    They enable 'Requirements Gathering' by focusing on user goals.
    Data Flow Diagrams are a component of wider system analysis.
    The goal of System Analysis is to build robust 'Information Systems'.
    """

    Path("demo_learning_1.txt").write_text(demo_content_1)
    Path("demo_learning_2.txt").write_text(demo_content_2)

    print("--- Running Synthesis Spark with Demo Data ---")
    print("\nTo experience the full interactive flow, run:")
    print("python your_script_name.py --files demo_learning_1.txt demo_learning_2.txt --output_prefix my_synthesis")
    print("and follow the prompts to define concepts and relationships.")
    print("\nFor this automated `if __name__ == '__main__':` demo, we'll just ensure files are created.")

    print("\n--- Demo Instructions ---")
    print("Run this script interactively: `python synthesis_spark.py --files demo_learning_1.txt demo_learning_2.txt --output_prefix demo_output`")
    print("You will be prompted to enter concepts and relationships.")
    print("Output files will be generated as 'demo_output_knowledge.md' and 'demo_output_questions.txt'.")

    try:
        main(["--files", "demo_learning_1.txt", "demo_learning_2.txt", "--output_prefix", "demo_output"])
    except EOFError:
        print("\nDemo interrupted: EOFError. Please run interactively to provide input.")
    except Exception as e:
        print(f"\nAn error occurred during demo execution: {e}")

    # Clean up demo files after potential execution
    # Path("demo_learning_1.txt").unlink(missing_ok=True)
    # Path("demo_learning_2.txt").unlink(missing_ok=True)
    # Path("demo_output_knowledge.md").unlink(missing_ok=True)
    # Path("demo_output_questions.txt").unlink(missing_ok=True)