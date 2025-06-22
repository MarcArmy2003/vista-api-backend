import os
import pandas as pd
import glob

# --- Configuration ---
# ** UPDATED **: The source folder is now directly under the main project folder.
SOURCE_XLS_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\XLS_TO_PROCESS"

# The dedicated output folder inside the repository.
MARKDOWN_OUTPUT_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository\ABR Excel Table Markdowns"

def convert_xls_to_markdown(source_path, output_path):
    """
    Finds all .xls files in the source path, reads all sheets from each,
    converts them to a single markdown .txt file, and deletes the source .xls file.
    """
    print(f"Scanning for Excel files in: {source_path}")
    os.makedirs(output_path, exist_ok=True)
    print(f"Markdown files will be saved to: {output_path}")

    # Find all .xls files in the source folder
    xls_files = glob.glob(os.path.join(source_path, '*.xls'))
    
    if not xls_files:
        print("No .xls files found in the 'XLS_TO_PROCESS' folder.")
        return

    print(f"Found {len(xls_files)} Excel files to convert.")
    print("-" * 60)

    # Process each Excel file
    for xls_path in xls_files:
        original_filename = os.path.basename(xls_path)
        print(f"Processing: {original_filename}")
        
        try:
            all_sheets = pd.read_excel(xls_path, sheet_name=None)
            txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '.txt')}")
            markdown_content = f"# Data from {original_filename}\n\n"

            for sheet_name, df in all_sheets.items():
                markdown_content += f"### {sheet_name}\n"
                if df.empty:
                    markdown_content += "*(No data in this sheet)*\n\n"
                    continue
                
                markdown_content += df.to_markdown(index=False)
                markdown_content += "\n\n"

            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"  -> Successfully created: {os.path.basename(txt_filename)}")

            try:
                os.remove(xls_path)
                print(f"  -> Successfully deleted original file: {original_filename}")
            except OSError as e:
                print(f"  -> WARNING: Could not delete original file {original_filename}. Error: {e}")

        except Exception as e:
            print(f"  -> ERROR: Could not process file {original_filename}. It may be corrupted or in an unexpected format. Error: {e}")
            
# --- Main Execution Block ---
if __name__ == "__main__":
    print("This script will convert all .xls files into clean .txt files.")
    print("Please ensure you have installed the required libraries.")
    print("Run: pip install pandas xlrd")
    
    try:
        import pandas
        import xlrd
    except ImportError as e:
        print(f"\nERROR: Missing required library. Please run 'pip install pandas xlrd'. Details: {e}")
    else:
        convert_xls_to_markdown(SOURCE_XLS_FOLDER, MARKDOWN_OUTPUT_FOLDER)
        print("\n" + "=" * 60)
        print("Automation complete.")
        print("=" * 60)