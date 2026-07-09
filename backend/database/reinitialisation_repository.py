import os
import random
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from database.db import get_db_connection


def verifier_mot_de_passe_doyen(utilisateur_id, mot_de_passe):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT mot_de_passe_hash, role, actif
            FROM utilisateurs
            WHERE id = %s
            """,
            (utilisateur_id,)
        )

        utilisateur = cursor.fetchone()

        if utilisateur is None:
            return False

        if utilisateur["role"] != "doyen" or utilisateur["actif"] != 1:
            return False

        return check_password_hash(
            utilisateur["mot_de_passe_hash"],
            mot_de_passe
        )

    finally:
        cursor.close()
        connection.close()


def get_resume_reinitialisation_annuelle(annee_universitaire):
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
            SELECT COUNT(*) AS total_etudiants
            FROM etudiants
            WHERE promotion = %s
            """,
            (annee_universitaire,)
        )

        total_etudiants = cursor.fetchone()["total_etudiants"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total_tests
            FROM tests_orientation t
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_tests = cursor.fetchone()["total_tests"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total_fiches
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_fiches = cursor.fetchone()["total_fiches"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total_choix
            FROM choix_finaux_orientation cfo
            JOIN etudiants e ON cfo.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_choix = cursor.fetchone()["total_choix"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total_documents
            FROM documents_choix_final d
            JOIN etudiants e ON d.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_documents = cursor.fetchone()["total_documents"]

        cursor.execute(
            """
            SELECT
                s.nom AS specialite,
                COUNT(cfo.id) AS total_confirmes
            FROM specialites s
            LEFT JOIN choix_finaux_orientation cfo
                ON cfo.specialite_id = s.id
               AND cfo.statut_choix = 'choix_confirme'
            LEFT JOIN etudiants e
                ON cfo.etudiant_id = e.id
               AND e.promotion = %s
            GROUP BY s.id, s.nom
            ORDER BY s.nom
            """,
            (annee_universitaire,)
        )

        repartition = cursor.fetchall()

        return {
            "success": True,
            "annee_universitaire": annee_universitaire,
            "phrase_attendue": f"SUPPRIMER LES ETUDIANTS {annee_universitaire}",
            "resume": {
                "total_etudiants": total_etudiants,
                "total_tests": total_tests,
                "total_fiches": total_fiches,
                "total_choix": total_choix,
                "total_documents": total_documents,
                "repartition_confirmes": repartition
            }
        }

    finally:
        cursor.close()
        connection.close()


def creer_demande_reinitialisation(
    utilisateur_id,
    annee_universitaire,
    mot_de_passe,
    phrase_securite
):
    phrase_attendue = f"SUPPRIMER LES ETUDIANTS {annee_universitaire}"

    if phrase_securite != phrase_attendue:
        return {
            "success": False,
            "message": "La phrase de sécurité est incorrecte."
        }

    if not verifier_mot_de_passe_doyen(utilisateur_id, mot_de_passe):
        return {
            "success": False,
            "message": "Mot de passe du doyen incorrect."
        }

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    verification_documents = verifier_aucun_document_en_attente(
        connection,
        annee_universitaire
    )

    if not verification_documents.get("success"):
        connection.close()
        return verification_documents

    code_confirmation = str(random.randint(100000, 999999))
    date_expiration = datetime.now() + timedelta(minutes=10)

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        verification_documents = verifier_aucun_document_en_attente(
            connection,
            annee_universitaire
        )

        if not verification_documents.get("success"):
            return verification_documents

        cursor.execute(
            """
            INSERT INTO reinitialisations_annuelles
            (utilisateur_id, annee_universitaire, phrase_securite,
             code_confirmation, statut, date_expiration)
            VALUES (%s, %s, %s, %s, 'en_attente', %s)
            """,
            (
                utilisateur_id,
                annee_universitaire,
                phrase_securite,
                code_confirmation,
                date_expiration
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": (
                "Code de confirmation généré. Pour la démonstration, "
                "le code est affiché directement."
            ),
            "reinitialisation_id": cursor.lastrowid,
            "code_demo": code_confirmation,
            "expiration_minutes": 10
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        cursor.close()
        connection.close()


def supprimer_fichier_si_existe(chemin):
    try:
        if chemin and os.path.exists(chemin):
            os.remove(chemin)
    except Exception:
        pass


def compter_documents_en_attente_pour_annee(connection, annee_universitaire):
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total_documents_en_attente
            FROM documents_choix_final d
            JOIN etudiants e ON d.etudiant_id = e.id
            WHERE e.promotion = %s
              AND d.statut_document = 'en_attente_confirmation_doyen'
            """,
            (annee_universitaire,)
        )

        ligne = cursor.fetchone()
        return ligne["total_documents_en_attente"] if ligne else 0

    finally:
        cursor.close()


def verifier_aucun_document_en_attente(connection, annee_universitaire):
    total = compter_documents_en_attente_pour_annee(
        connection,
        annee_universitaire
    )

    if total > 0:
        return {
            "success": False,
            "message": (
                "Réinitialisation impossible : il reste "
                f"{total} document(s) signé(s) en attente de vérification par le doyen. "
                "Veuillez d’abord confirmer ou refuser tous les documents en attente."
            ),
            "documents_en_attente": total
        }

    return {
        "success": True,
        "documents_en_attente": 0
    }


def executer_reinitialisation_annuelle(
    utilisateur_id,
    reinitialisation_id,
    code_confirmation
):
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
            FROM reinitialisations_annuelles
            WHERE id = %s
              AND utilisateur_id = %s
              AND statut = 'en_attente'
            """,
            (reinitialisation_id, utilisateur_id)
        )

        demande = cursor.fetchone()

        if demande is None:
            return {
                "success": False,
                "message": "Demande de réinitialisation introuvable ou déjà utilisée."
            }

        if demande["code_confirmation"] != code_confirmation:
            return {
                "success": False,
                "message": "Code de confirmation incorrect."
            }

        if datetime.now() > demande["date_expiration"]:
            return {
                "success": False,
                "message": "Le code de confirmation a expiré."
            }

        annee_universitaire = demande["annee_universitaire"]

        verification_documents = verifier_aucun_document_en_attente(
            connection,
            annee_universitaire
        )

        if not verification_documents.get("success"):
            return verification_documents

        cursor.execute(
            """
            SELECT id, utilisateur_id
            FROM etudiants
            WHERE promotion = %s
            """,
            (annee_universitaire,)
        )

        etudiants = cursor.fetchall()

        etudiant_ids = [etudiant["id"] for etudiant in etudiants]
        utilisateur_ids = [etudiant["utilisateur_id"] for etudiant in etudiants]

        if len(etudiant_ids) == 0:
            cursor.execute(
                """
                UPDATE reinitialisations_annuelles
                SET statut = 'executee',
                    date_execution = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (reinitialisation_id,)
            )

            connection.commit()

            return {
                "success": True,
                "message": "Aucun étudiant trouvé pour cette année.",
                "total_supprimes": 0
            }

        placeholders_etudiants = ",".join(["%s"] * len(etudiant_ids))
        placeholders_utilisateurs = ",".join(["%s"] * len(utilisateur_ids))

        cursor.execute(
            f"""
            SELECT chemin_fichier
            FROM documents_choix_final
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        documents = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT pdf_engagement_path
            FROM choix_finaux_orientation
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        fiches_pdf = cursor.fetchall()

        for document in documents:
            supprimer_fichier_si_existe(document.get("chemin_fichier"))

        for fiche_pdf in fiches_pdf:
            supprimer_fichier_si_existe(fiche_pdf.get("pdf_engagement_path"))

        cursor.execute(
            f"""
            DELETE FROM messages_chat_orientation
            WHERE session_chat_id IN (
                SELECT id
                FROM sessions_chat_orientation
                WHERE etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM sessions_chat_orientation
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM documents_choix_final
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM choix_finaux_orientation
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM validations
            WHERE fiche_id IN (
                SELECT fi.id
                FROM fiches_intelligentes fi
                JOIN tests_orientation t ON fi.test_orientation_id = t.id
                WHERE t.etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM historique_orientations
            WHERE fiche_id IN (
                SELECT fi.id
                FROM fiches_intelligentes fi
                JOIN tests_orientation t ON fi.test_orientation_id = t.id
                WHERE t.etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM fiches_intelligentes
            WHERE test_orientation_id IN (
                SELECT id
                FROM tests_orientation
                WHERE etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM scores_orientation
            WHERE test_orientation_id IN (
                SELECT id
                FROM tests_orientation
                WHERE etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM reponses_etudiants
            WHERE test_orientation_id IN (
                SELECT id
                FROM tests_orientation
                WHERE etudiant_id IN ({placeholders_etudiants})
            )
            """,
            etudiant_ids
        )

        try:
            cursor.execute(
                f"""
                DELETE FROM analyses_reponses_libres
                WHERE test_orientation_id IN (
                    SELECT id
                    FROM tests_orientation
                    WHERE etudiant_id IN ({placeholders_etudiants})
                )
                """,
                etudiant_ids
            )
        except Exception:
            pass

        cursor.execute(
            f"""
            DELETE FROM tests_orientation
            WHERE etudiant_id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM reinitialisations_mots_de_passe
            WHERE utilisateur_id IN ({placeholders_utilisateurs})
            """,
            utilisateur_ids
        )

        cursor.execute(
            f"""
            DELETE FROM etudiants
            WHERE id IN ({placeholders_etudiants})
            """,
            etudiant_ids
        )

        cursor.execute(
            f"""
            DELETE FROM utilisateurs
            WHERE id IN ({placeholders_utilisateurs})
              AND role = 'etudiant'
            """,
            utilisateur_ids
        )

        cursor.execute(
            """
            UPDATE reinitialisations_annuelles
            SET statut = 'executee',
                date_execution = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (reinitialisation_id,)
        )

        cursor.execute(
            """
            INSERT INTO historique_admin
            (utilisateur_id, action, description)
            VALUES (%s, 'reinitialisation_annuelle', %s)
            """,
            (
                utilisateur_id,
                f"Réinitialisation annuelle exécutée pour l'année {annee_universitaire}. "
                f"{len(etudiant_ids)} étudiant(s) supprimé(s)."
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": (
                f"Réinitialisation annuelle terminée. "
                f"{len(etudiant_ids)} étudiant(s) supprimé(s)."
            ),
            "total_supprimes": len(etudiant_ids)
        }

    except Exception as e:
        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        cursor.close()
        connection.close()