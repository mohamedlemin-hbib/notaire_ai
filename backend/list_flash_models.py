
from google import genai
from app.core.config import settings

def list_flash_models():
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    models = client.models.list()
    print("Flash models found:")
    for m in models:
        if "flash" in m.name.lower():
            print(f"- {m.name}")

if __name__ == "__main__":
    list_flash_models()
