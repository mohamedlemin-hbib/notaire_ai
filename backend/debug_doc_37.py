from app.db.session import SessionLocal
from app.db.models import Document, ActType
import json

db = SessionLocal()
doc = db.query(Document).filter(Document.id == 37).first()

if doc:
    print(f"ID: {doc.id}")
    print(f"doc.act_type: {doc.act_type} (type: {type(doc.act_type)})")
    if hasattr(doc.act_type, 'value'):
        print(f"doc.act_type.value: {doc.act_type.value}")
    
    meta = doc.metadata_json or {}
    req_type = meta.get("requested_type")
    print(f"meta['requested_type']: {req_type} (type: {type(req_type)})")
    
    print(f"doc.title: {doc.title}")
else:
    print("Document 37 not found")

db.close()
