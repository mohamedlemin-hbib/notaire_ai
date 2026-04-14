from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.core import security
from app.api.deps import get_current_active_admin

router = APIRouter(dependencies=[Depends(get_current_active_admin)])

@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Affiche la liste des utilisateurs."""
    return db.query(User).all()

@router.post("/users", response_model=UserOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Créer un utilisateur (Action admin)."""
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Cet email est déjà utilisé."
        )
    
    # Combiner first_name et last_name pour full_name si non fourni
    full_name = user_in.full_name
    if not full_name and user_in.first_name and user_in.last_name:
        full_name = f"{user_in.first_name} {user_in.last_name}"

    obj_in_data = user_in.model_dump(exclude={"password", "full_name"})
    new_user = User(
        **obj_in_data,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Désactive un utilisateur."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # On fait une suppression logique pour garder l'intégrité
    user.is_active = 0
    db.commit()
    return {"message": "Utilisateur désactivé avec succès"}

@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un utilisateur."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.hashed_password = security.get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

