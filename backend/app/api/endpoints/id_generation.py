from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import io

from app.db.session import get_db
from app.db.models import Document, ActType, ActStatus, User
from app.services.ocr_service import extract_info_from_id, extract_info_from_ids_batch
from app.services.rag_service import generate_notarial_draft, identify_missing_fields
from app.services.pdf_service import generate_act_pdf
from app.api.deps import get_current_user

router = APIRouter()

class CompletionData(BaseModel):
    prix: Optional[str] = None
    quartier: Optional[str] = None
    moughataa: Optional[str] = None
    parcelle: Optional[str] = None
    surface: Optional[str] = None
    date_effet: Optional[str] = None

@router.post("/from-id-cards")
async def generate_from_ids(
    act_type: str = "vente_immobilier",
    vendeur_id: UploadFile = File(...),
    acheteur_id: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère un acte à partir des photos des cartes d'identité.
    Le type d'acte peut être : vente_immobilier, vente_vehicule, vente_societe, mariage.
    """
    try:
        # 1. Extraction OCR via Gemini
        vendeur_bytes = await vendeur_id.read()
        acheteur_bytes = await acheteur_id.read()
        
        extracted = extract_info_from_ids_batch(vendeur_bytes, acheteur_bytes)
        
        # Mapping des rôles selon le type d'acte
        p1_info = extracted.get("vendeur", {})
        p2_info = extracted.get("acheteur", {})

        if "error" in p1_info or "error" in p2_info:
            err_p1 = p1_info.get('error', '')
            err_p2 = p2_info.get('error', '')
            detail_msg = err_p1 if err_p1 == err_p2 else f"{err_p1} / {err_p2}"
            raise HTTPException(
                status_code=429 if "429" in detail_msg else 500, 
                detail=f"Erreur OCR: {detail_msg}"
            )

        # Structure pour le RAG
        parties_info = {}
        if act_type == "mariage":
            parties_info = {"monsieur": p1_info, "madame": p2_info}
            special_clauses = "Acte de mariage civil et religieux."
            doc_title_prefix = "Acte de Mariage"
        else:
            parties_info = {"vendeur": p1_info, "acheteur": p2_info}
            special_clauses = f"Acte de {act_type.replace('_', ' ')} généré."
            doc_title_prefix = f"Acte de {act_type.split('_')[-1].capitalize()}"

        # 2. Identification des champs manquants
        missing_vars = identify_missing_fields(parties_info, special_clauses, act_type)
        
        # 3. Génération du brouillon initial
        draft_content = generate_notarial_draft(
            act_type=act_type,
            parties_info=parties_info,
            special_clauses=special_clauses,
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
        )

        # 4. Titre
        p1_nom = p1_info.get("nom", "Partie 1")
        p2_nom = p2_info.get("nom", "Partie 2")
        doc_title = f"{doc_title_prefix} - {p1_nom} / {p2_nom}"
        
        # 5. Sauvegarde
        # Conversion du string act_type en Enum member
        try:
            db_act_type = ActType(act_type)
        except ValueError:
            db_act_type = ActType.AUTRE

        new_doc = Document(
            title=doc_title,
            act_type=db_act_type,
            status=ActStatus.BROUILLON,
            content=draft_content,
            metadata_json={
                "parties": parties_info, 
                "missing_vars": missing_vars,
                "completion_data": {},
                "requested_type": act_type
            },
            owner_id=current_user.id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return {
            "document_id": new_doc.id,
            "parties_extrait": parties_info,
            "content": draft_content,
            "pdf_url": f"/api/v1/id-processing/download-pdf/{new_doc.id}",
            "missing_fields": missing_vars,
            "notary_name": current_user.full_name,
            "notary_bureau": current_user.bureau,
            "status": "brouillon",
            "message": f"Brouillon '{act_type}' créé avec succès."
        }

    except Exception as e:
        import traceback
        print(f"Erreur generate_from_ids: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/complete/{document_id}")
async def complete_act(
    document_id: int,
    completion: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complète un acte quel que soit son type.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    try:
        meta = doc.metadata_json or {}
        parties_info = meta.get("parties", {})
        act_type = meta.get("requested_type") or doc.act_type.value
        completion_dict = completion
        
        existing_completion = meta.get("completion_data", {})
        existing_completion.update(completion_dict)
        
        # Régénération
        updated_content = generate_notarial_draft(
            act_type=act_type,
            parties_info=parties_info,
            special_clauses=f"Acte de {act_type} finalisé.",
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
            completion_data=existing_completion
        )
        
        # Vérification des champs restants
        combined_clauses = " ".join([f"{k}:{v}" for k, v in existing_completion.items()])
        remaining_missing = identify_missing_fields(parties_info, combined_clauses, act_type)
        
        doc.content = updated_content
        doc.status = ActStatus.BROUILLON if remaining_missing else ActStatus.VALIDE
        doc.metadata_json = {
            **meta,
            "completion_data": existing_completion,
            "missing_vars": remaining_missing
        }
        db.commit()
        db.refresh(doc)

        return {
            "document_id": doc.id,
            "content": updated_content,
            "pdf_url": f"/api/v1/id-processing/download-pdf/{doc.id}",
            "missing_fields": remaining_missing,
            "status": doc.status.value,
            "message": (
                "Acte validé et finalisé avec succès !" 
                if doc.status == ActStatus.VALIDE 
                else f"Acte mis à jour. {len(remaining_missing)} champ(s) encore manquant(s)."
            )
        }

    except Exception as e:
        db.rollback()
        import traceback
        print(f"Erreur complete_act: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-pdf/{document_id}")
async def download_pdf(
    document_id: int, 
    db: Session = Depends(get_db)
):
    """Télécharger l'acte au format PDF professionnel."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    # Récupérer les infos pour enrichir le PDF
    meta = doc.metadata_json or {}
    act_type = meta.get("requested_type") or (doc.act_type.value if doc.act_type else "vente_immobilier")
    
    # Debug log pour confirmer le type envoyé au service PDF
    print(f"DEBUG: Generating PDF for Doc {document_id}, ActType: {act_type}")
    
    pdf_buffer = generate_act_pdf(
        title=doc.title,
        content=doc.content,
        act_number=str(document_id),
        notary_name=doc.owner.full_name if doc.owner else "............",
        notary_bureau=doc.owner.bureau if doc.owner and doc.owner.bureau else "............",
        status=doc.status.value if doc.status else "brouillon",
        act_type=act_type
    )
    
    content = pdf_buffer.getvalue()
    print(f"DEBUG: Serving PDF ID {document_id}, size: {len(content)} bytes")
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=acte_{document_id}.pdf",
            "Content-Length": str(len(content)),
            "Access-Control-Allow-Origin": "*"
        }
    )
