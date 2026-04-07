from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
import os

def test_prompt_only():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "standard_template.txt")
        with open(template_path, "r", encoding="utf-8") as f:
            custom_template = f.read()
    except Exception as e:
        print("Erreur de lecture du template: ", e)
        return

    prompt = PromptTemplate.from_template(
        "Vous êtes un système automatisé de rédaction d'actes notariés. Vous rédigez un acte de type : {act_type}.\n\n"
        "STRUCTURE OBLIGATOIRE À REPRODUIRE (MODÈLE D'ACTE) :\n"
        "```\n"
        "{custom_template}\n"
        "```\n\n"
        "INFORMATIONS À INSÉRER :\n"
        "- Numéro d'acte généré : {act_number} (Remplacez 'Acte N° : ............' par 'Acte N° : {act_number}')\n"
        "- Bureau d'enregistrement et Nom du Notaire : Remplacez les pointillés du bureau et de 'Maître' par le nom du notaire connecté.\n"
        "- Parties : {parties_info}\n"
        "- Clauses spécifiques / compléments : {special_clauses}\n"
        "- Contexte (RAG) : {rag_context}\n\n"
        "CONSIGNES TRÈS STRICTES :\n"
        "1. Votre réponse finale doit être UNIQUEMENT le texte complet du modèle d'acte, sans aucun titre (ex: pas de 'Acte de vente' au-dessus de 'Acte N°...'), aucune introduction, et aucune phrase de conclusion.\n"
        "2. N'inventez AUCUNE information. Utilisez UNIQUEMENT les informations issues de la reconnaissance des cartes d'identité (fournies dans 'Parties') pour remplir les pointillés.\n"
        "3. Laissez les pointillés vides s'ils correspondent à une information non fournie.\n"
        "4. NE rajoutez AUCUNE zone de signature à la fin du document. Le document doit se terminer par 'Fait en notre bureau...' et laisser exclusivement la place prévue par le modèle."
    )
    
    llm = ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
        model="gemini-2.0-flash"
    )
    chain = prompt | llm
    
    parties_info = {
        "notaire": {"nom": "Me. Diallo", "bureau": "Nouakchott Centre"},
        "vendeur": {"nom": "Ahmed", "prenom": "Ould Sidi", "date_naissance": "01/01/1980", "lieu_naissance": "Nouakchott", "nni": "1234567890"},
        "acheteur": {"nom": "Fatima", "prenom": "Mint Ahmed", "date_naissance": "15/05/1990", "lieu_naissance": "Nouadhibou", "nni": "0987654321"}
    }
    special_clauses = "La construction édifiée sur la parcelle de terrain n° : 500, située dans le quartier : Tevragh Zeina, Moughataa de : Tevragh Zeina. Montant : 5000 (soit cinq mille) Nouvelles Ouguiyas (MRU). Durée / Date d'effet : À compter du 02 Avril 2026."

    res = chain.invoke({
        "act_type": "Vente",
        "custom_template": custom_template,
        "parties_info": str(parties_info),
        "special_clauses": special_clauses,
        "rag_context": "Veuillez insérer 'vendu' dans les crochets [vendu/loué/cédé].",
        "act_number": "0001"
    })
    
    with open("resultat_generation.txt", "w", encoding="utf-8") as f:
        f.write(res.content)
    
    print("\n" + "="*50)
    print("RÉSULTAT GÉNÉRÉ PAR GEMINI :")
    print("="*50)
    print(res.content)
    print("="*50 + "\n")

if __name__ == "__main__":
    test_prompt_only()
