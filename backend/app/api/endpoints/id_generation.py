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
    vendeur_id: UploadFile = File(...),
    acheteur_id: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère un acte de vente complet à partir des photos des cartes d'identité.
    Retourne également les champs manquants à compléter par le notaire.
    """
    try:
        # 1. Extraction OCR via Gemini en un seul batch pour économiser le quota (429)
        vendeur_bytes = await vendeur_id.read()
        acheteur_bytes = await acheteur_id.read()
        
        extracted = extract_info_from_ids_batch(vendeur_bytes, acheteur_bytes)
        vendeur_info = extracted.get("vendeur", {})
        acheteur_info = extracted.get("acheteur", {})

        if "error" in vendeur_info or "error" in acheteur_info:
            err_vendeur = vendeur_info.get('error', '')
            err_acheteur = acheteur_info.get('error', '')
            detail_msg = err_vendeur if err_vendeur == err_acheteur else f"{err_vendeur} / {err_acheteur}"
            raise HTTPException(
                status_code=429 if "429" in detail_msg else 500, 
                detail=f"Erreur OCR: {detail_msg}"
            )

        # 2. Identification des champs manquants AVANT génération
        parties_info = {"vendeur": vendeur_info, "acheteur": acheteur_info}
        special_clauses = "Acte de vente immobilière généré automatiquement."
        missing_vars = identify_missing_fields(parties_info, special_clauses)
        
        # 3. Génération du brouillon initial via Gemini RAG
        draft_content = generate_notarial_draft(
            act_type="vente",
            parties_info=parties_info,
            special_clauses=special_clauses,
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
        )

        # 4. Titre professionnel sans noms de test
        v_nom = vendeur_info.get("nom", "Vendeur Inconnu")
        a_nom = acheteur_info.get("nom", "Acheteur Inconnu")
        doc_title = f"Acte de Vente - {v_nom} / {a_nom}"
        
        # 5. Sauvegarde en BDD avec statut BROUILLON
        new_doc = Document(
            title=doc_title,
            act_type=ActType.VENTE,
            status=ActStatus.BROUILLON,
            content=draft_content,
            metadata_json={
                "parties": parties_info, 
                "missing_vars": missing_vars,
                "completion_data": {}
            },
            owner_id=current_user.id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return {
            "document_id": new_doc.id,
            "vendeur_extrait": vendeur_info,
            "acheteur_extrait": acheteur_info,
            "content": draft_content,
            "pdf_url": f"/api/v1/id-processing/download-pdf/{new_doc.id}",
            "missing_fields": missing_vars,
            "notary_name": current_user.full_name,
            "notary_bureau": current_user.bureau,
            "status": "brouillon",
            "message": (
                f"Brouillon créé avec succès. {len(missing_vars)} information(s) manquante(s) à compléter."
                if missing_vars else
                "Acte généré et complet."
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Erreur generate_from_ids: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/complete/{document_id}")
async def complete_act(
    document_id: int,
    completion: CompletionData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complète un acte de vente avec les informations manquantes (prix, quartier, parcelle, etc.)
    et régénère le document final.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    if doc.status == ActStatus.VALIDE:
        raise HTTPException(status_code=400, detail="Cet acte est déjà validé et ne peut plus être modifié.")

    try:
        # Récupérer les données d'origine
        meta = doc.metadata_json or {}
        parties_info = meta.get("parties", {})
        completion_dict = completion.dict(exclude_none=True)
        
        # Mettre à jour les données de complétion
        existing_completion = meta.get("completion_data", {})
        existing_completion.update(completion_dict)
        
        # Régénération de l'acte avec les données complètes
        updated_content = generate_notarial_draft(
            act_type="vente",
            parties_info=parties_info,
            special_clauses="Acte de vente immobilière finalisé.",
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
            completion_data=existing_completion
        )
        
        # Vérifier les champs manquants restants
        combined_clauses = " ".join([f"{k}:{v}" for k, v in existing_completion.items()])
        remaining_missing = identify_missing_fields(parties_info, combined_clauses)
        
        # Mise à jour en BDD
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
    parties = meta.get("parties", {})
    
    pdf_buffer = generate_act_pdf(
        title=doc.title,
        content=doc.content,
        act_number=str(document_id),
        notary_name=doc.owner.full_name if doc.owner else "............",
        notary_bureau=doc.owner.bureau if doc.owner and doc.owner.bureau else "............",
        status=doc.status.value if doc.status else "brouillon"
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
