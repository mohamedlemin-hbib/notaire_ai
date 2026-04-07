from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User

router = APIRouter()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Affiche la liste des utilisateurs pour vérification."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "full_name": u.full_name,
            "is_active": u.is_active
        } for u in users
    ]
