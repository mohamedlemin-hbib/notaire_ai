from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash
import sys

def reset_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Utilisateur {email} non trouvé.")
            return
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"Succès : Mot de passe réinitialisé pour {email}")
        print(f"Nouveau mot de passe : {new_password}")
    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    email = "sidimohamedkh087@gmail.com"
    reset_password(email, "Notaire2024!")
