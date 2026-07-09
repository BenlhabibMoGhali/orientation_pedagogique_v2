import csv
import json
import os
import re
import shutil
from io import StringIO
from datetime import datetime

from database.db import get_db_connection
from services.annee_universitaire_service import get_code_annee_universitaire_active


def json_to_text(data):
    return json.dumps(data, ensure_ascii=False)


def text_to_json(texte, valeur_defaut):
    if texte is None or texte == "":
        return valeur_defaut

    try:
        return json.loads(texte)
    except Exception:
        return valeur_defaut


def creer_session_chat(etudiant_id, raison_droit, scores_initials):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO sessions_chat_orientation
            (etudiant_id, statut, raison_droit, index_question, scores_json, reponses_json)
            VALUES (%s, 'en_cours', %s, 0, %s, %s)
            """,
            (
                etudiant_id,
                raison_droit,
                json_to_text(scores_initials),
                json_to_text([])
            )
        )

        connection.commit()
        return cursor.lastrowid

    except Exception as e:
        connection.rollback()
        print("Erreur création session chat :", e)
        return None

    finally:
        cursor.close()
        connection.close()


def get_session_chat(session_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM sessions_chat_orientation
            WHERE id = %s
            """,
            (session_id,)
        )

        session = cursor.fetchone()

        if session is None:
            return None

        session["scores"] = text_to_json(session.get("scores_json"), {})
        session["reponses"] = text_to_json(session.get("reponses_json"), [])

        return session

    finally:
        cursor.close()
        connection.close()


def ajouter_message_chat(session_id, role_message, contenu):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO messages_chat_orientation
            (session_chat_id, role_message, contenu)
            VALUES (%s, %s, %s)
            """,
            (session_id, role_message, contenu)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur ajout message chat :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def mettre_a_jour_session_chat(session_id, index_question, scores, reponses):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE sessions_chat_orientation
            SET index_question = %s,
                scores_json = %s,
                reponses_json = %s
            WHERE id = %s
            """,
            (
                index_question,
                json_to_text(scores),
                json_to_text(reponses),
                session_id
            )
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur mise à jour session chat :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def terminer_session_chat(session_id, test_orientation_id, fiche_id):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE sessions_chat_orientation
            SET statut = 'termine',
                test_orientation_id = %s,
                fiche_id = %s
            WHERE id = %s
            """,
            (test_orientation_id, fiche_id, session_id)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur terminaison session chat :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def get_specialite_id_by_nom(nom_specialite):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM specialites
            WHERE nom = %s
            """,
            (nom_specialite,)
        )

        specialite = cursor.fetchone()

        if specialite is None:
            return None

        return specialite["id"]

    finally:
        cursor.close()
        connection.close()


def get_places_filiere(specialite_id):
    """
    Ancienne fonction conservée uniquement pour compatibilité technique.
    La plateforme ne gère plus les capacités ni les places disponibles par filière.
    """
    return {
        "gestion_places_active": False,
        "message": "La gestion des places par filière a été retirée du projet."
    }


