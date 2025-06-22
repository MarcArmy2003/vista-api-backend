import os
import argparse
import shutil
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Get paths from environment variables
XLS_INPUT_FOLDER = os.getenv("XLS_INPUT_FOLDER", "data/XLS_TO_PROCESS")
TXT_OUTPUT_FOLDER = os.getenv("TXT_OUTPUT_FOLDER", "C:/VISTA_Repository/ABR Excel Table Markdowns")


def process_excel_to_txt(input_folder, output_folder):
    """Simulated processing function."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Simulate creation of output files
    for filename in os.listdir(input_folder):
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            with open(output_file, "w") as f:
                f.write(f"Processed content of {filename}\n")
    print(f"✅ Processed Excel files from {input_folder} to {output_folder}")


def clean_output_folder(output_folder):
    if os.path.exists(output_folder):
        for file in os.listdir(output_folder):
            if file.endswith(".txt"):
                os.remove(os.path.join(output_folder, file))
        print(f"🧹 Cleaned up all .txt files from {output_folder}")
    else:
        print(f"⚠️ Output folder not found: {output_folder}")


def main():
    parser = argparse.ArgumentParser(description="Process Excel files and optionally clean output.")
    parser.add_argument("--clean", action="store_true", help="Remove all .txt files from output folder after processing")
    args = parser.parse_args()

    process_excel_to_txt(XLS_INPUT_FOLDER, TXT_OUTPUT_FOLDER)

    if args.clean:
        clean_output_folder(TXT_OUTPUT_FOLDER)


if __name__ == "__main__":
    main()
