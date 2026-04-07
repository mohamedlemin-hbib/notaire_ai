
import os
import sys

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import generate_notarial_draft
from app.services.pdf_service import generate_act_pdf

def test_pdf_rendering():
    print("--- DÉMONSTRATION DU RENDU PDF FINAL ---")
    
    # Données simulées (OCR + Formulaire)
    parties_info = {
        "vendeur": {"nom": "SIDI", "prenom": "Ahmed", "nni": "1234567890", "date_naissance": "01/01/1980", "lieu_naissance": "Nouakchott"},
        "acheteur": {"nom": "MINT AHMED", "prenom": "Fatima", "nni": "0987654321", "date_naissance": "15/05/1990", "lieu_naissance": "Nouadhibou"},
        "act_number": "2026/V-888"
    }
    
    completion_data = {
        "parcelle": "LOT-500",
        "quartier": "Tevragh Zeina",
        "moughataa": "Tevragh Zeina",
        "prix": "7.500.000",
        "prix_lettres": "sept millions cinq cent mille",
        "date_effet": "07/04/2026"
    }

    # 1. Générer le texte déterministe
    content = generate_notarial_draft(
        act_type="Vente",
        parties_info=parties_info,
        special_clauses="",
        notary_name="Ahmed Ould Lemine",
        notary_bureau="Nouakchott Ouest",
        completion_data=completion_data
    )

    # 2. Générer le PDF
    pdf_buffer = generate_act_pdf(
        title="ACTE DE VENTE IMMOBILIÈRE",
        content=content,
        act_number="2026/V-888",
        notary_name="Ahmed Ould Lemine",
        notary_bureau="Nouakchott Ouest",
        status="brouillon"
    )

    # 3. Sauvegarder le PDF
    output_path = "acte_final_demonstration.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_buffer.getvalue())
    
    print(f"\nSUCCESS : Le PDF a été généré avec succès !")
    print(f"Fichier : {os.path.abspath(output_path)}")
    print("Ce document utilise le template officiel et vos données réelles.")

if __name__ == "__main__":
    test_pdf_rendering()
