from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, UserRole
from app.core.security import get_password_hash
import sys

def seed_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin_email = "mohamedleminaidelha@gmail.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        if admin_user:
            print(f"L'administrateur {admin_email} existe déjà.")
            return

        new_admin = User(
            email=admin_email,
            hashed_password=get_password_hash("Notaire2024!"),
            full_name="Maître Mohamed Elamine",
            bureau="Bureau central de Nouakchott",
            role=UserRole.ADMIN,
            is_active=1
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"Succès : Notaire Responsable créé avec l'email {admin_email}")
        print("Mot de passe par défaut : Notaire2024!")
        
    except Exception as e:
        print(f"Erreur lors de la création de l'admin : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
