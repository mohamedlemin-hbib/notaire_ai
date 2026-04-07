from google import genai
from google.genai import types
from app.core.config import settings
import json
import time
from PIL import Image
import io

def extract_info_from_ids_batch(vendeur_bytes: bytes, acheteur_bytes: bytes) -> dict:
    """
    Utilise Gemini 2.0 Flash pour extraire les infos de deux pièces d'identité en un seul appel (réduction du quota API).
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return {"vendeur": {"error": "Clé API non configurée"}, "acheteur": {"error": "Clé API non configurée"}}

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    prompt = """Analyse ces DEUX images (Image 1: Vendeur, Image 2: Acheteur).
Extrais les informations au format JSON UNIQUEMENT, structuré exactement comme ceci :
{
    "vendeur": {
        "nom": "string",
        "prenom": "string",
        "nni": "string",
        "date_naissance": "string",
        "lieu_naissance": "string",
        "genre": "M ou F"
    },
    "acheteur": {
        "nom": "string",
        "prenom": "string",
        "nni": "string",
        "date_naissance": "string",
        "lieu_naissance": "string",
        "genre": "M ou F"
    }
}
Si une image n'est pas une pièce d'identité ou est illisible, mets la valeur "error" dans le sous-objet correspondant.

CONSIGNE CRITIQUE : NE JAMAIS INVENTER D'INFORMATIONS.
Si vous ne voyez pas clairement un champ, mettez null.
Ne mettez aucun nom fictif ou de démonstration."""

    try:
        pil_v = Image.open(io.BytesIO(vendeur_bytes))
        pil_v.thumbnail((300, 300))
        byte_arr_v = io.BytesIO()
        pil_v.save(byte_arr_v, format='JPEG', quality=65)
        
        pil_a = Image.open(io.BytesIO(acheteur_bytes))
        pil_a.thumbnail((300, 300))
        byte_arr_a = io.BytesIO()
        pil_a.save(byte_arr_a, format='JPEG', quality=65)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=[
                        types.Part.from_bytes(data=byte_arr_v.getvalue(), mime_type="image/jpeg"),
                        types.Part.from_bytes(data=byte_arr_a.getvalue(), mime_type="image/jpeg"),
                        prompt
                    ]
                )
                
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_json)
                return result
            except Exception as e:
                error_msg = str(e)
                if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)
                    print(f"429 Quota API Gemini dpass. Attente de {wait_time}s avant la tentative {attempt + 2}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise e
                    
    except json.JSONDecodeError as e:
        print(f"OCR JSON parse error: {e}")
        return {"vendeur": {"error": "Erreur parse"}, "acheteur": {"error": "Erreur parse"}}
    except Exception as e:
        print(f"OCR Gemini API Error: {e}")
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
             error_msg = "Quota API Gemini dpass (429). Version LITE active. Veuillez patienter 20 secondes et ressayer."
        return {"vendeur": {"error": error_msg}, "acheteur": {"error": error_msg}}

def extract_info_from_id(image_bytes: bytes) -> dict:
    """Conserve l'ancienne mthode pour compatibilit"""
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return {"error": "Cl API non configure"}

    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    prompt = """Analyse cette image de carte d'identit ou passeport... (Voir batch pour dtails)
Renvoyez uniquement du JSON."""

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.thumbnail((300, 300))
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=65)
        img_bytes = img_byte_arr.getvalue()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=[types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"), "Extrais les informations sous forme JSON: nom, prenom, nni, date_naissance, lieu_naissance, genre. N'invente rien."]
                )
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_json)
            except Exception as e:
                error_msg = str(e)
                if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries - 1:
                    wait_time = 20 * (attempt + 1)
                    print(f"429 Quota API Gemini dépassé. Attente de {wait_time}s avant la tentative {attempt + 2}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise e
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
             error_msg = "Quota API Gemini dépassé (429). Veuillez patienter 1 minute avant de recommencer."
        return {"error": error_msg}
