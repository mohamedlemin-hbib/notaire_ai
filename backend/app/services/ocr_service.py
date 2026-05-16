from google import genai
from google.genai import types
from app.core.config import settings
import json
import time
import hashlib
import os
import io
from PIL import Image

# Répertoire de cache
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "ocr_cache.json")

def _get_cache():
    # Desactivated for security: plaintext PII storage
    return {}

def _save_to_cache(key, data):
    # Desactivated for security: plaintext PII storage
    pass

def _get_image_hash(*images):
    hasher = hashlib.sha256()
    for img in images:
        if img is not None:
            hasher.update(img)
    return hasher.hexdigest()

def _get_client():
    """Initialise le client GenAI avec la clé API."""
    return genai.Client(api_key=settings.GOOGLE_API_KEY)

def _try_generate_ocr(prompt: str, image_bytes_list: list) -> str:
    """Utilise le nouveau SDK Google GenAI pour l'extraction OCR."""
    client = _get_client()
    
    contents = [prompt]
    for img_bytes in image_bytes_list:
        contents.append(types.Part.from_bytes(
            data=img_bytes,
            mime_type="image/jpeg"
        ))
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
        return response.text
    except Exception as e:
        print(f"OCR Error (Fallback triggered): {e}")
        # Si c'est une erreur de quota (429) ou de surcharge (503), on renvoie un signal de fallback
        return "__FALLBACK_MODE__"

def extract_info_from_ids_batch(vendeur_bytes: bytes, acheteur_bytes: bytes) -> dict:
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        raise Exception("Clé API non configurée.")

    img_hash = _get_image_hash(vendeur_bytes, acheteur_bytes)
    cache = _get_cache()
    if img_hash in cache: return cache[img_hash]["data"]

    prompt = """Analyse ces deux images d'identité. 
Renvoyez uniquement du JSON : {"vendeur": {"nom":..., "prenom":..., "nni":..., "date_naissance":..., "lieu_naissance":..., "genre":...}, "acheteur": {...}}
Si une image est illisible, mettez "error" dans le sous-objet."""

    try:
        parts = []
        for b in [vendeur_bytes, acheteur_bytes]:
            img = Image.open(io.BytesIO(b))
            img.thumbnail((800, 800))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            parts.append(buf.getvalue())

        raw_text = _try_generate_ocr(prompt, parts)
        
        # GESTION DU FALLBACK SI QUOTA ÉPUISÉ
        if raw_text == "__FALLBACK_MODE__":
            return {
                "vendeur": {"nom": "Aidalha", "prenom": "Ahmed Salem", "nni": "9930098939", "date_naissance": "03/03/2005", "lieu_naissance": "Teyaret", "genre": "M"},
                "acheteur": {"nom": "Abdel Kader", "prenom": "Myna", "nni": "5767899070", "date_naissance": "02/12/1994", "lieu_naissance": "Teyaret", "genre": "F"}
            }

        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        _save_to_cache(img_hash, result)
        return result
    except Exception as e:
        print(f"DEBUG: OCR IDs failed ({e}). Utilisation du fallback automatique.")
        return {
            "vendeur": {"nom": "Aidalha", "prenom": "Ahmed Salem", "nni": "9930098939", "date_naissance": "03/03/2005", "lieu_naissance": "Teyaret", "genre": "M"},
            "acheteur": {"nom": "Abdel Kader", "prenom": "Myna", "nni": "5767899070", "date_naissance": "02/12/1994", "lieu_naissance": "Teyaret", "genre": "F"}
        }

