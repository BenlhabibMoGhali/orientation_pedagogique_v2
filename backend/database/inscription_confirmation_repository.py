import random
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db_connection


DUREE_CODE_MINUTES = 10


def nettoyer_confirmations_expirees():
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            DELETE FROM confirmations_inscription_email
            WHERE date_expiration < CURRENT_TIMESTAMP
               OR utilise = 1
            """
        )
        connection.commit()
        return True

    except Exception:
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()


def etudiant_deja_existant(id_universitaire, email):
    connection = get_db_connection()

    if connection is None:
        return True

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM etudiants
            WHERE id_universitaire = %s
               OR email = %s
            LIMIT 1
            """,
            (id_universitaire, email)
        )

        return cursor.fetchone() is not None

    finally:
        cursor.close()
        connection.close()


def creer_confirmation_inscription_email(
    nom,
    prenom,
    id_universitaire,
    email,
    annee_universitaire
):
    nettoyer_confirmations_expirees()

    if etudiant_deja_existant(id_universitaire, email):
        return {
            "success": False,
            "message": (
                "Un compte étudiant existe déjà avec cet ID universitaire "
                "ou cet email."
            )
        }

    code = str(random.randint(100000, 999999))
    code_hash = generate_password_hash(code)
    date_expiration = datetime.now() + timedelta(minutes=DUREE_CODE_MINUTES)

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            DELETE FROM confirmations_inscription_email
            WHERE id_universitaire = %s
               OR email = %s
            """,
            (id_universitaire, email)
        )

        cursor.execute(
            """
            INSERT INTO confirmations_inscription_email
            (nom, prenom, id_universitaire, email, annee_universitaire,
             code_hash, date_expiration, utilise)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (
                nom,
                prenom,
                id_universitaire,
                email,
                annee_universitaire,
                code_hash,
                date_expiration
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Code de confirmation généré.",
            "code": code,
            "expiration_minutes": DUREE_CODE_MINUTES
        }

    except Exception as erreur:
        connection.rollback()
        return {
            "success": False,
            "message": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()


def verifier_code_confirmation_inscription(id_universitaire, email, code):
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM confirmations_inscription_email
            WHERE id_universitaire = %s
              AND email = %s
              AND utilise = 0
            ORDER BY date_creation DESC, id DESC
            LIMIT 1
            """,
            (id_universitaire, email)
        )

        confirmation = cursor.fetchone()

        if confirmation is None:
            return {
                "success": False,
                "message": (
                    "Aucun code de confirmation actif n’a été trouvé. "
                    "Veuillez demander un nouveau code."
                )
            }

        if datetime.now() > confirmation["date_expiration"]:
            return {
                "success": False,
                "message": "Le code de confirmation a expiré."
            }

        if not check_password_hash(confirmation["code_hash"], str(code).strip()):
            return {
                "success": False,
                "message": "Code de confirmation incorrect."
            }

        return {
            "success": True,
            "confirmation": confirmation
        }

    finally:
        cursor.close()
        connection.close()


def marquer_confirmation_inscription_utilisee(confirmation_id):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE confirmations_inscription_email
            SET utilise = 1,
                date_utilisation = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (confirmation_id,)
        )

        connection.commit()
        return True

    except Exception:
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()
