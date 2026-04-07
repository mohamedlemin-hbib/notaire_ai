from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from google import genai
from google.genai import types

from app.core.config import settings
from app.services.vector_store import get_template_collection

def get_llm():
    """Initialise le LLM de manière paresseuse."""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        model="gemini-2.0-flash"
    )

def retrieve_templates(act_type: str, context_query: str, n_results=2):
    """Retrieve similar clauses/templates from ChromaDB."""
    collection = get_template_collection()
    
    if collection.count() == 0:
        return ""
    
    results = collection.query(
        query_texts=[f"{act_type}: {context_query}"],
        n_results=n_results
    )
    
    if not results or not results['documents'] or not results['documents'][0]:
        return ""
    
    return "\n".join(results['documents'][0])

def identify_missing_fields(parties_info: dict, special_clauses: str) -> list:
    """Identify which mandatory fields are missing from the input."""
    missing = []
    
    vendeur = parties_info.get("vendeur", {})
    if not vendeur or vendeur.get("error"):
        missing.append("Informations du Vendeur (Photo illisible ou absente)")
    
    acheteur = parties_info.get("acheteur", {})
    if not acheteur or acheteur.get("error"):
        missing.append("Informations de l'Acheteur (Photo illisible ou absente)")

    sc_lower = special_clauses.lower() if special_clauses else ""
    if "montant" not in sc_lower and "prix" not in sc_lower:
        missing.append("Prix de vente / Montant (MRU)")
    if "quartier" not in sc_lower:
        missing.append("Quartier de situation du bien")
    if "moughataa" not in sc_lower:
        missing.append("Moughataa (Département)")
    if "parcelle" not in sc_lower and "terrain" not in sc_lower:
        missing.append("Numéro de parcelle / Terrain")
    if "surface" not in sc_lower and "m²" not in sc_lower:
        missing.append("Surface du terrain (m²)")

    return missing

