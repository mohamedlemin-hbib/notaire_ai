from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
import datetime
from xml.sax.saxutils import escape

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False

# Enregistrement de la police pour le support de l'arabe sur Windows
# Priorité : Arial Unicode MS (meilleur support arabe) > Arial > Helvetica
try:
    unicode_font_path = "C:\\Windows\\Fonts\\ARIALUNI.TTF"
    arial_font_path = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(unicode_font_path):
        pdfmetrics.registerFont(TTFont('ArialUnicode', unicode_font_path))
        DEFAULT_FONT = "ArialUnicode"
    elif os.path.exists(arial_font_path):
        pdfmetrics.registerFont(TTFont('Arial', arial_font_path))
        DEFAULT_FONT = "Arial"
    else:
        DEFAULT_FONT = "Helvetica"
except:
    DEFAULT_FONT = "Helvetica"

def _fix_text(text, lang="fr"):
    """Reshape Arabic text for proper connected letter rendering in PDFs.
    IMPORTANT: Call this AFTER xml escape to avoid breaking reshaped glyphs."""
    if lang == "ar" and HAS_ARABIC_SUPPORT:
        reshaped_text = arabic_reshaper.reshape(text)
        return get_display(reshaped_text)
    return text


# ── Palette de couleurs ──────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0D1B4B")   # Bleu marine professionnel
GOLD       = colors.HexColor("#B8860B")   # Or foncé (tampons)
LIGHT_GREY = colors.HexColor("#F4F6FA")   # Fond des articles
MED_GREY   = colors.HexColor("#6B7280")   # Textes secondaires
RED_SEAL   = colors.HexColor("#8B0000")   # Pour le tampon BROUILLON


def _build_styles(lang="fr"):
    """Construit le système de styles ReportLab."""
    styles = getSampleStyleSheet()
    font_name = DEFAULT_FONT if lang == "ar" else "Helvetica"
    alignment = TA_RIGHT if lang == "ar" else TA_LEFT
    body_alignment = TA_RIGHT if lang == "ar" else TA_JUSTIFY

    institution = ParagraphStyle(
        "Institution",
        fontName=font_name + "-Bold" if font_name == "Helvetica" else font_name,
        fontSize=10,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=1,
    )
    republic = ParagraphStyle(
        "Republic",
        fontName=font_name + "-Oblique" if font_name == "Helvetica" else font_name,
        fontSize=8,
        textColor=MED_GREY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    act_title = ParagraphStyle(
        "ActTitle",
        fontName=font_name + "-Bold" if font_name == "Helvetica" else font_name,
        fontSize=14,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=2,
    )
    act_number = ParagraphStyle(
        "ActNumber",
        fontName=font_name,
        fontSize=8,
        textColor=GOLD,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    article_title = ParagraphStyle(
        "ArticleTitle",
        fontName=font_name + "-Bold" if font_name == "Helvetica" else font_name,
        fontSize=9,
        textColor=NAVY,
        alignment=alignment,
        spaceBefore=6,
        spaceAfter=2,
    )
    body = ParagraphStyle(
        "Body",
        fontName=font_name,
        fontSize=9,
        leading=11,
        alignment=body_alignment,
        spaceAfter=2,
    )
    footer = ParagraphStyle(
        "Footer",
        fontName=font_name + "-Oblique" if font_name == "Helvetica" else font_name,
        fontSize=7,
        textColor=MED_GREY,
        alignment=TA_CENTER,
    )
    meta = ParagraphStyle(
        "Meta",
        fontName=font_name,
        fontSize=7,
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


def _build_header(styles, notary_name: str, notary_bureau: str, lang: str = "fr") -> list:
    """En-tête officielle avec nom du notaire et institution."""
    elements = []

    republic_text = "الجمهورية الإسلامية الموريتانية" if lang == "ar" else "République Islamique de Mauritanie"
    motto_text = "شرف – إخاء – عدل" if lang == "ar" else "Honneur – Fraternité – Justice"
    notary_prefix = "الأستاذ" if lang == "ar" else "Maître"
    notary_role = "موثق / محرر معتمد" if lang == "ar" else "Notaire / Rédacteur Agréé"

    # Logo textuel – ligne République
    elements.append(Paragraph(_fix_text(republic_text, lang), styles["republic"]))
    elements.append(Paragraph(_fix_text(motto_text, lang), styles["republic"]))
    elements.append(Spacer(1, 1))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=NAVY))
    elements.append(Spacer(1, 1))

    # Nom du notaire
    elements.append(Paragraph(_fix_text(f"{notary_prefix} {notary_name}", lang), styles["institution"]))
    elements.append(Paragraph(_fix_text(f"{notary_role} — {notary_bureau}", lang), styles["republic"]))
    elements.append(Spacer(1, 1))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD))
    elements.append(Spacer(1, 2))

    return elements