def get_filieres_disponibles_pour_fiche(fiche_id):
    """
    Retourne les filières classées par score pour une fiche donnée, sans filtrage par capacité.
    """
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT test_orientation_id
            FROM fiches_intelligentes
            WHERE id = %s
            """,
            (fiche_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return []

        cursor.execute(
            """
            SELECT
                s.id AS specialite_id,
                s.nom AS specialite,
                so.pourcentage
            FROM scores_orientation so
            JOIN specialites s ON so.specialite_id = s.id
            WHERE so.test_orientation_id = %s
            ORDER BY so.pourcentage DESC
            """,
            (fiche["test_orientation_id"],)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

def get_choix_final_details(choix_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                cfo.id AS choix_id,
                cfo.fiche_id,
                cfo.etudiant_id,
                cfo.specialite_id,
                cfo.commentaire,
                cfo.statut_choix,
                cfo.pdf_engagement_path,
                cfo.annee_universitaire,
                e.nom,
                e.prenom,
                e.id_universitaire,
                e.email,
                s.nom AS filiere_choisie,
                d.id AS document_id,
                d.statut_document,
                d.nom_fichier_original AS dernier_document_nom,
                d.date_upload AS derniere_date_upload
            FROM choix_finaux_orientation cfo
            JOIN etudiants e ON cfo.etudiant_id = e.id
            JOIN specialites s ON cfo.specialite_id = s.id
            LEFT JOIN documents_choix_final d
                ON d.id = (
                    SELECT d2.id
                    FROM documents_choix_final d2
                    WHERE d2.choix_final_id = cfo.id
                    ORDER BY d2.date_upload DESC, d2.id DESC
                    LIMIT 1
                )
            WHERE cfo.id = %s
            """,
            (choix_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

def enregistrer_pdf_engagement_choix(choix_id, chemin_pdf):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE choix_finaux_orientation
            SET pdf_engagement_path = %s,
                date_generation_pdf = CURRENT_TIMESTAMP,
                statut_choix = 'fiche_generee'
            WHERE id = %s
            """,
            (chemin_pdf, choix_id)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur enregistrement PDF :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def enregistrer_choix_final_etudiant(
    fiche_id,
    etudiant_id,
    nom_specialite,
    commentaire=None
):
    specialite_id = get_specialite_id_by_nom(nom_specialite)

    if specialite_id is None:
        return {
            "success": False,
            "message": "Spécialité introuvable."
        }

    # La plateforme ne bloque pas le choix selon une capacité ou une organisation de classes.
    # Le doyen utilise ensuite les listes par filière pour gérer l’organisation hors système.

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
            FROM choix_finaux_orientation
            WHERE fiche_id = %s
            """,
            (fiche_id,)
        )

        choix_existant = cursor.fetchone()

        if choix_existant:
            statut_existant = choix_existant.get("statut_choix")

            if statut_existant in [
                "en_attente_confirmation_doyen",
                "choix_confirme"
            ]:
                return {
                    "success": False,
                    "message": (
                        "Ce choix final ne peut plus être modifié car il est "
                        "déjà en attente de validation ou confirmé."
                    )
                }

        cursor.execute(
            """
            INSERT INTO choix_finaux_orientation
            (fiche_id, etudiant_id, specialite_id, commentaire,
             annee_universitaire, statut_choix, date_choix)
            VALUES (%s, %s, %s, %s, %s, 'fiche_generee', CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                specialite_id = VALUES(specialite_id),
                commentaire = VALUES(commentaire),
                annee_universitaire = VALUES(annee_universitaire),
                statut_choix = 'fiche_generee',
                date_choix = CURRENT_TIMESTAMP
            """,
            (
                fiche_id,
                etudiant_id,
                specialite_id,
                commentaire,
                get_code_annee_universitaire_active()
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT id
            FROM choix_finaux_orientation
            WHERE fiche_id = %s
            """,
            (fiche_id,)
        )

        choix = cursor.fetchone()

        return {
            "success": True,
            "message": (
                "Choix enregistré. La fiche d’engagement peut maintenant "
                "être générée."
            ),
            "fiche_id": fiche_id,
            "choix_id": choix["id"],
            "specialite_choisie": nom_specialite,
            "statut_choix": "fiche_generee",
            "organisation_hors_plateforme": True
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


def verifier_document_upload(nom_fichier, taille_fichier):
    if nom_fichier is None or "." not in nom_fichier:
        return {
            "statut": "attention",
            "message": "Nom de fichier invalide."
        }

    extension = nom_fichier.rsplit(".", 1)[-1].lower()

    extensions_autorisees = ["pdf", "png", "jpg", "jpeg"]

    if extension not in extensions_autorisees:
        return {
            "statut": "attention",
            "message": "Type de fichier non autorisé. Formats acceptés : PDF, PNG, JPG, JPEG."
        }

    if taille_fichier <= 0:
        return {
            "statut": "attention",
            "message": "Le fichier est vide."
        }

    if taille_fichier < 10 * 1024:
        return {
            "statut": "attention",
            "message": "Le fichier semble trop petit ou incomplet."
        }

    taille_max = 10 * 1024 * 1024

    if taille_fichier > taille_max:
        return {
            "statut": "attention",
            "message": "Le fichier est trop volumineux. La taille maximale autorisée est de 10 Mo."
        }

    return {
        "statut": "ok",
        "message": (
            "Document reçu. Une vérification administrative par le doyen "
            "reste nécessaire."
        )
    }


def enregistrer_document_signe(
    choix_id,
    etudiant_id,
    nom_fichier_original,
    nom_fichier_stocke,
    chemin_fichier,
    type_fichier,
    taille_fichier
):
    verification = verifier_document_upload(
        nom_fichier_original,
        taille_fichier
    )

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
            INSERT INTO documents_choix_final
            (choix_final_id, etudiant_id, nom_fichier_original,
             nom_fichier_stocke, chemin_fichier, type_fichier,
             taille_fichier, statut_document, verification_auto_statut,
             verification_auto_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    'en_attente_confirmation_doyen', %s, %s)
            """,
            (
                choix_id,
                etudiant_id,
                nom_fichier_original,
                nom_fichier_stocke,
                chemin_fichier,
                type_fichier,
                taille_fichier,
                verification["statut"],
                verification["message"]
            )
        )

        cursor.execute(
            """
            UPDATE choix_finaux_orientation
            SET statut_choix = 'en_attente_confirmation_doyen'
            WHERE id = %s
            """,
            (choix_id,)
        )

        connection.commit()

        return {
            "success": True,
            "message": (
                "Document signé déposé avec succès. Il est maintenant "
                "en attente de confirmation par le doyen."
            ),
            "verification_auto": verification
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


def get_document_info(document_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM documents_choix_final
            WHERE id = %s
            """,
            (document_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def normaliser_nom_archive(valeur):
    texte = str(valeur or "").strip()
    texte = texte.replace("/", "_").replace("\\", "_")
    texte = re.sub(r"[^0-9A-Za-zÀ-ÿ _.-]", "", texte)
    texte = texte.strip().replace(" ", "_")

    if texte == "":
        return "non_defini"

    return texte


def get_dossier_archives_backend():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(backend_dir, "archives")


def get_dossier_archives_fiches_engagement():
    dossier_env = os.getenv("DOSSIER_ARCHIVES_FICHES_ENGAGEMENT", "").strip()

    if dossier_env:
        return dossier_env

    return os.path.join(
        get_dossier_archives_backend(),
        "fiches_engagement_validees"
    )


def get_dossier_archives_exports_excel():
    dossier_env = os.getenv("DOSSIER_ARCHIVES_EXPORTS_EXCEL", "").strip()

    if dossier_env:
        return dossier_env

    return os.path.join(
        get_dossier_archives_backend(),
        "exports_excel"
    )


def archiver_document_signe_valide(cursor, choix_id, document_en_attente):
    cursor.execute(
        """
        SELECT
            cfo.id AS choix_id,
            cfo.annee_universitaire,
            e.id AS etudiant_id,
            e.id_universitaire,
            e.nom,
            e.prenom,
            e.email,
            s.nom AS filiere_choisie
        FROM choix_finaux_orientation cfo
        JOIN etudiants e ON cfo.etudiant_id = e.id
        JOIN specialites s ON cfo.specialite_id = s.id
        WHERE cfo.id = %s
        """,
        (choix_id,)
    )

    details = cursor.fetchone()

    if details is None:
        return {
            "success": False,
            "message": "Choix final introuvable pour l’archivage."
        }

    chemin_source = document_en_attente.get("chemin_fichier")

    if not chemin_source or not os.path.exists(chemin_source):
        return {
            "success": False,
            "message": "Document signé introuvable pour l’archivage."
        }

    extension = os.path.splitext(
        document_en_attente.get("nom_fichier_original")
        or document_en_attente.get("nom_fichier_stocke")
        or chemin_source
    )[1].lower()

    if extension == "":
        extension = ".pdf"

    dossier_annee = normaliser_nom_archive(details.get("annee_universitaire"))
    dossier_filiere = normaliser_nom_archive(details.get("filiere_choisie"))
    matricule = normaliser_nom_archive(details.get("id_universitaire"))

    dossier_destination = os.path.join(
        get_dossier_archives_fiches_engagement(),
        dossier_annee,
        dossier_filiere
    )

    os.makedirs(dossier_destination, exist_ok=True)

    nom_fichier_archive = f"{matricule}{extension}"
    chemin_destination = os.path.join(dossier_destination, nom_fichier_archive)

    shutil.copy2(chemin_source, chemin_destination)

    cursor.execute(
        """
        INSERT INTO archives_fiches_engagement
        (document_id, choix_final_id, etudiant_id, id_universitaire, nom,
         prenom, email_outlook, filiere_choisie, annee_universitaire,
         nom_fichier_archive, chemin_archive, type_fichier)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nom = VALUES(nom),
            prenom = VALUES(prenom),
            email_outlook = VALUES(email_outlook),
            filiere_choisie = VALUES(filiere_choisie),
            annee_universitaire = VALUES(annee_universitaire),
            nom_fichier_archive = VALUES(nom_fichier_archive),
            chemin_archive = VALUES(chemin_archive),
            type_fichier = VALUES(type_fichier),
            date_archivage = CURRENT_TIMESTAMP
        """,
        (
            document_en_attente.get("id"),
            choix_id,
            details.get("etudiant_id"),
            details.get("id_universitaire"),
            details.get("nom"),
            details.get("prenom"),
            details.get("email"),
            details.get("filiere_choisie"),
            details.get("annee_universitaire"),
            nom_fichier_archive,
            chemin_destination,
            document_en_attente.get("type_fichier") or "application/octet-stream"
        )
    )

    try:
        cursor.execute(
            """
            UPDATE documents_choix_final
            SET archive_document_valide_path = %s
            WHERE id = %s
            """,
            (chemin_destination, document_en_attente.get("id"))
        )
    except Exception:
        pass

    return {
        "success": True,
        "chemin_archive": chemin_destination,
        "nom_fichier_archive": nom_fichier_archive
    }


def enregistrer_archive_export_excel(annee_universitaire, nom_fichier, chemin_archive):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO archives_exports_excel
            (annee_universitaire, nom_fichier, chemin_archive)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                chemin_archive = VALUES(chemin_archive),
                date_generation = CURRENT_TIMESTAMP
            """,
            (annee_universitaire, nom_fichier, chemin_archive)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur enregistrement archive export Excel :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def lister_archives_administratives():
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
            SELECT
                id,
                id_universitaire,
                nom,
                prenom,
                email_outlook,
                filiere_choisie,
                annee_universitaire,
                nom_fichier_archive,
                date_archivage
            FROM archives_fiches_engagement
            ORDER BY date_archivage DESC, id DESC
            """
        )
        fiches = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                id,
                annee_universitaire,
                nom_fichier,
                date_generation
            FROM archives_exports_excel
            ORDER BY date_generation DESC, id DESC
            """
        )
        exports = cursor.fetchall()

        return {
            "success": True,
            "fiches": fiches,
            "exports": exports
        }

    finally:
        cursor.close()
        connection.close()


def get_archive_fiche_engagement(archive_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM archives_fiches_engagement
            WHERE id = %s
            """,
            (archive_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_archive_export_excel(archive_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM archives_exports_excel
            WHERE id = %s
            """,
            (archive_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def lister_documents_a_confirmer():
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                d.id AS document_id,
                d.choix_final_id,
                d.nom_fichier_original,
                d.type_fichier,
                d.taille_fichier,
                d.verification_auto_statut,
                d.verification_auto_message,
                d.date_upload,
                cfo.statut_choix,
                s.nom AS filiere_choisie,
                e.nom,
                e.prenom,
                e.id_universitaire
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            JOIN specialites s ON cfo.specialite_id = s.id
            JOIN etudiants e ON d.etudiant_id = e.id
            WHERE d.statut_document = 'en_attente_confirmation_doyen'
            ORDER BY d.date_upload ASC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def confirmer_ou_refuser_document(choix_id, doyen_id, decision, remarque=None):
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
            FROM choix_finaux_orientation
            WHERE id = %s
            """,
            (choix_id,)
        )

        choix = cursor.fetchone()

        if choix is None:
            return {
                "success": False,
                "message": "Choix final introuvable."
            }

        if decision not in ["confirmer", "refuser"]:
            return {
                "success": False,
                "message": "Décision invalide."
            }

        cursor.execute(
            """
            SELECT *
            FROM documents_choix_final
            WHERE choix_final_id = %s
              AND statut_document = 'en_attente_confirmation_doyen'
            ORDER BY date_upload DESC, id DESC
            LIMIT 1
            """,
            (choix_id,)
        )

        document_en_attente = cursor.fetchone()

        if document_en_attente is None:
            return {
                "success": False,
                "message": (
                    "Aucun document en attente de confirmation n’a été trouvé "
                    "pour ce choix final."
                )
            }

        if decision == "confirmer":
            # La confirmation du doyen est une validation administrative du document signé.
            # Elle ne réalise aucune réservation de place ni organisation de classe.

            cursor.execute(
                """
                UPDATE documents_choix_final
                SET statut_document = 'document_confirme',
                    remarque_doyen = %s,
                    date_decision_doyen = CURRENT_TIMESTAMP,
                    doyen_id = %s
                WHERE id = %s
                  AND statut_document = 'en_attente_confirmation_doyen'
                """,
                (remarque, doyen_id, document_en_attente["id"])
            )

            if cursor.rowcount == 0:
                connection.rollback()
                return {
                    "success": False,
                    "message": "Le document n’est plus en attente de confirmation."
                }

            cursor.execute(
                """
                UPDATE choix_finaux_orientation
                SET statut_choix = 'choix_confirme',
                    date_confirmation_doyen = CURRENT_TIMESTAMP,
                    doyen_confirmation_id = %s,
                    remarque_doyen = %s
                WHERE id = %s
                """,
                (doyen_id, remarque, choix_id)
            )

            archivage = archiver_document_signe_valide(
                cursor,
                choix_id,
                document_en_attente
            )

            if archivage.get("success"):
                message = (
                    "Document confirmé. Le choix de filière est maintenant "
                    "enregistré administrativement. Le document signé validé "
                    "a été archivé dans les archives administratives."
                )
            else:
                message = (
                    "Document confirmé. Le choix de filière est maintenant "
                    "enregistré administrativement. Attention : l’archivage "
                    f"du document signé n’a pas pu être réalisé : {archivage.get('message')}"
                )

        else:
            remarque = (remarque or "").strip()

            if remarque == "":
                return {
                    "success": False,
                    "message": "Une remarque est obligatoire pour refuser un document."
                }

            cursor.execute(
                """
                UPDATE documents_choix_final
                SET statut_document = 'document_refuse',
                    remarque_doyen = %s,
                    date_decision_doyen = CURRENT_TIMESTAMP,
                    doyen_id = %s
                WHERE id = %s
                  AND statut_document = 'en_attente_confirmation_doyen'
                """,
                (remarque, doyen_id, document_en_attente["id"])
            )

            if cursor.rowcount == 0:
                connection.rollback()
                return {
                    "success": False,
                    "message": "Le document n’est plus en attente de confirmation."
                }

            cursor.execute(
                """
                UPDATE choix_finaux_orientation
                SET statut_choix = 'document_refuse',
                    remarque_doyen = %s
                WHERE id = %s
                """,
                (remarque, choix_id)
            )

            message = "Document refusé. L’étudiant devra déposer une fiche corrigée."

        connection.commit()

        return {
            "success": True,
            "message": message
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

def get_statistiques_places_filieres():
    """
    Retourne une répartition simple des choix par filière.
    Cette fonction ne gère aucune place, capacité ou classe.
    Elle conserve son nom technique pour compatibilité avec les anciennes routes.
    """
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        annee_universitaire = get_code_annee_universitaire_active()

        cursor.execute(
            """
            SELECT
                s.id AS specialite_id,
                s.nom AS specialite,
                COALESCE(COUNT(cfo.id), 0) AS total_choix,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'choix_confirme' THEN 1 ELSE 0 END), 0) AS documents_confirmes,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'en_attente_confirmation_doyen' THEN 1 ELSE 0 END), 0) AS documents_en_attente,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'document_refuse' THEN 1 ELSE 0 END), 0) AS documents_refuses,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'fiche_generee' THEN 1 ELSE 0 END), 0) AS fiches_engagement_generees
            FROM specialites s
            LEFT JOIN choix_finaux_orientation cfo
                ON cfo.specialite_id = s.id
               AND cfo.annee_universitaire = %s
            GROUP BY s.id, s.nom
            ORDER BY s.nom
            """,
            (annee_universitaire,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_etat_orientation_etudiant(utilisateur_id):
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
            SELECT
                id,
                utilisateur_id,
                id_universitaire,
                nom,
                prenom,
                email,
                promotion
            FROM etudiants
            WHERE utilisateur_id = %s
            """,
            (utilisateur_id,)
        )

        etudiant = cursor.fetchone()

        if etudiant is None:
            return {
                "success": False,
                "message": "Étudiant introuvable."
            }

        etudiant_id = etudiant["id"]

        cursor.execute(
            """
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.date_generation,
                s.nom AS specialite_recommandee
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            WHERE t.etudiant_id = %s
            ORDER BY fi.date_generation DESC, fi.id DESC
            LIMIT 1
            """,
            (etudiant_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return {
                "success": True,
                "a_passe_test": False,
                "message": "Aucun test d’orientation n’a encore été réalisé.",
                "etudiant": etudiant,
                "fiche": None,
                "scores": [],
                "choix_final": None,
                "document": None
            }

        cursor.execute(
            """
            SELECT
                s.nom AS specialite,
                so.score,
                so.pourcentage
            FROM scores_orientation so
            JOIN specialites s ON so.specialite_id = s.id
            WHERE so.test_orientation_id = %s
            ORDER BY so.pourcentage DESC
            """,
            (fiche["test_orientation_id"],)
        )

        scores = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                cfo.id AS choix_id,
                cfo.fiche_id,
                cfo.etudiant_id,
                cfo.specialite_id,
                cfo.commentaire,
                cfo.statut_choix,
                cfo.pdf_engagement_path,
                cfo.date_choix,
                cfo.date_confirmation_doyen,
                cfo.remarque_doyen,
                s.nom AS filiere_choisie
            FROM choix_finaux_orientation cfo
            JOIN specialites s ON cfo.specialite_id = s.id
            WHERE cfo.fiche_id = %s
            ORDER BY cfo.date_choix DESC, cfo.id DESC
            LIMIT 1
            """,
            (fiche["fiche_id"],)
        )

        choix_final = cursor.fetchone()

        document = None

        if choix_final is not None:
            choix_final["pdf_engagement_url"] = (
                f"/api/chat-orientation/choix-final/{choix_final['choix_id']}/pdf"
            )

            cursor.execute(
                """
                SELECT
                    id AS document_id,
                    choix_final_id,
                    etudiant_id,
                    nom_fichier_original,
                    nom_fichier_stocke,
                    chemin_fichier,
                    type_fichier,
                    taille_fichier,
                    statut_document,
                    verification_auto_statut,
                    verification_auto_message,
                    remarque_doyen,
                    date_upload,
                    date_decision_doyen
                FROM documents_choix_final
                WHERE choix_final_id = %s
                ORDER BY date_upload DESC, id DESC
                LIMIT 1
                """,
                (choix_final["choix_id"],)
            )

            document = cursor.fetchone()

        return {
            "success": True,
            "a_passe_test": True,
            "message": "État de l’étudiant chargé avec succès.",
            "etudiant": etudiant,
            "fiche": fiche,
            "scores": scores,
            "choix_final": choix_final,
            "document": document,
            "organisation_hors_plateforme": True
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        cursor.close()
        connection.close()

def _normaliser_valeur_export(valeur):
    if isinstance(valeur, datetime):
        return valeur.strftime("%d/%m/%Y %H:%M:%S")

    if type(valeur).__name__ == "Decimal":
        return float(valeur)

    return valeur


def _normaliser_ligne_export(ligne):
    if ligne is None:
        return None

    resultat = {}

    for cle, valeur in ligne.items():
        resultat[cle] = _normaliser_valeur_export(valeur)

    return resultat


def _normaliser_liste_export(lignes):
    return [_normaliser_ligne_export(ligne) for ligne in lignes]


def _formater_role_message(role_message):
    if role_message == "assistant":
        return "Chatbot"

    if role_message == "etudiant":
        return "Étudiant"

    if role_message == "user":
        return "Étudiant"

    if role_message == "bot":
        return "Chatbot"

    return role_message or "Message"


def _recuperer_date_message(message):
    return (
        message.get("date_creation")
        or message.get("date_message")
        or message.get("created_at")
        or message.get("date_envoi")
        or ""
    )


def get_discussion_chat_par_fiche(fiche_id):
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
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.date_generation,
                s.nom AS specialite_recommandee,
                e.id AS etudiant_id,
                e.id_universitaire,
                e.nom,
                e.prenom,
                e.email,
                e.promotion
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            WHERE fi.id = %s
            """,
            (fiche_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return {
                "success": False,
                "message": "Fiche intelligente introuvable."
            }

        cursor.execute(
            """
            SELECT
                s.nom AS specialite,
                so.score,
                so.pourcentage
            FROM scores_orientation so
            JOIN specialites s ON so.specialite_id = s.id
            WHERE so.test_orientation_id = %s
            ORDER BY so.pourcentage DESC
            """,
            (fiche["test_orientation_id"],)
        )

        scores = cursor.fetchall()

        cursor.execute(
            """
            SELECT *
            FROM sessions_chat_orientation
            WHERE fiche_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (fiche_id,)
        )

        session_chat = cursor.fetchone()

        if session_chat is None:
            cursor.execute(
                """
                SELECT *
                FROM sessions_chat_orientation
                WHERE test_orientation_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (fiche["test_orientation_id"],)
            )

            session_chat = cursor.fetchone()

        messages = []

        if session_chat is not None:
            cursor.execute(
                """
                SELECT *
                FROM messages_chat_orientation
                WHERE session_chat_id = %s
                ORDER BY id ASC
                """,
                (session_chat["id"],)
            )

            messages = cursor.fetchall()

        return {
            "success": True,
            "message": "Discussion récupérée avec succès.",
            "discussion_disponible": len(messages) > 0,
            "fiche": _normaliser_ligne_export(fiche),
            "session_chat": _normaliser_ligne_export(session_chat),
            "scores": _normaliser_liste_export(scores),
            "messages": _normaliser_liste_export(messages)
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        cursor.close()
        connection.close()


def get_discussion_chat_par_choix_final(choix_id):
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
            SELECT fiche_id
            FROM choix_finaux_orientation
            WHERE id = %s
            """,
            (choix_id,)
        )

        choix = cursor.fetchone()

        if choix is None:
            return {
                "success": False,
                "message": "Choix final introuvable."
            }

        return get_discussion_chat_par_fiche(choix["fiche_id"])

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        cursor.close()
        connection.close()


def generer_contenu_txt_discussion(fiche_id):
    resultat = get_discussion_chat_par_fiche(fiche_id)

    if not resultat.get("success"):
        return resultat

    fiche = resultat["fiche"]
    session_chat = resultat["session_chat"]
    scores = resultat["scores"]
    messages = resultat["messages"]

    lignes = []

    lignes.append("============================================================")
    lignes.append("TRACE DE DISCUSSION - CHATBOT D'ORIENTATION")
    lignes.append("============================================================")
    lignes.append("")

    lignes.append("INFORMATIONS ÉTUDIANT")
    lignes.append("------------------------------------------------------------")
    lignes.append(f"Nom complet          : {fiche.get('prenom', '')} {fiche.get('nom', '')}")
    lignes.append(f"ID universitaire     : {fiche.get('id_universitaire', '')}")
    lignes.append(f"Email                : {fiche.get('email', '')}")
    lignes.append(f"Promotion            : {fiche.get('promotion', '')}")
    lignes.append("")

    lignes.append("INFORMATIONS ORIENTATION")
    lignes.append("------------------------------------------------------------")
    lignes.append(f"Fiche ID             : {fiche.get('fiche_id', '')}")
    lignes.append(f"Test orientation ID  : {fiche.get('test_orientation_id', '')}")
    lignes.append(f"Spécialité proposée  : {fiche.get('specialite_recommandee', '')}")
    lignes.append(f"Date génération      : {fiche.get('date_generation', '')}")
    lignes.append("")

    lignes.append("SCORES PAR FILIÈRE")
    lignes.append("------------------------------------------------------------")

    if len(scores) == 0:
        lignes.append("Aucun score enregistré.")
    else:
        for score in scores:
            lignes.append(
                f"{score.get('specialite', '')} : "
                f"{score.get('pourcentage', '')}% "
                f"(score : {score.get('score', '')})"
            )

    lignes.append("")

    lignes.append("SESSION CHAT")
    lignes.append("------------------------------------------------------------")

    if session_chat is None:
        lignes.append("Aucune session chat trouvée pour cette fiche.")
    else:
        lignes.append(f"Session ID           : {session_chat.get('id', '')}")
        lignes.append(f"Statut session       : {session_chat.get('statut', '')}")
        lignes.append(f"Raison droit         : {session_chat.get('raison_droit', '')}")

    lignes.append("")

    lignes.append("DISCUSSION COMPLÈTE")
    lignes.append("------------------------------------------------------------")

    if len(messages) == 0:
        lignes.append("Aucun message enregistré pour cette discussion.")
    else:
        for index, message in enumerate(messages, start=1):
            role = _formater_role_message(message.get("role_message"))
            date_message = _recuperer_date_message(message)
            contenu = message.get("contenu") or ""

            lignes.append("")
            lignes.append(f"Message {index}")
            lignes.append(f"Rôle : {role}")

            if date_message:
                lignes.append(f"Date : {date_message}")

            lignes.append("Contenu :")
            lignes.append(str(contenu))

    lignes.append("")
    lignes.append("============================================================")
    lignes.append("FIN DE LA TRACE DE DISCUSSION")
    lignes.append("============================================================")

    nom_fichier = (
        f"discussion_chat_"
        f"{fiche.get('id_universitaire', 'etudiant')}_"
        f"fiche_{fiche_id}.txt"
    )

    return {
        "success": True,
        "message": "Contenu TXT généré avec succès.",
        "nom_fichier": nom_fichier,
        "contenu": "\n".join(lignes),
        "discussion": resultat
    }

def _get_colonnes_table(cursor, nom_table):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (nom_table,)
    )

    return {ligne["COLUMN_NAME"] for ligne in cursor.fetchall()}


def _table_existe(cursor, nom_table):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
        """,
        (nom_table,)
    )

    ligne = cursor.fetchone()

    return ligne is not None and ligne["total"] > 0


def _premiere_colonne_existante(colonnes, possibilites):
    for colonne in possibilites:
        if colonne in colonnes:
            return colonne

    return None


def _valeur_date(ligne, colonnes_possibles):
    for colonne in colonnes_possibles:
        if ligne and colonne in ligne and ligne.get(colonne):
            return ligne.get(colonne)

    return None


def _convertir_date_historique(valeur):
    if valeur is None:
        return None

    if isinstance(valeur, datetime):
        return valeur.strftime("%Y-%m-%d %H:%M:%S")

    return str(valeur)


def _ajouter_evenement_historique(
    evenements,
    type_evenement,
    titre,
    description,
    date_evenement=None,
    statut="information",
    details=None
):
    evenements.append({
        "type": type_evenement,
        "titre": titre,
        "description": description,
        "date": _convertir_date_historique(date_evenement),
        "statut": statut,
        "details": details or {}
    })


def _cle_tri_historique(evenement):
    date_evenement = evenement.get("date")

    if not date_evenement:
        return "9999-12-31 23:59:59"

    return str(date_evenement)


def get_historique_etudiant_par_fiche(fiche_id):
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
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.statut_validation,
                fi.remarque_doyen AS remarque_fiche_doyen,
                fi.date_generation,
                s.nom AS specialite_recommandee,
                e.id AS etudiant_id,
                e.utilisateur_id,
                e.id_universitaire,
                e.nom,
                e.prenom,
                e.email,
                e.promotion
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            WHERE fi.id = %s
            """,
            (fiche_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return {
                "success": False,
                "message": "Fiche introuvable."
            }

        etudiant_id = fiche["etudiant_id"]
        utilisateur_id = fiche["utilisateur_id"]
        test_orientation_id = fiche["test_orientation_id"]

        evenements = []

        colonnes_etudiants = _get_colonnes_table(cursor, "etudiants")
        colonne_date_etudiant = _premiere_colonne_existante(
            colonnes_etudiants,
            ["date_creation", "date_inscription", "created_at"]
        )

        date_inscription = None

        if colonne_date_etudiant:
            cursor.execute(
                f"""
                SELECT {colonne_date_etudiant} AS date_inscription
                FROM etudiants
                WHERE id = %s
                """,
                (etudiant_id,)
            )

            ligne_inscription = cursor.fetchone()
            date_inscription = ligne_inscription.get("date_inscription") if ligne_inscription else None

        _ajouter_evenement_historique(
            evenements,
            "inscription",
            "Inscription de l’étudiant",
            (
                f"{fiche.get('prenom', '')} {fiche.get('nom', '')} "
                f"a été inscrit dans la plateforme avec l’ID universitaire "
                f"{fiche.get('id_universitaire', '')}."
            ),
            date_inscription,
            "success",
            {
                "id_universitaire": fiche.get("id_universitaire"),
                "email": fiche.get("email"),
                "promotion": fiche.get("promotion")
            }
        )

        if _table_existe(cursor, "tests_orientation"):
            colonnes_tests = _get_colonnes_table(cursor, "tests_orientation")

            colonnes_selection = ["id"]

            for colonne in [
                "statut",
                "date_creation",
                "date_debut",
                "date_lancement",
                "date_fin",
                "date_cloture",
                "date_terminaison"
            ]:
                if colonne in colonnes_tests:
                    colonnes_selection.append(colonne)

            curseur_sql = ", ".join(colonnes_selection)

            cursor.execute(
                f"""
                SELECT {curseur_sql}
                FROM tests_orientation
                WHERE id = %s
                """,
                (test_orientation_id,)
            )

            test = cursor.fetchone()

            if test:
                date_lancement = _valeur_date(
                    test,
                    ["date_debut", "date_lancement", "date_creation"]
                )
                date_fin = _valeur_date(
                    test,
                    ["date_fin", "date_cloture", "date_terminaison"]
                )

                _ajouter_evenement_historique(
                    evenements,
                    "test_orientation",
                    "Test d’orientation lancé",
                    "L’étudiant a commencé le test d’orientation pédagogique.",
                    date_lancement,
                    "information",
                    {
                        "test_orientation_id": test_orientation_id,
                        "statut": test.get("statut")
                    }
                )

                _ajouter_evenement_historique(
                    evenements,
                    "test_orientation_termine",
                    "Test d’orientation terminé",
                    "Le test d’orientation a été terminé et les réponses ont été enregistrées.",
                    date_fin,
                    "success",
                    {
                        "test_orientation_id": test_orientation_id,
                        "statut": test.get("statut")
                    }
                )

        if _table_existe(cursor, "sessions_chat_orientation"):
            colonnes_sessions = _get_colonnes_table(cursor, "sessions_chat_orientation")
            colonne_date_session = _premiere_colonne_existante(
                colonnes_sessions,
                ["date_creation", "created_at", "date_debut"]
            )

            colonnes_selection = ["id", "statut", "raison_droit"]

            if "fiche_id" in colonnes_sessions:
                colonnes_selection.append("fiche_id")

            if "test_orientation_id" in colonnes_sessions:
                colonnes_selection.append("test_orientation_id")

            if colonne_date_session:
                colonnes_selection.append(colonne_date_session)

            conditions = ["etudiant_id = %s"]
            params = [etudiant_id]

            if "fiche_id" in colonnes_sessions:
                conditions.append("fiche_id = %s")
                params.append(fiche_id)
            elif "test_orientation_id" in colonnes_sessions:
                conditions.append("test_orientation_id = %s")
                params.append(test_orientation_id)

            cursor.execute(
                f"""
                SELECT {", ".join(colonnes_selection)}
                FROM sessions_chat_orientation
                WHERE {" AND ".join(conditions)}
                ORDER BY id ASC
                """,
                tuple(params)
            )

            sessions = cursor.fetchall()

            for session in sessions:
                _ajouter_evenement_historique(
                    evenements,
                    "session_chatbot",
                    "Session chatbot enregistrée",
                    (
                        "Une session de discussion avec le chatbot "
                        "d’orientation a été enregistrée."
                    ),
                    session.get(colonne_date_session) if colonne_date_session else None,
                    "information",
                    {
                        "session_id": session.get("id"),
                        "statut": session.get("statut"),
                        "raison_droit": session.get("raison_droit")
                    }
                )

        _ajouter_evenement_historique(
            evenements,
            "fiche_intelligente",
            "Fiche intelligente générée",
            (
                "La fiche intelligente a été générée avec la spécialité "
                f"recommandée : {fiche.get('specialite_recommandee', '')}."
            ),
            fiche.get("date_generation"),
            "success",
            {
                "fiche_id": fiche_id,
                "specialite_recommandee": fiche.get("specialite_recommandee"),
                "statut_validation": fiche.get("statut_validation")
            }
        )

        cursor.execute(
            """
            SELECT
                s.nom AS specialite,
                so.score,
                so.pourcentage
            FROM scores_orientation so
            JOIN specialites s ON so.specialite_id = s.id
            WHERE so.test_orientation_id = %s
            ORDER BY so.pourcentage DESC
            LIMIT 1
            """,
            (test_orientation_id,)
        )

        meilleur_score = cursor.fetchone()

        if meilleur_score:
            _ajouter_evenement_historique(
                evenements,
                "resultat_orientation",
                "Résultat principal calculé",
                (
                    f"Le meilleur score calculé est {meilleur_score.get('specialite')} "
                    f"avec {meilleur_score.get('pourcentage')}%."
                ),
                fiche.get("date_generation"),
                "information",
                meilleur_score
            )

        cursor.execute(
            """
            SELECT
                cfo.id AS choix_id,
                cfo.commentaire,
                cfo.statut_choix,
                cfo.pdf_engagement_path,
                cfo.annee_universitaire,
                cfo.date_choix,
                cfo.date_generation_pdf,
                cfo.date_confirmation_doyen,
                cfo.remarque_doyen,
                s.nom AS filiere_choisie
            FROM choix_finaux_orientation cfo
            JOIN specialites s ON cfo.specialite_id = s.id
            WHERE cfo.fiche_id = %s
            ORDER BY cfo.date_choix ASC, cfo.id ASC
            """,
            (fiche_id,)
        )

        choix_finaux = cursor.fetchall()
        choix_ids = []

        for choix in choix_finaux:
            choix_ids.append(choix["choix_id"])

            _ajouter_evenement_historique(
                evenements,
                "choix_final",
                "Choix final enregistré",
                (
                    "L’étudiant a choisi la filière "
                    f"{choix.get('filiere_choisie', '')}."
                ),
                choix.get("date_choix"),
                "information",
                {
                    "choix_id": choix.get("choix_id"),
                    "filiere_choisie": choix.get("filiere_choisie"),
                    "statut_choix": choix.get("statut_choix"),
                    "annee_universitaire": choix.get("annee_universitaire"),
                    "commentaire": choix.get("commentaire")
                }
            )

            if choix.get("date_generation_pdf") or choix.get("pdf_engagement_path"):
                _ajouter_evenement_historique(
                    evenements,
                    "fiche_engagement_pdf",
                    "Fiche d’engagement PDF générée",
                    (
                        "La fiche d’engagement officielle a été générée "
                        "pour signature par l’étudiant."
                    ),
                    choix.get("date_generation_pdf") or choix.get("date_choix"),
                    "success",
                    {
                        "choix_id": choix.get("choix_id"),
                        "pdf_engagement_path": choix.get("pdf_engagement_path")
                    }
                )

            if choix.get("date_confirmation_doyen"):
                _ajouter_evenement_historique(
                    evenements,
                    "confirmation_doyen",
                    "Choix confirmé administrativement",
                    (
                        "Le doyen a confirmé le document signé. "
                        "Le choix de filière est enregistré administrativement."
                    ),
                    choix.get("date_confirmation_doyen"),
                    "success",
                    {
                        "choix_id": choix.get("choix_id"),
                        "remarque_doyen": choix.get("remarque_doyen")
                    }
                )

            if choix.get("statut_choix") == "document_refuse":
                _ajouter_evenement_historique(
                    evenements,
                    "choix_document_refuse",
                    "Choix en attente de correction du document",
                    (
                        "Le choix final existe, mais le dernier document signé "
                        "a été refusé et doit être corrigé."
                    ),
                    choix.get("date_choix"),
                    "warning",
                    {
                        "choix_id": choix.get("choix_id"),
                        "remarque_doyen": choix.get("remarque_doyen")
                    }
                )

        if len(choix_ids) > 0:
            placeholders = ", ".join(["%s"] * len(choix_ids))

            cursor.execute(
                f"""
                SELECT
                    d.id AS document_id,
                    d.choix_final_id,
                    d.nom_fichier_original,
                    d.type_fichier,
                    d.taille_fichier,
                    d.statut_document,
                    d.verification_auto_statut,
                    d.verification_auto_message,
                    d.remarque_doyen,
                    d.date_upload,
                    d.date_decision_doyen
                FROM documents_choix_final d
                WHERE d.choix_final_id IN ({placeholders})
                ORDER BY d.date_upload ASC, d.id ASC
                """,
                tuple(choix_ids)
            )

            documents = cursor.fetchall()

            for index, document in enumerate(documents, start=1):
                _ajouter_evenement_historique(
                    evenements,
                    "document_depose",
                    "Document signé déposé",
                    (
                        f"Dépôt numéro {index} : "
                        f"{document.get('nom_fichier_original', '')}."
                    ),
                    document.get("date_upload"),
                    "information",
                    {
                        "document_id": document.get("document_id"),
                        "choix_final_id": document.get("choix_final_id"),
                        "statut_document": document.get("statut_document"),
                        "verification_auto_statut": document.get("verification_auto_statut"),
                        "verification_auto_message": document.get("verification_auto_message")
                    }
                )

                if document.get("date_decision_doyen"):
                    if document.get("statut_document") == "document_confirme":
                        titre = "Document confirmé par le doyen"
                        description = (
                            "Le document signé a été confirmé par le doyen."
                        )
                        statut = "success"
                    elif document.get("statut_document") == "document_refuse":
                        titre = "Document refusé par le doyen"
                        description = (
                            "Le document signé a été refusé par le doyen. "
                            "L’étudiant doit déposer une version corrigée."
                        )
                        statut = "warning"
                    else:
                        titre = "Décision doyen enregistrée"
                        description = "Une décision administrative a été enregistrée."
                        statut = "information"

                    _ajouter_evenement_historique(
                        evenements,
                        "decision_document",
                        titre,
                        description,
                        document.get("date_decision_doyen"),
                        statut,
                        {
                            "document_id": document.get("document_id"),
                            "statut_document": document.get("statut_document"),
                            "remarque_doyen": document.get("remarque_doyen")
                        }
                    )

        if _table_existe(cursor, "notifications_internes"):
            cursor.execute(
                """
                SELECT
                    id,
                    titre,
                    message,
                    type_notification,
                    lue,
                    date_creation
                FROM notifications_internes
                WHERE utilisateur_id = %s
                  AND type_notification IN (
                      'autorisation_nouveau_test',
                      'nouveau_test_autorise'
                  )
                ORDER BY date_creation ASC, id ASC
                """,
                (utilisateur_id,)
            )

            notifications_autorisation = cursor.fetchall()

            for notification in notifications_autorisation:
                _ajouter_evenement_historique(
                    evenements,
                    "autorisation_nouveau_test",
                    "Autorisation de repasser le test",
                    notification.get("message") or notification.get("titre"),
                    notification.get("date_creation"),
                    "warning",
                    {
                        "notification_id": notification.get("id"),
                        "type_notification": notification.get("type_notification"),
                        "lue": notification.get("lue")
                    }
                )

        evenements = sorted(evenements, key=_cle_tri_historique)

        for index, evenement in enumerate(evenements, start=1):
            evenement["ordre"] = index

        return {
            "success": True,
            "fiche": fiche,
            "historique": evenements,
            "total_evenements": len(evenements)
        }

    except Exception as erreur:
        print("Erreur historique étudiant :", erreur)

        return {
            "success": False,
            "message": "Erreur lors du chargement de l’historique étudiant.",
            "erreur": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()



def _compter_lignes_tableau_bord(cursor, requete, params=None):
    if params is None:
        params = ()

    cursor.execute(requete, params)
    ligne = cursor.fetchone()

    if ligne is None:
        return 0

    return int(ligne.get("total", 0) or 0)


def get_tableau_bord_doyen_avance():
    """
    Construit un tableau de bord global pour l'espace doyen.
    Les indicateurs sont filtrés sur l'année universitaire active.
    """
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)
    annee_universitaire = get_code_annee_universitaire_active()

    try:
        total_etudiants = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM etudiants
            WHERE promotion = %s
            """,
            (annee_universitaire,)
        )

        total_tests = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM tests_orientation t
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_fiches = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE e.promotion = %s
            """,
            (annee_universitaire,)
        )

        total_choix_final = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM choix_finaux_orientation
            WHERE annee_universitaire = %s
            """,
            (annee_universitaire,)
        )

        total_documents = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            WHERE cfo.annee_universitaire = %s
            """,
            (annee_universitaire,)
        )

        documents_en_attente = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            WHERE cfo.annee_universitaire = %s
              AND d.statut_document = 'en_attente_confirmation_doyen'
            """,
            (annee_universitaire,)
        )

        documents_confirmes = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            WHERE cfo.annee_universitaire = %s
              AND d.statut_document IN ('document_confirme', 'confirme', 'valide')
            """,
            (annee_universitaire,)
        )

        documents_refuses = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            WHERE cfo.annee_universitaire = %s
              AND d.statut_document IN ('document_refuse', 'refuse')
            """,
            (annee_universitaire,)
        )

        choix_confirmes = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM choix_finaux_orientation
            WHERE annee_universitaire = %s
              AND statut_choix = 'choix_confirme'
            """,
            (annee_universitaire,)
        )

        choix_en_attente = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM choix_finaux_orientation
            WHERE annee_universitaire = %s
              AND statut_choix = 'en_attente_confirmation_doyen'
            """,
            (annee_universitaire,)
        )

        choix_fiche_generee = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM choix_finaux_orientation
            WHERE annee_universitaire = %s
              AND statut_choix = 'fiche_generee'
            """,
            (annee_universitaire,)
        )

        notifications_non_lues = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM notifications_internes
            WHERE role_destinataire = 'doyen'
              AND lue = 0
            """
        )

        cursor.execute(
            """
            SELECT
                s.id AS specialite_id,
                s.nom AS specialite,
                COALESCE(SUM(CASE WHEN cfo.id IS NOT NULL THEN 1 ELSE 0 END), 0) AS total_choix,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'choix_confirme' THEN 1 ELSE 0 END), 0) AS total_confirmes,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'en_attente_confirmation_doyen' THEN 1 ELSE 0 END), 0) AS total_en_attente,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'document_refuse' THEN 1 ELSE 0 END), 0) AS total_refuses,
                COALESCE(SUM(CASE WHEN cfo.statut_choix = 'fiche_generee' THEN 1 ELSE 0 END), 0) AS fiches_engagement_generees,
                (
                    SELECT COUNT(*)
                    FROM fiches_intelligentes fi
                    JOIN specialites sr ON fi.specialite_recommandee_id = sr.id
                    JOIN tests_orientation t ON fi.test_orientation_id = t.id
                    JOIN etudiants e ON t.etudiant_id = e.id
                    WHERE sr.id = s.id
                      AND e.promotion = %s
                ) AS total_recommandations
            FROM specialites s
            LEFT JOIN choix_finaux_orientation cfo
                ON cfo.specialite_id = s.id
               AND cfo.annee_universitaire = %s
            GROUP BY s.id, s.nom
            ORDER BY s.nom
            """,
            (annee_universitaire, annee_universitaire)
        )

        repartition_filieres = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                cfo.statut_choix AS statut,
                COUNT(*) AS total
            FROM choix_finaux_orientation cfo
            WHERE cfo.annee_universitaire = %s
            GROUP BY cfo.statut_choix
            ORDER BY total DESC
            """,
            (annee_universitaire,)
        )
        choix_par_statut = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                d.statut_document AS statut,
                COUNT(*) AS total
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            WHERE cfo.annee_universitaire = %s
            GROUP BY d.statut_document
            ORDER BY total DESC
            """,
            (annee_universitaire,)
        )
        documents_par_statut = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                d.id AS document_id,
                d.choix_final_id,
                d.nom_fichier_original,
                d.statut_document,
                d.date_upload,
                s.nom AS filiere_choisie,
                e.nom,
                e.prenom,
                e.id_universitaire
            FROM documents_choix_final d
            JOIN choix_finaux_orientation cfo ON d.choix_final_id = cfo.id
            JOIN etudiants e ON d.etudiant_id = e.id
            JOIN specialites s ON cfo.specialite_id = s.id
            WHERE cfo.annee_universitaire = %s
            ORDER BY d.date_upload DESC, d.id DESC
            LIMIT 5
            """,
            (annee_universitaire,)
        )
        documents_recents = cursor.fetchall()

        taux_tests = round((total_tests / total_etudiants) * 100, 2) if total_etudiants > 0 else 0
        taux_choix = round((total_choix_final / total_fiches) * 100, 2) if total_fiches > 0 else 0
        taux_confirmation = round((choix_confirmes / total_choix_final) * 100, 2) if total_choix_final > 0 else 0

        return {
            "success": True,
            "annee_universitaire": annee_universitaire,
            "indicateurs": {
                "total_etudiants": total_etudiants,
                "total_tests": total_tests,
                "total_fiches": total_fiches,
                "total_choix_final": total_choix_final,
                "total_documents": total_documents,
                "documents_en_attente": documents_en_attente,
                "documents_confirmes": documents_confirmes,
                "documents_refuses": documents_refuses,
                "choix_confirmes": choix_confirmes,
                "choix_en_attente": choix_en_attente,
                "choix_fiche_generee": choix_fiche_generee,
                "notifications_non_lues": notifications_non_lues,
                "taux_tests": taux_tests,
                "taux_choix": taux_choix,
                "taux_confirmation": taux_confirmation
            },
            "repartition_filieres": repartition_filieres,
            "choix_par_statut": choix_par_statut,
            "documents_par_statut": documents_par_statut,
            "documents_recents": documents_recents
        }

    except Exception as erreur:
        print("Erreur tableau de bord doyen avancé :", erreur)

        return {
            "success": False,
            "message": "Erreur lors du chargement du tableau de bord avancé.",
            "erreur": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()



# ============================================================
# ÉTAPE 7 - SUIVI DE PROMOTION ET EXPORTS PAR FILIÈRE
# Cette partie ne fait aucune organisation de classes.
# Elle sert uniquement au contrôle administratif et aux listes.
# ============================================================


def _assurer_table_etudiants_officiels(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS etudiants_officiels_promotion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            annee_universitaire VARCHAR(20) NOT NULL,
            id_universitaire VARCHAR(100) NOT NULL,
            nom VARCHAR(150) NOT NULL,
            prenom VARCHAR(150) NOT NULL,
            email_outlook VARCHAR(255) NULL,
            source_import VARCHAR(80) NULL,
            active TINYINT(1) NOT NULL DEFAULT 1,
            date_import DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_officiel_annee_id (annee_universitaire, id_universitaire),
            INDEX idx_officiel_annee_active (annee_universitaire, active),
            INDEX idx_officiel_id_universitaire (id_universitaire)
        )
        """
    )


