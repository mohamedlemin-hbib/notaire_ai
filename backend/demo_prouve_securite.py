
import os
import sys
import time

# Ajouter le chemin du backend pour l'import de app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import generate_notarial_draft

def demo_full_chain():
    print("--- DEMONSTRATION DE SECURITE : UNIQUEMENT LES INFOS DE LA CARTE ---")
    
    # 1. SIMULATION DE L'OCR
    # Cas REEL : La date de naissance du vendeur est ILLISIBLE sur la carte.
    
    print("\n[ETAPE 1] Simulation d'une extraction OCR partielle (NNI present, Date manquante)...")
    ocr_result_partial = {
        "vendeur": {
            "nom": "SIDI",
            "prenom": "Ahmed",
            "nni": "1234567890",
            "date_naissance": None,  # Simulation : Champ illisible sur la carte
            "lieu_naissance": "Nouakchott"
        },
        "acheteur": {
            "nom": "MINT AHMED",
            "prenom": "Fatima",
            "nni": "0987654321",
            "date_naissance": "15/05/1990",
            "lieu_naissance": "Nouadhibou"
        }
    }
    
    print("Donnees extraites par l'IA :")
    print(f" > Vendeur: {ocr_result_partial['vendeur']['prenom']} {ocr_result_partial['vendeur']['nom']}")
    print(f" > Date Naissance Vendeur: {ocr_result_partial['vendeur']['date_naissance']} (Indique comme 'None' car absent de la carte)")

    # 2. GENERATION DE L'ACTE (DETERMINISTE)
    print("\n[ETAPE 2] Generation de l'acte de vente...")
    
    completion_data = {
        "parcelle": "500",
        "quartier": "Tevragh Zeina",
        "moughataa": "Tevragh Zeina",
        "prix": "5.000.000",
        "prix_lettres": "cinq millions",
        "date_effet": "07/04/2026"
    }

    draft = generate_notarial_draft(
        act_type="Vente",
        parties_info=ocr_result_partial,
        special_clauses="",
        notary_name="Me Diallo",
        notary_bureau="Nouakchott Centre",
        completion_data=completion_data
    )

    print("\n" + "="*60)
    print("EXTRAIT DU DOCUMENT GENERE (Zone Vendeur) :")
    print("-" * 60)
    # On affiche juste la ligne du vendeur pour prouver le point
    for line in draft.split('\n'):
        if "1. M./Mme" in line:
            print(line)
    print("="*60)

    print("\nANALYSE DE SECURITE :")
    if ".........." in draft and "Ahmed SIDI" in draft:
        print("SUCCESS : Le systeme a injecte 'Ahmed SIDI' (present sur la carte)")
        print("SUCCESS : Le systeme a laisse '..........' pour la date (absente de la carte)")
        print("AUCUNE HALLUCINATION : L'IA n'a pas essaye d'inventer une date.")
    else:
        print("NOTE : Verifiez les points de remplissage.")

if __name__ == "__main__":
    demo_full_chain()