def _build_status_stamp(status: str, lang: str = "fr") -> list:
    """Affiche un bandeau de statut (BROUILLON, VALIDÉ ou SCELLÉ)."""
    if status == "scelle":
        color = NAVY
        label = "★  عقد مختوم - تم تطبيق ختم الموثق  ★" if lang == "ar" else "★  ACTE SCELLÉ - CACHET DU NOTAIRE APPLIQUÉ  ★"
    elif status == "valide":
        return []
    else:
        return []

    data = [[Paragraph(_fix_text(label, lang), ParagraphStyle("Stamp", fontName=DEFAULT_FONT if lang == "ar" else "Helvetica-Bold", fontSize=9, textColor=colors.white, alignment=TA_CENTER))]]
    table = Table(data, colWidths=[450])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return [table, Spacer(1, 5)]


def _build_signature_block(styles, act_type: str = "vente_immobilier", lang: str = "fr") -> list:
    """Bloc de signature unique pour le Notaire."""
    elements = []
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MED_GREY))
    elements.append(Spacer(1, 5))

    font_name = DEFAULT_FONT if lang == "ar" else "Helvetica"
    sig_label = "توقيع وختم الموثق الرسمي" if lang == "ar" else "SIGNATURE ET CACHET OFFICIEL DU NOTAIRE"
    sig_sublabel = "(الأستاذ الموثق / المحرر المعتمد)" if lang == "ar" else "(Maître Notaire / Rédacteur Agréé)"

    sig_style = ParagraphStyle("Sig", fontName=font_name + "-Bold" if font_name == "Helvetica" else font_name,
                               fontSize=11, alignment=TA_CENTER, textColor=NAVY)
    line_style = ParagraphStyle("Line", fontName=font_name,
                                fontSize=10, alignment=TA_CENTER, textColor=MED_GREY)

    sig_data = [
        [Paragraph(_fix_text(sig_label, lang), sig_style)],
        [Spacer(1, 5)],
        [Paragraph("\n\n\n__________________________________________", line_style)],
        [Paragraph(_fix_text(sig_sublabel, lang), line_style)],
    ]
    
    sig_table = Table(sig_data, colWidths=[400])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    
    elements.append(sig_table)
    return elements


def _build_footer(styles, act_number: str, lang: str = "fr") -> list:
    """Pied de page avec numéro d'acte et date."""
    elements = []
    elements.append(Spacer(1, 5))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=MED_GREY))
    now = datetime.datetime.now().strftime("%d/%m/%Y")
    elements.append(Spacer(1, 2))
    
    act_label = "عقد رقم" if lang == "ar" else "Acte N°"
    gen_label = "تم إنشاء المستند في" if lang == "ar" else "Document généré le"
    
    footer_text = f"{act_label} {act_number}  —  {gen_label} {now}  —  Agentic Notary System"
    elements.append(Paragraph(_fix_text(footer_text, lang), styles["footer"]))
    return elements


