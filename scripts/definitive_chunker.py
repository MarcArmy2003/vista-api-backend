import os
import argparse
import shutil
from dotenv import load_dotenv
from google.cloud import storage
import pandas as pd
import fitz # PyMuPDF for PDF processing

# Load .env variables from the environment where the script is run
load_dotenv()

# Get GCS paths from environment variables, with defaults
XLS_INPUT_FOLDER = os.getenv("XLS_INPUT_FOLDER", "gs://vista-api-backend-rag-files")
TXT_OUTPUT_FOLDER = os.getenv("TXT_OUTPUT_FOLDER", "gs://vista-processed-markdowns")

# Initialize GCS client
storage_client = storage.Client()

# This is a hard limit in bytes. 2MB to be safe for Vertex AI.
MAX_BYTES = 2000000

# --- Helper function to write a DataFrame chunk to a GCS text file ---
def write_gcs_chunk_to_file(df_chunk, original_filename_base, sheet_name, part_num, output_bucket, output_prefix):
    """
    Helper function to write a DataFrame chunk to a GCS text file.
    It sanitizes sheet names and constructs the GCS blob path.
    """
    if df_chunk.empty:
        return

    # Sanitize sheet name to be a valid filename part for GCS blob name
    # Removes non-alphanumeric characters except spaces and underscores, then strips trailing whitespace.
    safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()

    # Construct the output blob name
    output_filename = f"{original_filename_base}_{safe_sheet_name}_part_{part_num}.txt"
    output_blob_name = os.path.join(output_prefix, output_filename)

    # Prepare header for the markdown content
    header = f"# Data from {original_filename_base}\n## Sheet: {sheet_name} (Part {part_num})\n\n"
    markdown_content = header + df_chunk.to_markdown(index=False)

    # Upload the chunk to GCS
    output_blob = output_bucket.blob(output_blob_name)
    output_blob.upload_from_string(markdown_content)
    print(f"  -> Uploaded Excel chunk part {part_num} for sheet '{sheet_name}' to {output_blob_name} ({len(markdown_content.encode('utf-8'))} bytes) in {output_bucket.name}")

# --- PDF Processing Function ---
def process_pdf_document(temp_pdf_path, output_bucket, output_prefix, original_filename):
    """
    Processes PDF documents by extracting all text and uploading it to GCS.
    Note: For very large PDFs, this function currently uploads the entire text as one chunk.
    More sophisticated NLP-based chunking would be required for optimal results with extremely large PDFs.
    """
    print(f"  -> Processing PDF: {original_filename}")
    try:
        doc = fitz.open(temp_pdf_path)
        full_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            full_text += page.get_text() + "\n" # Extract text from each page

        if not full_text.strip():
            print(f"  -> WARNING: No readable text found in PDF: {original_filename}")
            return

        # Derive base name for output files
        original_filename_base = os.path.splitext(original_filename)[0]

        # Upload the entire PDF text as a single chunk (if it fits within Vertex AI limits)
        chunk_content = full_text
        output_filename = f"{original_filename_base}_full_text_chunk_1.txt" # Add chunk indicator
        output_blob_name = os.path.join(output_prefix, output_filename)

        output_blob = output_bucket.blob(output_blob_name)
        output_blob.upload_from_string(chunk_content)
        print(f"  -> Uploaded PDF chunk to {output_blob_name} in {output_bucket.name} ({len(chunk_content.encode('utf-8'))} bytes)")

    except Exception as e:
        print(f"  -> ERROR processing PDF {original_filename}: {e}")

