# requirements:
# pandas>=1.0.0
# openpyxl (if outputting to xlsx, pandas dependency)
# xlsxwriter (pandas dependency for to_excel engine)

import argparse
import pandas as pd
from pathlib import Path
import sys

def streamliner(input_dir: Path, output_file: Path, key_column: str, agg_columns: list, file_type: str):
    """
    Combines and aggregates data from multiple CSV or Excel files into a single report.

    Args:
        input_dir (Path): Directory containing input data files.
        output_file (Path): Path and filename for the consolidated output report.
        key_column (str): The column name to use for merging/joining and grouping.
        agg_columns (list): List of column names to aggregate (sum) after grouping.
        file_type (str): Type of input files ('csv' or 'xlsx').
    """
    print(f"Hey there! Super-Lili here, ready to make your reports sparkle! ✨")
    print(f"Looking for {file_type.upper()} files in '{input_dir}' to combine and aggregate...")

    if not input_dir.is_dir():
        print(f"Oopsie! The input directory '{input_dir}' doesn't seem to exist. Can you double-check?")
        sys.exit(1)

    files = list(input_dir.glob(f'*.{file_type}'))
    if not files:
        print(f"Aww, no {file_type.upper()} files found in '{input_dir}'. Let's find some data to work with!")
        sys.exit(1)

    print(f"Found {len(files)} files. Let's get them organized and aggregated!")
    processed_dfs = [] # To store pre-aggregated dataframes from each file

    for i, file in enumerate(files):
        try:
            if file_type == 'csv':
                df = pd.read_csv(file)
            elif file_type == 'xlsx':
                df = pd.read_excel(file)
            else: # This case should ideally be caught by argparse choices, but good for robustness
                print(f"Whoops! Unknown file type '{file_type}'. I only know 'csv' and 'xlsx' right now. Maybe next time?")
                continue # Skip to next file if an unexpected type somehow slips through

            if key_column not in df.columns:
                print(f"Uh oh! The key column '{key_column}' is missing in '{file.name}'. Can't process this file without it!")
                continue # Skip to the next file if key_column is missing

            current_agg_cols = []
            for col in agg_columns:
                if col in df.columns:
                    # Convert to numeric, filling non-convertible values with 0 for summation
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    current_agg_cols.append(col)
                else:
                    print(f"Heads up! Aggregation column '{col}' is missing in '{file.name}'. I'll just skip it for this file.")

            if not current_agg_cols:
                print(f"Looks like there are no valid aggregation columns in '{file.name}'. Skipping aggregation for this file.")
                continue # Skip if no columns to aggregate

            # Group by key_column and sum the specified aggregate columns for *this* file
            file_aggregated_df = df.groupby(key_column, as_index=False)[current_agg_cols].sum()
            processed_dfs.append(file_aggregated_df)
            print(f"  Processed and aggregated '{file.name}'! ({i+1}/{len(files)})")

        except pd.errors.EmptyDataError:
            print(f"Hmm, '{file.name}' seems to be empty. Skipping it for now!")
            continue
        except Exception as e:
            print(f"Oh dear, something went wrong processing '{file.name}': {e}. Skipping this one for now!")
            continue # Move to the next file

    if not processed_dfs:
        print("Looks like I couldn't process and aggregate any files. Let's try again with some valid data!")
        sys.exit(1)

    # Now, concatenate all pre-aggregated dataframes and perform a final aggregation
    print(f"Alright, let's weave all these aggregated bits into one grand report!")
    combined_dfs_for_final_agg = pd.concat(processed_dfs, ignore_index=True)

    # Ensure all original agg_columns are present in the combined DataFrame, filling missing ones with 0
    for col in agg_columns:
        if col not in combined_dfs_for_final_agg.columns:
            combined_dfs_for_final_agg[col] = 0
        else:
            # Re-ensure numeric type in case of mixed types after concat
            combined_dfs_for_final_agg[col] = pd.to_numeric(combined_dfs_for_final_agg[col], errors='coerce').fillna(0)

    # Final aggregation across all concatenated data
    print(f"One last powerful sum! Grouping everything by '{key_column}'...")
    final_report_df = combined_dfs_for_final_agg.groupby(key_column, as_index=False)[agg_columns].sum()

    # Save the output
    try:
        if output_file.suffix == '.csv':
            final_report_df.to_csv(output_file, index=False)
            print(f"Woohoo! Your shiny new CSV report is ready at '{output_file}'! 🎉")
        elif output_file.suffix == '.xlsx':
            # Create a Pandas Excel writer using XlsxWriter as the engine.
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                final_report_df.to_excel(writer, sheet_name='Consolidated Report', index=False)
                print(f"Woohoo! Your shiny new Excel report is ready at '{output_file}'! 🎉")
        else:
            print(f"Gah! I only know how to save as '.csv' or '.xlsx'. Please give me a proper file extension for '{output_file.name}'.")
            sys.exit(1)
    except Exception as e:
        print(f"Oh no, I couldn't save the report! Here's what happened: {e}. Let's try again!")
        sys.exit(1)

