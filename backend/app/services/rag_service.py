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
        model="gemini-3-flash-preview"
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
def identify_missing_fields(parties_info: dict, special_clauses: str, act_type: str = "vente_immobilier") -> list:
    """Identify which mandatory fields are missing from the input based on act type."""
    missing = []
    
    # Validation de base des parties
    p1_key = "monsieur" if act_type == "mariage" else "vendeur"
    p2_key = "madame" if act_type == "mariage" else "acheteur"
    
    p1 = parties_info.get(p1_key, {})
    if not p1 or p1.get("error"):
        label = "Monsieur" if act_type == "mariage" else "Vendeur"
        missing.append(f"Informations du {label} (Photo illisible ou absente)")
    
    p2 = parties_info.get(p2_key, {})
    if not p2 or p2.get("error"):
        label = "Madame" if act_type == "mariage" else "Acheteur"
        missing.append(f"Informations de l'Acheteur (Photo illisible ou absente)")

    sc_lower = special_clauses.lower() if special_clauses else ""
    
    if act_type == "mariage":
        if "wali" not in sc_lower and "tuteur" not in sc_lower:
            missing.append("Nom du Wali (Tuteur légal)")
        if "témoin" not in sc_lower:
            missing.append("Premier Témoin")
            missing.append("Second Témoin")
        if "mahr" not in sc_lower and "dot" not in sc_lower:
            missing.append("Montant de la Dot (Mahr)")
            missing.append("État de la Dot (Payé/Différé)")
        if "conditions" not in sc_lower:
            missing.append("Conditions particulières")
            
    elif act_type == "vente_vehicule":
        if "marque" not in sc_lower and "modèle" not in sc_lower:
            missing.append("Marque et Modèle du véhicule")
        if "châssis" not in sc_lower:
            missing.append("Numéro de Châssis")
        if "immatriculation" not in sc_lower and "matricule" not in sc_lower:
            missing.append("Numéro d'immatriculation")
        if "prix" not in sc_lower and "montant" not in sc_lower:
            missing.append("Prix de vente (MRU)")
        if "année" not in sc_lower and "annee" not in sc_lower:
            missing.append("Année de mise en circulation")

    elif act_type == "vente_societe":
        if "société" not in sc_lower and "dénomination" not in sc_lower:
            missing.append("Dénomination de la société")
        if "registre" not in sc_lower and "commerce" not in sc_lower:
            missing.append("Registre du Commerce")
        if "parts" not in sc_lower:
            missing.append("Nombre de parts cédées")
        if "valeur" not in sc_lower:
            missing.append("Valeur nominale")
        if "prix" not in sc_lower and "montant" not in sc_lower:
            missing.append("Prix de cession (MRU)")
        if "lettres" not in sc_lower:
            missing.append("Prix en lettres")

    else: # vente_immobilier ou par défaut
        if "montant" not in sc_lower and "prix" not in sc_lower:
            missing.append("Prix de vente / Montant (MRU)")
        if "quartier" not in sc_lower:
            missing.append("Quartier de situation du bien")
        if "moughataa" not in sc_lower:
            missing.append("Moughataa (Département)")
        if "parcelle" not in sc_lower and "terrain" not in sc_lower:
            missing.append("Numéro de parcelle / Terrain")

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
    Génère un brouillon d'acte de manière déterministe en utilisant le template approprié.
    """
    import os
    import datetime
    import random
    
    # Sélection du template
    template_filename = f"template_{act_type}.txt"
    if act_type == "vente": template_filename = "template_vente_immobilier.txt" # Fallback mapping
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        template_path = os.path.join(backend_dir, template_filename)
        
        # Fallback si le template spécifique n'existe pas
        if not os.path.exists(template_path):
            template_path = os.path.join(backend_dir, "standard_template.txt")
            
        with open(template_path, "r", encoding="utf-8") as f:
            template_text = f.read()
    except Exception as e:
        print(f"Erreur chargement template {template_filename}: {e}")
        template_text = "Acte N° : ............\nPar-devant Maître ............\nOnt comparu : ..."

    # Données temporelles
    act_number = parties_info.get("act_number", f"{random.randint(100, 999)}/{datetime.datetime.now().year}")
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Mapping des parties selon le type d'acte
    p1_key = "monsieur" if act_type == "mariage" else "vendeur"
    p2_key = "madame" if act_type == "mariage" else "acheteur"
    
    p1 = parties_info.get(p1_key, {})
    p1_full = f"{(p1.get('prenom') or '').capitalize()} {(p1.get('nom') or '').upper()}".strip() or "........................"
    p1_nni = p1.get("nni") or "........................"
    p1_date = p1.get("date_naissance") or ".........."
    p1_lieu = p1.get("lieu_naissance") or ".........."
    
    p2 = parties_info.get(p2_key, {})
    p2_full = f"{(p2.get('prenom') or '').capitalize()} {(p2.get('nom') or '').upper()}".strip() or "........................"
    p2_nni = p2.get("nni") or "........................"
    p2_date = p2.get("date_naissance") or ".........."
    p2_lieu = p2.get("lieu_naissance") or ".........."
    
    comp = completion_data or {}
    
    # Remplacement générique
    res = template_text.replace("Acte N° : ............", f"Acte N° : {act_number}")
    res = res.replace("au bureau de : ............", f"au bureau de : {notary_bureau}")
    res = res.replace("Maître ........................", f"Maître {notary_name}")
    res = res.replace("correspondant au (date) ..........", f"correspondant au (date) {current_date}")
    
    # Remplacement des parties (1. M./Mme ...)
    # On gère les deux types de préfixes dans les templates
    res = res.replace("1. M./Mme : ........................", f"1. M./Mme : {p1_full}")
    res = res.replace("1. M. : ........................", f"1. M. : {p1_full}")
    
    res = res.replace("né(e) le .......... à ..........", f"né(e) le {p1_date} à {p1_lieu}", 1)
    res = res.replace("né le .......... à ..........", f"né le {p1_date} à {p1_lieu}", 1)
    
    res = res.replace("titulaire de la Carte Nationale d'Identité n° : ........................", f"titulaire de la Carte Nationale d'Identité n° : {p1_nni}", 1)
    
    res = res.replace("2. M./Mme : ........................", f"2. M./Mme : {p2_full}")
    res = res.replace("2. Mme : ........................", f"2. Mme : {p2_full}")
    
    res = res.replace("né(e) le .......... à ..........", f"né(e) le {p2_date} à {p2_lieu}", 1)
    res = res.replace("née le .......... à ..........", f"née le {p2_date} à {p2_lieu}", 1)
    
    res = res.replace("titulaire de la Carte Nationale d'Identité n° : ........................", f"titulaire de la Carte Nationale d'Identité n° : {p2_nni}", 1)
    
    # Remplacement des données spécifiques (selon les clés présentes dans les templates)
    for key, value in comp.items():
        placeholder = f".........." # Très générique, on va plutôt chercher par label
        # Cette partie est plus complexe sans un mapping strict par type d'acte dans le template
        # Mais pour l'instant on garde la logique de remplacement direct pour les champs connus
        pass

    # Champs spécifiques IMMOBILIER
    res = res.replace("terrain n° : ..........", f"terrain n° : {comp.get('parcelle', '..........')}")
    res = res.replace("quartier : ........................", f"quartier : {comp.get('quartier', '........................')}")
    res = res.replace("Moughataa de : ........................", f"Moughataa de : {comp.get('moughataa', '........................')}")
    
    # Champs spécifiques VÉHICULE
    res = res.replace("Marque/Modèle : ........................", f"Marque/Modèle : {comp.get('marque_modele', '........................')}")
    res = res.replace("N° de Châssis : ........................", f"N° de Châssis : {comp.get('chassis', '........................')}")
    res = res.replace("Immatriculation : ........................", f"Immatriculation : {comp.get('matricule', '........................')}")
    res = res.replace("- Année : ........................", f"- Année : {comp.get('annee', '........................')}")
    res = res.replace("Année : ........................", f"Année : {comp.get('annee', '........................')}")
    
    # Champs spécifiques SOCIÉTÉ (Parts sociales)
    res = res.replace("société dénommée : ........................", f"société dénommée : {comp.get('nom_societe', '........................')}")
    res = res.replace("sous le n° : .........................", f"sous le n° : {comp.get('registre_commerce', '.........................')}")
    res = res.replace("Nombre de parts cédées : ........................", f"Nombre de parts cédées : {comp.get('parts_cedees', '........................')}")
    res = res.replace("Valeur nominale : ........................", f"Valeur nominale : {comp.get('valeur_nominale', '........................')}")

    # Champs spécifiques MARIAGE
    res = res.replace("Le Wali (Tuteur légal) de l'épouse : ........................", f"Le Wali (Tuteur légal) de l'épouse : {comp.get('wali', '........................')}")
    res = res.replace("- Témoin 1 : ........................", f"- Témoin 1 : {comp.get('temoin1', '........................')}")
    res = res.replace("- Témoin 2 : ........................", f"- Témoin 2 : {comp.get('temoin2', '........................')}")
    res = res.replace("- Montant : ........................", f"- Montant : {comp.get('mahr', '........................')}")
    res = res.replace("- État : ........................ (Payé / Différé)", f"- État : {comp.get('mahr_etat', '........................')} (Payé / Différé)")
    res = res.replace("Conditions particulières : ........................", f"Conditions particulières : {comp.get('conditions', '........................')}")
    
    # Montant global (Prix)
    res = res.replace("Prix de la cession : ..........", f"Prix de la cession : {comp.get('prix', '..........')}")
    res = res.replace("Montant : ..........", f"Montant : {comp.get('prix', '..........')}")
    res = res.replace("Montant de la vente : ..........", f"Montant de la vente : {comp.get('prix', '..........')}")
    res = res.replace("(soit ............) ", f"(soit {comp.get('prix_lettres', '............')}) ")
    res = res.replace("(soit ............) Nouvelles", f"(soit {comp.get('prix_lettres', '............')}) Nouvelles")
    
    res = res.replace("À compter du ..........", f"À compter du {comp.get('date_effet', current_date)}")
    res = res.replace("Le (jour) .......... correspondant", f"Le (jour) {current_date} correspondant")
    res = res.replace("correspondant au (date) ..........", f"correspondant au (date) {current_date}")
    res = res.replace("l'an ..........", f"l'an {datetime.datetime.now().year}")
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
        
        message = messages[-1]["content"] if messages else ""
        
        # --- MODE DÉMONSTRATION v2.1.0 ---
        if "Générer un acte de vente de démonstration" in message:
            return {
                "reply": "🔔 **MODE DÉMONSTRATION ACTIVÉ**\n\nJe simule la lecture de deux cartes d'identité valides...\n\n✅ **Extraction réussie** :\n• Vendeur : Maître Mohamed Lamine\n• Acheteur : Sarah Lemine\n\n⚙️ **Génération de l'acte en cours...**\n\nVoici le brouillon professionnel généré avec le nouveau moteur de rédaction v2.1.0 :",
                "pdf_url": "/api/v1/generation/download/demo_act.pdf",
                "document_id": 999
            }
        
        # Créer la config avec system instruction
        config = types.GenerateContentConfig(
            system_instruction=system_inst,
            temperature=0.3,
        )
        
        # Dernier message
        last_content = message if message else "Bonjour"
        
        # Ajouter l'historique + dernier message
        all_contents = history + [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=last_content)]
            )
        ]
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=all_contents,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        err_str = str(e)
        print(f"Gemini Chat Error: {err_str}")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
             return "*(Attention: Quota IA dépassé, ceci est un faux message)* Bonjour ! Je vois que vous testez l'application. Je suis l'assistant notarial. Que puis-je faire pour vous ?"
        if "11001" in err_str or "getaddrinfo" in err_str or "NameResolutionError" in err_str or "Max retries exceeded" in err_str:
             return "Erreur réseau : Impossible de contacter le serveur d'Intelligence Artificielle. Vérifiez votre connexion internet."
        return f"Erreur de communication avec l'IA : {err_str}"
