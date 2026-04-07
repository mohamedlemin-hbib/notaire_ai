
from google import genai
from app.core.config import settings
import os

def check_models():
    print(f"Checking API Key (starts with): {settings.GOOGLE_API_KEY[:10]}...")
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    try:
        models = client.models.list()
        print("Available models:")
        for m in models:
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    check_models()