def generate_act_pdf(
    title: str,
    content: str,
    act_number: str = "----",
    notary_name: str = "............",
    notary_bureau: str = "............",
    status: str = "brouillon",
    act_type: str = "vente_immobilier",
    lang: str = "fr"
) -> io.BytesIO:
    """
    Génère un PDF professionnel notarial avec en-tête officielle,
    numéro d'acte, statut tampon et bloc de signatures.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.0 * cm,
        leftMargin=1.0 * cm,
        topMargin=0.7 * cm,
        bottomMargin=0.7 * cm,
        title=title,
        author=f"Maître {notary_name}",
    )

    styles = _build_styles(lang)
    elements = []

    # ── En-tête ──────────────────────────────────────────────────────────────
    elements.extend(_build_header(styles, notary_name, notary_bureau, lang))

    # ── Titre de l'acte dynamique ─────────────────────────────────────────────
    # Mapping des titres selon le type d'acte
    titles_map = {
        "mariage": "ACTE DE MARIAGE" if lang != "ar" else "عقد زواج شرعي",
        "vente_immobilier": "ACTE DE VENTE IMMOBILIÈRE" if lang != "ar" else "عقد بيع عقاري",
        "vente_vehicule": "ACTE DE VENTE DE VÉHICULE" if lang != "ar" else "عقد بيع مركبة",
        "vente_societe": "ACTE DE CESSION DE PARTS SOCIALES" if lang != "ar" else "عقد تنازل عن حصص في شركة",
        "testament": "ACTE DE TESTAMENT" if lang != "ar" else "عقد وصية شرعية",
        "procuration": "PROCURATION NOTARIÉE" if lang != "ar" else "وكالة توثيقية",
        "hypotheque": "ACTE D'HYPOTHÈQUE" if lang != "ar" else "عقد رهن عقاري (تأميني)"
    }
    
    # On normalise act_type en minuscule pour le mapping
    norm_type = (act_type or "").lower()
    
    # Sécurité supplémentaire : détection par contenu pour le titre
    if "mariage" in content.lower() or "époux" in content.lower():
        norm_type = "mariage"
        
    display_title = titles_map.get(norm_type, "ACTE NOTARIÉ")
    
    elements.append(Paragraph(_fix_text(display_title, lang), styles["act_title"]))
    num_label = "عقد رقم" if lang == "ar" else "Acte N°"
    elements.append(Paragraph(_fix_text(f"{num_label} {act_number}", lang), styles["act_number"]))
    elements.append(HRFlowable(width="100%", thickness=1.0, color=NAVY))
    elements.append(Spacer(1, 4))

    # ── Tampon de statut ─────────────────────────────────────────────────────
    elements.extend(_build_status_stamp(status, lang))

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
                line.startswith("═") or line.startswith("=") or
                # Arabe
                line.startswith("المادة") or
                line.startswith("أمامنا نحن") or
                line.startswith("حضر كل من") or
                line.startswith("حضر بمجلسنا") or
                line.startswith("الطرف الأول") or
                line.startswith("الطرف الثاني") or
                line.startswith("الزوج :") or
                line.startswith("الزوجة :") or
                line.startswith("الموصي :") or
                line.startswith("الموصى له") or
                line.startswith("بيانات المركبة") or
                line.startswith("حرر في") or
                line.startswith("حُرِّر") or
                line.startswith("إثباتاً")
            )

            if is_article:
                # Vider l'article précédent
                if current_article_lines:
                    block = []
                    if current_article_title:
                        block.append(Paragraph(_fix_text(escape(current_article_title), lang), styles["article_title"]))
                    bg_data = [[Paragraph(_fix_text(escape(l), lang), styles["body"])] for l in current_article_lines]
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
                    elements.append(Paragraph(_fix_text(escape(line), lang), styles["body"]))
                    is_first_line = False
                else:
                    current_article_lines.append(line)

        # Vider le dernier article
        if current_article_lines:
            block = []
            if current_article_title:
                block.append(Paragraph(_fix_text(escape(current_article_title), lang), styles["article_title"]))
            for l in current_article_lines:
                block.append(Paragraph(_fix_text(escape(l), lang), styles["body"]))
            elements.append(KeepTogether(block))

    # ── Signatures ────────────────────────────────────────────────────────────
    elements.extend(_build_signature_block(styles, act_type=act_type, lang=lang))

    # ── Pied de page ──────────────────────────────────────────────────────────
    elements.extend(_build_footer(styles, act_number, lang))

    doc.build(elements)
    buffer.seek(0)
    return buffer
