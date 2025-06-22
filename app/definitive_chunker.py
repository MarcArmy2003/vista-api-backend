import os
import pandas as pd
import glob

SOURCE_XLS_FOLDER = "XLS_TO_PROCESS"
MARKDOWN_OUTPUT_FOLDER = "VISTA_Repository/ABR Excel Table Markdowns"
# This is now a hard limit in bytes. 2MB to be safe.
MAX_BYTES = 2000000  

def write_chunk_to_file(df, original_filename, sheet_name, part_num, output_path):
    """Helper function to write a dataframe chunk to a text file."""
    if df.empty:
        return
    
    txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {sheet_name} - part_{part_num}.txt")
    header = f"# Data from {original_filename}\n## Sheet: {sheet_name} (Part {part_num})\n\n"
    
    # Convert the final, safe chunk to markdown
    markdown_content = df.to_markdown(index=False)
    
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(header + markdown_content)
    print(f"  -> Wrote part {part_num} for sheet '{sheet_name}' ({len(markdown_content.encode('utf-8'))} bytes)")

def definitive_chunk_and_convert_v2(source_path, output_path):
    print(f"Scanning for Excel files in: {source_path}")
    os.makedirs(output_path, exist_ok=True)
    print(f"Deep-chunked Markdown files will be saved to: {output_path}")
    
    xls_files = glob.glob(os.path.join(source_path, '*.xls'))
    if not xls_files:
        print("No .xls files found.")
        return
        
    print(f"Found {len(xls_files)} Excel files to convert.")

    for xls_path in xls_files:
        original_filename = os.path.basename(xls_path)
        print(f"Processing: {original_filename}")
        
        try:
            all_sheets = pd.read_excel(xls_path, sheet_name=None)
            for sheet_name, df in all_sheets.items():
                if df.empty:
                    continue

                safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                part_num = 1
                
                # This list will hold the row data for the current chunk
                rows_for_chunk = []
                
                for index, row in df.iterrows():
                    # Add the next row to our list
                    rows_for_chunk.append(row)
                    
                    # Create a temporary DataFrame from the current list of rows
                    temp_chunk_df = pd.DataFrame(rows_for_chunk, columns=df.columns)
                    
                    # Convert to markdown and check the REAL byte size
                    markdown_size = len(temp_chunk_df.to_markdown(index=False).encode('utf-8'))

                    # If this chunk is now too big...
                    if markdown_size > MAX_BYTES:
                        # ...the chunk we want to write is the one BEFORE we added the last row.
                        chunk_to_write = pd.DataFrame(rows_for_chunk[:-1], columns=df.columns)
                        
                        write_chunk_to_file(chunk_to_write, original_filename, safe_sheet_name, part_num, output_path)
                        
                        # The next chunk starts with the row that caused the overflow
                        rows_for_chunk = [row]
                        part_num += 1

                # After the loop, write any remaining rows to a final part
                if rows_for_chunk:
                    final_chunk_df = pd.DataFrame(rows_for_chunk, columns=df.columns)
                    write_chunk_to_file(final_chunk_df, original_filename, safe_sheet_name, part_num, output_path)
            
            # The script deletes the original file after processing
            os.remove(xls_path)
            print(f"  -> Successfully processed and removed {original_filename}")

        except Exception as e:
            print(f"ERROR processing {original_filename}: {e}")

if __name__ == "__main__":
    definitive_chunk_and_convert_v2(SOURCE_XLS_FOLDER, MARKDOWN_OUTPUT_FOLDER)
    print("\n" + "=" * 60)
    print("Automation complete.")
    print("=" * 60)