import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

try:
    for m in client.models.list():
        print(f"Model: {m.name}, Methods: {m.supported_generation_methods}")
except Exception as e:
    print("Error:", e)
