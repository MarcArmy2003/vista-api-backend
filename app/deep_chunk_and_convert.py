import os
import pandas as pd
import glob

# --- Configuration ---
SOURCE_XLS_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\XLS_TO_PROCESS"
MARKDOWN_OUTPUT_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository\ABR Excel Table Markdowns"
# Set a conservative chunk size limit in characters (well below the 2.5MB byte limit)
MAX_CHUNK_SIZE = 2000000 

def deep_chunk_and_convert(source_path, output_path):
    """
    Converts each sheet of each .xls file into one or more chunked .txt files,
    ensuring no single file exceeds the MAX_CHUNK_SIZE.
    """
    print(f"Scanning for Excel files in: {source_path}")
    os.makedirs(output_path, exist_ok=True)
    print(f"Deep-chunked Markdown files will be saved to: {output_path}")

    xls_files = glob.glob(os.path.join(source_path, '*.xls'))
    
    if not xls_files:
        print("No .xls files found in the 'XLS_TO_PROCESS' folder.")
        return

    print(f"Found {len(xls_files)} Excel files to convert.")
    print("-" * 60)

    for xls_path in xls_files:
        original_filename = os.path.basename(xls_path)
        print(f"Processing: {original_filename}")
        
        try:
            all_sheets = pd.read_excel(xls_path, sheet_name=None)
            
            for sheet_name, df in all_sheets.items():
                print(f"  - Reading sheet: {sheet_name}")
                
                if df.empty:
                    continue

                markdown_content = df.to_markdown(index=False)
                
                # ** NEW DEEP CHUNKING LOGIC **
                if len(markdown_content) > MAX_CHUNK_SIZE:
                    print(f"    -> Sheet is too large. Splitting into multiple parts...")
                    part_num = 1
                    start_char = 0
                    while start_char < len(markdown_content):
                        end_char = start_char + MAX_CHUNK_SIZE
                        # Find the next newline character to avoid cutting a line in half
                        if end_char < len(markdown_content):
                            split_pos = markdown_content.rfind('\n', start_char, end_char)
                            if split_pos != -1 and split_pos > start_char:
                                end_char = split_pos
                        
                        chunk_content = markdown_content[start_char:end_char]
                        
                        # Save this chunk to its own file
                        safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                        txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {safe_sheet_name} - part_{part_num}.txt")
                        
                        header = f"# Data from {original_filename}\n## Sheet: {sheet_name} (Part {part_num})\n\n"
                        with open(txt_filename, 'w', encoding='utf-8') as f:
                            f.write(header + chunk_content)
                        print(f"      -> Saved chunk: {os.path.basename(txt_filename)}")
                        
                        part_num += 1
                        start_char = end_char
                else:
                    # If sheet is small enough, save as one file
                    safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                    txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {safe_sheet_name}.txt")
                    header = f"# Data from {original_filename}\n## Sheet: {sheet_name}\n\n"
                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(header + markdown_content)
                    print(f"    -> Saved single file: {os.path.basename(txt_filename)}")

            os.remove(xls_path)
            print(f"  -> Successfully processed and deleted original: {original_filename}")

        except Exception as e:
            print(f"  -> ERROR: Could not process file {original_filename}. Error: {e}")

# --- Main Execution Block ---
if __name__ == "__main__":
    try:
        import pandas, xlrd, tabulate
    except ImportError as e:
        print(f"\nERROR: Missing required library. Please run 'pip install pandas xlrd tabulate'. Details: {e}")
    else:
        deep_chunk_and_convert(SOURCE_XLS_FOLDER, MARKDOWN_OUTPUT_FOLDER)
        print("\n" + "=" * 60)
        print("Deep chunking and conversion complete.")
        print("=" * 60)