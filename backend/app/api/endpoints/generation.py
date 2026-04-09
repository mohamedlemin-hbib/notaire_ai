from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.models import Document, ActType, ActStatus, User
from app.services.rag_service import generate_notarial_draft
from app.api.deps import get_current_user

router = APIRouter()

class DraftRequest(BaseModel):
    title: str
    act_type: ActType
    parties_info: Dict[str, Any]
    special_clauses: str

@router.post("/draft", response_model=dict)
def create_act_draft(
    request: DraftRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a notarial act draft using LangChain RAG.
    It retrieves similar templates from ChromaDB and passes them to GPT-4.
    """
    try:
        draft_content = generate_notarial_draft(
            act_type=request.act_type.value,
            parties_info=request.parties_info,
            special_clauses=request.special_clauses,
            notary_name=current_user.full_name,
            notary_bureau=current_user.bureau or "............"
        )

        new_doc = Document(
            title=request.title,
            act_type=request.act_type,
            status=ActStatus.BROUILLON,
            content=draft_content,
            metadata_json={
                "parties_info": request.parties_info,
                "special_clauses": request.special_clauses
            },
            owner_id=current_user.id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return {
            "document_id": new_doc.id,
            "status": new_doc.status,
            "content": new_doc.content
        }

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)} | Traceback: {trace}")
@router.get("/download/demo_act.pdf")
def download_demo_act():
    from fastapi.responses import FileResponse
    import os
    # On renvoie l'acte de démonstration que je viens de générer
    demo_path = "acte_final_demonstration.pdf"
    if os.path.exists(demo_path):
        return FileResponse(demo_path, media_type="application/pdf", filename="acte_de_vente_demo.pdf")
    raise HTTPException(status_code=404, detail="Fichier de démonstration non trouvé")
