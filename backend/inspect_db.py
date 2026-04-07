import sys
import os

# Add backend dir to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from app.db.session import SessionLocal
from app.db.models import Document

def main():
    db = SessionLocal()
    last_doc = db.query(Document).order_by(Document.id.desc()).first()
    if last_doc:
        print(f"Document ID: {last_doc.id}")
        print(f"Title: {last_doc.title}")
        print(f"Metadata: {last_doc.metadata_json}")
        print(f"Content:\n{last_doc.content}")
    else:
        print("No documents found.")
    db.close()

if __name__ == "__main__":
    main()
