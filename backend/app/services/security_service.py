from sqlalchemy.orm import Session
from app.db.models import AuditLog
from typing import Optional, Any

def log_security_event(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
    details: Optional[Any] = None
):
    """
    Enregistre un événement de sécurité dans la table AuditLog.
    """
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            document_id=document_id,
            details=details
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # On ne veut pas bloquer l'application si le log échoue, 
        # mais on devrait au moins l'afficher en console.
        print(f"CRITICAL: Failed to log security event: {e}")
        db.rollback()
