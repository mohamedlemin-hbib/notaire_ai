import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

try:
    models = client.models.list()
    for m in models:
        print(f"Model: {m.name}")
except Exception as e:
    print("Error:", e)
