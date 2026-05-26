import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import csv

# Requirements:
# pandas
# numpy

# Define spaced repetition intervals in days
# Level 0: New item, review next day
# Level 1: Recalled once, review in 3 days
# Level 2: Recalled twice, review in 7 days
# Level 3: Recalled thrice, review in 14 days
# Level 4: Mastered, review in 30 days
REVIEW_INTERVALS = {
    0: 1,
    1: 3,
    2: 7,
    3: 14,
    4: 30
}
MAX_RECALL_LEVEL = max(REVIEW_INTERVALS.keys())


def _format_table(df: pd.DataFrame, columns: list) -> str:
    """Format a DataFrame subset as a plain-text table."""
    sub = df[columns].copy()
    # Convert datetime columns to strings
    for col in sub.columns:
        if pd.api.types.is_datetime64_any_dtype(sub[col]):
            sub[col] = sub[col].dt.strftime('%Y-%m-%d').fillna('N/A')
    col_widths = {col: max(len(str(col)), sub[col].astype(str).str.len().max()) for col in columns}
    header = "  ".join(str(col).ljust(col_widths[col]) for col in columns)
    sep = "  ".join("-" * col_widths[col] for col in columns)
    rows = [header, sep]
    for _, row in sub.iterrows():
        rows.append("  ".join(str(row[col]).ljust(col_widths[col]) for col in columns))
    return "\n".join(rows)


def load_knowledge_base(filepath: Path) -> pd.DataFrame:
    """
    Loads the knowledge base from a CSV file. If the file does not exist or is empty,
    it returns an empty DataFrame with the correct columns.
    """
    if not filepath.exists():
        print(f"Heads up! No knowledge base found at '{filepath}'. Starting fresh!")
        return pd.DataFrame(columns=['id', 'knowledge_point', 'last_reviewed', 'next_review', 'recall_level'])

    try:
        df = pd.read_csv(filepath, parse_dates=['last_reviewed', 'next_review'])
        if df.empty:
            print(f"Oops! The knowledge base at '{filepath}' is empty. Let's fill it up!")
            return pd.DataFrame(columns=['id', 'knowledge_point', 'last_reviewed', 'next_review', 'recall_level'])

        if 'id' not in df.columns:
            df['id'] = range(len(df))
        else:
            df['id'] = df['id'].astype(int)
        df = df.set_index('id', drop=False)

        df['recall_level'] = df['recall_level'].fillna(0).astype(int)
        df['last_reviewed'] = df['last_reviewed'].fillna(pd.NaT)
        df['next_review'] = df['next_review'].fillna(pd.NaT)

        print(f"Knowledge base loaded with {len(df)} items!")
        return df
    except Exception as e:
        print(f"Oh dear, couldn't load the knowledge base from '{filepath}'. Error: {e}. Starting fresh!")
        return pd.DataFrame(columns=['id', 'knowledge_point', 'last_reviewed', 'next_review', 'recall_level'])


def save_knowledge_base(df: pd.DataFrame, filepath: Path) -> None:
    """Saves the current knowledge base DataFrame to a CSV file."""
    try:
        df.to_csv(filepath, index=False)
        print(f"Super-duper! Knowledge base saved to '{filepath}'.")
    except Exception as e:
        print(f"Whoopsie! Couldn't save the knowledge base to '{filepath}'. Error: {e}.")


def add_knowledge_item(df: pd.DataFrame, knowledge_point: str) -> pd.DataFrame:
    """Adds a new knowledge point to the DataFrame with an initial review schedule."""
    if knowledge_point.strip() == "":
        print("Whoa there! An empty knowledge point? Let's add something real!")
        return df

    next_id = df['id'].max() + 1 if not df.empty else 1

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_item = {
        'id': next_id,
        'knowledge_point': knowledge_point,
        'last_reviewed': pd.NaT,
        'next_review': today + timedelta(days=REVIEW_INTERVALS[0]),
        'recall_level': 0
    }

    new_row_df = pd.DataFrame([new_item]).set_index('id', drop=False)
    df = pd.concat([df, new_row_df])

    print(f"Zoom! Added new knowledge point (ID: {next_id}): '{knowledge_point}'. Get ready to recall!")
    return df


def update_review_schedule(df: pd.DataFrame, item_id: int, recalled: bool) -> pd.DataFrame:
    """Updates the review schedule for a specific knowledge point based on recall success."""
    if item_id not in df.index:
        print(f"Hmm, can't find item with ID {item_id}. Double-check that number!")
        return df

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    item = df.loc[item_id]
    current_level = item['recall_level']

    if recalled:
        new_level = min(current_level + 1, MAX_RECALL_LEVEL)
        next_interval = REVIEW_INTERVALS.get(new_level, REVIEW_INTERVALS[MAX_RECALL_LEVEL])
        df.loc[item_id, 'recall_level'] = new_level
        df.loc[item_id, 'next_review'] = today + timedelta(days=next_interval)
        print(f"Brilliant! Item ID {item_id} moved to recall level {new_level}. Next review in {next_interval} days.")
    else:
        new_level = 0
        next_interval = REVIEW_INTERVALS[new_level]
        df.loc[item_id, 'recall_level'] = new_level
        df.loc[item_id, 'next_review'] = today + timedelta(days=next_interval)
        print(f"No worries! Item ID {item_id} reset to recall level {new_level}. We'll try again tomorrow (in {next_interval} day!).")

    df.loc[item_id, 'last_reviewed'] = today
    return df


