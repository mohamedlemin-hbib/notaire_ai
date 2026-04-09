from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        email: str = payload.get("sub")
        if email is None:
            print(f"DEBUG AUTH: No 'sub' in payload: {payload}")
            raise credential_exception
    except jwt.PyJWTError as e:
        print(f"DEBUG AUTH: JWT Decode Error: {str(e)} - Token: {token[:10]}...")
        raise credential_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        print(f"DEBUG AUTH: User not found for email: {email}")
        raise credential_exception
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs sont autorisés à effectuer cette action."
        )
    return current_user
