import os
import argparse
import shutil
from dotenv import load_dotenv
from google.cloud import storage # Ensure this is imported

# Load .env variables
load_dotenv()

# Get paths from environment variables
XLS_INPUT_FOLDER = os.getenv("XLS_INPUT_FOLDER", "gs://vista-api-backend-rag-files")
TXT_OUTPUT_FOLDER = os.getenv("TXT_OUTPUT_FOLDER", "gs://vista-processed-markdowns")

# Initialize GCS client
storage_client = storage.Client()

def process_excel_to_txt(input_uri, output_uri):
    """
    Processes Excel files from a GCS input URI and uploads processed .txt files
    to a GCS output URI.
    """
    input_bucket_name = input_uri.replace("gs://", "").split("/")[0]
    input_prefix = "/".join(input_uri.replace("gs://", "").split("/")[1:])
    output_bucket_name = output_uri.replace("gs://", "").split("/")[0]
    output_prefix = "/".join(output_uri.replace("gs://", "").split("/")[1:])

    input_bucket = storage_client.bucket(input_bucket_name)
    output_bucket = storage_client.bucket(output_bucket_name)

    print(f"--- Processing Excel files from {input_uri} to {output_uri} ---")

    # List blobs (files) in the input folder (prefix)
    # Using 'delimiter' helps list contents of a "folder" in a bucket
    blobs = input_bucket.list_blobs(prefix=input_prefix)
    
    # Filter for Excel files (assuming no subfolders under the prefix for simplicity)
    excel_blobs = [blob for blob in blobs if blob.name.endswith(".xlsx") or blob.name.endswith(".xls")]

    if not excel_blobs:
        print(f"WARNING: No Excel files found in {input_uri}")
        return

    for blob in excel_blobs:
        original_filename = os.path.basename(blob.name)
        
        # Download blob to a temporary local file for processing
        # In Cloud Run, /tmp is a writeable filesystem
        temp_input_path = f"/tmp/{original_filename}"
        blob.download_to_filename(temp_input_path)
        print(f"  -> Downloaded {original_filename} to {temp_input_path}")

        # --- THIS IS WHERE YOUR ACTUAL CHUNKING LOGIC GOES ---
        # Instead of just writing a simulated line, you will:
        # 1. Read the Excel file from temp_input_path using pandas/xlrd.
        # 2. Apply your chunking logic (sheet by sheet, row by row).
        # 3. For each chunk, generate its content as a string.
        # 4. Upload each generated chunk as a separate .txt file to GCS.
        
        # Example of simulating one output file:
        processed_content = f"Processed content of {original_filename}\n"
        output_filename = f"{os.path.splitext(original_filename)[0]}.txt"
        
        # Upload processed content to GCS output bucket
        output_blob_name = os.path.join(output_prefix, output_filename)
        output_blob = output_bucket.blob(output_blob_name)
        output_blob.upload_from_string(processed_content)
        print(f"  -> Uploaded {output_filename} to {output_blob_name} in {output_bucket_name}")
        
        # Clean up temporary local file after processing
        os.remove(temp_input_path)
        print(f"  -> Cleaned up temporary file {temp_input_path}")
        
    print(f"SUCCESS: Processed Excel files from {input_uri} to {output_uri}")

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
    
    print(f" Cleaned up all .txt files from {output_uri}")

def main():
    parser = argparse.ArgumentParser(description="Process Excel files and optionally clean output.")
    parser.add_argument("--clean", action="store_true", help="Remove all .txt files from output folder after processing")
    args = parser.parse_args()

    process_excel_to_txt(XLS_INPUT_FOLDER, TXT_OUTPUT_FOLDER)

    if args.clean:
        clean_output_folder(TXT_OUTPUT_FOLDER)

if __name__ == "__main__":
    main()