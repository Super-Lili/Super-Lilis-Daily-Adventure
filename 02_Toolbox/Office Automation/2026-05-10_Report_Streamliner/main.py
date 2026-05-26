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
    print(f"Hey there! Super-Lili here, ready to make your reports sparkle!")
    print(f"Looking for {file_type.upper()} files in '{input_dir}' to combine and aggregate...")

    if not input_dir.is_dir():
        print(f"Oopsie! The input directory '{input_dir}' doesn't seem to exist. Can you double-check?")
        sys.exit(1)

    files = list(input_dir.glob(f'*.{file_type}'))
    if not files:
        print(f"Aww, no {file_type.upper()} files found in '{input_dir}'. Let's find some data to work with!")
        sys.exit(1)

    print(f"Found {len(files)} files. Let's get them organized and aggregated!")
    processed_dfs = []

    for i, file in enumerate(files):
        try:
            if file_type == 'csv':
                df = pd.read_csv(file)
            elif file_type == 'xlsx':
                df = pd.read_excel(file)
            else:
                print(f"Whoops! Unknown file type '{file_type}'. I only know 'csv' and 'xlsx' right now.")
                continue

            if key_column not in df.columns:
                print(f"Uh oh! The key column '{key_column}' is missing in '{file.name}'. Can't process this file without it!")
                continue

            current_agg_cols = []
            for col in agg_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    current_agg_cols.append(col)
                else:
                    print(f"Heads up! Aggregation column '{col}' is missing in '{file.name}'. I'll skip it for this file.")

            if not current_agg_cols:
                print(f"Looks like there are no valid aggregation columns in '{file.name}'. Skipping.")
                continue

            file_aggregated_df = df.groupby(key_column, as_index=False)[current_agg_cols].sum()
            processed_dfs.append(file_aggregated_df)
            print(f"  Processed and aggregated '{file.name}'! ({i+1}/{len(files)})")

        except pd.errors.EmptyDataError:
            print(f"Hmm, '{file.name}' seems to be empty. Skipping it for now!")
            continue
        except Exception as e:
            print(f"Oh dear, something went wrong processing '{file.name}': {e}. Skipping!")
            continue

    if not processed_dfs:
        print("Looks like I couldn't process and aggregate any files. Let's try again with some valid data!")
        sys.exit(1)

    print(f"Alright, let's weave all these aggregated bits into one grand report!")
    combined_dfs_for_final_agg = pd.concat(processed_dfs, ignore_index=True)

    for col in agg_columns:
        if col not in combined_dfs_for_final_agg.columns:
            combined_dfs_for_final_agg[col] = 0
        else:
            combined_dfs_for_final_agg[col] = pd.to_numeric(combined_dfs_for_final_agg[col], errors='coerce').fillna(0)

    print(f"One last powerful sum! Grouping everything by '{key_column}'...")
    final_report_df = combined_dfs_for_final_agg.groupby(key_column, as_index=False)[agg_columns].sum()

    try:
        if output_file.suffix == '.csv':
            final_report_df.to_csv(output_file, index=False)
            print(f"Woohoo! Your shiny new CSV report is ready at '{output_file}'!")
        elif output_file.suffix == '.xlsx':
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                final_report_df.to_excel(writer, sheet_name='Consolidated Report', index=False)
                print(f"Woohoo! Your shiny new Excel report is ready at '{output_file}'!")
        else:
            print(f"Gah! I only know how to save as '.csv' or '.xlsx'. Please give me a proper file extension.")
            sys.exit(1)
    except Exception as e:
        print(f"Oh no, I couldn't save the report! Here's what happened: {e}.")
        sys.exit(1)


