from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import User
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_admin():
    db = SessionLocal()
    try:
        # Check if already exists
        user = db.query(User).filter(User.email == "admin@notaire-ia.com").first()
        if user:
            print("User already exists, updating password.")
            user.hashed_password = pwd_context.hash("admin123")
        else:
            print("Creating new admin user.")
            user = User(
                email="admin@notaire-ia.com",
                full_name="Administrateur",
                hashed_password=pwd_context.hash("admin123"),
                role="ADMIN",
                is_active=1
            )
            db.add(user)
        db.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
