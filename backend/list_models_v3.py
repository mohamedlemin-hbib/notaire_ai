import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

try:
    for m in client.models.list():
        # Check if it supports generateContent
        # In the new SDK, m has 'supported_generation_methods'? No, earlier it failed.
        # Let's just print them all again but carefully.
        print(f"Name: {m.name}")
except Exception as e:
    print("Error:", e)
