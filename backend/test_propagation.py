import os
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print(f"Testing new key: {api_key[:5]}...{api_key[-5:]}")

models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro-latest", "gemini-flash-latest"]

for model in models:
    print(f"\n--- Testing model: {model} ---")
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model,
                contents="Hello"
            )
            print(f"SUCCESS with {model} on attempt {attempt+1}!")
            print("Response:", response.text)
            exit(0)
        except Exception as e:
            print(f"Attempt {attempt+1} FAILED: {e}")
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Quota limit hit (limit: 0). Waiting 5s before retry...")
            time.sleep(5)

print("\nConclusion: The key is still returning quota errors for all tested models.")
