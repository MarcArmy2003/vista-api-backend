import requests
import zipfile
import io
import os

# --- Configuration ---
# The local folder where you want to save the extracted files.
EXTRACT_TO_FOLDER = r"C:\Users\gillo\OneDrive\Documents\ChatGPT Instructions\VISTA API Backend\VISTA_Repository"

def download_and_unzip_in_memory(url, destination_folder):
    """
    Downloads a ZIP file from a URL, unzips it in memory,
    and saves the contents to a destination folder.
    Returns True on success, False on failure.
    """
    print(f"Attempting download from: {url}")
    try:
        # Use a timeout to prevent the script from hanging indefinitely
        response = requests.get(url, timeout=30)
        # Raise an exception for bad status codes (like 404, 500)
        response.raise_for_status()
        print("Download successful. Unzipping contents...")

        # Unzip from memory
        with io.BytesIO(response.content) as zip_in_memory:
            with zipfile.ZipFile(zip_in_memory, 'r') as zip_ref:
                zip_ref.extractall(destination_folder)
                print(f"Successfully extracted {len(zip_ref.namelist())} file(s).")
        return True

    except requests.exceptions.HTTPError as e:
        # Specifically handle the case where a file doesn't exist (404)
        if e.response.status_code == 404:
            print(f"Warning: File not found at this URL (404 Error). Skipping.")
        else:
            print(f"Error: A web error occurred. {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to download the file due to a network issue. {e}")
        return False
    except zipfile.BadZipFile:
        print("Error: The downloaded file is not a valid ZIP archive. Skipping.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

# --- Main Execution Block ---
if __name__ == "__main__":
    print("Starting comprehensive download and unzip process...")

    # Step 1: Generate the list of URLs based on the provided pattern
    base_url = "http://www.va.gov/budget/docs/archive/FY-{}_VA-PerformanceAccountabilityReport.zip"
    years_to_process = range(2014, 1999, -1)  # Generates numbers from 2014 down to 2000
    url_list = [base_url.format(year) for year in years_to_process]

    # Ensure the destination directory exists before we start
    os.makedirs(EXTRACT_TO_FOLDER, exist_ok=True)
    print(f"All extracted files will be saved to: {EXTRACT_TO_FOLDER}")
    print("-" * 60)

    # Step 2: Loop through the list and process each URL
    total_urls = len(url_list)
    success_count = 0
    fail_count = 0
    for i, url in enumerate(url_list):
        print(f"\n--- Processing URL {i + 1} of {total_urls} ---")
        if download_and_unzip_in_memory(url, EXTRACT_TO_FOLDER):
            success_count += 1
        else:
            fail_count += 1
    
    # Step 3: Print a final summary report
    print("\n" + "=" * 60)
    print("                PROCESS COMPLETE")
    print("-" * 60)
    print(f"Summary: {success_count} URLs processed successfully.")
    print(f"         {fail_count} URLs failed or were skipped.")
    print(f"All extracted files are now in your local repository.")
    print("=" * 60)