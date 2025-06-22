import os
import pandas as pd
import glob

# --- Configuration ---
# The folder where you will place all the .xls files you want to convert.
SOURCE_XLS_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\XLS_TO_PROCESS"

# The dedicated folder where all new .txt Markdown files will be saved.
MARKDOWN_OUTPUT_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository\ABR Excel Table Markdowns"

def chunk_and_convert_xls(source_path, output_path):
    """
    Finds all .xls files, reads each sheet, converts each sheet to its OWN
    markdown .txt file (chunking), and deletes the source .xls file.
    """
    print(f"Scanning for Excel files in: {source_path}")
    os.makedirs(output_path, exist_ok=True)
    print(f"Chunked Markdown files will be saved to: {output_path}")

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
            # Read all sheets from the Excel file into a dictionary of DataFrames
            all_sheets = pd.read_excel(xls_path, sheet_name=None)
            
            # ** NEW LOGIC: Loop through each sheet and save it as its OWN file **
            for sheet_name, df in all_sheets.items():
                
                # Sanitize sheet name to be a valid filename
                safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                
                # Define the new .txt filename for each sheet
                txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {safe_sheet_name}.txt")
                
                markdown_content = f"# Data from {original_filename}\n## Sheet: {sheet_name}\n\n"
                
                if df.empty:
                    markdown_content += "*(No data in this sheet)*"
                else:
                    markdown_content += df.to_markdown(index=False)

                # Save the new .txt file for the individual sheet
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f"  -> Successfully created chunk: {os.path.basename(txt_filename)}")

            # If all sheets were processed successfully, delete the original .xls file
            try:
                os.remove(xls_path)
                print(f"  -> Successfully deleted original file: {original_filename}")
            except OSError as e:
                print(f"  -> WARNING: Could not delete original file {original_filename}. Error: {e}")

        except Exception as e:
            print(f"  -> ERROR: Could not process file {original_filename}. It may be corrupted or in an unexpected format. Error: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    print("This script will convert and CHUNK all .xls files into separate .txt files per sheet.")
    
    try:
        import pandas
        import xlrd
        import tabulate
    except ImportError as e:
        print(f"\nERROR: Missing required library. Please run 'pip install pandas xlrd tabulate'. Details: {e}")
    else:
        chunk_and_convert_xls(SOURCE_XLS_FOLDER, MARKDOWN_OUTPUT_FOLDER)
        print("\n" + "=" * 60)
        print("Automation complete. Your files are now chunked and ready for upload.")
        print("=" * 60)