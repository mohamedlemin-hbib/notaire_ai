import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

models_to_try = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro"
]

for model in models_to_try:
    print(f"Testing {model}...")
    try:
        response = client.models.generate_content(
            model=model,
            contents="Hi"
        )
        print(f"SUCCESS with {model}!")
        break
    except Exception as e:
        print(f"FAILED {model}: {e}")
