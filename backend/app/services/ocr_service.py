from google import genai
from google.genai import types
from app.core.config import settings
import json
import time
import hashlib
import os
from PIL import Image
import io

# Répertoire de cache
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "ocr_cache.json")

def _get_cache():
    """Récupère le cache local depuis le fichier JSON."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_to_cache(key: str, data: dict):
    """Sauvegarde un résultat dans le cache local."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache = _get_cache()
        cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde cache: {e}")

def _get_image_hash(*images: bytes) -> str:
    """Génère un hash SHA256 à partir d'une ou plusieurs images."""
    hasher = hashlib.sha256()
    for img in images:
        hasher.update(img)
    return hasher.hexdigest()

# Modèles Gemini à essayer dans l'ordre (optimisé pour Gemini 3 Flash et fallbacks validés)
GEMINI_MODELS_FALLBACK = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

# Données de démonstration réalistes (données mauritaniennes fictives)
DEMO_DATA = {
    "vendeur": {
        "nom": "OULD AHMED",
        "prenom": "Abdallahi",
        "nni": "3001456789",
        "date_naissance": "15/03/1972",
        "lieu_naissance": "Nouakchott",
        "genre": "M"
    },
    "acheteur": {
        "nom": "MINT BRAHIM",
        "prenom": "Mariem",
        "nni": "3009876543",
        "date_naissance": "22/07/1985",
        "lieu_naissance": "Nouadhibou",
        "genre": "F"
    }
}


def _try_generate_content(prompt: str, parts: list) -> str:
    """
    Tente d'appeler l'API Gemini avec plusieurs modèles en fallback automatique.
    Lève une exception si tous les modèles échouent.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    last_error = None

    for model_name in GEMINI_MODELS_FALLBACK:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=parts + [prompt]
            )
            print(f"OCR: Modèle utilisé avec succès: {model_name}")
            return response.text
        except Exception as e:
            err_str = str(e)
            print(f"OCR: Modèle {model_name} échoué -> {err_str[:100]}")
            # Attente progressive entre les tentatives pour le quota
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_time = 3 + (GEMINI_MODELS_FALLBACK.index(model_name) * 2)
                print(f"OCR: Quota atteint. Attente de {wait_time}s...")
                time.sleep(wait_time)
            last_error = e
            continue

    raise last_error


def extract_info_from_ids_batch(vendeur_bytes: bytes, acheteur_bytes: bytes) -> dict:
    """
    Utilise Gemini pour extraire les infos de deux pièces d'identité en un seul appel.
    Fallback automatique sur plusieurs modèles, puis mode démonstration si tout échoue.
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        raise Exception("Clé API non configurée. (Erreur 429 implicite)")

    # Vérification du cache
    img_hash = _get_image_hash(vendeur_bytes, acheteur_bytes)
    cache = _get_cache()
    if img_hash in cache:
        print("OCR: Cache Hit (Batch)!")
        return cache[img_hash]["data"]

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

CONSIGNE CRITIQUE : NE JAMAIS INVENTER D'INFORMATIONS. TU NE DOIS PRENDRE QUE CE QUI EST EXACTEMENT VISIBLE SUR LA CARTE (NOM, PRENOM, NNI, DATE DE NAISSANCE).
Si vous ne voyez pas clairement un champ, mettez null.
Ne mettez aucun nom fictif ou de démonstration. Seuls le NNI, prénom, nom, et date de naissance réels de l'image."""

    try:
        # Compression des images
        pil_v = Image.open(io.BytesIO(vendeur_bytes))
        pil_v.thumbnail((300, 300))
        byte_arr_v = io.BytesIO()
        pil_v.save(byte_arr_v, format='JPEG', quality=65)

        pil_a = Image.open(io.BytesIO(acheteur_bytes))
        pil_a.thumbnail((300, 300))
        byte_arr_a = io.BytesIO()
        pil_a.save(byte_arr_a, format='JPEG', quality=65)

        parts = [
            types.Part.from_bytes(data=byte_arr_v.getvalue(), mime_type="image/jpeg"),
            types.Part.from_bytes(data=byte_arr_a.getvalue(), mime_type="image/jpeg"),
        ]

        raw_text = _try_generate_content(prompt, parts)
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        # Mise en cache du résultat réussi
        _save_to_cache(img_hash, result)
        return result

    except json.JSONDecodeError as e:
        print(f"OCR JSON parse error: {e}")
        return {
            "vendeur": {"error": "Format de réponse invalide. Veuillez réessayer."},
            "acheteur": {"error": "Format de réponse invalide. Veuillez réessayer."}
        }

    except Exception as e:
        err_str = str(e)
        print(f"OCR: Tous les modèles ont échoué ({err_str[:150]}) -> mode démonstration")

        # Si quota ou permission refusée sur tous les modèles
        if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "403", "PERMISSION_DENIED"]):
            print("OCR: Quota ou permission API (429/403) depasse")
            return {
                "vendeur": {"error": "(Erreur 429) Le quota de l'Intelligence Artificielle est épuisé. Veuillez réessayer dans quelques instants ou changer la clé API. Nous n'inventons aucune donnée de substitution."},
                "acheteur": {"error": "(Erreur 429) Quota IA épuisé."}
            }

        # Si pas d'internet ou DNS introuvable (Erreur 11001 getaddrinfo)
        if "11001" in err_str or "getaddrinfo" in err_str or "NameResolutionError" in err_str or "Max retries exceeded" in err_str:
            print(f"OCR: Erreur de connexion réseau ({err_str[:50]})")
            return {
                "vendeur": {"error": "Vérifiez votre connexion internet. Impossible de joindre le serveur d'Intelligence Artificielle (Erreur réseau/DNS)."},
                "acheteur": {"error": "Erreur réseau globale ou proxy bloquant."}
            }

        # Autre erreur inattendue
        return {
            "vendeur": {"error": f"Erreur de communication API: {err_str[:150]}"},
            "acheteur": {"error": f"Veuillez vérifier la connexion ou la validité des images."}
        }


def extract_info_from_id(image_bytes: bytes) -> dict:
    """Extraits les infos d'une seule pièce d'identité (compatibilité ascendante)."""
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        raise Exception("Clé API non configurée. (Erreur 429 implicite)")

    # Vérification du cache
    img_hash = _get_image_hash(image_bytes)
    cache = _get_cache()
    if img_hash in cache:
        print("OCR: Cache Hit (Single)!")
        return cache[img_hash]["data"]

    prompt = """Analyse cette image de carte d'identité ou passeport.
Renvoyez uniquement du JSON avec: nom, prenom, nni, date_naissance, lieu_naissance, genre.
NE JAMAIS INVENTER. Si un champ est illisible, mettez null."""

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image.thumbnail((300, 300))
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=65)

        parts = [types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type="image/jpeg")]
        raw_text = _try_generate_content(prompt, parts)
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_json)
        
        # Mise en cache
        _save_to_cache(img_hash, result)
        return result

    except Exception as e:
        err_str = str(e)
        print(f"OCR single: Erreur -> {err_str[:150]}")
        if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "403", "PERMISSION_DENIED"]):
            return {"error": "(Erreur 429) Quota épuisé, impossible de lire la carte."}
        if "11001" in err_str or "getaddrinfo" in err_str or "NameResolutionError" in err_str or "Max retries exceeded" in err_str:
            return {"error": "Vérifiez votre connexion internet. Serveur inaccessible."}
        return {"error": f"Erreur de communication API: {err_str[:200]}"}
