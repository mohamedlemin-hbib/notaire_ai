import sys
import os
from sqlalchemy import create_engine, text

# Ajouter le chemin du backend pour importer les settings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings

def fix_enum():
    engine = create_engine(settings.DATABASE_URL)
    
    # Liste des nouveaux types d'actes à ajouter
    new_types = ["hypotheque", "HYPOTHEQUE", "testament", "TESTAMENT", "mariage", "MARIAGE", "procuration", "PROCURATION", "vente_vehicule", "vente_societe", "vente_immobilier"]
    
    # On utilise AUTOCOMMIT car ALTER TYPE ADD VALUE ne peut pas être dans une transaction
    with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        print("Vérification des types existants dans l'énumération 'acttype'...")
        try:
            # Récupérer les valeurs actuelles de l'énumération
            result = conn.execute(text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'acttype'"))
            existing_types = [row[0] for row in result]
            print(f"Types actuels : {existing_types}")
            
            # Ajouter les types manquants
            for t in new_types:
                if t not in existing_types:
                    print(f"Ajout du type : {t}")
                    try:
                        conn.execute(text(f"ALTER TYPE acttype ADD VALUE '{t}'"))
                        print(f"Succès : {t} ajouté.")
                    except Exception as e:
                        print(f"Erreur lors de l'ajout de {t} : {e}")
                else:
                    print(f"Le type {t} existe déjà.")
                    
        except Exception as e:
            print(f"Erreur lors de la lecture des types : {e}")
            print("Tentative de création de l'énumération si elle n'existe pas (attention, ceci est risqué si elle existe déjà)...")

if __name__ == "__main__":
    fix_enum()
