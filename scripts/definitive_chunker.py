import os
import argparse
import shutil
from dotenv import load_dotenv
from google.cloud import storage # Ensure this is imported
import pandas as pd # Make sure pandas is imported for Excel processing
import fitz # PyMuPDF for PDF processing

# Load .env variables
load_dotenv()

# Get paths from environment variables
XLS_INPUT_FOLDER = os.getenv("XLS_INPUT_FOLDER", "gs://vista-api-backend-rag-files")
TXT_OUTPUT_FOLDER = os.getenv("TXT_OUTPUT_FOLDER", "gs://vista-processed-markdowns")

# Initialize GCS client
storage_client = storage.Client()

# --- PDF Processing Function ---
def process_pdf_document(temp_pdf_path, output_bucket, output_prefix, original_filename):
    print(f"  -> Processing PDF: {original_filename}")
    try:
        doc = fitz.open(temp_pdf_path)
        full_text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            full_text += page.get_text() + "\n" # Extract text from each page

        # --- Implement PDF Chunking Logic Here ---
        # This is a basic example; you'll need to refine your chunking strategy
        # to ensure chunks are meaningful and within Vertex AI's size limits (e.g., 2.5MB).
        # For simplicity, this example just uploads the entire text as one chunk.
        # You'll likely need to split `full_text` into smaller `chunk_content` parts.
        # Example: if full_text is too large, split it into multiple parts and
        # then iterate to upload each `chunk_content`.

        if not full_text.strip():
            print(f"  -> WARNING: No readable text found in PDF: {original_filename}")
            return

        # Example of writing one chunk per PDF for now, to be refined later
        chunk_content = full_text
        output_filename = f"{os.path.splitext(original_filename)[0]}_chunk_1.txt" # Add chunk indicator
        output_blob_name = os.path.join(output_prefix, output_filename)

        output_blob = output_bucket.blob(output_blob_name)
        output_blob.upload_from_string(chunk_content)
        print(f"  -> Uploaded PDF chunk to {output_blob_name} in {output_bucket.name}")

    except Exception as e:
        print(f"  -> ERROR processing PDF {original_filename}: {e}")

# --- EXCEL Processing Function ---
def process_excel_document(temp_excel_path, output_bucket, output_prefix, original_filename):
    print(f"  -> Processing Excel: {original_filename}")
    try:
        # Use pandas to read the Excel file (assuming `xlrd` or `openpyxl` are installed via requirements.txt)
        xls = pd.ExcelFile(temp_excel_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # Convert DataFrame to Markdown string
            markdown_content = df.to_markdown(index=False)
            
            # --- Implement EXCEL Chunking Logic Here ---
            # Similar to PDF, you might need to split this markdown_content
            # if a single sheet's content is too large for Vertex AI.
            # For simplicity, this uploads each sheet's content as one chunk.

            safe_sheet_name = sheet_name.replace(' ', '_').replace('/', '_') # Make sheet name safe for filenames
            output_filename = f"{os.path.splitext(original_filename)[0]}_{safe_sheet_name}.txt"
            output_blob_name = os.path.join(output_prefix, output_filename)

            output_blob = output_bucket.blob(output_blob_name)
            output_blob.upload_from_string(markdown_content)
            print(f"  -> Uploaded Excel sheet to {output_blob_name} in {output_bucket.name}")

    except Exception as e:
        print(f"  -> ERROR processing Excel {original_filename}: {e}")

# --- Main File Dispatcher Function ---
def process_files_from_gcs(input_uri, output_uri):
    input_bucket_name = input_uri.replace("gs://", "").split("/")[0]
    input_prefix = "/".join(input_uri.replace("gs://", "").split("/")[1:])
    output_bucket_name = output_uri.replace("gs://", "").split("/")[0]
    output_prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])

    input_bucket = storage_client.bucket(input_bucket_name)
    output_bucket = storage_client.bucket(output_bucket_name)

    print(f"--- Initiating file processing from {input_uri} to {output_uri} ---")

    blobs = input_bucket.list_blobs(prefix=input_prefix)
    
    # Filter for relevant file types
    files_to_process = [
        blob for blob in blobs 
        if blob.name.lower().endswith((".xlsx", ".xls", ".pdf"))
    ]

    if not files_to_process:
        print(f"WARNING: No supported Excel or PDF files found in {input_uri}")
        return

    for blob in files_to_process:
        original_filename = os.path.basename(blob.name)
        temp_input_path = f"/tmp/{original_filename}" # /tmp is writeable in Cloud Run
        
        try:
            # Download blob to a temporary local file
            blob.download_to_filename(temp_input_path)
            print(f"  -> Downloaded {original_filename} to {temp_input_path}")

            if original_filename.lower().endswith((".xlsx", ".xls")):
                process_excel_document(temp_input_path, output_bucket, output_prefix, original_filename)
            elif original_filename.lower().endswith(".pdf"):
                process_pdf_document(temp_input_path, output_bucket, output_prefix, original_filename)
            else:
                print(f"  -> INFO: Skipping unsupported file type after download: {original_filename}")

        except Exception as e:
            print(f"  -> ERROR processing file {original_filename}: {e}")
        finally:
            # Ensure temporary file is cleaned up, even if processing fails
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
                print(f"  -> Cleaned up temporary file {temp_input_path}")
    
    print(f"SUCCESS: Finished processing files from {input_uri} to {output_uri}")

def clean_output_folder(output_uri):
    """Cleans up .txt files from a GCS output URI."""
    output_bucket_name = output_uri.replace("gs://", "").split("/")[0]
    output_prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])
    
    output_bucket = storage_client.bucket(output_bucket_name)
    
    print(f"--- Cleaning up .txt files from {output_uri} ---")
    
    blobs_to_delete = output_bucket.list_blobs(prefix=output_prefix)
    txt_blobs = [blob for blob in blobs_to_delete if blob.name.endswith(".txt")]

    if not txt_blobs:
        print(f"WARNING: No .txt files found in {output_uri} to clean.")
        return

    for blob in txt_blobs:
        blob.delete() # Use blob.delete() to remove from GCS
        print(f"  -> Deleted {blob.name} from {output_bucket_name}")
    
    print(f"INFO: Cleaned up all .txt files from {output_uri}")

def main():
    parser = argparse.ArgumentParser(description="Process files from GCS and optionally clean output.")
    parser.add_argument("--clean", action="store_true", help="Remove all .txt files from output folder after processing")
    args = parser.parse_args()

    process_files_from_gcs(XLS_INPUT_FOLDER, TXT_OUTPUT_FOLDER)

    if args.clean:
        clean_output_folder(TXT_OUTPUT_FOLDER)

if __name__ == "__main__":
    main()