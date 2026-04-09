from google import genai
from app.core.config import settings
import os

def transcribe_voice_message(audio_bytes: bytes, mime_type: str = "audio/mpeg") -> dict:
    """
    Transcrit un message vocal et extrait l'intention de l'utilisateur via Gemini.
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return {"text": "Simulation: Crée un acte de vente.", "intent": "generation_acte"}

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    prompt = """
    Écoute ce message vocal de notaire. 
    1. Transcris le texte exactement.
    2. Identifie l'intention (ex: 'generer_acte', 'auditer_doc', 'information').
    
    Réponds au format JSON :
    {
        "transcription": "texte ici",
        "intention": "intention_ici",
        "resume": "résumé court"
    }
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                prompt,
                {"mime_type": mime_type, "data": audio_bytes}
            ]
        )
    except Exception as e:
        # Fallback if gemini-3 fails
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                prompt,
                {"mime_type": mime_type, "data": audio_bytes}
            ]
        )

    try:
        import json
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        return {
            "transcription": response.text,
            "error": "Failed to parse JSON intent",
            "raw": response.text
        }
