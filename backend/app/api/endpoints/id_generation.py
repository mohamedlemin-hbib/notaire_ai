from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import io

from app.db.session import get_db
from app.db.models import Document, ActType, ActStatus, User
from app.services.ocr_service import extract_info_from_id, extract_info_from_ids_batch, extract_info_from_carte_grise, extract_info_from_permis_occuper
from app.services.rag_service import generate_notarial_draft, identify_missing_fields
from app.services.pdf_service import generate_act_pdf
from app.api.deps import get_current_user
from app.services.security_service import log_security_event

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
    carte_grise_front: Optional[UploadFile] = File(None),
    carte_grise_back: Optional[UploadFile] = File(None),
    permis_occuper: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lang: str = "fr"
):
    print(f"DEBUG: generate_from_ids called for act_type={act_type}")
    """
    Génère un acte à partir des photos des cartes d'identité et optionnellement de la carte grise.
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
        completion_data = {}
        
        if act_type == "mariage":
            parties_info = {"monsieur": p1_info, "madame": p2_info}
            special_clauses = "Acte de mariage civil et religieux."
            doc_title_prefix = "Acte de Mariage"
        elif act_type == "testament":
            parties_info = {"testateur": p1_info, "beneficiaire": p2_info}
            special_clauses = "Acte de testament généré."
            doc_title_prefix = "Acte de Testament"
        elif act_type == "hypotheque":
            parties_info = {"debiteur": p1_info, "creancier": p2_info}
            special_clauses = "Acte d'hypothèque généré."
            doc_title_prefix = "Acte d'Hypothèque"
        else:
            parties_info = {"vendeur": p1_info, "acheteur": p2_info}
            special_clauses = f"Acte de {act_type.replace('_', ' ')} généré."
            doc_title_prefix = f"Acte de {act_type.split('_')[-1].capitalize()}"

        # 1.1 Extraction Carte Grise si fournie
        if act_type == "vente_vehicule" and (carte_grise_front or carte_grise_back):
            print("DEBUG: Lancement de l'extraction Carte Grise...")
            cg_front_bytes = await carte_grise_front.read() if carte_grise_front else None
            cg_back_bytes = await carte_grise_back.read() if carte_grise_back else None
            cg_info = extract_info_from_carte_grise(cg_front_bytes, cg_back_bytes)
            
            if "error" not in cg_info:
                print(f"DEBUG: Carte Grise extraite avec succès: {list(cg_info.keys())}")
                completion_data.update(cg_info)
                # On enrichit les clauses spéciales pour que identify_missing_fields les voit
                for k, v in cg_info.items():
                    if v: special_clauses += f" {k}: {v}."
            else:
                print(f"DEBUG: Échec extraction Carte Grise: {cg_info.get('error')}")

        # 1.2 Extraction Permis d'Occuper si fourni (Immobilier ou Hypothèque)
        if (act_type == "vente_immobilier" or act_type == "hypotheque") and permis_occuper:
            print("DEBUG: Lancement de l'extraction Permis d'Occuper...")
            permis_bytes = await permis_occuper.read()
            permis_info = extract_info_from_permis_occuper(permis_bytes)
            
            if "error" not in permis_info:
                print(f"DEBUG: Permis d'occuper extrait avec succès: {list(permis_info.keys())}")
                completion_data.update(permis_info)
                # On enrichit les clauses spéciales
                for k, v in permis_info.items():
                    if v: special_clauses += f" {k}: {v}."
            else:
                err_msg = permis_info.get('error')
                print(f"DEBUG: Échec extraction Permis: {err_msg}")
                if err_msg == "not_a_permis":
                    raise HTTPException(status_code=400, detail="Le document envoyé n'est pas reconnu comme un Permis d'Occuper. Veuillez envoyer la photo du document foncier.")

        # 2. Identification des champs manquants
        missing_vars = identify_missing_fields(parties_info, special_clauses, act_type)
        
        # 3. Génération du brouillon initial
        draft_content = generate_notarial_draft(
            act_type=act_type,
            parties_info=parties_info,
            special_clauses=special_clauses,
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
            completion_data=completion_data,
            lang=lang
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
                "completion_data": completion_data,
                "requested_type": act_type,
                "lang": lang
            },
            owner_id=current_user.id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Log de sécurité : Création
        log_security_event(
            db=db,
            user_id=current_user.id,
            action="GENERATE_ACT",
            document_id=new_doc.id,
            details={"act_type": act_type, "title": doc_title}
        )

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
    current_user: User = Depends(get_current_user),
    lang: Optional[str] = None
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
    
    if doc.status == ActStatus.SCELLE:
        raise HTTPException(
            status_code=403, 
            detail="Cet acte est scellé (cachet du notaire appliqué) et ne peut plus être modifié."
        )
    
    try:
        meta = doc.metadata_json or {}
        parties_info = meta.get("parties", {})
        act_type = meta.get("requested_type") or doc.act_type.value
        completion_dict = completion
        
        existing_completion = meta.get("completion_data", {})
        existing_completion.update(completion_dict)
        
        # Déterminer la langue (paramètre > meta > défaut fr)
        act_lang = lang or meta.get("lang") or "fr"
        
        # Régénération
        updated_content = generate_notarial_draft(
            act_type=act_type,
            parties_info=parties_info,
            special_clauses=f"Acte de {act_type} finalisé.",
            notary_name=current_user.full_name or ".........................",
            notary_bureau=current_user.bureau or "............",
            completion_data=existing_completion,
            lang=act_lang
        )
        
        # Vérification des champs restants
        combined_clauses = " ".join([f"{k}:{v}" for k, v in existing_completion.items()])
        remaining_missing = identify_missing_fields(parties_info, combined_clauses, act_type)
        
        doc.content = updated_content
        doc.status = ActStatus.BROUILLON if remaining_missing else ActStatus.VALIDE
        doc.metadata_json = {
            **meta,
            "completion_data": existing_completion,
            "missing_vars": remaining_missing,
            "lang": act_lang
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
                "Acte finalisé avec succès !" 
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Télécharger l'acte au format PDF professionnel."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not doc:
        # Check if user is admin as an exception
        if current_user.role == "ADMIN":
            doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document non trouvé ou accès refusé")
    
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
        act_type=act_type,
        lang=meta.get("lang", "fr")
    )
    
    # Log de sécurité : Téléchargement
    log_security_event(
        db=db,
        user_id=current_user.id,
        action="DOWNLOAD_PDF",
        document_id=document_id,
        details={"title": doc.title}
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


@router.post("/seal/{document_id}")
async def seal_act(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Applique le cachet du notaire (scelle l'acte).
    Une fois scellé, l'acte ne peut plus être modifié.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
        
    doc.status = ActStatus.SCELLE
    db.commit()
    db.refresh(doc)
    
    # Log de sécurité : Scellement
    log_security_event(
        db=db,
        user_id=current_user.id,
        action="SEAL_ACT",
        document_id=document_id,
        details={"title": doc.title}
    )
    
    return {
        "document_id": doc.id,
        "status": doc.status.value,
        "message": "L'acte a été scellé avec succès. Il est désormais protégé contre toute modification."
    }