def get_due_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Returns knowledge points that are due for review today or in the past."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    due_items = df[df['next_review'] <= today].copy()
    if due_items.empty:
        print("Yay! Nothing due for review today. Go enjoy your day (or add more knowledge!).")
    else:
        print(f"Time to shine! You have {len(due_items)} items due for review today:")
        print(_format_table(due_items, ['id', 'knowledge_point', 'next_review', 'recall_level']))
    return due_items


def process(text: str) -> str:
    """
    Demonstrate the Recall Navigator with sample knowledge points.
    Input can be newline-separated knowledge points to add, or empty for a demo.
    """
    df = pd.DataFrame(columns=['id', 'knowledge_point', 'last_reviewed', 'next_review', 'recall_level'])

    points = [p.strip() for p in text.strip().splitlines() if p.strip()]
    if not points:
        points = [
            "What is the capital of France?",
            "Explain Newton's first law of motion.",
            "Who painted the Mona Lisa?",
            "What is the purpose of the 'finally' block in Python?",
        ]

    lines = []
    for point in points:
        df = add_knowledge_item(df, point)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Make all items due today so the demo shows results
    df['next_review'] = today

    lines.append(f"\nKnowledge base has {len(df)} items. All set for review today:")
    lines.append(_format_table(df, ['id', 'knowledge_point', 'recall_level']))
    lines.append(f"\nAll {len(df)} items are due for review.")
    lines.append("Use: python3 main.py <filepath> --add 'Your fact' | --review | --update <id> true/false")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Recall Navigator: Your friendly guide to remembering more of what you learn!"
    )
    parser.add_argument(
        "filepath", type=str, help="Path to your knowledge base CSV file (e.g., 'my_knowledge.csv')."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--add", type=str,
        help="Add a new knowledge point."
    )
    group.add_argument(
        "--review", action="store_true",
        help="Show all knowledge points due for review today."
    )
    group.add_argument(
        "--update", nargs=2, metavar=('ITEM_ID', 'RECALLED'),
        help="Update the review status for an item. Provide item ID and 'true' or 'false'."
    )

    args = parser.parse_args()
    knowledge_filepath = Path(args.filepath)

    df = load_knowledge_base(knowledge_filepath)

    if args.add:
        df = add_knowledge_item(df, args.add)
    elif args.review:
        get_due_reviews(df)
    elif args.update:
        try:
            item_id = int(args.update[0])
            recalled_str = args.update[1].lower()
            recalled = True if recalled_str == 'true' else False
            if recalled_str not in ['true', 'false']:
                raise ValueError("RECALLED must be 'true' or 'false'.")
            df = update_review_schedule(df, item_id, recalled)
        except ValueError as e:
            print(f"Oops! Problem with your update command: {e}.")
        except Exception as e:
            print(f"An unexpected error occurred during update: {e}.")

    save_knowledge_base(df, knowledge_filepath)


def _cli_main():
    DEMO_FILE = Path("demo_knowledge_base.csv")

    if DEMO_FILE.exists():
        DEMO_FILE.unlink()

    print("\n--- DEMO: Initializing new knowledge base ---")
    initial_df = pd.DataFrame(columns=['id', 'knowledge_point', 'last_reviewed', 'next_review', 'recall_level'])
    initial_df = add_knowledge_item(initial_df, "What is the capital of France?")
    initial_df = add_knowledge_item(initial_df, "Explain Newton's first law of motion.")
    initial_df = add_knowledge_item(initial_df, "Who painted the Mona Lisa?")
    initial_df = add_knowledge_item(initial_df, "What is the purpose of the 'finally' block in Python?")
    save_knowledge_base(initial_df, DEMO_FILE)

    print("\n--- DEMO: Loading knowledge base and checking reviews for today ---")
    df_loaded = load_knowledge_base(DEMO_FILE)
    get_due_reviews(df_loaded)

    print("\n--- DEMO: Simulating a day later, and some reviews ---")
    df_loaded['next_review'] = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    df_loaded.loc[df_loaded.index[0], 'last_reviewed'] = today - timedelta(days=3)
    df_loaded.loc[df_loaded.index[0], 'next_review'] = today
    df_loaded.loc[df_loaded.index[0], 'recall_level'] = 1

    get_due_reviews(df_loaded)

    print("\n--- DEMO: Updating review status for an item ---")
    if not df_loaded.empty:
        first_id = df_loaded['id'].iloc[0]
        df_updated = update_review_schedule(df_loaded, first_id, True)
        if len(df_updated) > 1:
            second_id = df_updated['id'].iloc[1]
            df_updated = update_review_schedule(df_updated, second_id, False)
        save_knowledge_base(df_updated, DEMO_FILE)

    print("\n--- DEMO: Checking reviews again after updates ---")
    df_final = load_knowledge_base(DEMO_FILE)
    get_due_reviews(df_final)

    print("\n--- DEMO COMPLETE ---")
    print(f"You can find the demo knowledge base at: {DEMO_FILE.resolve()}")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