def _nettoyer_texte_simple(valeur):
    if valeur is None:
        return ""

    return str(valeur).strip()


def _normaliser_cle_import(cle):
    cle = _nettoyer_texte_simple(cle).lower()
    cle = cle.replace("é", "e").replace("è", "e").replace("ê", "e")
    cle = cle.replace("à", "a").replace("ç", "c")
    cle = cle.replace(" ", "_").replace("-", "_")

    if cle in ["id", "id_universitaire", "identifiant", "matricule", "code_etudiant"]:
        return "id_universitaire"

    if cle in ["nom", "last_name", "lastname"]:
        return "nom"

    if cle in ["prenom", "prénom", "first_name", "firstname"]:
        return "prenom"

    if cle in ["email", "email_outlook", "mail", "adresse_email", "adresse_mail"]:
        return "email_outlook"

    return cle


def _detecter_dialecte_csv(texte_csv):
    extrait = texte_csv[:1500]

    try:
        return csv.Sniffer().sniff(extrait, delimiters=";,\t,")
    except Exception:
        class DialecteSimple(csv.excel):
            delimiter = ";"

        return DialecteSimple


def _parser_liste_officielle_csv(texte_csv):
    texte_csv = _nettoyer_texte_simple(texte_csv)

    if not texte_csv:
        return []

    dialecte = _detecter_dialecte_csv(texte_csv)
    lecteur = csv.reader(StringIO(texte_csv), dialecte)
    lignes = [ligne for ligne in lecteur if any(_nettoyer_texte_simple(cellule) for cellule in ligne)]

    if not lignes:
        return []

    premiere_ligne = [_normaliser_cle_import(cellule) for cellule in lignes[0]]
    contient_entete = any(
        cellule in ["id_universitaire", "nom", "prenom", "email_outlook"]
        for cellule in premiere_ligne
    )

    etudiants = []

    if contient_entete:
        entetes = premiere_ligne
        lignes_donnees = lignes[1:]

        for ligne in lignes_donnees:
            element = {}

            for index, valeur in enumerate(ligne):
                if index < len(entetes):
                    element[entetes[index]] = _nettoyer_texte_simple(valeur)

            etudiants.append(element)
    else:
        for ligne in lignes:
            valeurs = [_nettoyer_texte_simple(valeur) for valeur in ligne]

            if len(valeurs) >= 4:
                etudiants.append({
                    "id_universitaire": valeurs[0],
                    "nom": valeurs[1],
                    "prenom": valeurs[2],
                    "email_outlook": valeurs[3]
                })
            elif len(valeurs) >= 3:
                etudiants.append({
                    "id_universitaire": valeurs[0],
                    "nom": valeurs[1],
                    "prenom": valeurs[2],
                    "email_outlook": ""
                })

    return etudiants


