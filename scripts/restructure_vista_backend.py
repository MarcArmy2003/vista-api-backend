import os
import shutil

# Base directory (update if needed)
base = r"C:\Users\gillo\OneDrive\Documents\veteran-analytics\vista-api-backend"

# Folder setup
structure = {
    "app": [
        "app.py", "convert_and_clean.py", "convert_xls_files.py",
        "sheets_reader.py", "unzip_utility.py", "definitive_chunker.py",
        "deep_chunk_and_convert.py", "convert_and_chunk.py"
    ],
    "scripts": [
        "extract.py.txt", "Python Auto-Unzip.txt", "Set-ExecutionPolicy"
    ],
    "specs": [
        "Category OpenAPI JSON spec for VA Data.txt",
        "VA Core Datasets API.txt", "VA Demographics & Population API.txt",
        "VA Facilities & War-Era Data API.txt", "VA Benefits & Expenditures API.txt",
        "OpenAPI JSON spec for VA Data.txt", "VISTA_CustomGPT_Actions_Config 2025-06-03 04_58_52.json"
    ],
    "docs": [
        "-- Tableau Calculated Field Cohort.txt", "U.S. Census Bureau API.txt"
    ],
    "data": [
        "Transcripts"
    ]
}

# Make folders and move files
for folder, files in structure.items():
    folder_path = os.path.join(base, folder)
    os.makedirs(folder_path, exist_ok=True)

    for f in files:
        src = os.path.join(base, f)
        if os.path.exists(src):
            dst = os.path.join(folder_path, os.path.basename(f))
            shutil.move(src, dst)

print("✅ Files organized successfully!")