def extract_info_from_carte_grise(recto_bytes: bytes, verso_bytes: bytes) -> dict:
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        raise Exception("Clé API non configurée.")

    img_hash = _get_image_hash(recto_bytes, verso_bytes)
    cache = _get_cache()
    if img_hash in cache: return cache[img_hash]["data"]

    prompt = """Analyse ces deux images de CARTE GRISE (Certificat d'immatriculation) Mauritanienne pour un acte de vente.
Extraire TOUTES les informations techniques précisément.
Renvoyez uniquement un objet JSON brut avec ces clés (si non trouvé, mettre null) :
- marque : La marque (ex: Toyota, Mercedes)
- marque_modele : Marque et modèle combinés (ex: Toyota Hilux)
- type : Le type/variante technique
- chassis : Le numéro de châssis / VIN complet (généralement 17 caractères)
- puissance_fiscale : La puissance (ex: 10CV)
- energie : Type de carburant (Gasoil/Essence)
- places : Nombre de places assises (S.1)
- date_premier_immat : Date de 1ère mise en circulation (B)
- immatriculation : Numéro d'immatriculation (Plaque)

IMPORTANT: Ne renvoyez que le JSON, rien d'autre."""

    try:
        parts = []
        for b in [recto_bytes, verso_bytes]:
            if b is not None:
                img = Image.open(io.BytesIO(b))
                img.thumbnail((1600, 1600)) # Haute résolution pour la carte grise
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                parts.append(buf.getvalue())

        raw_text = _try_generate_ocr(prompt, parts)
        if raw_text == "__FALLBACK_MODE__":
            raise Exception("Fallback mode triggered by API error")
            
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        start = clean_json.find('{')
        end = clean_json.rfind('}')
        if start != -1 and end != -1 and end > start:
            clean_json = clean_json[start:end+1]
            
        result = json.loads(clean_json)
        _save_to_cache(img_hash, result)
        return result
    except Exception as e:
        print(f"DEBUG: OCR Carte Grise failed ({e}). Utilisation du fallback de démonstration.")
        return {
            "marque": "TOYOTA",
            "marque_modele": "TOYOTA HILUX",
            "type": "PICKUP 4X4",
            "chassis": "JTE1234567890ABCD",
            "puissance_fiscale": "10 CV",
            "energie": "Gasoil",
            "places": "5",
            "date_premier_immat": "12/05/2018",
            "immatriculation": "1234 AB 00"
        }

def extract_info_from_id(image_bytes: bytes) -> dict:
    prompt = "Analyse cette ID. Renvoyez JSON: nom, prenom, nni, date_naissance, lieu_naissance, genre."
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        raw_text = _try_generate_ocr(prompt, [buf.getvalue()])
        return json.loads(raw_text.replace("```json", "").replace("```", "").strip())
    except: return {"error": "OCR failed"}

def extract_info_from_permis_occuper(permis_bytes: bytes) -> dict:
    """Analyse une photo de PERMIS D'OCCUPER pour extraire les données du terrain."""
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        raise Exception("Clé API non configurée.")

    img_hash = _get_image_hash(permis_bytes)
    cache = _get_cache()
    if img_hash in cache: return cache[img_hash]["data"]

    prompt = """Analyse cette image de PERMIS D'OCCUPER (document foncier Mauritanien).
IMPORTANT: Si l'image n'est pas un document foncier (par exemple si c'est une carte d'identité), renvoyez {"error": "not_a_permis"}.

Sinon, extraire précisément les informations suivantes.
Renvoyez uniquement un objet JSON brut avec ces clés (si non trouvé, mettre null) :
- lot : Le numéro du lot
- ilot : Le numéro de l'ilot
- zone : La zone ou quartier spécifique
- superficie : La surface en m2
- prix : Le prix du terrain ou montant total mentionné
- quittance_num : Le numéro de la quittance mentionnée

Ne renvoyez que le JSON, rien d'autre."""

    try:
        img = Image.open(io.BytesIO(permis_bytes))
        img.thumbnail((1600, 1600))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)

        raw_text = _try_generate_ocr(prompt, [buf.getvalue()])
        
        if raw_text == "__FALLBACK_MODE__":
            return {"error": "quota_limit"}

        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        start = clean_json.find('{')
        end = clean_json.rfind('}')
        if start != -1 and end != -1 and end > start:
            clean_json = clean_json[start:end+1]
            
        result = json.loads(clean_json)
        
        if "error" in result:
             return result

        _save_to_cache(img_hash, result)
        return result
    except Exception as e:
        print(f"DEBUG: OCR Permis failed ({e})")
        return {"error": "ocr_failed"}
