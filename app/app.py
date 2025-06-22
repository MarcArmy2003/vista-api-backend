from flask import Flask, jsonify, request
import gspread
import pandas as pd
import os

app = Flask(__name__)

# --- Global Cache ---
# We will store the data here after it's loaded once to minimize calls to Google Sheets
# and improve response times for subsequent requests.
_spreadsheet_data_cache = None

def get_data():
    """
    This function manages the retrieval of spreadsheet data.
    It first checks a global cache (_spreadsheet_data_cache). If the cache is already
    populated, it returns the cached data immediately.
    If the cache is empty (e.g., on the first request to the API), it loads the data
    from the specified Google Sheet and then populates the cache for future use.

    Expected Data:
        - Google Sheets service account key file ('vista-api-backend-6578a1a1c769.json')
        - Google Sheet titled 'Open VA Data APIs'
        - Specific worksheets within the spreadsheet: "API Name and Path",
          "VA Data Census Bureau APIs", "Census Bureau APIs - Full List",
          "VISTA Custom GPT Actions", "Utilities".

    Returns:
        A dictionary where keys are worksheet names and values are pandas DataFrames
        containing the data from each respective worksheet.
        If an error occurs during data loading, it returns a dictionary with an
        'error' key and a descriptive message, along with a 500 status.
    """
    global _spreadsheet_data_cache
    if _spreadsheet_data_cache is not None:
        # If data is already in cache, return it directly.
        return _spreadsheet_data_cache

    print("--- First request received. Loading data from Google Sheets into cache... ---")
    try:
        # Path to your Google Sheets service account key file.
        # This file contains credentials to authenticate with Google Sheets API.
        key_file = 'vista-api-backend-6578a1a1c769.json'
        spreadsheet_title = 'Open VA Data APIs'
        # List of worksheet names to load from the Google Spreadsheet.
        worksheet_names = [
            "API Name and Path", "VA Data Census Bureau APIs",
            "Census Bureau APIs - Full List", "VISTA Custom GPT Actions", "Utilities"
        ]

        # Authenticate with Google Sheets using the service account.
        gc = gspread.service_account(filename=key_file)
        # Open the specified spreadsheet by its title.
        spreadsheet = gc.open(spreadsheet_title)
        all_data = {}
        # Iterate through each specified worksheet and load its contents into a pandas DataFrame.
        for sheet_name in worksheet_names:
            worksheet = spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records() # Get all rows as a list of dictionaries.
            if records:
                df = pd.DataFrame(records)
                all_data[sheet_name] = df # Store DataFrame in the dictionary with sheet name as key.

        _spreadsheet_data_cache = all_data # Cache the loaded data.
        print("--- Caching complete. ---")
        return _spreadsheet_data_cache

    except Exception as e:
        # If any error occurs during data loading, capture it and store in cache.
        error_info = {"error": "Failed to load data on first request", "message": str(e)}
        _spreadsheet_data_cache = error_info
        print(f"--- ERROR during data load: {str(e)} ---")
        return _spreadsheet_data_cache

@app.route('/')
def home():
    """
    Handles the root endpoint of the API. This is typically used for health checks
    or to confirm the API is running.

    Expected Data: None. It triggers the data loading if not already cached.

    Returns:
        A simple string message indicating the API is running, or a JSON error
        response if data loading failed.
    """
    data = get_data()
    if isinstance(data, dict) and data.get("error"):
        # If get_data returned an error, jsonify it and return with a 500 status.
        return jsonify(data), 500
    # If data loaded successfully, return a success message.
    return "VA Data Backend API is running."

@app.route('/query_api_paths')
def query_api_paths():
    """
    Queries the 'API Name and Path' sheet from the cached spreadsheet data.
    Allows filtering of API paths by 'category'.

    Expected Data (Query Parameters):
        - `category` (optional, string): A string to filter the 'Categorization' column
          (e.g., 'Demographics', 'Benefits & Claims'). The search is case-insensitive.

    Returns:
        A JSON array of dictionaries, where each dictionary represents a row from
        the 'API Name and Path' sheet that matches the query.
        If no `category` parameter is provided, it returns all records from the sheet.
        Returns a JSON error response if the 'API Name and Path' sheet is not found
        in the cached data or if initial data loading failed.
    """
    data = get_data()
    if isinstance(data, dict) and data.get("error"):
        # If get_data returned an error, jsonify it and return with a 500 status.
        return jsonify(data), 500

    if "API Name and Path" not in data:
        # Ensure the required sheet is present in the loaded data.
        return jsonify({"error": "Sheet 'API Name and Path' not found in cache."}), 500

    df_api_paths = data["API Name and Path"] # Access the DataFrame for this specific sheet.
    category = request.args.get('category') # Get the 'category' query parameter.

    if not category:
        # If no category is provided, return all records from the sheet.
        return jsonify(df_api_paths.to_dict(orient='records'))

    # Filter the DataFrame based on the 'Categorization' column, case-insensitive.
    # .str.contains() is used for flexible substring matching.
    results = df_api_paths[df_api_paths['Categorization'].str.contains(category, case=False, na=False)]
    return jsonify(results.to_dict(orient='records'))

@app.route('/query_census_apis_full_list')
def query_census_apis_full_list():
    """
    Queries the 'Census Bureau APIs - Full List' sheet from the cached spreadsheet data.
    Allows filtering by 'dataset_name' or 'year'.

    Expected Data (Query Parameters):
        - `dataset_name` (optional, string): Filter by Census dataset name (e.g., 'cbp', 'acs').
          The search is case-insensitive.
        - `year` (optional, string): Filter by year (e.g., '1986'). This searches
          within the 'API Base URL' field. The search is case-insensitive.

    Returns:
        A JSON array of dictionaries, where each dictionary represents a row from
        the 'Census Bureau APIs - Full List' sheet that matches the query.
        If no filtering parameters are provided, it returns all records from the sheet.
        Returns a JSON error response if the 'Census Bureau APIs - Full List' sheet
        is not found in the cached data or if initial data loading failed.
    """
    data = get_data()
    if isinstance(data, dict) and data.get("error"):
        return jsonify(data), 500

    if "Census Bureau APIs - Full List" not in data:
        return jsonify({"error": "Sheet 'Census Bureau APIs - Full List' not found in cache."}), 500

    df_census_apis = data["Census Bureau APIs - Full List"]
    dataset_name = request.args.get('dataset_name')
    year = request.args.get('year')

    # Start with all data and apply filters sequentially.
    filtered_results = df_census_apis

    if dataset_name:
        filtered_results = filtered_results[
            filtered_results['Dataset Name'].str.contains(dataset_name, case=False, na=False)
        ]

    if year:
        # Search for the year within the 'API Base URL' column.
        filtered_results = filtered_results[
            filtered_results['API Base URL'].str.contains(year, case=False, na=False)
        ]

    return jsonify(filtered_results.to_dict(orient='records'))

if __name__ == '__main__':
    # This block is executed when the script is run directly.
    # In a production environment (like Cloud Run with Gunicorn), the `gunicorn`
    # server will manage the Flask application's execution.
    # For local development and testing:
    # Ensure you have the 'vista-api-backend-6578a1a1c769.json' key file in the same directory.
    # The debug mode reloads the server on code changes, useful for development.
    # It also enables a debugger in the browser if an error occurs.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))