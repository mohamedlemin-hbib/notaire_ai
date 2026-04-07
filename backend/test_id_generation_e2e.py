import requests
import json
import os

from PIL import Image

def test_id_flow():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Login
    print("Connexion...")
    login_data = {"username": "mohamedleminaidelha@gmail.com", "password": "Notaire2024!"}
    res_login = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
    
    if res_login.status_code != 200:
        print(f"Erreur Login: {res_login.text}")
        return

    data = res_login.json()
    token = data["access_token"]
    
    # 2. Preparation des fichiers "images" (on crée des petites images réelles)
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save("vendeur.jpg")
    img.save("acheteur.jpg")

    # 3. Appel de l'ID Generation
    print("Envoi des cartes d'identité...")
    headers = {"Authorization": f"Bearer {token}"}
    
    with open('vendeur.jpg', 'rb') as f1:
        with open('acheteur.jpg', 'rb') as f2:
            files = {
                'vendeur_id': ('vendeur.jpg', f1, 'image/jpeg'),
                'acheteur_id': ('acheteur.jpg', f2, 'image/jpeg')
            }
            
            res_gen = requests.post(
                f"{base_url}/api/v1/id-processing/from-id-cards",
                headers=headers,
                files=files
            )
    
    print(f"Statut Génération: {res_gen.status_code}")
    gen_data = res_gen.json()
    print(f"Réponse: {json.dumps(gen_data, indent=2)}")

    if res_gen.status_code == 200:
        doc_id = gen_data["document_id"]
        pdf_url = gen_data["pdf_url"]
        
        # 4. Test du téléchargement PDF
        print(f"Téléchargement du PDF via {pdf_url}...")
        res_pdf = requests.get(f"{base_url}{pdf_url}")
        print(f"Statut PDF: {res_pdf.status_code}")
        
        if res_pdf.status_code == 200:
            with open(f"acte_{doc_id}.pdf", "wb") as f:
                f.write(res_pdf.content)
            print(f"PDF sauvegardé : acte_{doc_id}.pdf")

    # Cleanup
    os.unlink("vendeur.jpg")
    os.unlink("acheteur.jpg")

if __name__ == "__main__":
    # Ensure server is running on 8002
    try:
        test_id_flow()
    except Exception as e:
        print(f"Erreur test: {e}")
        # Make sure to close files and clean up if error
        if os.path.exists("vendeur.jpg"): os.unlink("vendeur.jpg")
        if os.path.exists("acheteur.jpg"): os.unlink("acheteur.jpg")
