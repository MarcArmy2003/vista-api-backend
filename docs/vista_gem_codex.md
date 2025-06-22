# VISTA Project Knowledge Base - Initial Load
## Mission & Vision
The VISTA project aims to create a "LegalZoom-style" platform to help veterans navigate the complex world of VA benefits. It will automate data retrieval, power research with an AI-driven knowledge base, and streamline the claims process.
## Core Technology Stack
- **Language:** Python 3.11+
- **Libraries:** pandas, xlrd, tabulate, requests
- **Cloud Platform:** Google Cloud Platform (GCP)
- **AI/RAG System:** Vertex AI Search
- **API Backend:** Flask
- **Deployment:** Docker, Cloud Run, Gunicorn
- **Storage:** Google Cloud Storage
## Key Workflow 1: Data Ingestion & Cleaning
This process takes raw source files (.zip, .xls, .pdf) and prepares them for the AI.
### The Problem
The source data contained unsupported file types (`.xls`, `.db`, `.DS_Store`) and text files that exceeded the 2.5MB size limit for Vertex AI ingestion, causing import failures.
### The Solution
The solution is a multi-stage Python script that performs "deep chunking." It reads `.xls` files, processes them sheet by sheet and row by row, and splits them into multiple smaller `.txt` files to guarantee no single file is too large. It also cleans up all unsupported and intermediate files.
### Final Data Processing Script (`definitive_chunker.py`)
```python
import os
import pandas as pd
import glob
SOURCE_XLS_FOLDER = "XLS_TO_PROCESS" # Assumes this is in the same dir as script
MARKDOWN_OUTPUT_FOLDER = "VISTA_Repository/ABR Excel Table Markdowns"
MAX_CHUNK_SIZE = 500000 
def definitive_chunk_and_convert(source_path, output_path):
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
                if df.empty: continue
                safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                
                current_chunk_rows = []
                current_size = 0
                part_num = 1
                
                for index, row in df.iterrows():
                    row_str = '| ' + ' | '.join(map(str, row.values)) + ' |\n'
                    if current_chunk_rows and current_size + len(row_str) > MAX_CHUNK_SIZE:
                        chunk_df = pd.DataFrame(current_chunk_rows, columns=df.columns)
                        txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {safe_sheet_name} - part_{part_num}.txt")
                        header = f"# Data from {original_filename}\n## Sheet: {sheet_name} (Part {part_num})\n\n"
                        with open(txt_filename, 'w', encoding='utf-8') as f:
                            f.write(header + chunk_df.to_markdown(index=False))
                        current_chunk_rows, current_size, part_num = [], 0, part_num + 1
                    current_chunk_rows.append(row)
                    current_size += len(row_str)
                if current_chunk_rows:
                    chunk_df = pd.DataFrame(current_chunk_rows, columns=df.columns)
                    part_str = f" - part_{part_num}" if part_num > 1 else ""
                    txt_filename = os.path.join(output_path, f"{original_filename.replace('.xls', '')} - {safe_sheet_name}{part_str}.txt")
                    header = f"# Data from {original_filename}\n## Sheet: {sheet_name}{part_str.replace('_', ' ').title()}\n\n"
                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(header + chunk_df.to_markdown(index=False))
                        
            os.remove(xls_path)
        except Exception as e:
            print(f"ERROR processing {original_filename}: {e}")
if __name__ == "__main__":
    definitive_chunk_and_convert(SOURCE_XLS_FOLDER, MARKDOWN_OUTPUT_FOLDER)
