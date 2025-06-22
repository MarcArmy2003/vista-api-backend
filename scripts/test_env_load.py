from dotenv import load_dotenv
import os

load_dotenv()

key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print("Loaded credential path:", key_path)
