# requirements:
# pandas
# networkx (optional, for CLI visualization)
# matplotlib (optional, for visualization)
# argparse
# pathlib

import argparse
import json
import pandas as pd
from pathlib import Path

# Try to import networkx and matplotlib — only used in CLI visualization
try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    nx = None
    _NX_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    _MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None
    _MATPLOTLIB_AVAILABLE = False


def build_concept_graph_dict(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame) -> dict:
    """Build a simple dict-based graph representation."""
    graph = {"nodes": {}, "edges": []}
    for _, row in concepts_df.iterrows():
        graph["nodes"][row['concept_name']] = row['definition']
    for _, row in relationships_df.iterrows():
        graph["edges"].append({
            "source": row['source'],
            "target": row['target'],
            "type": row['type']
        })
    return graph


def format_concept_map_text(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame) -> str:
    """Format the concept map as plain text."""
    lines = ["=== Insight Loom: Your Woven Concept Map ===", ""]

    if not concepts_df.empty:
        lines.append("CONCEPTS:")
        for _, row in concepts_df.iterrows():
            lines.append(f"  [{row['concept_name']}]: {row['definition']}")
        lines.append("")

    if not relationships_df.empty:
        lines.append("RELATIONSHIPS:")
        for _, row in relationships_df.iterrows():
            lines.append(f"  {row['source']}  --[{row['type']}]-->  {row['target']}")
        lines.append("")
    else:
        lines.append("No relationships defined yet.")

    return "\n".join(lines)


def create_concept_map_data(input_file: Path, output_json: Path, output_graph_png: Path):
    """
    Guides the user through creating a concept map from input text,
    then saves the map data and a visualization.
    """
    print(f"Hey there, knowledge explorer! Let's weave some insights from {input_file.name}.")

    if not input_file.exists():
        print(f"Oops! The file '{input_file}' doesn't exist. Double-check your path and try again!")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Uh oh, couldn't read your file! Error: {e}")
        return

    print("\nFirst, let's identify the core concepts.")
    print("Your text snippet:\n---")
    print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
    print("---\n")

    concepts_df = pd.DataFrame(columns=['concept_name', 'definition'])
    relationships_df = pd.DataFrame(columns=['source', 'target', 'type'])

    while True:
        concept_name = input("Enter a key concept (or 'done' to finish concepts): ").strip()
        if concept_name.lower() == 'done':
            break
        if not concept_name:
            continue

        if concept_name in concepts_df['concept_name'].values:
            print(f"'{concept_name}' is already a concept. Let's try a new one or 'done'.")
            continue

        definition = input(f"Define '{concept_name}': ").strip()
        new_concept = pd.DataFrame([{'concept_name': concept_name, 'definition': definition}])
        concepts_df = pd.concat([concepts_df, new_concept], ignore_index=True)
        print(f"Awesome! '{concept_name}' added. Current concepts: {', '.join(concepts_df['concept_name'].tolist())}")
        print("-" * 30)

    if concepts_df.empty:
        print("No concepts added! We need some ideas to connect.")
        return

    print("\nNow, let's connect those brilliant ideas!")
    available_concepts = concepts_df['concept_name'].tolist()

    if len(available_concepts) < 2:
        print("Not enough concepts to form relationships. We need at least two!")
        save_concept_map_data(concepts_df, relationships_df, output_json, output_graph_png)
        return

    while True:
        print(f"\nYour concepts: {', '.join(available_concepts)}")
        source_concept = input("Source concept (or 'done' to finish relationships): ").strip()
        if source_concept.lower() == 'done':
            break
        if source_concept not in available_concepts:
            print(f"Hmm, '{source_concept}' isn't in your concept list.")
            continue

        target_concept = input("Target concept: ").strip()
        if target_concept not in available_concepts:
            print(f"Looks like '{target_concept}' isn't a defined concept.")
            continue

        if source_concept == target_concept:
            print("A concept can't be related to itself in this way!")
            continue

        relationship_type = input("Type of relationship (e.g., 'influences', 'causes', 'is_part_of'): ").strip()
        if not relationship_type:
            print("Relationship type can't be empty!")
            continue

        new_relationship = pd.DataFrame([{'source': source_concept, 'target': target_concept, 'type': relationship_type}])
        relationships_df = pd.concat([relationships_df, new_relationship], ignore_index=True)
        print(f"Connection added: '{source_concept}' --[{relationship_type}]--> '{target_concept}'.")
        print("-" * 30)

    save_concept_map_data(concepts_df, relationships_df, output_json, output_graph_png)
    print("\nYour Insight Loom is woven! Go forth and ponder.")


