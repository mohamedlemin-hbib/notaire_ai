import chromadb
from app.core.config import settings
import os

# Ensure the directory exists
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_data")
os.makedirs(DB_PATH, exist_ok=True)

# Initialize Chroma Persistent Client
chroma_client = chromadb.PersistentClient(path=DB_PATH)

# Create or get the collection for legal templates
template_collection = chroma_client.get_or_create_collection(
    name="legal_templates",
    metadata={"description": "Vector store for notarial act templates and legal clauses"}
)

def get_template_collection():
    """Dependency to inject the ChromaDB collection."""
    return template_collection
