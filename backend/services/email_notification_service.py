import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database.chat_orientation_repository import lister_documents_a_confirmer


def get_configuration_email():
    smtp_port = os.getenv("SMTP_PORT", "587")

    try:
        smtp_port = int(smtp_port)
    except Exception:
        smtp_port = 587

    return {
        "smtp_host": os.getenv("SMTP_HOST", "").strip(),
        "smtp_port": smtp_port,
        "smtp_username": os.getenv("SMTP_USERNAME", "").strip(),
        "smtp_password": os.getenv("SMTP_PASSWORD", "").strip(),
        "email_expediteur": os.getenv("EMAIL_EXPEDITEUR", "").strip(),
        "email_destinataire_documents": os.getenv(
            "EMAIL_DESTINATAIRE_DOCUMENTS",
            ""
        ).strip()
    }


def email_configure():
    configuration = get_configuration_email()

    champs_obligatoires = [
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "email_expediteur",
        "email_destinataire_documents"
    ]

    for champ in champs_obligatoires:
        if configuration.get(champ) is None or configuration.get(champ) == "":
            return False

    return True


def compter_documents_en_attente():
    documents = lister_documents_a_confirmer()
    return len(documents)


def construire_message_document_depose(details_document, total_documents):
    prenom = details_document.get("prenom", "")
    nom = details_document.get("nom", "")
    id_universitaire = details_document.get("id_universitaire", "")
    filiere = details_document.get("filiere_choisie", "")
    nom_fichier = details_document.get("nom_fichier_original", "")

    sujet = (
        f"Nouveau document signé à valider - "
        f"{prenom} {nom} ({id_universitaire})"
    )

    contenu = f"""
Bonjour,

Un nouveau document signé vient d’être déposé sur la plateforme d’orientation pédagogique.

Informations de l’étudiant :
- Nom complet : {prenom} {nom}
- ID universitaire : {id_universitaire}
- Filière choisie : {filiere}

Document déposé :
- Nom du fichier : {nom_fichier}

État actuel :
- Nombre total de documents en attente de validation : {total_documents}

Action demandée :
Veuillez accéder à l’espace doyen pour visualiser et traiter le document.

Cordialement,
Plateforme d’orientation pédagogique
"""

    return sujet, contenu


def envoyer_email(sujet, contenu):
    configuration = get_configuration_email()

    if not email_configure():
        return {
            "success": False,
            "message": (
                "Configuration email incomplète. "
                "L'email n'a pas été envoyé, mais l'action principale continue."
            )
        }

    message = MIMEMultipart()
    message["From"] = configuration["email_expediteur"]
    message["To"] = configuration["email_destinataire_documents"]
    message["Subject"] = sujet

    message.attach(MIMEText(contenu, "plain", "utf-8"))

    try:
        with smtplib.SMTP(
            configuration["smtp_host"],
            configuration["smtp_port"],
            timeout=20
        ) as serveur:
            serveur.starttls()
            serveur.login(
                configuration["smtp_username"],
                configuration["smtp_password"]
            )

            serveur.sendmail(
                configuration["email_expediteur"],
                configuration["email_destinataire_documents"],
                message.as_string()
            )

        return {
            "success": True,
            "message": "Email de notification envoyé avec succès."
        }

    except Exception as erreur:
        print("Erreur envoi email notification document :", erreur)

        return {
            "success": False,
            "message": (
                "Erreur lors de l'envoi de l'email de notification. "
                "Le document reste bien déposé."
            ),
            "erreur": str(erreur)
        }


def notifier_depot_document_signe(details_document):
    total_documents = compter_documents_en_attente()

    sujet, contenu = construire_message_document_depose(
        details_document,
        total_documents
    )

    resultat_email = envoyer_email(sujet, contenu)

    return {
        "success": resultat_email["success"],
        "message": resultat_email["message"],
        "total_documents_en_attente": total_documents
    }
