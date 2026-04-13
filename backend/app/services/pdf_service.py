from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
import io
import datetime
from xml.sax.saxutils import escape


# ── Palette de couleurs ──────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0D1B4B")   # Bleu marine professionnel
GOLD       = colors.HexColor("#B8860B")   # Or foncé (tampons)
LIGHT_GREY = colors.HexColor("#F4F6FA")   # Fond des articles
MED_GREY   = colors.HexColor("#6B7280")   # Textes secondaires
RED_SEAL   = colors.HexColor("#8B0000")   # Pour le tampon BROUILLON
GREEN_SEAL = colors.HexColor("#065F46")   # Pour le tampon VALIDE


def _build_styles():
    """Construit le système de styles ReportLab."""
    styles = getSampleStyleSheet()

    institution = ParagraphStyle(
        "Institution",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    republic = ParagraphStyle(
        "Republic",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=MED_GREY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    act_title = ParagraphStyle(
        "ActTitle",
        fontName="Helvetica-Bold",
        fontSize=17,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=4,
    )
    act_number = ParagraphStyle(
        "ActNumber",
        fontName="Helvetica",
        fontSize=10,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
    article_title = ParagraphStyle(
        "ArticleTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    footer = ParagraphStyle(
        "Footer",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=MED_GREY,
        alignment=TA_CENTER,
    )
    meta = ParagraphStyle(
        "Meta",
        fontName="Helvetica",
        fontSize=8,
        textColor=MED_GREY,
        alignment=TA_RIGHT,
    )

    return {
        "institution": institution,
        "republic": republic,
        "act_title": act_title,
        "act_number": act_number,
        "article_title": article_title,
        "body": body,
        "footer": footer,
        "meta": meta,
    }


def _build_header(styles, notary_name: str, notary_bureau: str) -> list:
    """En-tête officielle avec nom du notaire et institution."""
    elements = []

    # Logo textuel – ligne République
    elements.append(Paragraph("République Islamique de Mauritanie", styles["republic"]))
    elements.append(Paragraph("Honneur – Fraternité – Justice", styles["republic"]))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    elements.append(Spacer(1, 4))

    # Nom du notaire
    elements.append(Paragraph(f"Maître {notary_name}", styles["institution"]))
    elements.append(Paragraph(f"Notaire / Rédacteur Agréé — {notary_bureau}", styles["republic"]))
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1, color=GOLD))
    elements.append(Spacer(1, 8))

    return elements


def _build_status_stamp(status: str) -> list:
    """Affiche un bandeau de statut (BROUILLON ou VALIDÉ)."""
    if status == "valide":
        color = GREEN_SEAL
        label = "✓  ACTE VALIDÉ"
    else:
        return []

    data = [[label]]
    table = Table(data, colWidths=[450])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return [table, Spacer(1, 10)]


def _build_signature_block(styles, act_type: str = "vente_immobilier") -> list:
    """Bloc de signatures professionnel à 3 colonnes, adapté au type d'acte."""
    elements = []
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MED_GREY))
    elements.append(Spacer(1, 16))

    sig_style = ParagraphStyle("Sig", fontName="Helvetica-Bold",
                               fontSize=9, alignment=TA_CENTER, textColor=NAVY)
    line_style = ParagraphStyle("Line", fontName="Helvetica",
                                fontSize=9, alignment=TA_CENTER, textColor=MED_GREY)

    # Détection automatique basée sur le contenu (fallback)
    content_str = str(elements).upper() if elements else ""
    is_marriage_content = any(k in content_str for k in ["ÉPOUX", "ÉPOUSE", "WALI", "DOT (MAHR)", "MARIAGE"])

    # Définition des labels selon le type d'acte
    label_p1 = "LE VENDEUR"
    label_p2 = "L'ACHETEUR"

    if act_type == "mariage" or is_marriage_content:
        label_p1 = "MONSIEUR"
        label_p2 = "MADAME"
    elif act_type == "vente_societe":
        label_p1 = "LE CÉDANT"
        label_p2 = "LE CESSIONNAIRE"
    elif act_type == "testament":
        label_p1 = "LE TESTATEUR"
        label_p2 = "LES TÉMOINS"

    sig_data = [
        [Paragraph(label_p1, sig_style),
         Paragraph("LE NOTAIRE", sig_style),
         Paragraph(label_p2, sig_style)],
        [Paragraph("Signature & Cachet", line_style),
         Paragraph("Signature & Cachet Officiel", line_style),
         Paragraph("Signature & Cachet", line_style)],
        [Paragraph("\n\n\n_____________________", line_style),
         Paragraph("\n\n\n_____________________", line_style),
         Paragraph("\n\n\n_____________________", line_style)],
    ]
    sig_table = Table(sig_data, colWidths=[150, 150, 150])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)
    return elements


