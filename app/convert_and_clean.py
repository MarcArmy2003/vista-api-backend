import os
import pandas as pd
from collections import defaultdict
import glob

# --- Configuration ---
# The root folder to scan for source .csv files.
REPO_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository"

# The dedicated folder where all new .txt Markdown files will be saved.
MARKDOWN_OUTPUT_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository\ABR Excel Table Markdowns"


def convert_and_clean_all(repo_path, output_path):
    """
    Finds all .csv files, converts them to markdown .txt files,
    and cleans up all unsupported source and metadata files.
    """
    print(f"Scanning for CSV files in: {repo_path}")
    os.makedirs(output_path, exist_ok=True)
    print(f"Markdown files will be saved to: {output_path}")

    csv_files = glob.glob(os.path.join(repo_path, '**', '*.csv'), recursive=True)
    
    if not csv_files:
        print("No CSV files found to process.")
    else:
        # Group CSVs by their original .xls parent file
        grouped_files = defaultdict(list)
        for f in csv_files:
            basename = os.path.basename(f)
            if " - " in basename:
                original_xls_name = basename.split(" - ")[0]
                grouped_files[original_xls_name].append(f)

        print(f"Found {len(grouped_files)} groups of files to convert.")
        print("-" * 60)

        # Process each group
        for original_xls, csv_list in grouped_files.items():
            print(f"Processing group: {original_xls}")
            txt_filename = os.path.join(output_path, f"{original_xls.replace('.xls', '.txt')}")
            markdown_content = f"# Data from {original_xls}\n\n"

            for csv_path in sorted(csv_list):
                try:
                    sheet_name = os.path.basename(csv_path).split(" - ")[1].replace('.csv', '')
                    markdown_content += f"### {sheet_name}\n"
                    df = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip')
                    if df.empty:
                        markdown_content += "*(No data in this sheet)*\n\n"
                        continue
                    markdown_content += df.to_markdown(index=False)
                    markdown_content += "\n\n"
                except Exception as e:
                    print(f"  - Could not process file {os.path.basename(csv_path)}. Error: {e}")

            try:
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"  -> Successfully created: {os.path.basename(txt_filename)}")
            except Exception as e:
                print(f"  -> ERROR: Could not write file {os.path.basename(txt_filename)}. Error: {e}")

    # --- Comprehensive Cleanup Phase ---
    print("\n" + "-" * 60)
    print("Cleaning up all unsupported and intermediate files...")

    # Define a list of file patterns to delete
    patterns_to_delete = [
        os.path.join(repo_path, '**', '*.csv'),
        os.path.join(repo_path, '**', '*.xls'),
        os.path.join(repo_path, '**', '.DS_Store'),
        os.path.join(repo_path, '**', 'Thumbs.db')
    ]
    
    deleted_count = 0
    for pattern in patterns_to_delete:
        # Use glob to find all matching files and folders
        files_to_delete = glob.glob(pattern, recursive=True)
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
            except OSError as e: # More specific exception for file operations
                print(f"  - Could not delete {os.path.basename(file_path)}. Error: {e}")

    print(f"Cleanup complete. Deleted {deleted_count} unnecessary files.")


# --- Main Execution Block ---
if __name__ == "__main__":
    try:
        import pandas
    except ImportError:
        print("Pandas library not found. Please install it by running: pip install pandas")
    else:
        convert_and_clean_all(REPO_FOLDER, MARKDOWN_OUTPUT_FOLDER)
        print("\n" + "=" * 60)
        print("Automation complete. Your repository is now clean and ready for upload.")
        print("=" * 60)