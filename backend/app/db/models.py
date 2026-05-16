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
    HYPOTHEQUE = "hypotheque"
    AUTRE = "autre"

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    NOTAIRE = "NOTAIRE"
    CLERC = "CLERC"

class ActStatus(str, enum.Enum):
    BROUILLON = "brouillon"
    AUDIT_EN_COURS = "audit_en_cours"
    NON_CONFORME = "non_conforme"
    VALIDE = "valide"
    SCELLE = "scelle"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    birth_date = Column(String, nullable=True) # ISO format or string
    bureau = Column(String, nullable=True)
    nni = Column(String, unique=True, index=True, nullable=True) # Numéro National d'Identité
    phone_number = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CLERC)

    is_active = Column(Integer, default=1) # 1 for True, 0 for False (using Integer for compatibility)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
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

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False) # e.g., "DOWNLOAD_PDF", "GENERATE_ACT", "SEAL_ACT"
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    details = Column(JSON, nullable=True) # Browser, IP, or specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    document = relationship("Document")