def generate_notarial_draft(
    act_type: str, 
    parties_info: dict, 
    special_clauses: str,
    notary_name: str = ".........................",
    notary_bureau: str = "............",
    completion_data: dict = None
) -> str:
    """
    Génère un brouillon d'acte de manière 100% déterministe en utilisant standard_template.txt.
    Élimine les hallucinations IA en injectant les données OCR directement dans le template légal.
    """
    import os
    import datetime
    import random
    
    # Charger le template source de vérité
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Remonter d'un cran si on est dans app/services
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        template_path = os.path.join(backend_dir, "standard_template.txt")
        with open(template_path, "r", encoding="utf-8") as f:
            template_text = f.read()
    except Exception as e:
        print(f"Erreur chargement template: {e}")
        # Fallback au texte par défaut si le fichier manque
        template_text = "Acte N° : ............\nPar-devant Maître ............\nOnt comparu : ..."

    # Données temporelles
    act_number = parties_info.get("act_number", f"{random.randint(100, 999)}/{datetime.datetime.now().year}")
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Données Vendeur
    vendeur = parties_info.get("vendeur", {})
    v_nom = (vendeur.get("nom") or "").upper()
    v_prenom = (vendeur.get("prenom") or "").capitalize()
    v_full = f"{v_prenom} {v_nom}".strip() if (v_nom or v_prenom) else "........................"
    v_nni = vendeur.get("nni") or "........................"
    v_date = vendeur.get("date_naissance") or ".........."
    v_lieu = vendeur.get("lieu_naissance") or ".........."
    
    # Données Acheteur
    acheteur = parties_info.get("acheteur", {})
    a_nom = (acheteur.get("nom") or "").upper()
    a_prenom = (acheteur.get("prenom") or "").capitalize()
    a_full = f"{a_prenom} {a_nom}".strip() if (a_nom or a_prenom) else "........................"
    a_nni = acheteur.get("nni") or "........................"
    a_date = acheteur.get("date_naissance") or ".........."
    a_lieu = acheteur.get("lieu_naissance") or ".........."
    
    # Données Complémentaires (depuis le formulaire de complétion)
    comp = completion_data or {}
    p_parcelle = comp.get("parcelle") or ".........."
    p_quartier = comp.get("quartier") or "........................"
    p_moughataa = comp.get("moughataa") or "........................"
    p_prix = comp.get("prix") or ".........."
    p_prix_lettres = comp.get("prix_lettres") or "............"
    p_date_effet = comp.get("date_effet") or current_date

    # Remplacement déterministe dans le template
    # 1. En-tête
    res = template_text.replace("Acte N° : ............", f"Acte N° : {act_number}")
    res = res.replace("au bureau de : ............", f"au bureau de : {notary_bureau}")
    res = res.replace("Maître ........................", f"Maître {notary_name}")
    res = res.replace("correspondant au (date) ..........", f"correspondant au (date) {current_date}")
    
    # 2. Vendeur (1. M./Mme : ...)
    res = res.replace("1. M./Mme : ........................", f"1. M./Mme : {v_full}")
    # Attention: Remplacer le premier "né(e) le .......... à .........."
    # Comme .replace remplace tout ou N occurrences, on va être prudent.
    res = res.replace("né(e) le .......... à ..........", f"né(e) le {v_date} à {v_lieu}", 1)
    res = res.replace("titulaire de la Carte Nationale d'Identité n° : ........................", f"titulaire de la Carte Nationale d'Identité n° : {v_nni}", 1)
    
    # 3. Acheteur (2. M./Mme : ...)
    res = res.replace("2. M./Mme : ........................", f"2. M./Mme : {a_full}")
    res = res.replace("né(e) le .......... à ..........", f"né(e) le {a_date} à {a_lieu}", 1)
    res = res.replace("titulaire de la Carte Nationale d'Identité n° : ........................", f"titulaire de la Carte Nationale d'Identité n° : {a_nni}", 1)
    
    # 4. Détails du bien
    res = res.replace("terrain n° : ..........", f"terrain n° : {p_parcelle}")
    res = res.replace("quartier : ........................", f"quartier : {p_quartier}")
    res = res.replace("Moughataa de : ........................", f"Moughataa de : {p_moughataa}")
    
    # 5. Montant et Date
    res = res.replace("Montant : ..........", f"Montant : {p_prix}")
    res = res.replace("(soit ............) ", f"(soit {p_prix_lettres}) ")
    res = res.replace("À compter du ..........", f"À compter du {p_date_effet}")
    res = res.replace("conformes, le ..........", f"conformes, le {current_date}")

    return res


def chat_with_gemini(messages: list, system_prompt: str = None) -> str:
    """
    Appel direct à Gemini pour le chat conversationnel.
    messages: liste de dicts {"role": "user"/"assistant", "content": "..."}
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return "ERREUR : Clé API non configurée."
    
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        system_inst = system_prompt or (
            "Vous êtes l'assistant IA d'un notaire mauritanien professionnel. "
            "Répondez de manière concise, professionnelle et en français. "
            "Vous pouvez aider avec les questions juridiques notariales, "
            "la rédaction d'actes, et les procédures notariales en Mauritanie."
        )
        
        # Construire l'historique au format genai
        history = []
        for msg in messages[:-1]:  # Tous sauf le dernier
            role = "user" if msg["role"] == "user" else "model"
            history.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
        
        # Créer la config avec system instruction
        config = types.GenerateContentConfig(
            system_instruction=system_inst,
            temperature=0.3,
        )
        
        # Dernier message
        last_content = messages[-1]["content"] if messages else "Bonjour"
        
        # Ajouter l'historique + dernier message
        all_contents = history + [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=last_content)]
            )
        ]
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=all_contents,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
             return "*(Attention: Quota IA dépassé, ceci est un faux message)* Bonjour ! Je vois que vous testez l'application. Je suis l'assistant notarial. Que puis-je faire pour vous ?"
        return f"Erreur de communication avec l'IA : {str(e)}"
