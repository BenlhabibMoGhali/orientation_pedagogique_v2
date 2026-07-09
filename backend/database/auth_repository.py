from datetime import datetime, timedelta
import re
import secrets

from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db_connection


def nettoyer_texte(valeur):
    if valeur is None:
        return ""

    return str(valeur).strip()


def nettoyer_email(email):
    return nettoyer_texte(email).lower()


def nettoyer_id_universitaire(id_universitaire):
    return nettoyer_texte(id_universitaire).upper()


def email_valide(email):
    if email == "":
        return False

    pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(pattern, email) is not None


def mot_de_passe_valide(mot_de_passe):
    if mot_de_passe is None:
        return False

    return len(mot_de_passe) >= 6


def verifier_identifiant_existe(cursor, identifiant_connexion):
    cursor.execute(
        """
        SELECT id
        FROM utilisateurs
        WHERE identifiant_connexion = %s
        """,
        (identifiant_connexion,)
    )

    return cursor.fetchone() is not None


def verifier_id_universitaire_existe(cursor, id_universitaire):
    cursor.execute(
        """
        SELECT id
        FROM etudiants
        WHERE id_universitaire = %s
        """,
        (id_universitaire,)
    )

    return cursor.fetchone() is not None


def verifier_email_etudiant_existe(cursor, email):
    cursor.execute(
        """
        SELECT id
        FROM etudiants
        WHERE email = %s
        """,
        (email,)
    )

    return cursor.fetchone() is not None


def creer_etudiant(
    nom,
    prenom,
    id_universitaire,
    email,
    mot_de_passe,
    confirmation_mot_de_passe,
    promotion=None
):
    nom = nettoyer_texte(nom)
    prenom = nettoyer_texte(prenom)
    id_universitaire = nettoyer_id_universitaire(id_universitaire)
    email = nettoyer_email(email)
    promotion = nettoyer_texte(promotion)

    if nom == "":
        return {
            "success": False,
            "message": "Le nom est obligatoire."
        }

    if prenom == "":
        return {
            "success": False,
            "message": "Le prénom est obligatoire."
        }

    if id_universitaire == "":
        return {
            "success": False,
            "message": "L'ID universitaire est obligatoire."
        }

    if email == "":
        return {
            "success": False,
            "message": "L'email Outlook universitaire est obligatoire."
        }

    if not email_valide(email):
        return {
            "success": False,
            "message": "L'email saisi n'est pas valide."
        }

    if not mot_de_passe_valide(mot_de_passe):
        return {
            "success": False,
            "message": "Le mot de passe doit contenir au moins 6 caractères."
        }

    if mot_de_passe != confirmation_mot_de_passe:
        return {
            "success": False,
            "message": "La confirmation du mot de passe ne correspond pas."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base de données impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        if verifier_identifiant_existe(cursor, id_universitaire):
            return {
                "success": False,
                "message": "Cet ID universitaire est déjà utilisé comme identifiant."
            }

        if verifier_id_universitaire_existe(cursor, id_universitaire):
            return {
                "success": False,
                "message": "Cet ID universitaire existe déjà."
            }

        if verifier_email_etudiant_existe(cursor, email):
            return {
                "success": False,
                "message": "Cet email Outlook est déjà utilisé."
            }

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        cursor.execute(
            """
            INSERT INTO utilisateurs
            (identifiant_connexion, mot_de_passe_hash, role, actif)
            VALUES (%s, %s, 'etudiant', TRUE)
            """,
            (
                id_universitaire,
                mot_de_passe_hash
            )
        )

        utilisateur_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO etudiants
            (utilisateur_id, id_universitaire, nom, prenom, email, promotion)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                utilisateur_id,
                id_universitaire,
                nom,
                prenom,
                email,
                promotion
            )
        )

        etudiant_id = cursor.lastrowid

        connection.commit()

        return {
            "success": True,
            "message": "Compte étudiant créé avec succès.",
            "utilisateur_id": utilisateur_id,
            "etudiant_id": etudiant_id,
            "identifiant_connexion": id_universitaire
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": f"Erreur lors de la création du compte étudiant : {str(e)}"
        }

    finally:
        cursor.close()
        connection.close()


