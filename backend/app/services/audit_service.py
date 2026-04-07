from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings
from app.db.models import Document, ActStatus
from sqlalchemy.orm import Session
import json

def get_audit_llm():
    """Initialise le LLM d'audit de manière paresseuse."""
    return ChatGoogleGenerativeAI(
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
        model="gemini-flash-latest" # unified with Gemini 3 Flash
    )

def run_compliance_audit(db: Session, document_id: int):
    """Run an LLM-based compliance audit on a generated draft."""
    if settings.GOOGLE_API_KEY == "your_google_api_key_here":
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc.audit_feedback = {"conforme": False, "risques_juridiques": ["Ceci est un test"], "mentions_manquantes": [], "corrections_suggerees": ["Veuillez renseigner votre clé Gemini GOOGLE_API_KEY"]}
        doc.status = ActStatus.NON_CONFORME
        db.commit()
        return doc.audit_feedback

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return {"error": "Document Not Found"}

    prompt = PromptTemplate.from_template(
        "Vous êtes un inspecteur de conformité de la Chambre des Notaires. Vous êtes très strict.\n"
        "Analysez l'acte suivant ({act_type}) pour vérifier sa stricte conformité au droit français et aux instructions.\n\n"
        "ACTE À VÉRIFIER :\n{content}\n\n"
        "INSTRUCTIONS DE DÉPART (pour référence) :\n{metadata}\n\n"
        "Vérifiez absolument :\n"
        "1. La présence exacte des mentions obligatoires selon le type d'acte.\n"
        "2. Les clauses abusives, contradictions ou incohérences.\n"
        "3. La rigueur de la formulation juridique.\n\n"
        "RÉPONDEZ UNIQUEMENT AU FORMAT JSON VALIDE. Utilisez les clés suivantes :\n"
        "{{\n"
        "  \"conforme\": true ou false,\n"
        "  \"risques_juridiques\": [\"liste\"],\n"
        "  \"mentions_manquantes\": [\"liste\"],\n"
        "  \"corrections_suggerees\": [\"liste\"]\n"
        "}}"
    )

    audit_llm = get_audit_llm()
    chain = prompt | audit_llm
    
    response = chain.invoke({
        "act_type": doc.act_type.value,
        "content": doc.content,
        "metadata": str(doc.metadata_json)
    })

    try:
        content = response.content
        # Handle multi-part content if it's a list (common in newer Gemini/LangChain integrations)
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
                else:
                    text_parts.append(getattr(part, "text", str(part)))
            content = "".join(text_parts)

        # Strip potential markdown formatting from the response
        clean_json = content.replace("```json", "").replace("```", "").strip()
        feedback = json.loads(clean_json)
        
        doc.audit_feedback = feedback
        doc.status = ActStatus.VALIDE if feedback.get("conforme") else ActStatus.NON_CONFORME
        db.commit()
    except Exception as e:
        doc.audit_feedback = {"error": f"JSON Parsing failed: {str(e)}", "raw_response": response.content}
        doc.status = ActStatus.NON_CONFORME
        db.commit()

    return doc.audit_feedback