# --- EXCEL Processing Function with Advanced Chunking ---
def process_excel_document(temp_excel_path, output_bucket, output_prefix, original_filename):
    """
    Processes Excel documents sheet by sheet, implementing a row-by-row,
    byte-size-aware chunking strategy to keep output markdown files under MAX_BYTES.
    """
    print(f"  -> Processing Excel: {original_filename}")
    original_filename_base = os.path.splitext(original_filename)[0] # Base name without extension

    try:
        xls = pd.ExcelFile(temp_excel_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            if df.empty:
                print(f"    -> Sheet '{sheet_name}' is empty. Skipping.")
                continue

            rows_for_chunk = []
            current_chunk_size_bytes = 0
            part_num = 1

            # Iterate through rows and build chunks based on byte size
            for index, row in df.iterrows():
                # Convert the current row to markdown to estimate its size
                temp_df_row = pd.DataFrame([row.values], columns=df.columns)
                row_markdown = temp_df_row.to_markdown(index=False)
                row_size_bytes = len(row_markdown.encode('utf-8'))

                # If adding this row exceeds MAX_BYTES, write the current chunk
                # and start a new one with the current row.
                # 'current_chunk_size_bytes > 0' ensures that if the first row alone is
                # larger than MAX_BYTES, it still forms its own chunk instead of being skipped.
                if current_chunk_size_bytes > 0 and (current_chunk_size_bytes + row_size_bytes) > MAX_BYTES:
                    chunk_df = pd.DataFrame(rows_for_chunk, columns=df.columns)
                    write_gcs_chunk_to_file(chunk_df, original_filename_base, sheet_name, part_num, output_bucket, output_prefix)
                    
                    rows_for_chunk = [] # Reset for new chunk
                    current_chunk_size_bytes = 0
                    part_num += 1
                
                rows_for_chunk.append(row.to_dict()) # Convert row to dictionary for DataFrame reconstruction
                current_chunk_size_bytes += row_size_bytes

            # After the loop, write any remaining rows to a final part
            if rows_for_chunk:
                final_chunk_df = pd.DataFrame(rows_for_chunk, columns=df.columns)
                write_gcs_chunk_to_file(final_chunk_df, original_filename_base, sheet_name, part_num, output_bucket, output_prefix)

    except Exception as e:
        print(f"  -> ERROR processing Excel {original_filename}: {e}")

# --- Main File Dispatcher Function ---
def process_files_from_gcs(input_uri, output_uri):
    """
    Downloads supported files (Excel, PDF) from a GCS input URI, processes them,
    and uploads the resulting markdown chunks to a GCS output URI.
    """
    # Parse bucket name and prefix from URIs
    input_bucket_name = input_uri.replace("gs://", "").split("/")[0]
    input_prefix = "/".join(input_uri.replace("gs://", "").split("/")[1:])
    output_bucket_name = output_uri.replace("gs://", "").split("/")[0]
    output_prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])

    input_bucket = storage_client.bucket(input_bucket_name)
    output_bucket = storage_client.bucket(output_bucket_name)

    print(f"--- Initiating file processing from {input_uri} to {output_uri} ---")

    # List blobs in the input bucket with the specified prefix
    blobs = input_bucket.list_blobs(prefix=input_prefix)
    
    # Filter for relevant file types (.xlsx, .xls, .pdf)
    files_to_process = [
        blob for blob in blobs 
        if blob.name.lower().endswith((".xlsx", ".xls", ".pdf"))
    ]

    if not files_to_process:
        print(f"WARNING: No supported Excel or PDF files found in {input_uri}")
        return

    # Process each supported file
    for blob in files_to_process:
        original_filename = os.path.basename(blob.name)
        # Use /tmp for temporary files in Cloud Run environments as it's a writeable directory
        temp_input_path = f"/tmp/{original_filename}" 
        
        try:
            # Download blob to a temporary local file
            blob.download_to_filename(temp_input_path)
            print(f"  -> Downloaded {original_filename} to {temp_input_path}")

            # Dispatch to appropriate processing function based on file type
            if original_filename.lower().endswith((".xlsx", ".xls")):
                process_excel_document(temp_input_path, output_bucket, output_prefix, original_filename)
            elif original_filename.lower().endswith(".pdf"):
                process_pdf_document(temp_input_path, output_bucket, output_prefix, original_filename)
            else:
                # This case should ideally not be reached due to prior filtering
                print(f"  -> INFO: Skipping unsupported file type after download: {original_filename}")

        except Exception as e:
            print(f"  -> ERROR processing file {original_filename}: {e}")
        finally:
            # Ensure temporary local file is cleaned up, even if processing fails
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                print(f"  -> Cleaned up temporary file {temp_input_path}")
    
    print(f"SUCCESS: Finished processing files from {input_uri} to {output_uri}")

def clean_output_folder(output_uri):
    """
    Cleans up all .txt files from a specified GCS output URI.
    This is useful for clearing previous processing results before a new run.
    """
    output_bucket_name = output_uri.replace("gs://", "").split("/")[0]
    output_prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])
    
    output_bucket = storage_client.bucket(output_bucket_name)
    
    print(f"--- Cleaning up .txt files from {output_uri} ---")
    
    # List all .txt blobs in the output prefix
    blobs_to_delete = output_bucket.list_blobs(prefix=output_prefix)
    txt_blobs = [blob for blob in blobs_to_delete if blob.name.endswith(".txt")]

    if not txt_blobs:
        print(f"WARNING: No .txt files found in {output_uri} to clean.")
        return

    # Delete each .txt blob
    for blob in txt_blobs:
        blob.delete()
        print(f"  -> Deleted {blob.name} from {output_bucket_name}")
    
    print(f"INFO: Cleaned up all .txt files from {output_bucket_name}/{output_prefix}")

def main():
    """
    Main entry point for the script.
    Parses command-line arguments and orchestrates file processing and cleanup.
    """
    parser = argparse.ArgumentParser(description="Process files from GCS and optionally clean output.")
    parser.add_argument("--clean", action="store_true", help="Remove all .txt files from output folder after processing")
    args = parser.parse_args()

    # Process files
    process_files_from_gcs(XLS_INPUT_FOLDER, TXT_OUTPUT_FOLDER)

    # Conditionally clean output folder if --clean argument is provided
    if args.clean:
        clean_output_folder(TXT_OUTPUT_FOLDER)

if __name__ == "__main__":
    main()