def _normaliser_etudiant_officiel(element):
    element_normalise = {}

    for cle, valeur in element.items():
        element_normalise[_normaliser_cle_import(cle)] = _nettoyer_texte_simple(valeur)

    return {
        "id_universitaire": element_normalise.get("id_universitaire", ""),
        "nom": element_normalise.get("nom", ""),
        "prenom": element_normalise.get("prenom", ""),
        "email_outlook": element_normalise.get("email_outlook", "")
    }


def importer_liste_officielle_promotion(texte_csv=None, etudiants=None, remplacer=False):
    """
    Importe la liste officielle de la promotion pour permettre au doyen
    de vérifier qui est inscrit, qui a passé le test et qui a déposé le document.
    Cette fonction ne fait aucune affectation et aucune organisation pédagogique.
    """
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)
    annee_universitaire = get_code_annee_universitaire_active()

    try:
        _assurer_table_etudiants_officiels(cursor)

        if etudiants is None:
            etudiants = _parser_liste_officielle_csv(texte_csv or "")

        etudiants_nettoyes = []
        ids_vus = set()

        for element in etudiants:
            etudiant = _normaliser_etudiant_officiel(element)

            if not etudiant["id_universitaire"]:
                continue

            if not etudiant["nom"] and not etudiant["prenom"]:
                continue

            cle = etudiant["id_universitaire"].lower()

            if cle in ids_vus:
                continue

            ids_vus.add(cle)
            etudiants_nettoyes.append(etudiant)

        if len(etudiants_nettoyes) == 0:
            return {
                "success": False,
                "message": "Aucun étudiant valide n’a été trouvé dans la liste officielle."
            }

        if remplacer:
            cursor.execute(
                """
                DELETE FROM etudiants_officiels_promotion
                WHERE annee_universitaire = %s
                """,
                (annee_universitaire,)
            )

        total_importes = 0

        for etudiant in etudiants_nettoyes:
            cursor.execute(
                """
                INSERT INTO etudiants_officiels_promotion
                (annee_universitaire, id_universitaire, nom, prenom,
                 email_outlook, source_import, active)
                VALUES (%s, %s, %s, %s, %s, 'copier_coller_csv', 1)
                ON DUPLICATE KEY UPDATE
                    nom = VALUES(nom),
                    prenom = VALUES(prenom),
                    email_outlook = VALUES(email_outlook),
                    source_import = VALUES(source_import),
                    active = 1,
                    date_import = CURRENT_TIMESTAMP
                """,
                (
                    annee_universitaire,
                    etudiant["id_universitaire"],
                    etudiant["nom"],
                    etudiant["prenom"],
                    etudiant["email_outlook"]
                )
            )
            total_importes += 1

        connection.commit()

        return {
            "success": True,
            "message": f"Liste officielle importée avec succès : {total_importes} étudiant(s).",
            "annee_universitaire": annee_universitaire,
            "total_importes": total_importes
        }

    except Exception as erreur:
        connection.rollback()
        print("Erreur import liste officielle promotion :", erreur)

        return {
            "success": False,
            "message": "Erreur lors de l’import de la liste officielle.",
            "erreur": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()


def _convertir_bool_int(valeur):
    return 1 if valeur else 0


def _construire_ligne_suivi(ligne, source_reference):
    inscrit_plateforme = ligne.get("etudiant_id") is not None
    test_fait = ligne.get("test_id") is not None
    fiche_generee = ligne.get("fiche_id") is not None
    choix_fait = ligne.get("choix_id") is not None
    document_depose = ligne.get("document_id") is not None

    statut_document = ligne.get("statut_document") or "document_non_depose"
    statut_choix = ligne.get("statut_choix") or "choix_non_effectue"

    if not inscrit_plateforme:
        statut_global = "non_inscrit"
        action_attendue = "L’étudiant doit créer son compte sur la plateforme."
    elif not test_fait:
        statut_global = "test_non_fait"
        action_attendue = "L’étudiant doit passer le test d’orientation."
    elif not choix_fait:
        statut_global = "choix_non_fait"
        action_attendue = "L’étudiant doit choisir une filière."
    elif not document_depose:
        statut_global = "document_non_depose"
        action_attendue = "L’étudiant doit déposer la fiche d’engagement signée."
    elif statut_document in ["document_confirme", "confirme", "valide"] or statut_choix == "choix_confirme":
        statut_global = "dossier_complet"
        action_attendue = "Aucune action urgente."
    elif statut_document in ["document_refuse", "refuse"] or statut_choix == "document_refuse":
        statut_global = "document_refuse"
        action_attendue = "L’étudiant doit redéposer une version corrigée."
    else:
        statut_global = "document_en_attente"
        action_attendue = "Le doyen doit confirmer ou refuser le document."

    return {
        "source_reference": source_reference,
        "id_universitaire": ligne.get("id_universitaire") or "",
        "nom": ligne.get("nom") or "",
        "prenom": ligne.get("prenom") or "",
        "email_outlook": ligne.get("email_outlook") or ligne.get("email") or "",
        "email_plateforme": ligne.get("email_plateforme") or ligne.get("email") or "",
        "etudiant_id": ligne.get("etudiant_id"),
        "inscrit_plateforme": inscrit_plateforme,
        "test_fait": test_fait,
        "fiche_generee": fiche_generee,
        "choix_fait": choix_fait,
        "document_depose": document_depose,
        "filiere_recommandee": ligne.get("filiere_recommandee") or "",
        "filiere_choisie": ligne.get("filiere_choisie") or "Non choisie",
        "statut_choix": statut_choix,
        "statut_document": statut_document,
        "date_test": _convertir_date_historique(ligne.get("date_test")),
        "date_fiche": _convertir_date_historique(ligne.get("date_fiche")),
        "date_choix": _convertir_date_historique(ligne.get("date_choix")),
        "date_depot_document": _convertir_date_historique(ligne.get("date_depot_document")),
        "statut_global": statut_global,
        "action_attendue": action_attendue
    }


def _calculer_resume_suivi(lignes_suivi, source_reference):
    total_reference = len(lignes_suivi)
    total_non_inscrits = sum(1 for ligne in lignes_suivi if not ligne["inscrit_plateforme"])
    total_inscrits = sum(1 for ligne in lignes_suivi if ligne["inscrit_plateforme"])
    total_tests_faits = sum(1 for ligne in lignes_suivi if ligne["test_fait"])
    total_tests_non_faits = sum(1 for ligne in lignes_suivi if ligne["inscrit_plateforme"] and not ligne["test_fait"])
    total_choix_faits = sum(1 for ligne in lignes_suivi if ligne["choix_fait"])
    total_choix_non_faits = sum(1 for ligne in lignes_suivi if ligne["test_fait"] and not ligne["choix_fait"])
    total_documents_deposes = sum(1 for ligne in lignes_suivi if ligne["document_depose"])
    total_documents_non_deposes = sum(1 for ligne in lignes_suivi if ligne["choix_fait"] and not ligne["document_depose"])
    total_documents_confirmes = sum(1 for ligne in lignes_suivi if ligne["statut_global"] == "dossier_complet")
    total_documents_refuses = sum(1 for ligne in lignes_suivi if ligne["statut_global"] == "document_refuse")
    total_documents_en_attente = sum(1 for ligne in lignes_suivi if ligne["statut_global"] == "document_en_attente")

    return {
        "source_reference": source_reference,
        "total_reference": total_reference,
        "total_non_inscrits": total_non_inscrits,
        "total_inscrits": total_inscrits,
        "total_tests_faits": total_tests_faits,
        "total_tests_non_faits": total_tests_non_faits,
        "total_choix_faits": total_choix_faits,
        "total_choix_non_faits": total_choix_non_faits,
        "total_documents_deposes": total_documents_deposes,
        "total_documents_non_deposes": total_documents_non_deposes,
        "total_documents_confirmes": total_documents_confirmes,
        "total_documents_refuses": total_documents_refuses,
        "total_documents_en_attente": total_documents_en_attente
    }


def _calculer_repartition_suivi(lignes_suivi):
    repartition = {}

    for ligne in lignes_suivi:
        filiere = ligne.get("filiere_choisie") or "Non choisie"

        if filiere == "Non choisie":
            continue

        if filiere not in repartition:
            repartition[filiere] = {
                "filiere": filiere,
                "total_choix": 0,
                "documents_deposes": 0,
                "documents_confirmes": 0,
                "documents_en_attente": 0,
                "documents_refuses": 0
            }

        repartition[filiere]["total_choix"] += 1

        if ligne.get("document_depose"):
            repartition[filiere]["documents_deposes"] += 1

        if ligne.get("statut_global") == "dossier_complet":
            repartition[filiere]["documents_confirmes"] += 1
        elif ligne.get("statut_global") == "document_en_attente":
            repartition[filiere]["documents_en_attente"] += 1
        elif ligne.get("statut_global") == "document_refuse":
            repartition[filiere]["documents_refuses"] += 1

    return sorted(repartition.values(), key=lambda item: item["filiere"])


def get_suivi_promotion_doyen():
    """
    Retourne le suivi de la promotion pour le doyen.
    Le but est le contrôle : test fait, choix fait, document déposé/confirmé.
    Aucune organisation de classes n’est effectuée ici.
    """
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)
    annee_universitaire = get_code_annee_universitaire_active()

    try:
        _assurer_table_etudiants_officiels(cursor)

        colonnes_tests = _get_colonnes_table(cursor, "tests_orientation") if _table_existe(cursor, "tests_orientation") else set()
        colonne_date_test = _premiere_colonne_existante(
            colonnes_tests,
            ["date_creation", "date_debut", "date_lancement", "created_at"]
        )
        date_test_sql = f"t.{colonne_date_test}" if colonne_date_test else "NULL"

        total_officiels = _compter_lignes_tableau_bord(
            cursor,
            """
            SELECT COUNT(*) AS total
            FROM etudiants_officiels_promotion
            WHERE annee_universitaire = %s
              AND active = 1
            """,
            (annee_universitaire,)
        )

        if total_officiels > 0:
            source_reference = "liste_officielle"
            cursor.execute(
                f"""
                SELECT
                    o.id_universitaire,
                    o.nom,
                    o.prenom,
                    o.email_outlook,
                    e.id AS etudiant_id,
                    e.email AS email_plateforme,
                    t.id AS test_id,
                    {date_test_sql} AS date_test,
                    fi.id AS fiche_id,
                    fi.date_generation AS date_fiche,
                    sr.nom AS filiere_recommandee,
                    cfo.id AS choix_id,
                    cfo.statut_choix,
                    cfo.date_choix,
                    sc.nom AS filiere_choisie,
                    d.id AS document_id,
                    d.statut_document,
                    d.date_upload AS date_depot_document
                FROM etudiants_officiels_promotion o
                LEFT JOIN etudiants e ON e.id_universitaire = o.id_universitaire
                LEFT JOIN tests_orientation t ON t.id = (
                    SELECT MAX(t2.id)
                    FROM tests_orientation t2
                    WHERE t2.etudiant_id = e.id
                )
                LEFT JOIN fiches_intelligentes fi ON fi.test_orientation_id = t.id
                LEFT JOIN specialites sr ON fi.specialite_recommandee_id = sr.id
                LEFT JOIN choix_finaux_orientation cfo ON cfo.id = (
                    SELECT MAX(cfo2.id)
                    FROM choix_finaux_orientation cfo2
                    WHERE cfo2.etudiant_id = e.id
                      AND cfo2.annee_universitaire = %s
                )
                LEFT JOIN specialites sc ON cfo.specialite_id = sc.id
                LEFT JOIN documents_choix_final d ON d.id = (
                    SELECT MAX(d2.id)
                    FROM documents_choix_final d2
                    WHERE d2.choix_final_id = cfo.id
                )
                WHERE o.annee_universitaire = %s
                  AND o.active = 1
                ORDER BY o.nom, o.prenom, o.id_universitaire
                """,
                (annee_universitaire, annee_universitaire)
            )
        else:
            source_reference = "plateforme"
            cursor.execute(
                f"""
                SELECT
                    e.id_universitaire,
                    e.nom,
                    e.prenom,
                    e.email AS email_outlook,
                    e.email AS email_plateforme,
                    e.id AS etudiant_id,
                    t.id AS test_id,
                    {date_test_sql} AS date_test,
                    fi.id AS fiche_id,
                    fi.date_generation AS date_fiche,
                    sr.nom AS filiere_recommandee,
                    cfo.id AS choix_id,
                    cfo.statut_choix,
                    cfo.date_choix,
                    sc.nom AS filiere_choisie,
                    d.id AS document_id,
                    d.statut_document,
                    d.date_upload AS date_depot_document
                FROM etudiants e
                LEFT JOIN tests_orientation t ON t.id = (
                    SELECT MAX(t2.id)
                    FROM tests_orientation t2
                    WHERE t2.etudiant_id = e.id
                )
                LEFT JOIN fiches_intelligentes fi ON fi.test_orientation_id = t.id
                LEFT JOIN specialites sr ON fi.specialite_recommandee_id = sr.id
                LEFT JOIN choix_finaux_orientation cfo ON cfo.id = (
                    SELECT MAX(cfo2.id)
                    FROM choix_finaux_orientation cfo2
                    WHERE cfo2.etudiant_id = e.id
                      AND cfo2.annee_universitaire = %s
                )
                LEFT JOIN specialites sc ON cfo.specialite_id = sc.id
                LEFT JOIN documents_choix_final d ON d.id = (
                    SELECT MAX(d2.id)
                    FROM documents_choix_final d2
                    WHERE d2.choix_final_id = cfo.id
                )
                WHERE e.promotion = %s
                ORDER BY e.nom, e.prenom, e.id_universitaire
                """,
                (annee_universitaire, annee_universitaire)
            )

        lignes = cursor.fetchall()
        suivi = [_construire_ligne_suivi(ligne, source_reference) for ligne in lignes]
        resume = _calculer_resume_suivi(suivi, source_reference)
        repartition_filieres = _calculer_repartition_suivi(suivi)

        etudiants_a_suivre = [
            ligne for ligne in suivi
            if ligne["statut_global"] != "dossier_complet"
        ]

        return {
            "success": True,
            "annee_universitaire": annee_universitaire,
            "resume": resume,
            "repartition_filieres": repartition_filieres,
            "suivi": suivi,
            "etudiants_a_suivre": etudiants_a_suivre[:60],
            "source_reference": source_reference,
            "message": (
                "Suivi basé sur la liste officielle importée."
                if source_reference == "liste_officielle"
                else "Aucune liste officielle importée : suivi basé sur les étudiants inscrits dans la plateforme."
            )
        }

    except Exception as erreur:
        print("Erreur suivi promotion doyen :", erreur)

        return {
            "success": False,
            "message": "Erreur lors du chargement du suivi de promotion.",
            "erreur": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()
