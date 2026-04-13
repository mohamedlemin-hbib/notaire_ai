from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Document
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    docs = db.query(Document).order_by(Document.id.desc()).limit(5).all()
    for doc in docs:
        print(f"ID: {doc.id}, Title: {doc.title}, ActType: {doc.act_type}, MetaRequestedType: {doc.metadata_json.get('requested_type') if doc.metadata_json else 'None'}")
finally:
    db.close()
