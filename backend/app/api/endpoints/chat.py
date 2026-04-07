from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models import ChatSession, ChatMessage, User
from app.api.deps import get_current_user
from app.services.rag_service import chat_with_gemini
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class MessageSchema(BaseModel):
    role: str
    content: str
    message_type: str = "text"
    created_at: datetime

class SessionSchema(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/sessions", response_model=List[SessionSchema])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

@router.get("/sessions/{session_id}/messages", response_model=List[MessageSchema])
def get_session_messages(
    session_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, 
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    return session.messages

@router.post("/sessions", response_model=SessionSchema)
def create_session(
    title: str = "Nouvelle discussion", 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    new_session = ChatSession(title=title, user_id=current_user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

class AddMessageRequest(BaseModel):
    session_id: int
    role: str
    content: str
    message_type: str = "text"

@router.post("/messages")
def add_message(
    request: AddMessageRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == request.session_id, 
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")
    
    new_msg = ChatMessage(
        session_id=request.session_id,
        role=request.role,
        content=request.content,
        message_type=request.message_type
    )
    db.add(new_msg)
    
    # Update session title from first user message
    if session.title == "Nouvelle discussion" and request.role == "user":
        session.title = request.content[:50] + ("..." if len(request.content) > 50 else "")
        
    db.commit()
    return {"status": "ok"}


class AiChatRequest(BaseModel):
    session_id: int
    message: str

@router.post("/ai-reply")
def ai_reply(
    request: AiChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Envoie un message utilisateur à Gemini et retourne la réponse IA.
    Sauvegarde les deux messages (user + assistant) en base.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == request.session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    # Sauvegarder le message utilisateur
    user_msg = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message,
        message_type="text"
    )
    db.add(user_msg)

    # Mettre à jour le titre de session
    if session.title == "Nouvelle discussion":
        session.title = request.message[:50] + ("..." if len(request.message) > 50 else "")

    db.commit()

    # Récupérer l'historique complet pour le contexte
    history = db.query(ChatMessage).filter(
        ChatMessage.session_id == request.session_id
    ).order_by(ChatMessage.created_at.asc()).all()

    messages = [{"role": m.role, "content": m.content} for m in history]

    # Appel Gemini avec le contexte du notaire
    system_prompt = (
        f"Vous êtes l'assistant IA personnel de Maître {current_user.full_name or 'le Notaire'}, "
        f"notaire à {current_user.bureau or 'Nouakchott'}, Mauritanie. "
        "Vous êtes expert en droit notarial mauritanien. "
        "Répondez de façon professionnelle, concise et en français. "
        "Pour les actes de vente, aidez à compléter les informations manquantes : "
        "prix, quartier, moughataa, numéro de parcelle, surface."
    )

    ai_text = chat_with_gemini(messages, system_prompt)

    # Sauvegarder la réponse IA
    ai_msg = ChatMessage(
        session_id=request.session_id,
        role="assistant",
        content=ai_text,
        message_type="text"
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return {
        "reply": ai_text,
        "created_at": ai_msg.created_at
    }
