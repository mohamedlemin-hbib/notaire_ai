from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_login_success():
    print("==> Test de connexion réussi...")
    # Use the seeded admin credentials
    login_data = {
        "username": "mohamedleminaidelha@gmail.com",
        "password": "Notaire2024!"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    print(f"Statut HTTP: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("COOOOL! Connexion réussie.")
        print(f"Token: {data['access_token'][:50]}...")
        print(f"User: {data['user']['email']} (Role: {data['user']['role']})")
    else:
        print(f"ERREUR: {response.json()}")

def test_login_failure():
    print("\n==> Test de connexion échoué (mauvais mdp)...")
    login_data = {
        "username": "mohamedleminaidelha@gmail.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    print(f"Statut HTTP: {response.status_code}")
    print(f"Réponse: {response.json()}")

if __name__ == "__main__":
    test_login_success()
    test_login_failure()
