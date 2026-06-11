import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys

# Add the directory containing the main script to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import functions from the main script
from main import load_knowledge_base, save_knowledge_base, add_knowledge_item, update_review_schedule, get_due_reviews, REVIEW_INTERVALS, MAX_RECALL_LEVEL

def test_recall_navigator():
    test_file = Path("test_knowledge_base.csv")

    # Ensure clean slate
    if test_file.exists():
        os.remove(test_file)

    print("\n--- Running Recall Navigator Tests ---")

    # Test 1: Load empty/non-existent file
    print("Test 1: Loading non-existent file...")
    df = load_knowledge_base(test_file)
    assert df.empty, "DataFrame should be empty when loading a non-existent file."
    print("Test 1 Passed.")

    # Test 2: Add a knowledge item
    print("Test 2: Adding a knowledge item...")
    initial_item = "What is the capital of Spain?"
    df = add_knowledge_item(df, initial_item)
    assert not df.empty, "DataFrame should not be empty after adding an item."
    assert df['knowledge_point'].iloc[0] == initial_item, "The added knowledge point should match."
    assert df['recall_level'].iloc[0] == 0, "New item should have recall level 0."
    assert df['next_review'].iloc[0].date() == (datetime.now().normalize() + timedelta(days=REVIEW_INTERVALS[0])).date(), "Next review date incorrect for new item."
    print("Test 2 Passed.")

    # Test 3: Save and Load
    print("Test 3: Saving and loading the knowledge base...")
    save_knowledge_base(df, test_file)
    df_loaded = load_knowledge_base(test_file)
    assert len(df_loaded) == len(df), "Loaded DataFrame should have the same number of rows."
    assert df_loaded['knowledge_point'].iloc[0] == initial_item, "Loaded knowledge point should match."
    print("Test 3 Passed.")

    # Test 4: Get due reviews (initially, it should show up as due after 1 day)
    print("Test 4: Getting due reviews (adjusting date for immediate review)...")
    # Manually adjust next_review to be in the past for testing 'due' status
    df_loaded.loc[df_loaded.index[0], 'next_review'] = datetime.now().normalize() - timedelta(days=1)
    due_items = get_due_reviews(df_loaded)
    assert not due_items.empty, "There should be due items after adjusting the date."
    assert due_items['knowledge_point'].iloc[0] == initial_item, "Due item should be the one added."
    print("Test 4 Passed.")

    # Test 5: Update review status (recalled = True)
    print("Test 5: Updating review status to 'recalled=True'...")
    item_id_to_update = df_loaded['id'].iloc[0]
    df_updated_true = update_review_schedule(df_loaded, item_id_to_update, True)
    assert df_updated_true.loc[item_id_to_update, 'recall_level'] == 1, "Recall level should increase after successful recall."
    expected_next_review_date = (datetime.now().normalize() + timedelta(days=REVIEW_INTERVALS[1])).date()
    assert df_updated_true.loc[item_id_to_update, 'next_review'].date() == expected_next_review_date, "Next review date should be updated for successful recall."
    print("Test 5 Passed.")

    # Test 6: Update review status (recalled = False)
    print("Test 6: Updating review status to 'recalled=False'...")
    # Add another item for testing this, or reset the current one
    df_updated_true = add_knowledge_item(df_updated_true, "What is photosynthesis?")
    new_item_id = df_updated_true['id'].iloc[-1]
    df_updated_false = update_review_schedule(df_updated_true, new_item_id, False)
    assert df_updated_false.loc[new_item_id, 'recall_level'] == 0, "Recall level should reset to 0 after failed recall."
    expected_next_review_date_false = (datetime.now().normalize() + timedelta(days=REVIEW_INTERVALS[0])).date()
    assert df_updated_false.loc[new_item_id, 'next_review'].date() == expected_next_review_date_false, "Next review date should be reset for failed recall."
    print("Test 6 Passed.")

    # Test 7: Update non-existent item
    print("Test 7: Attempting to update a non-existent item...")
    original_df_len = len(df_updated_false)
    df_no_change = update_review_schedule(df_updated_false, 999, True) # Non-existent ID
    assert len(df_no_change) == original_df_len, "DataFrame length should not change for non-existent item update."
    print("Test 7 Passed.")
    
    # Test 8: Adding an empty knowledge point
    print("Test 8: Adding an empty knowledge point...")
    original_df_len = len(df_no_change)
    df_no_change_empty = add_knowledge_item(df_no_change, "  ")
    assert len(df_no_change_empty) == original_df_len, "DataFrame length should not change for empty knowledge point."
    print("Test 8 Passed.")


    # Clean up
    if test_file.exists():
        os.remove(test_file)
    print("\n--- All Recall Navigator Tests Passed! ---")

# To run tests:
# python test_main.py
if __name__ == "__main__":
    test_recall_navigator()
