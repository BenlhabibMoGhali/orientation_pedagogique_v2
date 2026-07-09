import os
from datetime import datetime
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.pdfgen.canvas import Canvas


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGO_UEMF_PATH = os.path.join(
    BASE_DIR,
    "static",
    "logos",
    "LOGO-UEMF-HD.png"
)

LOGO_EIDIA_PATH = os.path.join(
    BASE_DIR,
    "static",
    "logos",
    "logo-EIDIA.jpeg"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "fiches_engagement"
)


def dessiner_entete(canvas: Canvas, doc):
    largeur_page, hauteur_page = A4

    if os.path.exists(LOGO_UEMF_PATH):
        canvas.drawImage(
            LOGO_UEMF_PATH,
            2 * cm,
            hauteur_page - 3.2 * cm,
            width=5.1 * cm,
            height=1.8 * cm,
            preserveAspectRatio=True,
            mask="auto"
        )

    if os.path.exists(LOGO_EIDIA_PATH):
        canvas.drawImage(
            LOGO_EIDIA_PATH,
            largeur_page - 7 * cm,
            hauteur_page - 3.2 * cm,
            width=5 * cm,
            height=1.8 * cm,
            preserveAspectRatio=True,
            mask="auto"
        )


def generer_fiche_engagement_pdf(choix_details):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    choix_id = choix_details["choix_id"]
    nom = choix_details["nom"]
    prenom = choix_details["prenom"]
    id_universitaire = choix_details["id_universitaire"]
    filiere_choisie = choix_details["filiere_choisie"]

    nom_complet = f"{prenom} {nom}".strip()

    nom_fichier = f"fiche_engagement_choix_{choix_id}.pdf"
    chemin_pdf = os.path.join(OUTPUT_DIR, nom_fichier)

    doc = SimpleDocTemplate(
        chemin_pdf,
        pagesize=A4,
        rightMargin=2.2 * cm,
        leftMargin=2.2 * cm,
        topMargin=4.2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    titre_style = ParagraphStyle(
        "TitreBleu",
        parent=styles["Title"],
        textColor=colors.HexColor("#1d4ed8"),
        fontName="Helvetica-Bold",
        fontSize=16,
        alignment=1,
        spaceAfter=20
    )

    normal_style = ParagraphStyle(
        "NormalSimple",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=17,
        textColor=colors.black,
        spaceAfter=10
    )

    signature_style = ParagraphStyle(
        "Signature",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.black
    )

    story = []

    story.append(
        Paragraph(
            "Fiche d’engagement du choix de filière",
            titre_style
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    story.append(
        Paragraph(
            "À Monsieur le Doyen,<br/>"
            "Doyen de l’École d’Ingénierie Digitale et "
            "d’Intelligence Artificielle (EIDIA),<br/>"
            "Université Euromed de Fès.",
            normal_style
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    story.append(
        Paragraph(
            "Je soussigné(e) confirme par la présente mon choix "
            "de filière au sein de l’École d’Ingénierie Digitale et "
            "d’Intelligence Artificielle (EIDIA) à l’Université Euromed "
            "de Fès.",
            normal_style
        )
    )

    story.append(
        Paragraph(
            "Je certifie avoir effectué ce choix en toute connaissance de "
            "cause, après réflexion personnelle et en accord avec mon projet "
            "académique et professionnel.",
            normal_style
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    story.append(
        Paragraph(
            f"Nom complet : <b>{escape(nom_complet)}</b>",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"Identifiant universitaire : <b>{escape(id_universitaire)}</b>",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"Filière choisie : <b>{escape(filiere_choisie)}</b>",
            normal_style
        )
    )

    story.append(Spacer(1, 0.5 * cm))

    story.append(
        Paragraph(
            "Par la présente, je m’engage à m’investir pleinement dans la "
            "filière choisie et à respecter les règles et exigences "
            "pédagogiques de l’établissement.",
            normal_style
        )
    )

    story.append(
        Paragraph(
            "Je vous prie, Monsieur le Doyen, de bien vouloir prendre acte "
            "de mon choix de filière.",
            normal_style
        )
    )

    story.append(
        Paragraph(
            "Veuillez agréer, Monsieur le Doyen, l’expression de ma haute "
            "considération.",
            normal_style
        )
    )

    story.append(Spacer(1, 2.2 * cm))

    annee = datetime.now().year

    story.append(
        Paragraph(
            f"Fait à Fès, le …… / …… / {annee}",
            signature_style
        )
    )

    story.append(Spacer(1, 1.4 * cm))

    story.append(
        Paragraph(
            "Signature de l’étudiant",
            signature_style
        )
    )

    doc.build(
        story,
        onFirstPage=dessiner_entete,
        onLaterPages=dessiner_entete
    )

    return chemin_pdf