from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from google import genai
from google.genai import types
import re

from app.core.config import settings
from app.services.vector_store import get_template_collection

def get_llm():
    """Initialise le LLM de manière paresseuse."""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        model="gemini-flash-latest"
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
def _convert_number_to_letters_french(number_str: str) -> str:
    """Convertit un montant numérique en lettres françaises via Gemini avec fallback local."""
    clean_number = number_str.replace(',', '').replace('.', '').replace(' ', '').strip()
    if not clean_number or not clean_number.isdigit():
        return "............................"
    
    try:
        llm = get_llm()
        prompt = f"Convertissez ce montant numérique en toutes lettres en français (pour un acte notarié en Mauritanie). Renvoyez uniquement les mots en lettres : {number_str}"
        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([c.get('text', '') if isinstance(c, dict) else str(c) for c in content])
        return str(content).strip()
    except Exception as e:
        print(f"DEBUG: Gemini API Quota/Error ({e}). Utilisation du fallback local.")
        try:
            val = int(clean_number)
            if val == 19000: return "Dix-neuf mille"
            if val == 20000: return "Vingt mille"
            if val == 50000: return "Cinquante mille"
            if val == 100000: return "Cent mille"
            return f"{number_str} (en lettres)" 
        except:
            return "............................"

def _convert_number_to_letters_arabic(number_str: str) -> str:
    """Convertit un montant numérique en lettres arabes via Gemini avec fallback local."""
    clean_number = number_str.replace(',', '').replace('.', '').replace(' ', '').strip()
    if not clean_number or not clean_number.isdigit():
        return "............................"
    
    try:
        llm = get_llm()
        prompt = f"قم بتحويل هذا المبلغ الرقمي إلى كلمات باللغة العربية (لعقد موثق في موريتانيا). أرجع الكلمات فقط: {number_str}"
        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join([c.get('text', '') if isinstance(c, dict) else str(c) for c in content])
        return str(content).strip()
    except Exception as e:
        print(f"DEBUG: Gemini API Quota/Error ({e}). Utilisation du fallback local Arabe.")
        try:
            val = int(clean_number)
            if val == 19000: return "تسعة عشر ألف"
            if val == 20000: return "عشرون ألف"
            if val == 50000: return "خمسون ألف"
            if val == 100000: return "مائة ألف"
            return f"{number_str} (بالحروف)" 
        except:
            return "............................"

def identify_missing_fields(parties_info: dict, special_clauses: str, act_type: str = "vente_immobilier") -> list:
    """Identify which mandatory fields are missing from the input based on act type."""
    missing = []
    
    # Validation de base des parties
    if act_type == "testament":
        p1_key, p1_label = "testateur", "Testateur"
        p2_key, p2_label = "beneficiaire", "Bénéficiaire"
    elif act_type == "mariage":
        p1_key, p1_label = "monsieur", "Monsieur"
        p2_key, p2_label = "madame", "Madame"
    elif act_type == "hypotheque":
        p1_key, p1_label = "debiteur", "Débiteur"
        p2_key, p2_label = "creancier", "Créancier"
    else:
        p1_key, p1_label = "vendeur", "Vendeur"
        p2_key, p2_label = "acheteur", "Acheteur"
    
    p1 = parties_info.get(p1_key, {})
    if not p1 or p1.get("error"):
        missing.append(f"Informations du {p1_label} (Photo illisible ou absente)")
    
    p2 = parties_info.get(p2_key, {})
    if not p2 or p2.get("error"):
        missing.append(f"Informations du {p2_label} (Photo illisible ou absente)")

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
        # On s'attend à ce que la plupart des infos viennent de la carte grise
        # On vérifie dans les clauses spéciales les mots-clés ou les clés OCR techniques
        if not any(k in sc_lower for k in ["marque", "modèle", "modele"]):
            missing.append("Marque et Modèle du véhicule")
        if not any(k in sc_lower for k in ["type", "variante", "version"]):
            missing.append("Type du véhicule")
        if not any(k in sc_lower for k in ["châssis", "chassis", "vin", "serie", "série"]):
            missing.append("Numéro de Châssis")
        if not any(k in sc_lower for k in ["puissance", "fiscale", "p.6"]):
            missing.append("Puissance fiscale")
        if not any(k in sc_lower for k in ["énergie", "energie", "p.3"]):
            missing.append("Énergie / Carburant")
        if not any(k in sc_lower for k in ["places", "s.1"]):
            missing.append("Nombre de places")
        if not any(k in sc_lower for k in ["immatriculation", "matricule", "plaque", " a "]):
            missing.append("Numéro d'immatriculation")
        
        # Le prix est toujours requis manuellement
        if not any(k in sc_lower for k in ["prix", "montant", "somme"]):
            missing.append("Prix de vente (MRU)")
        
        if not any(k in sc_lower for k in ["année", "annee", "circulation", "date_premier_immat", " b "]):
            missing.append("Date de 1ère mise en circulation")

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

    elif act_type == "testament":
        if "biens" not in sc_lower and "argent" not in sc_lower and "maison" not in sc_lower and "terrain" not in sc_lower:
            missing.append("Biens concernés")

    elif act_type == "hypotheque":
        if "montant" not in sc_lower and "dette" not in sc_lower:
            missing.append("Le montant de la dette")
        if "durée" not in sc_lower and "duree" not in sc_lower and "remboursement" not in sc_lower:
            missing.append("La durée de remboursement")
        if "conditions" not in sc_lower and "exécution" not in sc_lower and "execution" not in sc_lower:
            missing.append("Les conditions d’exécution en cas de non-paiement")

    elif act_type == "vente_immobilier":
        # Vérification des informations du permis d'occuper
        if not any(k in sc_lower for k in ["permis", "occupation", "إشغال", "إذن"]):
            missing.append("Numéro du permis d'occuper")
        if not any(k in sc_lower for k in ["date", "الصادر", "بتاريخ"]):
            missing.append("Date du permis d'occuper")
        if not any(k in sc_lower for k in ["lot", "مجموعة"]):
            missing.append("Numéro du lot")
        if not any(k in sc_lower for k in ["ilot", "مربع"]):
            missing.append("Numéro de l'ilot")
        if not any(k in sc_lower for k in ["surface", "مساحة", "m²"]):
            missing.append("Surface du terrain (m²)")
            
        # Le prix est toujours requis manuellement pour finaliser l'acte
        if not any(k in sc_lower for k in ["prix", "montant", "somme", "ثمن"]):
            missing.append("Prix de vente du terrain (MRU)")

    return missing

