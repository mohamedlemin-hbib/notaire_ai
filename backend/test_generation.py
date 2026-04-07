from app.services.rag_service import generate_notarial_draft

def run_test():
    act_type = "Vente"
    parties_info = {
        "vendeur": {"nom": "Ahmed", "prenom": "Ould Sidi", "date_naissance": "01/01/1980", "lieu_naissance": "Nouakchott", "nni": "1234567890"},
        "acheteur": {"nom": "Fatima", "prenom": "Mint Ahmed", "date_naissance": "15/05/1990", "lieu_naissance": "Nouadhibou", "nni": "0987654321"}
    }
    special_clauses = "La construction édifiée sur la parcelle de terrain n° : 500, située dans le quartier : Tevragh Zeina, Moughataa de : Tevragh Zeina. Montant : 5000 (soit cinq mille) Nouvelles Ouguiyas (MRU). Durée / Date d'effet : À compter du 02 Avril 2026."

    print("--- LLM: Appel à Gemini avec personnalisation...")
    result = generate_notarial_draft(
        act_type=act_type,
        parties_info=parties_info,
        special_clauses=special_clauses,
        notary_name="Mohamed Lemine",
        notary_bureau="Bureau de Tevragh Zeina"
    )
    
    print("\n" + "="*50)
    print("RESULTAT GENERE PAR GEMINI :")
    print("="*50)
    print(result or "AUCUN RÉSULTAT (VIDE)")
    print("="*50 + "\n")
    
    with open("last_draft.txt", "w", encoding="utf-8") as f:
        f.write(result if result else "EMPTY")
    print(f"Draft saved to last_draft.txt (length: {len(result) if result else 0})")

if __name__ == "__main__":
    run_test()
