from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.audit_service import run_compliance_audit
from app.db.models import Document, ActStatus

router = APIRouter()

@router.post("/{document_id}/audit", response_model=dict)
def audit_act(document_id: int, db: Session = Depends(get_db)):
    """
    Trigger the LangChain compliance audit agent on a specific draft.
    It returns a JSON with conformity status and suggestions.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    if doc.status == ActStatus.VALIDE:
        return {"message": "Document is already validated.", "audit_feedback": doc.audit_feedback}

    # Run the LLM agent audit
    feedback = run_compliance_audit(db, document_id)
    
    if "error" in feedback:
        raise HTTPException(status_code=500, detail=feedback["error"])

    return {
        "document_id": document_id,
        "new_status": doc.status,
        "audit_feedback": feedback
    }
