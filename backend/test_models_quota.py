
from google import genai
from app.core.config import settings

def test_models():
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    models_to_test = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    
    for model_name in models_to_test:
        print(f"Test du modele: {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Dis 'OUI' si tu fonctionnes"
            )
            print(f"  -> SUCCESS: {response.text}")
        except Exception as e:
            print(f"  -> FAILURE: {str(e)[:100]}")

if __name__ == "__main__":
    test_models()
