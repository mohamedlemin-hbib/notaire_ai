# Comment Lancer l'Application Notaire IA

## 1. Backend (FastAPI)
Ouvrez un terminal dans le dossier `backend` :
```powershell
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python -m uvicorn app.main:app --reload
```
Le serveur sera disponible sur `http://localhost:8000`.

## 2. Mobile (Flutter)
Ouvrez un terminal dans le dossier `mobile_app` :
```powershell
# Récupérer les packages
flutter pub get

# Lancer sur un émulateur ou un appareil réel
flutter run
```

## 3. Identifiants de Test
Utilisez les identifiants suivants pour vous connecter (créés via le script de seeding) :
- **Email** : admin@notaire-ia.com
- **Mot de passe** : admin123 (ou celui configuré dans seed_admin.py)

## 4. Fonctionnalités à tester
- **Chat Vocal** : Restez appuyé sur le micro dans le chat.
- **Photos** : Utilisez l'icône appareil photo pour scanner une carte d'identité.
- **Documents** : Cliquez sur l'icône dossier en haut à droite pour voir vos actes générés.
