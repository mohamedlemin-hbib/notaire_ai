from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

class ActType(str, enum.Enum):
    VENTE = "vente" # Legacy/Generic
    VENTE_IMMOBILIER = "vente_immobilier"
    VENTE_VEHICULE = "vente_vehicule"
    VENTE_SOCIETE = "vente_societe"
    MARIAGE = "mariage"
    TESTAMENT = "testament"
    PROCURATION = "procuration"
    AUTRE = "autre"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    NOTAIRE = "notaire"
    CLERC = "clerc"

class ActStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    AUDIT_EN_COURS = "audit_en_cours"
    NON_CONFORME = "non_conforme"
    VALIDE = "valide"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    birth_date = Column(String, nullable=True) # ISO format or string
    bureau = Column(String, nullable=True)
    nni = Column(String, unique=True, index=True, nullable=True) # Numéro National d'Identité
    role = Column(Enum(UserRole), default=UserRole.CLERC)
    is_active = Column(Integer, default=1) # 1 for True, 0 for False (using Integer for compatibility)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    documents = relationship("Document", back_populates="owner")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    act_type = Column(Enum(ActType), nullable=False)
    status = Column(Enum(ActStatus), default=ActStatus.BROUILLON)
    
    # Generated content by the LLM
    content = Column(Text, nullable=True)
    
    # Metadata extracted from the prompt (parties involved, specific clauses requested)
    metadata_json = Column(JSON, nullable=True) 
    
    # Audit feedback from the agent
    audit_feedback = Column(JSON, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="documents")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, default="Nouvelle discussion")
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String, nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text") # 'text', 'image', 'audio', 'pdf'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
