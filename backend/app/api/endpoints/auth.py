from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.db.models import User
from app.core import security
from app.core.config import settings
from app.schemas.user import UserCreate, UserOut
from app.api.deps import get_current_user
from app.services import otp_service

router = APIRouter()

@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de connexion : vérifie les identifiants et déclenche l'envoi d'un OTP.
    """
    # Recherche par email, nom complet, numéro de téléphone ou NNI
    from sqlalchemy import or_
    user = db.query(User).filter(
        or_(
            User.email == form_data.username,
            User.full_name == form_data.username,
            User.phone_number == form_data.username,
            User.nni == form_data.username
        )
    ).first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte désactivé"
        )

    # Génération et envoi de l'OTP
    code = otp_service.generate_otp_code()
    user.otp_code = code
    # Expiration après 2 minutes
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)
    db.commit()
    
    otp_service.send_otp_simulated(user.phone_number or "NUMERO_INCONNU", code)
    
    return {
        "requires_otp": True,
        "email": user.email,
        "phone_number": user.phone_number,
        "message": "Un code de vérification a été envoyé."
    }

@router.post("/verify-otp")
def verify_otp(
    db: Session = Depends(get_db),
    email: str = Body(..., embed=True),
    code: str = Body(..., embed=True)
):
    """
    Vérifie le code OTP et renvoie le token JWT final.
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
    if not user.otp_code or user.otp_code != code:
        raise HTTPException(status_code=400, detail="Code OTP invalide")
        
    # Vérification de l'expiration
    if user.otp_expires_at and datetime.now(timezone.utc) > user.otp_expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Le code OTP a expiré (limite de 2 minutes)")
        
    # Code valide -> On génère le token
    user.otp_code = None # On invalide le code après usage
    user.otp_expires_at = None
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "role": user.role.value}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.post("/resend-otp")
def resend_otp(db: Session = Depends(get_db), email: str = Body(..., embed=True)):
    """
    Renvoie un nouveau code OTP.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
    code = otp_service.generate_otp_code()
    user.otp_code = code
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=2)
    db.commit()
    
    otp_service.send_otp_simulated(user.phone_number or "NUMERO_INCONNU", code)
    return {"message": "Nouveau code envoyé."}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Récupère les informations de l'utilisateur connecté.
    """
    return current_user