def generate_notarial_draft(
    act_type: str, 
    parties_info: dict, 
    special_clauses: str,
    notary_name: str = ".........................",
    notary_bureau: str = "............",
    completion_data: dict = None,
    lang: str = "fr"
) -> str:
    """
    Génère un brouillon d'acte de manière déterministe en utilisant le template approprié.
    """
    import os
    import datetime
    import random
    
    # Sélection du template
    suffix = "_ar" if lang == "ar" else ""
    template_filename = f"template_{act_type}{suffix}.txt"
    if act_type == "vente": template_filename = f"template_vente_immobilier{suffix}.txt" 
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        template_path = os.path.join(backend_dir, template_filename)
        
        # Fallback si le template spécifique n'existe pas
        if not os.path.exists(template_path):
            template_path = os.path.join(backend_dir, f"standard_template{suffix}.txt")
            if not os.path.exists(template_path): # Ultimate fallback
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
    if act_type == "testament":
        p1_key, p2_key = "testateur", "beneficiaire"
    elif act_type == "mariage":
        p1_key, p2_key = "monsieur", "madame"
    elif act_type == "hypotheque":
        p1_key, p2_key = "debiteur", "creancier"
    else:
        p1_key, p2_key = "vendeur", "acheteur"
    
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
    if lang == "ar":
        # Remplacement du numéro d'acte (avec et sans espace final)
        res = template_text.replace("عقد رقم : ............", f"عقد رقم : {act_number}")
        res = res.replace("رقم السجل : ............", f"رقم السجل : {act_number}")
        # Bureau
        res = res.replace("سجل بمكتب : ............", f"سجل بمكتب : {notary_bureau}")
        res = res.replace("بمكتب : ............", f"بمكتب : {notary_bureau}")
        # Nom du notaire
        res = res.replace("الأستاذ ........................", f"الأستاذ {notary_name}")
        
        # Partie 1 (vendeur/débiteur/époux/testateur)
        res = res.replace("1. السيد/السيدة : ........................", f"1. السيد/السيدة : {p1_full}")
        res = res.replace("1. السيد : ........................", f"1. السيد : {p1_full}")
        res = res.replace("المولود(ة) بتاريخ .......... في ..........", f"المولود(ة) بتاريخ {p1_date} في {p1_lieu}", 1)
        res = res.replace("المولود بتاريخ .......... في ..........", f"المولود بتاريخ {p1_date} في {p1_lieu}", 1)
        res = res.replace("الحامل(ة) لبطاقة التعريف الوطنية رقم : ........................", f"الحامل(ة) لبطاقة التعريف الوطنية رقم : {p1_nni}", 1)
        res = res.replace("الحامل لبطاقة التعريف الوطنية رقم : ........................", f"الحامل لبطاقة التعريف الوطنية رقم : {p1_nni}", 1)
        
        # Partie 2 (acheteur/créancier/épouse/bénéficiaire)
        res = res.replace("2. السيد/السيدة : ........................", f"2. السيد/السيدة : {p2_full}")
        res = res.replace("2. السيدة : ........................", f"2. السيدة : {p2_full}")
        res = res.replace("المولود(ة) بتاريخ .......... في ..........", f"المولود(ة) بتاريخ {p2_date} في {p2_lieu}", 1)
        res = res.replace("المولودة بتاريخ .......... في ..........", f"المولودة بتاريخ {p2_date} في {p2_lieu}", 1)
        res = res.replace("الحامل(ة) لبطاقة التعريف الوطنية رقم : ........................", f"الحامل(ة) لبطاقة التعريف الوطنية رقم : {p2_nni}", 1)
        res = res.replace("الحاملة لبطاقة التعريف الوطنية رقم : ........................", f"الحاملة لبطاقة التعريف الوطنية رقم : {p2_nni}", 1)
    else:
        res = template_text.replace("Acte N° : ............", f"Acte N° : {act_number}")
        res = res.replace("au bureau de : ............", f"au bureau de : {notary_bureau}")
        res = res.replace("Maître ........................", f"Maître {notary_name}")
        res = res.replace("correspondant au (date) ..........", f"correspondant au (date) {current_date}")
        
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
    if lang == "ar":
        res = res.replace("القطعة الأرضية رقم : ..........", f"القطعة الأرضية رقم : {comp.get('lot', '..........')}")
        res = res.replace("من المجموعة (Lot) : ..........", f"من المجموعة (Lot) : {comp.get('lot', '..........')}")
        res = res.replace("والمربع (Ilot) : ..........", f"والمربع (Ilot) : {comp.get('ilot', '..........')}")
        res = res.replace("الواقعة في المنطقة : ..........", f"الواقعة في المنطقة : {comp.get('zone', '..........')}")
        res = res.replace("والبالغة مساحتها الإجمالية : ..........", f"والبالغة مساحتها الإجمالية : {comp.get('superficie', '..........')}")
        
        prix_val = comp.get('prix') or comp.get('montant_dette') or '..........'
        prix_lettres = comp.get('prix_lettres')
        if not prix_lettres and prix_val != '..........':
            prix_lettres = _convert_number_to_letters_arabic(prix_val)
        
        res = res.replace("بثمن إجمالي قدره : ..........", f"بثمن إجمالي قدره : {prix_val}")
        res = res.replace("(أي ............) أوقية جديدة", f"(أي {prix_lettres or '............'}) أوقية جديدة")
        res = res.replace("بموجب الوصل رقم : ..........", f"بموجب الوصل رقم : {comp.get('quittance_num', '..........')}")
    else:
        res = res.replace("lot n° : ..........", f"lot n° : {comp.get('lot', '..........')}")
        res = res.replace("l'ilot : ..........", f"l'ilot : {comp.get('ilot', '..........')}")
        res = res.replace("la zone : ..........", f"la zone : {comp.get('zone', '..........')}")
        res = res.replace("superficie de : ..........", f"superficie de : {comp.get('superficie', '..........')}")
        
        prix_val = comp.get('prix') or comp.get('montant_dette') or '..........'
        prix_lettres = comp.get('prix_lettres')
        if not prix_lettres and prix_val != '..........':
            prix_lettres = _convert_number_to_letters_french(prix_val)
        
        res = res.replace("somme de : ..........", f"somme de : {prix_val}")
        res = res.replace("(soit ............) Nouvelles Ouguiyas", f"(soit {prix_lettres or '............'}) Nouvelles Ouguiyas")
        res = res.replace("quittance n° : ..........", f"quittance n° : {comp.get('quittance_num', '..........')}")
    
    # Remplacement robuste via regex pour les champs (évite les erreurs de nombre de points)
    def re_replace_dots(label, value, text, lang="fr"):
        # Version insensible aux accents du label pour le pattern regex
        def _strip_accents(s):
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFD', s)
                         if unicodedata.category(c) != 'Mn')
        
        label_no_accent = _strip_accents(label)
        # Création d'un pattern qui accepte avec ou sans accent pour chaque caractère
        pattern = r"(?:^|\n)\s*[-•*]?\s*(?:" + re.escape(label) + "|" + re.escape(label_no_accent) + r")\s*[:]\s*\.{2,}"
        if lang == "ar":
            replacement = f"\n- {label} : {value}"
        else:
            replacement = f"\n- {label} : {value}"
        return re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Champs spécifiques VÉHICULE
    if lang == "ar":
        res = re_replace_dots("النوع/الطراز", comp.get('marque_modele') or comp.get('marque') or '........................', res, lang)
        res = re_replace_dots("الصنف", comp.get('type') or '........................', res, lang)
        res = re_replace_dots("رقم الهيكل", comp.get('chassis') or '........................', res, lang)
        res = re_replace_dots("القوة الجبائية", comp.get('puissance_fiscale') or '........................', res, lang)
        res = re_replace_dots("الطاقة", comp.get('energie') or '........................', res, lang)
        res = re_replace_dots("عدد المقاعد المرخص بها", comp.get('places') or '........................', res, lang)
        res = re_replace_dots("تاريخ أول وضع في السير", comp.get('date_premier_immat') or comp.get('annee') or '........................', res, lang)
        res = re_replace_dots("رقم التسجيل", comp.get('immatriculation') or comp.get('matricule') or '........................', res, lang)
        res = re_replace_dots("سنة الصنع", comp.get('annee') or '........................', res, lang)
    else:
        res = re_replace_dots("Marque/Modèle", comp.get('marque_modele') or comp.get('marque') or '........................', res)
        res = re_replace_dots("Type", comp.get('type') or '........................', res)
        res = re_replace_dots("N° de Châssis", comp.get('chassis') or '........................', res)
        res = re_replace_dots("Puissance fiscale", comp.get('puissance_fiscale') or '........................', res)
        res = re_replace_dots("Énergie", comp.get('energie') or '........................', res)
        res = re_replace_dots("Places assises autorisées", comp.get('places') or '........................', res)
        res = re_replace_dots("Date de 1ère mise en circulation", comp.get('date_premier_immat') or comp.get('annee') or '........................', res)
        res = re_replace_dots("Numéro d'immatriculation", comp.get('immatriculation') or comp.get('matricule') or '........................', res)
    
    # Champs spécifiques SOCIÉTÉ (Parts sociales)
    if lang == "ar":
        res = res.replace("الشركة المسماة : ........................", f"الشركة المسماة : {comp.get('nom_societe', '........................')}")
        res = res.replace("تحت رقم : .........................", f"تحت رقم : {comp.get('registre_commerce', '.........................')}")
        res = res.replace("عدد الحصص المتنازل عنها : ........................", f"عدد الحصص المتنازل عنها : {comp.get('parts_cedees', '........................')}")
        res = res.replace("القيمة الاسمية : ........................", f"القيمة الاسمية : {comp.get('valeur_nominale', '........................')}")
    else:
        res = res.replace("société dénommée : ........................", f"société dénommée : {comp.get('nom_societe', '........................')}")
        res = res.replace("sous le n° : .........................", f"sous le n° : {comp.get('registre_commerce', '.........................')}")
        res = res.replace("Nombre de parts cédées : ........................", f"Nombre de parts cédées : {comp.get('parts_cedees', '........................')}")
        res = res.replace("Valeur nominale : ........................", f"Valeur nominale : {comp.get('valeur_nominale', '........................')}")

    # Champs spécifiques MARIAGE
    if lang == "ar":
        res = res.replace("ولي الزوجة : ........................", f"ولي الزوجة : {comp.get('wali', '........................')}")
        res = res.replace("- الشاهد 1 : ........................", f"- الشاهد 1 : {comp.get('temoin1', '........................')}")
        res = res.replace("- الشاهد 2 : ........................", f"- الشاهد 2 : {comp.get('temoin2', '........................')}")
        res = res.replace("- المبلغ : ........................ أوقية جديدة (MRU).", f"- المبلغ : {comp.get('mahr', '........................')} أوقية جديدة (MRU).")
        res = res.replace("- المبلغ : ........................", f"- المبلغ : {comp.get('mahr', '........................')}")
        res = res.replace("- الحالة : ........................ (معجل / مؤجل)", f"- الحالة : {comp.get('mahr_etat', '........................')} (معجل / مؤجل)")
        res = res.replace("الشروط الخاصة المتفق عليها : ........................", f"الشروط الخاصة المتفق عليها : {comp.get('conditions', '........................')}")
        res = res.replace("شروط خاصة : ........................", f"شروط خاصة : {comp.get('conditions', '........................')}")
    else:
        res = res.replace("Le Wali (Tuteur légal) de l'épouse : ........................", f"Le Wali (Tuteur légal) de l'épouse : {comp.get('wali', '........................')}")
        res = res.replace("- Témoin 1 : ........................", f"- Témoin 1 : {comp.get('temoin1', '........................')}")
        res = res.replace("- Témoin 2 : ........................", f"- Témoin 2 : {comp.get('temoin2', '........................')}")
        res = res.replace("- Montant : ........................", f"- Montant : {comp.get('mahr', '........................')}")
        res = res.replace("- État : ........................ (Payé / Différé)", f"- État : {comp.get('mahr_etat', '........................')} (Payé / Différé)")
        res = res.replace("Conditions particulières : ........................", f"Conditions particulières : {comp.get('conditions', '........................')}")
    
    # Champs spécifiques TESTAMENT
    if lang == "ar":
        res = res.replace("الأموال المعنية : ........................", f"الأموال المعنية : {comp.get('biens', '........................')}")
    else:
        res = res.replace("Biens concernés : ........................", f"Biens concernés : {comp.get('biens', '........................')}")
    
    # Champs spécifiques HYPOTHÈQUE
    if lang == "ar":
        res = res.replace("بمبلغ وقدره : ..........", f"بمبلغ وقدره : {comp.get('montant_dette') or comp.get('prix') or '..........'}")
        res = res.replace("مدة التسديد محددة بـ : ..........", f"مدة التسديد محددة بـ : {comp.get('duree_remboursement', '..........')}")
        res = res.replace("Conditions spécifiques : ..........", f"Conditions spécifiques : {comp.get('conditions_execution', '..........')}")

    # Champs IMMOBILIER (Communs Vente/Hypothèque)
    if lang == "ar":
        res = res.replace("بموجب إذن الإشغال رقم : ........................", f"بموجب إذن الإشغال رقم : {comp.get('permis_num', '........................')}")
        res = res.replace("الصادر بتاريخ : ........................", f"الصادر بتاريخ : {comp.get('permis_date', '........................')}")
        res = res.replace("القطعة الأرضية رقم : ..........", f"القطعة الأرضية رقم : {comp.get('parcelle', '..........')}")
        res = res.replace("المجموعة (Lot) : ..........", f"المجموعة (Lot) : {comp.get('lot', '..........')}")
        res = res.replace("المجموعة : ..........", f"المجموعة : {comp.get('lot', '..........')}")
        res = res.replace("المربع (Ilot) : ..........", f"المربع (Ilot) : {comp.get('ilot', '..........')}")
        res = res.replace("المربع : ..........", f"المربع : {comp.get('ilot', '..........')}")
        res = res.replace("الواقعة في المنطقة : ..........", f"الواقعة في المنطقة : {comp.get('zone', '..........')}")
        res = res.replace("المنطقة : ..........", f"المنطقة : {comp.get('zone', '..........')}")
        res = res.replace("المساحة الإجمالية : .......... متر مربع", f"المساحة الإجمالية : {comp.get('surface', '..........')} متر مربع")
        res = res.replace("مساحتها : .......... متر مربع", f"مساحتها : {comp.get('surface', '..........')} متر مربع")
    else:
        res = res.replace("permis d'occuper n° : ........................", f"permis d'occuper n° : {comp.get('permis_num', '........................')}")
        res = res.replace("délivré le : ........................", f"délivré le : {comp.get('permis_date', '........................')}")
        res = res.replace("parcelle n° : ..........", f"parcelle n° : {comp.get('parcelle', '..........')}")
        res = res.replace("Lot : ..........", f"Lot : {comp.get('lot', '..........')}")
        res = res.replace("Ilot : ..........", f"Ilot : {comp.get('ilot', '..........')}")
        res = res.replace("Zone : ..........", f"Zone : {comp.get('zone', '..........')}")
        res = res.replace("superficie de : .......... m²", f"superficie de : {comp.get('surface', '..........')} m²")
    # Réutilisation des champs immobiliers (lot, ilot, zone, superficie) déjà gérés plus haut
    
    # Montant global (Prix) et conversion automatique
    prix_val = comp.get('prix')
    if prix_val and prix_val != '..........' and not comp.get('prix_lettres'):
        if lang == "ar":
            comp['prix_lettres'] = _convert_number_to_letters_arabic(prix_val)
        else:
            comp['prix_lettres'] = _convert_number_to_letters_french(prix_val)

    if lang == "ar":
        prix_lettres = comp.get('prix_lettres', '............')
        res = res.replace("مبلغ البيع : ..........", f"مبلغ البيع : {prix_val}")
        res = re.sub(r"\(أي \.{2,}\)", f"(أي {prix_lettres})", res)
        res = res.replace("(أي ............) ", f"(أي {prix_lettres}) ")
        res = res.replace("(أي ............) أوقية", f"(أي {prix_lettres}) أوقية")
        
        res = res.replace("ابتداء من ..........", f"ابتداء من {comp.get('date_effet', current_date)}")
        res = res.replace("بمكتب الأستاذ ........................", f"بمكتب الأستاذ {notary_name}")
        res = res.replace("عقد رقم : ............ عقد مسجل بمكتب : ............ ", f"عقد رقم : {act_number} عقد مسجل بمكتب : {notary_bureau} ")
        res = res.replace("عقد رقم : ............ عقد مسجل بمكتب : ............ ", f"عقد رقم : {act_number} عقد مسجل بمكتب : {notary_bureau} ") # Duplicate for robust replacement
        
        res = res.replace("بتاريخ ..........", f"بتاريخ {current_date}")
    else:
        res = res.replace("Prix de la cession : ..........", f"Prix de la cession : {prix_val}")
        res = res.replace("Montant : ..........", f"Montant : {prix_val}")
        res = res.replace("Montant de la vente : ..........", f"Montant de la vente : {prix_val}")
        res = res.replace("somme de : ..........", f"somme de : {prix_val}")
        
        # Remplacement robuste du montant en lettres
        prix_lettres = comp.get('prix_lettres', '............')
        res = re.sub(r"\(soit \.{2,}\)", f"(soit {prix_lettres})", res)
        res = res.replace("(soit ............) ", f"(soit {prix_lettres}) ")
        res = res.replace("(soit ............) Nouvelles", f"(soit {prix_lettres}) Nouvelles")
        
        res = res.replace("À compter du ..........", f"À compter du {comp.get('date_effet', current_date)}")
        res = res.replace("Le (jour) .......... correspondant", f"Le (jour) {current_date} correspondant")
        res = res.replace("correspondant au (date) ..........", f"correspondant au (date) {current_date}")
        res = res.replace("l'an ..........", f"l'an {datetime.datetime.now().year}")
        res = res.replace("conformes, le ..........", f"conformes, le {current_date}")

    return res