def creer_doyen(
    identifiant_connexion,
    mot_de_passe,
    nom,
    prenom,
    email
):
    identifiant_connexion = nettoyer_texte(identifiant_connexion)
    nom = nettoyer_texte(nom)
    prenom = nettoyer_texte(prenom)
    email = nettoyer_email(email)

    if identifiant_connexion == "":
        return {
            "success": False,
            "message": "L'identifiant du doyen est obligatoire."
        }

    if nom == "":
        return {
            "success": False,
            "message": "Le nom du doyen est obligatoire."
        }

    if prenom == "":
        return {
            "success": False,
            "message": "Le prénom du doyen est obligatoire."
        }

    if not email_valide(email):
        return {
            "success": False,
            "message": "L'email du doyen n'est pas valide."
        }

    if not mot_de_passe_valide(mot_de_passe):
        return {
            "success": False,
            "message": "Le mot de passe doit contenir au moins 6 caractères."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base de données impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        if verifier_identifiant_existe(cursor, identifiant_connexion):
            return {
                "success": False,
                "message": "Cet identifiant est déjà utilisé."
            }

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        cursor.execute(
            """
            INSERT INTO utilisateurs
            (identifiant_connexion, mot_de_passe_hash, role, actif)
            VALUES (%s, %s, 'doyen', TRUE)
            """,
            (
                identifiant_connexion,
                mot_de_passe_hash
            )
        )

        utilisateur_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO doyens
            (utilisateur_id, nom, prenom, email)
            VALUES (%s, %s, %s, %s)
            """,
            (
                utilisateur_id,
                nom,
                prenom,
                email
            )
        )

        doyen_id = cursor.lastrowid

        connection.commit()

        return {
            "success": True,
            "message": "Compte doyen créé avec succès.",
            "utilisateur_id": utilisateur_id,
            "doyen_id": doyen_id
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": f"Erreur lors de la création du compte doyen : {str(e)}"
        }

    finally:
        cursor.close()
        connection.close()


def verifier_connexion(identifiant_connexion, mot_de_passe):
    identifiant_connexion = nettoyer_texte(identifiant_connexion)

    if identifiant_connexion == "":
        return {
            "success": False,
            "message": "Identifiant obligatoire."
        }

    if mot_de_passe is None or mot_de_passe == "":
        return {
            "success": False,
            "message": "Mot de passe obligatoire."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base de données impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, identifiant_connexion, mot_de_passe_hash, role, actif
            FROM utilisateurs
            WHERE identifiant_connexion = %s
            """,
            (identifiant_connexion,)
        )

        utilisateur = cursor.fetchone()

        if utilisateur is None:
            return {
                "success": False,
                "message": "Identifiant ou mot de passe incorrect."
            }

        if not utilisateur["actif"]:
            return {
                "success": False,
                "message": "Ce compte est désactivé."
            }

        mot_de_passe_correct = check_password_hash(
            utilisateur["mot_de_passe_hash"],
            mot_de_passe
        )

        if not mot_de_passe_correct:
            return {
                "success": False,
                "message": "Identifiant ou mot de passe incorrect."
            }

        profil = None

        if utilisateur["role"] == "etudiant":
            cursor.execute(
                """
                SELECT id, id_universitaire, nom, prenom, email, promotion
                FROM etudiants
                WHERE utilisateur_id = %s
                """,
                (utilisateur["id"],)
            )

            profil = cursor.fetchone()

        elif utilisateur["role"] == "doyen":
            cursor.execute(
                """
                SELECT id, nom, prenom, email
                FROM doyens
                WHERE utilisateur_id = %s
                """,
                (utilisateur["id"],)
            )

            profil = cursor.fetchone()

        return {
            "success": True,
            "message": "Connexion réussie.",
            "utilisateur": {
                "id": utilisateur["id"],
                "identifiant": utilisateur["identifiant_connexion"],
                "role": utilisateur["role"],
                "profil": profil
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de la connexion : {str(e)}"
        }

    finally:
        cursor.close()
        connection.close()


def demander_reinitialisation_mot_de_passe(identifiant_ou_email):
    identifiant_ou_email = nettoyer_texte(identifiant_ou_email)
    email_normalise = nettoyer_email(identifiant_ou_email)

    if identifiant_ou_email == "":
        return {
            "success": False,
            "message": "Veuillez saisir votre ID universitaire ou votre email."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base de données impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                u.id AS utilisateur_id,
                u.identifiant_connexion,
                u.role,
                e.email AS email_etudiant,
                d.email AS email_doyen
            FROM utilisateurs u
            LEFT JOIN etudiants e ON e.utilisateur_id = u.id
            LEFT JOIN doyens d ON d.utilisateur_id = u.id
            WHERE u.identifiant_connexion = %s
               OR e.email = %s
               OR d.email = %s
            LIMIT 1
            """,
            (
                identifiant_ou_email,
                email_normalise,
                email_normalise
            )
        )

        utilisateur = cursor.fetchone()

        if utilisateur is None:
            return {
                "success": False,
                "message": "Aucun compte ne correspond à ces informations."
            }

        token = secrets.token_urlsafe(32)
        date_expiration = datetime.now() + timedelta(minutes=30)

        cursor.execute(
            """
            INSERT INTO reinitialisations_mots_de_passe
            (utilisateur_id, token, date_expiration, utilise)
            VALUES (%s, %s, %s, FALSE)
            """,
            (
                utilisateur["utilisateur_id"],
                token,
                date_expiration
            )
        )

        connection.commit()

        email_destination = utilisateur["email_etudiant"]

        if email_destination is None:
            email_destination = utilisateur["email_doyen"]

        return {
            "success": True,
            "message": "Demande de réinitialisation créée. En version finale, un email sera envoyé.",
            "email_destination": email_destination,
            "token_demo": token,
            "expiration_minutes": 30
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": f"Erreur lors de la demande de réinitialisation : {str(e)}"
        }

    finally:
        cursor.close()
        connection.close()


def reinitialiser_mot_de_passe(
    token,
    nouveau_mot_de_passe,
    confirmation_mot_de_passe
):
    token = nettoyer_texte(token)

    if token == "":
        return {
            "success": False,
            "message": "Token obligatoire."
        }

    if not mot_de_passe_valide(nouveau_mot_de_passe):
        return {
            "success": False,
            "message": "Le nouveau mot de passe doit contenir au moins 6 caractères."
        }

    if nouveau_mot_de_passe != confirmation_mot_de_passe:
        return {
            "success": False,
            "message": "La confirmation du mot de passe ne correspond pas."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base de données impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, utilisateur_id, date_expiration, utilise
            FROM reinitialisations_mots_de_passe
            WHERE token = %s
            LIMIT 1
            """,
            (token,)
        )

        demande = cursor.fetchone()

        if demande is None:
            return {
                "success": False,
                "message": "Token invalide."
            }

        if demande["utilise"]:
            return {
                "success": False,
                "message": "Ce lien de réinitialisation a déjà été utilisé."
            }

        if demande["date_expiration"] < datetime.now():
            return {
                "success": False,
                "message": "Ce lien de réinitialisation a expiré."
            }

        nouveau_hash = generate_password_hash(nouveau_mot_de_passe)

        cursor.execute(
            """
            UPDATE utilisateurs
            SET mot_de_passe_hash = %s
            WHERE id = %s
            """,
            (
                nouveau_hash,
                demande["utilisateur_id"]
            )
        )

        cursor.execute(
            """
            UPDATE reinitialisations_mots_de_passe
            SET utilise = TRUE
            WHERE id = %s
            """,
            (demande["id"],)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Mot de passe réinitialisé avec succès."
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": f"Erreur lors de la réinitialisation : {str(e)}"
        }

    finally:
        cursor.close()
        connection.close()