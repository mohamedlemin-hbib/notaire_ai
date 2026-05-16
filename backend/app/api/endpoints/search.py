from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, String, desc
from typing import List, Optional
from app.db.session import get_db
from app.db.models import Document, User
from app.api.deps import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class DocumentSearchResponse(BaseModel):
    id: int
    title: str
    act_type: str
    created_at: datetime
    pdf_url: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.get("/documents", response_model=List[DocumentSearchResponse])
def search_documents(
    q: Optional[str] = Query(None, description="Recherche par NNI, nom ou contenu"),
    act_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recherche des documents par NNI ou autres critères dans metadata_json.
    """
    query = db.query(Document).filter(Document.owner_id == current_user.id)
    
    if q:
        # Recherche simple dans le JSON converti en texte
        # Note: Pour une recherche plus précise sur le NNI spécifiquement, 
        # on pourrait cibler metadata_json['parties_info']
        search_filter = cast(Document.metadata_json, String).ilike(f"%{q}%")
        query = query.filter(search_filter)
        
    if act_type:
        query = query.filter(Document.act_type == act_type)
        
    documents = query.order_by(desc(Document.created_at)).limit(20).all()
    
    # On ajoute l'URL du PDF pour chaque document si elle existe
    # Note: Dans le modèle actuel, le PDF est généré et stocké. 
    # Supposons qu'on a une convention d'URL ou qu'elle est dans metadata.
    results = []
    for doc in documents:
        # On utilise le point de terminaison de téléchargement PDF réel
        pdf_url = f"/api/v1/id-processing/download-pdf/{doc.id}"
        
        results.append(DocumentSearchResponse(
            id=doc.id,
            title=doc.title,
            act_type=doc.act_type,
            created_at=doc.created_at,
            pdf_url=pdf_url
        ))
        
    return results