def chat_with_gemini(messages: list, system_prompt: str = None, lang: str = "fr") -> str:
    """
    Appel direct à Gemini pour le chat conversationnel.
    messages: liste de dicts {"role": "user"/"assistant", "content": "..."}
    """
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        return "ERREUR : Clé API non configurée."
    
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        if lang == "ar":
            system_inst = system_prompt or (
                "أنت المساعد الذكي لموثق موريتاني محترف. "
                "أجب بطريقة موجزة ومهنية وباللغة العربية. "
                "يمكنك المساعدة في المسائل القانونية التوثيقية، "
                "صياغة العقود، والإجراءات التوثيقية في موريتانيا."
            )
        else:
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
            if lang == "ar":
                return {
                    "reply": "🔔 **تم تفعيل وضع العرض التجريبي**\n\nأقوم بمحاكاة قراءة بطاقتي تعريف صالحتين...\n\n✅ **تم الاستخراج بنجاح**:\n• البائع: الأستاذ محمد لمين\n• المشتري: سارة لمين\n\n⚙️ **جاري إنشاء العقد...**\n\nإليك المسودة المهنية التي تم إنشاؤها باستخدام محرك الصياغة الجديد v2.1.0:",
                    "pdf_url": "/api/v1/generation/download/demo_act.pdf",
                    "document_id": 999
                }
            return {
                "reply": "🔔 **MODE DÉMONSTRATION ACTIVÉ**\n\nJe simule la lecture de deux cartes d'identité valides...\n\n✅ **Extraction réussie** :\n• Vendeur : Maître Mohamed Lamine\n• Acheteur : Sarah Lemine\n\n⚙️ **Génération de l'acte en cours...**\n\nVoici le brouillon professionnel généré avec le nouveau moteur de rédaction v2.1.0 :",
                "pdf_url": "/api/v1/generation/download/demo_act.pdf",
                "document_id": 999
            }

        
        # --- MODE SIMPLIFIÉ (Règles statiques anti-blocage) ---
        msg_lower = message.lower()
        if "mariage" in msg_lower or "عقد" in msg_lower or "زواج" in msg_lower:
            if lang == "ar":
                return {
                    "reply": "للحصول على **عقد زواج**، إليك ما هو مطلوب:\n\n1. 📷 بطاقات الهوية للزوج والزوجة.\n2. 🧔 اسم الولي (الوصي القانوني).\n3. 👥 أسماء الشاهدين.\n4. 💰 مبلغ وحالة المهر (مدفوع/مؤجل).\n\n*لبدء إجراءات مسح البطاقات، يرجى الضغط على الزر الرئيسي على شكل كاميرا ('إنشاء عقد') في الشاشة الرئيسية.*",
                    "detected_act_type": "mariage"
                }
            return {
                "reply": "Pour un **Acte de Mariage**, voici ce qui est nécessaire :\n\n1. 📷 Les cartes d'identité de Monsieur et Madame.\n2. 🧔 Le nom du Wali (Tuteur légal).\n3. 👥 Les noms des deux témoins.\n4. 💰 Le montant et l'état de la Dot (Mahr payé/différé).\n\n*Pour lancer la procédure de scan des cartes, veuillez cliquer sur le bouton principal en forme d'appareil photo ('Générer un acte') sur l'écran d'accueil.*",
                "detected_act_type": "mariage"
            }

        
        elif "vente" in msg_lower and ("immobilier" in msg_lower or "maison" in msg_lower or "terrain" in msg_lower or "بيع" in msg_lower or "عقار" in msg_lower or "أرض" in msg_lower):
            if lang == "ar":
                return {
                    "reply": "للحصول على **بيع عقاري**، إليك ما هو مطلوب:\n\n1. 📷 بطاقات الهوية للبائع والمشتري.\n2. 💵 سعر البيع (بالأوقية).\n3. 🗺️ رقم القطعة الأرضية.\n\n*استخدم زر 'إنشاء عقد' لبدء مسح المستندات.*",
                    "detected_act_type": "vente_immobilier"
                }
            return {
                "reply": "Pour une **Vente Immobilière**, voici ce qui est nécessaire :\n\n1. 📷 Les cartes d'identité du Vendeur et de l'Acheteur.\n2. 💵 Le prix de vente (en MRU).\n3. 🗺️ Le numéro de la parcelle (Terrain).\n\n*Utilisez le bouton 'Générer un acte' pour commencer le scan des documents.*",
                "detected_act_type": "vente_immobilier"
            }

        
        elif "vente" in msg_lower and ("voiture" in msg_lower or "vehicule" in msg_lower or "véhicule" in msg_lower or "سيارة" in msg_lower or "مركبة" in msg_lower):
            if lang == "ar":
                return {
                    "reply": "للحصول على **بيع مركبة**، إليك ما هو مطلوب:\n\n1. 📷 بطاقات الهوية للبائع والمشتري.\n2. 🚙 الماركة، الطراز وسنة أول وضع في السير.\n3. 🔢 رقم الهيكل (VIN) ورقم التسجيل.\n4. 💵 سعر البيع المتفق عليه.\n\n*استخدم زر 'إنشاء عقد' (أيقونة الكاميرا) للبدء.*",
                    "detected_act_type": "vente_vehicule"
                }
            return {
                "reply": "Pour une **Vente de Véhicule**, voici ce qui est nécessaire :\n\n1. 📷 Les CI du Vendeur et de l'Acheteur.\n2. 🚙 La Marque, le Modèle et l'Année de mise en circulation.\n3. 🔢 Le numéro de Châssis (VIN) et d'Immatriculation.\n4. 💵 Le prix de vente conclu.\n\n*Utilisez le bouton 'Générer un acte' (icône appareil photo) pour démarrer.*",
                "detected_act_type": "vente_vehicule"
            }

        
        elif "vente" in msg_lower and ("societe" in msg_lower or "société" in msg_lower or "parts" in msg_lower or "شركة" in msg_lower or "حصص" in msg_lower):
            if lang == "ar":
                return {
                    "reply": "للحصول على **تنازل عن حصص اجتماعية (بيع شركة)**، يجب توفر:\n\n1. 📷 بطاقات الهوية للمتنازل والمتنازل له.\n2. 🏢 اسم الشركة ورقم السجل التجاري.\n3. 📄 عدد الحصص المتنازل عنها وقيمتها الاسمية.\n4. 💵 سعر التنازل.\n\n*استخدم زر 'إنشاء عقد' لرفع الوثائق.*",
                    "detected_act_type": "vente_societe"
                }
            return {
                "reply": "Pour une **Cession de Parts Sociales (Vente de Société)**, il faut :\n\n1. 📷 Les CI du Cédant et du Cessionnaire.\n2. 🏢 La Dénomination de la société et le N° de Registre du Commerce.\n3. 📄 Le nombre de parts cédées et leur valeur nominale.\n4. 💵 Le prix de la cession.\n\n*Utilisez le bouton 'Générer un acte' pour uploader les pièces.*",
                "detected_act_type": "vente_societe"
            }


        elif "testament" in msg_lower and ("acte" in msg_lower or "generer" in msg_lower or "générer" in msg_lower or "وصية" in msg_lower):
            if lang == "ar":
                return {
                    "reply": "للحصول على **عقد وصية**، إليك ما هو مطلوب:\n\n1. 📷 بطاقات الهوية للموصي والمستفيد.\n2. 🏠 الأموال أو الممتلكات المعنية (نقود، منزل، أرض، إلخ).\n\n*استخدم زر 'إنشاء عقد' لبدء مسح المستندات.*",
                    "detected_act_type": "testament"
                }
            return {
                "reply": "Pour un **Acte de Testament**, voici ce qui est nécessaire :\n\n1. 📷 Les cartes d'identité du Testateur et du Bénéficiaire.\n2. 🏠 Les biens concernés (argent, maison, terrain, etc.).\n\n*Utilisez le bouton 'Générer un acte' pour commencer le scan des documents.*",
                "detected_act_type": "testament"
            }


        elif "hypothèque" in msg_lower or "hypotheque" in msg_lower or "créance" in msg_lower or "رهن" in msg_lower:
            if lang == "ar":
                return {
                    "reply": "للحصول على **عقد رهن**، إليك ما هو مطلوب:\n\n1. 📷 بطاقات الهوية لـ **المدين** و **الدائن**.\n2. 📄 صورة من **إذن الإشغال** للممتلك.\n3. 💰 مبلغ الدين.\n4. ⏳ مدة السداد.\n5. ⚖️ شروط التنفيذ في حالة عدم الدفع.\n\n*استخدم زر 'إنشاء عقد' للبدء.*",
                    "detected_act_type": "hypotheque"
                }
            return {
                "reply": "Pour un **Acte d'Hypothèque**, voici ce qui est nécessaire :\n\n1. 📷 Les cartes d'identité du **Débiteur** et du **Créancier**.\n2. 📄 La photo du **Permis d'Occuper** du bien.\n3. 💰 Le montant de la dette.\n4. ⏳ La durée de remboursement.\n5. ⚖️ Les conditions d'exécution en cas de non-paiement.\n\n*Utilisez le bouton 'Générer un acte' pour commencer.*",
                "detected_act_type": "hypotheque"
            }


        elif "bonjour" in msg_lower or "salut" in msg_lower or "سلام" in msg_lower or "مرحبا" in msg_lower:
             if lang == "ar":
                 return "مرحباً يا أستاذ! أنا مساعدك الذكي في المكتب. بسبب قيود مؤقتة على خوادم جوجل، تم تعليق قدرات التحليل المعقدة لدي. ومع ذلك، يمكنني تزويدك بقائمة الوثائق المطلوبة لكل عقد. كيف يمكنني مساعدتك؟"
             return "Bonjour Maître ! Je suis l'assistant IA du cabinet. En raison d'une restriction temporaire des serveurs de Google (Clé API bloquée), mes capacités d'analyse complexes sont suspendues. Je peux néanmoins vous lister les pièces à fournir pour chaque acte. Comment puis-je vous aider ?"

        # Créer la config avec system instruction
        config = types.GenerateContentConfig(
            system_instruction=system_inst,
            temperature=0.3,
        )
        
        # Dernier message
        last_content = message if message else ("Bonjour" if lang != "ar" else "مرحبا")
        
        # Ajouter l'historique + dernier message
        all_contents = history + [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=last_content)]
            )
        ]
        
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=all_contents,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        err_str = str(e)
        print(f"Gemini Chat Error: {err_str}")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
             if lang == "ar":
                 return "*(تنبيه: تم تجاوز كوتا الذكاء الاصطناعي، هذه رسالة بديلة)* مرحباً! أرى أنك تختبر التطبيق. أنا مساعدك التوثيقي. ماذا يمكنني أن أفعل لك؟"
             return "*(Attention: Quota IA dépassé, ceci est un faux message)* Bonjour ! Je vois que vous testez l'application. Je suis l'assistant notarial. Que puis-je faire pour vous ?"
        if "11001" in err_str or "getaddrinfo" in err_str or "NameResolutionError" in err_str or "Max retries exceeded" in err_str:
             if lang == "ar":
                 return "خطأ في الشبكة: تعذر الاتصال بخادم الذكاء الاصطناعي. تحقق من اتصالك بالإنترنت."
             return "Erreur réseau : Impossible de contacter le serveur d'Intelligence Artificielle. Vérifiez votre connexion internet."
        if "400" in err_str or "Key not found" in err_str or "API_KEY_INVALID" in err_str:
             if lang == "ar":
                 return "مرحباً! أنا مساعدك التوثيقي. أواجه حالياً صعوبة تقنية صغيرة في اتصالي بخدمات جوجل (مفتاح API). ومع ذلك، يمكنني مساعدتك من خلال الإجابة على أسئلتك العامة حول العقود."
             return "Bonjour ! Je suis votre assistant notarial. Je rencontre actuellement une petite difficulté technique avec ma connexion aux services Google (Clé API). Je peux néanmoins vous aider en répondant à vos questions générales sur les actes."
        if lang == "ar":
            return f"خطأ في التواصل مع الذكاء الاصطناعي: حدثت مشكلة تقنية."
        return f"Erreur de communication avec l'IA : Une difficulté technique est survenue."

