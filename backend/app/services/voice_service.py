import google.generativeai as genai
from app.core.config import settings
import os

def transcribe_voice_message(audio_bytes: bytes, mime_type: str = "audio/mpeg") -> dict:
    """
    Transcrit un message vocal et extrait l'intention de l'utilisateur via Gemini.
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return {"text": "Simulation: Crée un acte de vente.", "intent": "generation_acte"}

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

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

    # Gemini can take raw bytes for audio
    response = model.generate_content([
        prompt,
        {
            "mime_type": mime_type,
            "data": audio_bytes
        }
    ])

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
