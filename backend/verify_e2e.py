from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

try:
    print("==> 1. Test du serveur...")
    res_health = client.get("/")
    print("Statut racine :", res_health.json())

    print("\n==> 2. Test de Endpoint de Génération (/api/v1/generation/draft)...")
    payload = {
        "title": "Vente Maison Toulouse",
        "act_type": "vente",
        "parties_info": {"vendeur": "Jean DUPONT", "acheteur": "Marie CURIE"},
        "special_clauses": "Clause de servitude"
    }
    res_gen = client.post("/api/v1/generation/draft", json=payload)
    print(f"Statut HTTP: {res_gen.status_code}")
    doc_data = res_gen.json()
    if res_gen.status_code != 200:
        print(f"ERREUR GÉNÉRATION: {doc_data}")
    else:
        print("Réponse JSON reçue avec succès.")

    print("\n==> 3. Test de Endpoint d'Audit (/api/v1/documents/{id}/audit)...")
    if "document_id" in doc_data:
        doc_id = doc_data["document_id"]
        res_audit = client.post(f"/api/v1/documents/{doc_id}/audit")
        print(f"Statut HTTP: {res_audit.status_code}")
        print("Réponse JSON Audit :", json.dumps(res_audit.json(), indent=2, ensure_ascii=False))
    else:
        print("Erreur: document_id introuvable.")
except Exception as e:
    import traceback
    print(f"\nCRASH DU SCRIPT DE TEST: {e}")
    print(traceback.format_exc())