def _build_footer(styles, act_number: str) -> list:
    """Pied de page avec numéro d'acte et date."""
    elements = []
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MED_GREY))
    now = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        f"Acte N° {act_number}  —  Document généré le {now}  —  Agentic Notary System",
        styles["footer"]
    ))
    return elements


def generate_act_pdf(
    title: str,
    content: str,
    act_number: str = "----",
    notary_name: str = "............",
    notary_bureau: str = "............",
    status: str = "brouillon",
    act_type: str = "vente_immobilier"
) -> io.BytesIO:
    """
    Génère un PDF professionnel notarial avec en-tête officielle,
    numéro d'acte, statut tampon et bloc de signatures.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=title,
        author=f"Maître {notary_name}",
    )

    styles = _build_styles()
    elements = []

    # ── En-tête ──────────────────────────────────────────────────────────────
    elements.extend(_build_header(styles, notary_name, notary_bureau))

    # ── Titre de l'acte dynamique ─────────────────────────────────────────────
    # Mapping des titres selon le type d'acte
    titles_map = {
        "mariage": "ACTE DE MARIAGE",
        "vente_immobilier": "ACTE DE VENTE IMMOBILIÈRE",
        "vente_vehicule": "ACTE DE VENTE DE VÉHICULE",
        "vente_societe": "ACTE DE CESSION DE PARTS SOCIALES",
        "testament": "ACTE DE TESTAMENT",
        "procuration": "PROCURATION NOTARIÉE"
    }
    
    # On normalise act_type en minuscule pour le mapping
    norm_type = (act_type or "").lower()
    
    # Sécurité supplémentaire : détection par contenu pour le titre
    if "mariage" in content.lower() or "époux" in content.lower():
        norm_type = "mariage"
        
    display_title = titles_map.get(norm_type, "ACTE NOTARIÉ")
    
    elements.append(Paragraph(display_title, styles["act_title"]))
    elements.append(Paragraph(f"Acte N° {act_number}", styles["act_number"]))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=NAVY))
    elements.append(Spacer(1, 10))

    # ── Tampon de statut ─────────────────────────────────────────────────────
    elements.extend(_build_status_stamp(status))

    # ── Corps du document ─────────────────────────────────────────────────────
    if content:
        lines = content.split("\n")
        current_article_lines = []
        current_article_title = None
        is_first_line = True

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            # Détection des titres d'articles
            is_article = (
                line.upper().startswith("ARTICLE") or
                line.upper().startswith("PAR-DEVANT") or
                line.upper().startswith("ONT COMPARU") or
                line.upper().startswith("FAIT EN") or
                (line.startswith("═") or line.startswith("="))
            )

            if is_article:
                # Vider l'article précédent
                if current_article_lines:
                    block = []
                    if current_article_title:
                        block.append(Paragraph(escape(current_article_title), styles["article_title"]))
                    bg_data = [[Paragraph(escape(l), styles["body"])] for l in current_article_lines]
                    if bg_data:
                        art_table = Table(bg_data, colWidths=[450])
                        art_table.setStyle(TableStyle([
                            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                            ("LEFTPADDING", (0, 0), (-1, -1), 12),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                        ]))
                        block.append(art_table)
                    elements.append(KeepTogether(block))
                    current_article_lines = []

                current_article_title = line
            else:
                if is_first_line:
                    # Première ligne introductive directement en body
                    elements.append(Paragraph(escape(line), styles["body"]))
                    is_first_line = False
                else:
                    current_article_lines.append(line)

        # Vider le dernier article
        if current_article_lines:
            block = []
            if current_article_title:
                block.append(Paragraph(escape(current_article_title), styles["article_title"]))
            for l in current_article_lines:
                block.append(Paragraph(escape(l), styles["body"]))
            elements.append(KeepTogether(block))

    # ── Signatures ────────────────────────────────────────────────────────────
    elements.extend(_build_signature_block(styles, act_type=act_type))

    # ── Pied de page ──────────────────────────────────────────────────────────
    elements.extend(_build_footer(styles, act_number))

    doc.build(elements)
    buffer.seek(0)
    return buffer
