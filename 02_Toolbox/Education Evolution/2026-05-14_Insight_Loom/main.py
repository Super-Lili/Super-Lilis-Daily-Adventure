# requirements:
# pandas
# networkx
# matplotlib (optional, for visualization)
# argparse
# pathlib

import argparse
import json
import networkx as nx
import pandas as pd
from pathlib import Path

# Try to import matplotlib; if not available, the graph visualization will be skipped.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    # print("Warning: 'matplotlib' not found. Graph visualization features will be unavailable.")
    plt = None
    MATPLOTLIB_AVAILABLE = False


def create_concept_map_data(input_file: Path, output_json: Path, output_graph_png: Path):
    """
    Guides the user through creating a concept map from input text,
    then saves the map data and a visualization.
    """
    print(f"Hey there, knowledge explorer! Let's weave some insights from {input_file.name}. ✨")
    
    if not input_file.exists():
        print(f"Oops! The file '{input_file}' doesn't exist. Double-check your path and try again!")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Uh oh, couldn't read your file! Error: {e}")
        return

    print("\nFirst, let's identify the core concepts. Think of the big ideas, the nouns, the key terms.")
    print("Your text snippet:\n---")
    print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
    print("---\n")

    # Use a DataFrame to store concepts
    concepts_df = pd.DataFrame(columns=['concept_name', 'definition'])
    # Use a DataFrame to store relationships
    relationships_df = pd.DataFrame(columns=['source', 'target', 'type'])

    while True:
        concept_name = input("Enter a key concept (or 'done' to finish concepts): ").strip()
        if concept_name.lower() == 'done':
            break
        if not concept_name:
            continue
        
        # Check for duplicates before adding
        if concept_name in concepts_df['concept_name'].values:
            print(f"'{concept_name}' is already a concept. Let's try a new one or 'done'.")
            continue

        definition = input(f"Define '{concept_name}': ").strip()
        new_concept = pd.DataFrame([{'concept_name': concept_name, 'definition': definition}])
        concepts_df = pd.concat([concepts_df, new_concept], ignore_index=True)
        print(f"Awesome! '{concept_name}' added. Current concepts: {', '.join(concepts_df['concept_name'].tolist())}")
        print("-" * 30)

    if concepts_df.empty:
        print("No concepts added! We need some ideas to connect. Let's try again another time. 😊")
        return

    print("\nNow, let's connect those brilliant ideas! What relationships do you see?")
    print("Think: 'Concept A --[relationship type]--> Concept B'")
    print("For example: 'Cause-Effect', 'Is-A', 'Part-Of', 'Influences'.")

    available_concepts = concepts_df['concept_name'].tolist()
    if len(available_concepts) < 2:
        print("Not enough concepts to form relationships. We need at least two! Maybe add more next time?")
        # Still save what we have, even if no relationships
        save_concept_map_data(concepts_df, relationships_df, output_json, output_graph_png)
        return

    while True:
        print(f"\nYour concepts: {', '.join(available_concepts)}")
        source_concept = input("Source concept (or 'done' to finish relationships): ").strip()
        if source_concept.lower() == 'done':
            break
        if source_concept not in available_concepts:
            print(f"Hmm, '{source_concept}' isn't in your concept list. Let's pick from: {', '.join(available_concepts)}")
            continue

        target_concept = input("Target concept: ").strip()
        if target_concept not in available_concepts:
            print(f"Looks like '{target_concept}' isn't a defined concept. Choose from: {', '.join(available_concepts)}")
            continue

        if source_concept == target_concept:
            print("A concept can't be related to itself in this way! Let's find another connection. 😉")
            continue

        relationship_type = input(f"Type of relationship (e.g., 'influences', 'causes', 'is_part_of'): ").strip()
        if not relationship_type:
            print("Relationship type can't be empty! Give it a name. 😊")
            continue
        
        new_relationship = pd.DataFrame([{'source': source_concept, 'target': target_concept, 'type': relationship_type}])
        relationships_df = pd.concat([relationships_df, new_relationship], ignore_index=True)
        print(f"Connection added: '{source_concept}' --[{relationship_type}]--> '{target_concept}'.")
        print("-" * 30)

    save_concept_map_data(concepts_df, relationships_df, output_json, output_graph_png)
    print("\nYour Insight Loom is woven! Go forth and ponder. ✨")