def main():
    """
    Parses command-line arguments and initiates the ReportStreamliner.
    """
    parser = argparse.ArgumentParser(
        description="""
        Super-Lili's ReportStreamliner: Your cheerful helper for merging and aggregating
        data from multiple CSV or Excel files into one beautiful report!
        Say goodbye to repetitive copy-pasting and hello to automated awesomeness! ✨
        """,
        formatter_class=argparse.RawTextHelpFormatter # For better multiline description display
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        required=True,
        help="""
        Path to the directory containing your input data files (CSV or XLSX).
        All files of the specified type in this directory will be processed.
        Example: --input-dir /path/to/my/data_folder
        """
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        required=True,
        help="""
        Path and filename for the consolidated output report.
        The file extension must be '.csv' or '.xlsx'.
        Example: --output-file /path/to/my/reports/monthly_summary.xlsx
        """
    )
    parser.add_argument(
        '--key-column',
        type=str,
        required=True,
        help="""
        The column name to use for grouping and aggregating your datasets.
        This column must exist in all input files you wish to process.
        Example: --key-column 'CustomerID'
        """
    )
    parser.add_argument(
        '--agg-columns',
        type=str,
        required=True,
        help="""
        Comma-separated list of column names to aggregate (sum) after grouping.
        These columns should contain numerical data.
        Example: --agg-columns 'SalesAmount,QuantitySold'
        """
    )
    parser.add_argument(
        '--file-type',
        type=str,
        choices=['csv', 'xlsx'],
        default='csv',
        help="""
        Type of input files you're using. Choose 'csv' or 'xlsx'.
        Defaults to 'csv' if not specified.
        Example: --file-type xlsx
        """
    )

    args = parser.parse_args()

    # Split the comma-separated string of aggregate columns into a list
    agg_columns_list = [col.strip() for col in args.agg_columns.split(',')]

    # Check if the output file extension is valid
    if args.output_file.suffix not in ['.csv', '.xlsx']:
        print(f"Oh no! The output file '{args.output_file.name}' needs to end with '.csv' or '.xlsx'. Let's fix that!")
        sys.exit(1)

    streamliner(
        args.input_dir,
        args.output_file,
        args.key_column,
        agg_columns_list,
        args.file_type
    )

if __name__ == "__main__":
    # Demo usage:
    # 1. Create a directory named 'demo_data'
    # 2. Create a few CSV or XLSX files inside 'demo_data'
    #    Example file 'data1.csv':
    #    CustomerID,SalesAmount,QuantitySold,Region
    #    101,150.50,2,East
    #    102,200.00,1,West
    #    103,75.25,3,North
    #
    #    Example file 'data2.csv':
    #    CustomerID,SalesAmount,QuantitySold,ProductCategory
    #    101,50.00,1,Electronics
    #    104,120.75,2,Apparel
    #    102,30.00,1,Books
    #
    # 3. Run the script from your terminal:
    # python your_script_name.py --input-dir demo_data --output-file reports/summary.xlsx --key-column CustomerID --agg-columns SalesAmount,QuantitySold --file-type csv

    # Example setup for quick local testing without manual file creation:
    # (Comment out or remove for actual production use, as it creates dummy files)
    demo_dir = Path("demo_data")
    demo_dir.mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True) # Ensure reports directory exists

    # Create dummy CSV files
    data_csv_1 = """CustomerID,SalesAmount,QuantitySold,Region
101,150.50,2,East
102,200.00,1,West
103,75.25,3,North"""
    (demo_dir / "sales_q1.csv").write_text(data_csv_1)

    data_csv_2 = """CustomerID,SalesAmount,QuantitySold,ProductCategory
101,50.00,1,Electronics
104,120.75,2,Apparel
102,30.00,1,Books"""
    (demo_dir / "sales_q2.csv").write_text(data_csv_2)

    # You could also make dummy XLSX files if needed using pandas
    # For example:
    # df_xlsx_1 = pd.DataFrame({'CustomerID':, 'SalesAmount': [90.0, 110.0], 'QuantitySold':, 'Dept': ['HR', 'IT']})
    # df_xlsx_1.to_excel(demo_dir / "hr_spending.xlsx", index=False)


    # Simulate command-line arguments for demo
    sys.argv = [
        "your_script.py", # Placeholder for script name
        "--input-dir", str(demo_dir),
        "--output-file", "reports/monthly_summary.xlsx",
        "--key-column", "CustomerID",
        "--agg-columns", "SalesAmount,QuantitySold",
        "--file-type", "csv"
    ]

    print("\n--- Running ReportStreamliner Demo ---")
    print(f"Using input directory: {sys.argv}")
    print(f"Output file: {sys.argv}")
    print(f"Key column: {sys.argv}")
    print(f"Aggregate columns: {sys.argv}")
    print(f"File type: {sys.argv}\n")

    main()
    print("\n--- Demo Finished! Check 'reports/monthly_summary.xlsx' ---")

    # Clean up demo files (optional)
    # import shutil
    # shutil.rmtree(demo_dir)
    # Path("reports/monthly_summary.xlsx").unlink()