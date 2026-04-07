from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from tempfile import NamedTemporaryFile

from app.db.session import get_db
from app.api.endpoints.auth import User
from app.services.ingestion_service import process_and_index_document
from app.core import security
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_admin(token: str = Depends(oauth2_scheme)):
    """Vérifie si l'utilisateur est admin via le token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        role = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.post("/upload-template")
async def upload_template(
    act_type: str,
    file: UploadFile = File(...),
    admin=Depends(get_current_admin)
):
    """Permet aux admins d'uploader un acte type pour le RAG."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Seuls PDF et DOCX sont acceptés.")

    try:
        # Save temporary file
        with NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Process and index
        chunks_count = process_and_index_document(tmp_path, act_type)
        
        # Cleanup
        os.unlink(tmp_path)
        
        return {
            "message": f"Document '{file.filename}' indexé avec succès.",
            "chunks": chunks_count,
            "act_type": act_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()