def save_concept_map_data(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame, output_json: Path, output_graph_png: Path):
    """Saves the concept map data to JSON and generates a graph visualization."""
    
    # Convert DataFrames to dictionary for JSON output
    # Concepts will be a dict where key is concept_name and value is its definition
    concepts_for_json = concepts_df.set_index('concept_name')['definition'].to_dict()

    full_data = {
        "concepts": concepts_for_json,
        "relationships": relationships_df.to_dict('records')
    }

    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, indent=4, ensure_ascii=False)
        print(f"Concept map data saved to '{output_json}'.")
    except Exception as e:
        print(f"Couldn't save concept map data to JSON! Error: {e}")

    # Generate graph visualization only if there are relationships to draw and matplotlib is available
    if not relationships_df.empty:
        if MATPLOTLIB_AVAILABLE:
            draw_concept_graph(concepts_df, relationships_df, output_graph_png)
        else:
            print("Matplotlib is not installed. Skipping graph visualization.")
    else:
        print("No relationships defined, skipping graph visualization for now. Add some connections next time! 📈")


def draw_concept_graph(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame, output_graph_png: Path):
    """Draws and saves the concept map as a PNG image."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot draw graph: matplotlib is not installed.")
        return

    G = nx.DiGraph() # Directed graph for relationships

    # Add nodes with definitions
    for _, row in concepts_df.iterrows():
        G.add_node(row['concept_name'], definition=row['definition'])

    # Add edges (relationships)
    for _, row in relationships_df.iterrows():
        G.add_edge(row['source'], row['target'], type=row['type'])

    plt.figure(figsize=(12, 8))
    # Using spring_layout for aesthetic placement of nodes; k adjusts optimal distance between nodes.
    # Iterations improve layout quality.
    pos = nx.spring_layout(G, k=0.8, iterations=50)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=3000, alpha=0.9)

    # Draw edges
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color='gray', width=1.5, arrowsize=20)

    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    # Draw edge labels
    # Extract relationship types to use as labels on edges
    edge_labels = {(u, v): d['type'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkgreen', font_size=8)

    plt.title("Your Woven Insights: Concept Map", size=15)
    plt.axis('off') # Hide axes to keep the focus on the map
    
    try:
        plt.savefig(output_graph_png, format="png", bbox_inches="tight")
        print(f"Concept map visualization saved to '{output_graph_png}'.")
    except Exception as e:
        print(f"Couldn't save the graph visualization! Error: {e}")
    plt.close() # Close the plot to free memory


def main(args=None):
    parser = argparse.ArgumentParser(
        description="""
        Welcome to Insight Loom! ✨
        This tool helps you untangle complex information by guiding you to
        identify core concepts and map the relationships between them.
        Turn your raw notes into a beautiful, connected knowledge graph!
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--input_file",
        type=Path,
        required=True,
        help="Path to a text file containing your notes or snippets to synthesize."
    )
    parser.add_argument(
        "--output_json",
        type=Path,
        default="concept_map.json",
        help="Path to save the structured concept map data (JSON format)."
    )
    parser.add_argument(
        "--output_graph_png",
        type=Path,
        default="concept_map.png",
        help="Path to save the visual concept map (PNG image)."
    )

    parsed_args = parser.parse_args(args)
    create_concept_map_data(parsed_args.input_file, parsed_args.output_json, parsed_args.output_graph_png)

def process(text: str = "") -> str:
    """Extract key concepts from text and show identified relationships."""
    if not text.strip():
        return "Paste your notes or article text to identify core concepts and connections."
    concepts = _simulate_langextract_concepts(text)
    if not concepts:
        return "No key concepts automatically identified. Try a more detailed passage with technical terms."
    out = ["## Concepts Identified:", ""]
    for c in concepts:
        out.append(f"- **{c}**")
    out += ["", "## How to use Insight Loom interactively:", "",
            "Run the tool from the command line to define relationships between these concepts",
            "and generate a visual concept map PNG.",
            "",
            "**Suggested concept pairs to explore:**"]
    for i, c1 in enumerate(concepts):
        for c2 in concepts[i+1:]:
            rel = _simulate_langextract_relationships(c1, c2, text)
            out.append(f"- '{c1}' {rel} '{c2}'")
    return "\n".join(out)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    # Create a dummy input file for demonstration and testing purposes
    demo_content = """
    The attention economy is a system where human attention is treated as a commodity.
    Platforms like social media compete for user engagement, often employing
    algorithms designed to maximize time spent on the app. This constant demand for
    attention can lead to cognitive overload and diminish our capacity for deep work
    and sustained learning. Deep work requires focused attention over extended periods.
    Conversely, the joy of learning, an intrinsic motivation, thrives in environments
    that minimize distractions and allow for open-ended exploration.
    Information overload is a common symptom of the attention economy, making it hard
    to synthesize complex ideas.
    """
    demo_file_path = Path("demo_notes.txt")
    with open(demo_file_path, "w", encoding="utf-8") as f:
        f.write(demo_content)

    print(f"Created a demo input file: '{demo_file_path}'")
    print("\nTo run the Insight Loom interactively, open your terminal and use:")
    print(f"python insight_loom.py --input_file {demo_file_path} --output_json my_concepts.json --output_graph_png my_concept_map.png")
    print("\nFollow the prompts to define your concepts and relationships!")