def process(text: str) -> str:
    """
    Demonstrate report aggregation on inline CSV data.
    Input: CSV-formatted data with a header row. Multiple files can be separated by '---'.
    Falls back to sample data if empty.
    """
    if not text.strip():
        text = """CustomerID,SalesAmount,QuantitySold
101,150.50,2
102,200.00,1
103,75.25,3
---
CustomerID,SalesAmount,QuantitySold
101,50.00,1
104,120.75,2
102,30.00,1"""

    import io
    blocks = [b.strip() for b in text.split('---') if b.strip()]
    dfs = []
    for block in blocks:
        try:
            df = pd.read_csv(io.StringIO(block))
            dfs.append(df)
        except Exception as e:
            return f"Error parsing input: {e}"

    if not dfs:
        return "No valid CSV data found in input."

    # Auto-detect key column (first column) and numeric columns
    first_cols = [df.columns[0] for df in dfs if len(df.columns) > 0]
    key_column = first_cols[0] if first_cols else None

    if key_column is None:
        return "Could not determine key column from input."

    # Find numeric columns common across all DataFrames
    all_numeric = []
    for df in dfs:
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if col not in all_numeric:
                all_numeric.append(col)

    combined = pd.concat(dfs, ignore_index=True)
    for col in all_numeric:
        if col not in combined.columns:
            combined[col] = 0
        else:
            combined[col] = pd.to_numeric(combined[col], errors='coerce').fillna(0)

    final = combined.groupby(key_column, as_index=False)[all_numeric].sum()

    lines = [
        "Report Streamliner: Aggregated Result",
        "=" * 40,
        f"Key column: {key_column}",
        f"Aggregated columns: {', '.join(all_numeric)}",
        f"Input files (blocks): {len(dfs)}",
        "",
    ]

    # Format as a simple table
    col_list = [key_column] + all_numeric
    col_widths = {col: max(len(str(col)), final[col].astype(str).str.len().max()) for col in col_list}
    header = "  ".join(str(col).ljust(col_widths[col]) for col in col_list)
    sep = "  ".join("-" * col_widths[col] for col in col_list)
    lines.append(header)
    lines.append(sep)
    for _, row in final.iterrows():
        lines.append("  ".join(str(row[col]).ljust(col_widths[col]) for col in col_list))

    lines.append("")
    lines.append(f"Total rows in consolidated report: {len(final)}")
    lines.append("For file-based processing, run: python3 main.py --input-dir ./data --output-file report.csv --key-column ID --agg-columns Amount")
    return "\n".join(lines)


def main():
    """Parses command-line arguments and initiates the ReportStreamliner."""
    parser = argparse.ArgumentParser(
        description="Super-Lili's ReportStreamliner: Your cheerful helper for merging and aggregating data!",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--input-dir', type=Path, required=True,
                        help="Path to the directory containing your input data files.")
    parser.add_argument('--output-file', type=Path, required=True,
                        help="Path and filename for the consolidated output report.")
    parser.add_argument('--key-column', type=str, required=True,
                        help="The column name to use for grouping and aggregating your datasets.")
    parser.add_argument('--agg-columns', type=str, required=True,
                        help="Comma-separated list of column names to aggregate (sum) after grouping.")
    parser.add_argument('--file-type', type=str, choices=['csv', 'xlsx'], default='csv',
                        help="Type of input files you're using. Choose 'csv' or 'xlsx'.")

    args = parser.parse_args()
    agg_columns_list = [col.strip() for col in args.agg_columns.split(',')]

    if args.output_file.suffix not in ['.csv', '.xlsx']:
        print(f"Oh no! The output file '{args.output_file.name}' needs to end with '.csv' or '.xlsx'.")
        sys.exit(1)

    streamliner(args.input_dir, args.output_file, args.key_column, agg_columns_list, args.file_type)


def _cli_main():
    demo_dir = Path("demo_data")
    demo_dir.mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

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

    sys.argv = [
        "main.py",
        "--input-dir", str(demo_dir),
        "--output-file", "reports/monthly_summary.csv",
        "--key-column", "CustomerID",
        "--agg-columns", "SalesAmount,QuantitySold",
        "--file-type", "csv"
    ]

    print("\n--- Running ReportStreamliner Demo ---")
    main()
    print("\n--- Demo Finished! Check 'reports/monthly_summary.csv' ---")


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    _cli_main()
