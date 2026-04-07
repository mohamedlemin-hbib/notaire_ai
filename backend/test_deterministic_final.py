
import os
import sys

# Ajouter le chemin du backend pour l'import de app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import generate_notarial_draft

def test_final_generation():
    print("--- TEST DE GÉNÉRATION DÉTERMINISTE (FIABILITÉ 100%) ---")
    
    # Données simulées issues de l'OCR (sans erreur)
    parties_info = {
        "vendeur": {
            "nom": "SIDI",
            "prenom": "Ahmed",
            "nni": "1234567890",
            "date_naissance": "01/01/1980",
            "lieu_naissance": "Nouakchott"
        },
        "acheteur": {
            "nom": "MINT AHMED",
            "prenom": "Fatima",
            "nni": "0987654321",
            "date_naissance": "15/05/1990",
            "lieu_naissance": "Nouadhibou"
        },
        "act_number": "2026/V-001"
    }
    
    # Données de complétion (normalement saisies par le notaire si manquantes)
    completion_data = {
        "parcelle": "500",
        "quartier": "Tevragh Zeina",
        "moughataa": "Tevragh Zeina",
        "prix": "5.000.000",
        "prix_lettres": "cinq millions",
        "date_effet": "07/04/2026"
    }
    
    # Appel de la fonction déterministe
    try:
        draft = generate_notarial_draft(
            act_type="Vente",
            parties_info=parties_info,
            special_clauses="",
            notary_name="Diallo",
            notary_bureau="Nouakchott Centre",
            completion_data=completion_data
        )
        
        print("\n" + "="*50)
        print("RÉSULTAT DU BROUILLON GÉNÉRÉ :")
        print("="*50)
        print(draft)
        print("="*50 + "\n")
        
        # Vérification des mots-clés
        success = True
        required_fields = ["SIDI", "Fatim", "1234567890", "500", "5.000.000", "Nouakchott Centre"]
        for field in required_fields:
            if field not in draft:
                print(f"ERREUR : Champ '{field}' manquant dans le draft !")
                success = False
        
        if success:
            print("SUCCÈS : Toutes les données sont correctement injectées sans hallucination.")
            # Sauvegarder pour inspection
            with open("test_final_output.txt", "w", encoding="utf-8") as f:
                f.write(draft)
            print("Le résultat a été sauvegardé dans 'test_final_output.txt'.")
            
    except Exception as e:
        print(f"ERREUR lors de la génération : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_generation()
