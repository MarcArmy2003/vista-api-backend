import gspread
import pandas as pd

# --- Configuration ---
SERVICE_ACCOUNT_KEY_FILE = 'vista-api-backend-6578a1a1c769.json'
SPREADSHEET_TITLE = 'Open VA Data APIs'
WORKSHEET_NAMES = [
    "API Name and Path",
    "VA Data Census Bureau APIs",
    "Census Bureau APIs - Full List",
    "VISTA Custom GPT Actions",
    "Utilities"
]

def get_data_from_sheet():
    """
    Connects to Google Sheets using a service account and retrieves data
    from specified worksheets, returning them as a dictionary of DataFrames.
    """
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_KEY_FILE)
        print(f"Type of gspread client object after authentication: {type(gc)}")
        spreadsheet = gc.open(SPREADSHEET_TITLE)

        all_data = {}
        for sheet_name in WORKSHEET_NAMES:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)

                # --- NEW LOGIC: Manually handle header rows for specific sheets ---
                if sheet_name in ["API Name and Path", "Census Bureau APIs - Full List"]:
                    # Get all values from the sheet
                    list_of_lists = worksheet.get_all_values()
                    
                    if not list_of_lists:
                        print(f"Worksheet '{sheet_name}' is empty.")
                        continue # Skip to next sheet

                    # Assuming headers are on row 2 (index 1 in a 0-indexed list)
                    headers = list_of_lists[1]
                    # Data starts from row 3 (index 2)
                    data_rows = list_of_lists[2:]

                    # Clean headers: remove empty strings if any appear due to sheet structure
                    # And handle potential duplicate names by making them unique
                    cleaned_headers = []
                    header_counts = {}
                    for h in headers:
                        if h: # Only include non-empty headers
                            original_h = h
                            count = header_counts.get(original_h, 0)
                            if count > 0:
                                h = f"{original_h}_{count}" # Append count for duplicates
                            cleaned_headers.append(h)
                            header_counts[original_h] = count + 1
                        else:
                            # If a header is completely empty, give it a generic name
                            # This handles the original '' duplicates error
                            unique_blank_name = f"Unnamed_Column_{len(cleaned_headers)}"
                            cleaned_headers.append(unique_blank_name)
                    
                    if data_rows:
                        df = pd.DataFrame(data_rows, columns=cleaned_headers)
                    else:
                        df = pd.DataFrame(columns=cleaned_headers) # Create empty DF with headers
                    
                else:
                    # For all other sheets, use the default get_all_records()
                    records = worksheet.get_all_records()
                    if records:
                        df = pd.DataFrame(records)
                    else:
                        df = pd.DataFrame() # Create empty DataFrame if no records/headers found

                if not df.empty: # Check if DataFrame was successfully created
                    all_data[sheet_name] = df
                    print(f"Successfully loaded data from '{sheet_name}'. Rows: {len(df)}")
                else:
                    print(f"Worksheet '{sheet_name}' is empty or has no recognizable headers/data.")

            except gspread.exceptions.WorksheetNotFound:
                print(f"Error: Worksheet '{sheet_name}' not found in the spreadsheet. Please check the name for typos and case-sensitivity.")
            except Exception as e:
                print(f"An error occurred while reading worksheet '{sheet_name}': {e}")
                print(f"Error details for {sheet_name}: {e}") # More detailed error
        return all_data

    except FileNotFoundError:
        print(f"Error: Service account key file not found at '{SERVICE_ACCOUNT_KEY_FILE}'.")
        print("Please ensure the JSON key file is in the same directory as this script and the filename is correct.")
        return None
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Error: Spreadsheet with title '{SPREADSHEET_TITLE}' not found or service account does not have access.")
        print("Please double-check the SPREADSHEET_TITLE and ensure the service account has 'Viewer' access to the sheet.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during Google Sheets connection: {e}")
        print(f"Error details: {e}")
        return None

if __name__ == "__main__":
    data = get_data_from_sheet()
    if data:
        for sheet_name, df in data.items():
            print(f"\n--- Data from '{sheet_name}' ---")
            print(df.head())
            # For debugging, print all columns to see what got loaded
            # print(df.columns)
    else:
        print("\nFailed to load any data from Google Sheets.")