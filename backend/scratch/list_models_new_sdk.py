import os
import sys
# Add project root to sys.path to import app
sys.path.append(os.getcwd())

from google import genai
from app.core.config import settings

def list_models():
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    print("Listing models with google-genai SDK:")
    for model in client.models.list():
        print(f"- {model.name}")

if __name__ == "__main__":
    # Add project root to sys.path to import app.core.config
    import sys
    sys.path.append(os.getcwd())
    list_models()