def save_concept_map_data(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame, output_json: Path, output_graph_png: Path):
    """Saves the concept map data to JSON and generates a graph visualization."""
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

    if not relationships_df.empty:
        if _MATPLOTLIB_AVAILABLE and _NX_AVAILABLE:
            draw_concept_graph(concepts_df, relationships_df, output_graph_png)
        else:
            print("matplotlib/networkx not installed. Skipping graph visualization.")
    else:
        print("No relationships defined, skipping graph visualization.")


def draw_concept_graph(concepts_df: pd.DataFrame, relationships_df: pd.DataFrame, output_graph_png: Path):
    """Draws and saves the concept map as a PNG image."""
    if not _MATPLOTLIB_AVAILABLE or not _NX_AVAILABLE:
        print("Cannot draw graph: matplotlib or networkx is not installed.")
        return

    G = nx.DiGraph()

    for _, row in concepts_df.iterrows():
        G.add_node(row['concept_name'], definition=row['definition'])

    for _, row in relationships_df.iterrows():
        G.add_edge(row['source'], row['target'], type=row['type'])

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.8, iterations=50)

    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=3000, alpha=0.9)
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color='gray', width=1.5, arrowsize=20)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    edge_labels = {(u, v): d['type'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkgreen', font_size=8)

    plt.title("Your Woven Insights: Concept Map", size=15)
    plt.axis('off')

    try:
        plt.savefig(output_graph_png, format="png", bbox_inches="tight")
        print(f"Concept map visualization saved to '{output_graph_png}'.")
    except Exception as e:
        print(f"Couldn't save the graph visualization! Error: {e}")
    plt.close()


def process(text: str) -> str:
    """
    Build a concept map from plain text.
    Input: multi-line text with concepts and relationships.
    Format:
      Line 1+: text to analyze (shown as context)
      Concepts are auto-extracted as significant capitalized words or
      the tool returns a demonstration map of the input text themes.

    For simplicity in browser mode, we extract noun-like words and show
    a sample relationship map.
    """
    if not text.strip():
        text = """The attention economy treats human attention as a commodity.
Platforms compete for engagement through algorithms. Deep work requires
sustained focus. Information overload makes synthesis difficult."""

    # Simple auto-extraction: find unique capitalized or long words as concepts
    import re
    words = re.findall(r'\b[A-Z][a-z]{3,}\b|\b[a-z]{6,}\b', text)
    # De-duplicate while preserving order, take top 6
    seen = set()
    concepts = []
    stop = {'through', 'requires', 'platforms', 'compete', 'treats', 'makes', 'human', 'difficult', 'sustained'}
    for w in words:
        wl = w.lower()
        if wl not in seen and wl not in stop and len(concepts) < 6:
            seen.add(wl)
            concepts.append(w.lower())

    if not concepts:
        concepts = ["attention", "engagement", "learning", "focus"]

    # Build a simple linear relationship chain for demo
    concepts_df = pd.DataFrame([
        {'concept_name': c, 'definition': f'Key concept: {c}'} for c in concepts
    ])

    relationships = []
    for i in range(len(concepts) - 1):
        relationships.append({'source': concepts[i], 'target': concepts[i + 1], 'type': 'leads to'})
    relationships_df = pd.DataFrame(relationships, columns=['source', 'target', 'type'])

    result = format_concept_map_text(concepts_df, relationships_df)
    result += "\n\nFor interactive concept mapping with file input, run: python3 main.py --input_file notes.txt"
    return result


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Welcome to Insight Loom! This tool helps you untangle complex information.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input_file", type=Path, required=True,
                        help="Path to a text file containing your notes or snippets to synthesize.")
    parser.add_argument("--output_json", type=Path, default="concept_map.json",
                        help="Path to save the structured concept map data (JSON format).")
    parser.add_argument("--output_graph_png", type=Path, default="concept_map.png",
                        help="Path to save the visual concept map (PNG image).")

    parsed_args = parser.parse_args(args)
    create_concept_map_data(parsed_args.input_file, parsed_args.output_json, parsed_args.output_graph_png)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
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
    print(f"python main.py --input_file {demo_file_path} --output_json my_concepts.json --output_graph_png my_concept_map.png")
    print("\nFollow the prompts to define your concepts and relationships!")
