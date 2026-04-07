import os
from pypdf import PdfReader
from docx import Document
from app.services.vector_store import get_template_collection

def extract_text_from_pdf(file_path: str) -> str:
    """Extraire le texte d'un fichier PDF."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extraire le texte d'un fichier DOCX."""
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def process_and_index_document(file_path: str, act_type: str):
    """Extrait le texte et l'indexe dans ChromaDB."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        content = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        content = extract_text_from_docx(file_path)
    else:
        raise ValueError("Format de fichier non supporté. Utilisez PDF ou DOCX.")

    if not content.strip():
        raise ValueError("Le document est vide.")

    # Chunking simple (par paragraphes ou taille fixe)
    # Pour l'instant, on indexe le document entier comme un seul bloc s'il n'est pas trop grand
    # Ou on le coupe en morceaux de 2000 caractères
    chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
    
    collection = get_template_collection()
    
    ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
    metadatas = [{"act_type": act_type, "source": os.path.basename(file_path)} for _ in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    
    return len(chunks)
