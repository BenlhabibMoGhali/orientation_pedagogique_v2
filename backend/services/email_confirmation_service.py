import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_configuration_email_confirmation():
    return {
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "email_expediteur": os.getenv("EMAIL_EXPEDITEUR", "")
    }


def email_confirmation_configure():
    configuration = get_configuration_email_confirmation()

    champs_obligatoires = [
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "email_expediteur"
    ]

    for champ in champs_obligatoires:
        if configuration.get(champ) is None or configuration.get(champ) == "":
            return False

    return True


def envoyer_email_confirmation_inscription(
    email_destinataire,
    nom,
    prenom,
    id_universitaire,
    code,
    expiration_minutes=10
):
    if not email_confirmation_configure():
        return {
            "success": False,
            "message": (
                "Configuration email incomplète. Impossible d’envoyer "
                "le code de confirmation d’identité."
            )
        }

    configuration = get_configuration_email_confirmation()

    sujet = "Code de confirmation - Inscription orientation pédagogique"

    contenu = f"""
Bonjour {prenom} {nom},

Une demande d’inscription vient d’être effectuée sur la plateforme d’orientation pédagogique avec votre ID universitaire : {id_universitaire}.

Pour confirmer que vous êtes bien l’étudiant concerné, veuillez saisir le code suivant dans la plateforme :

{code}

Ce code est valable pendant {expiration_minutes} minutes.

Si vous n’êtes pas à l’origine de cette demande, ignorez simplement cet email.

Cordialement,
Plateforme d’orientation pédagogique
"""

    message = MIMEMultipart()
    message["From"] = configuration["email_expediteur"]
    message["To"] = email_destinataire
    message["Subject"] = sujet
    message.attach(MIMEText(contenu, "plain", "utf-8"))

    try:
        serveur = smtplib.SMTP(
            configuration["smtp_host"],
            configuration["smtp_port"]
        )
        serveur.starttls()
        serveur.login(
            configuration["smtp_username"],
            configuration["smtp_password"]
        )
        serveur.sendmail(
            configuration["email_expediteur"],
            email_destinataire,
            message.as_string()
        )
        serveur.quit()

        return {
            "success": True,
            "message": "Code de confirmation envoyé à l’email Outlook de l’étudiant."
        }

    except Exception as erreur:
        print("Erreur envoi email confirmation inscription :", erreur)

        return {
            "success": False,
            "message": "Erreur lors de l’envoi du code de confirmation.",
            "erreur": str(erreur)
        }
