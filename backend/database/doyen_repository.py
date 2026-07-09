from database.db import get_db_connection
from database.orientation_repository import autoriser_nouveau_test_par_id_universitaire


def get_doyen_id_by_utilisateur_id(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM doyens
            WHERE utilisateur_id = %s
            """,
            (utilisateur_id,)
        )

        doyen = cursor.fetchone()

        if doyen is None:
            return None

        return doyen["id"]

    finally:
        cursor.close()
        connection.close()


def get_fiches_en_attente():
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.statut_validation,
                fi.date_generation,
                s.nom AS specialite_recommandee,
                e.id AS etudiant_id,
                e.id_universitaire,
                e.nom,
                e.prenom
            FROM fiches_intelligentes fi
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE fi.statut_validation = 'en_attente'
            ORDER BY fi.date_generation DESC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_fiche_complete(fiche_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.statut_validation,
                fi.remarque_doyen,
                fi.date_generation,
                s.nom AS specialite_recommandee,
                e.id AS etudiant_id,
                e.id_universitaire,
                e.nom,
                e.prenom
            FROM fiches_intelligentes fi
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE fi.id = %s
            """,
            (fiche_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return None

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

        fiche["scores"] = cursor.fetchall()

        return fiche

    finally:
        cursor.close()
        connection.close()


def enregistrer_historique_validation(fiche_id, action, description):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO historique_orientations
            (fiche_id, action, description)
            VALUES (%s, %s, %s)
            """,
            (fiche_id, action, description)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur historique validation :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def valider_ou_reviser_fiche(fiche_id, utilisateur_id, statut, remarque=None):
    if statut not in ["validee", "a_revoir"]:
        return {
            "success": False,
            "message": "Le statut doit être 'validee' ou 'a_revoir'."
        }

    doyen_id = get_doyen_id_by_utilisateur_id(utilisateur_id)

    if doyen_id is None:
        return {
            "success": False,
            "message": "Aucun doyen trouvé pour cet utilisateur."
        }

    fiche = get_fiche_complete(fiche_id)

    if fiche is None:
        return {
            "success": False,
            "message": "Fiche intelligente introuvable."
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
            INSERT INTO validations
            (fiche_id, doyen_id, statut, remarque)
            VALUES (%s, %s, %s, %s)
            """,
            (fiche_id, doyen_id, statut, remarque)
        )

        cursor.execute(
            """
            UPDATE fiches_intelligentes
            SET statut_validation = %s,
                remarque_doyen = %s
            WHERE id = %s
            """,
            (statut, remarque, fiche_id)
        )

        connection.commit()

        if statut == "validee":
            action = "validation_doyen"
            description = "La fiche intelligente a été validée par le doyen."
            message = "Fiche validée avec succès par le doyen."
        else:
            action = "demande_revision"
            description = "Le doyen a demandé une révision de la fiche intelligente."
            message = "Fiche marquée comme à revoir par le doyen."

        enregistrer_historique_validation(
            fiche_id,
            action,
            description
        )

        return {
            "success": True,
            "message": message,
            "fiche_id": fiche_id,
            "statut": statut,
            "remarque": remarque
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


def rechercher_fiches_par_id_universitaire(recherche):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    recherche = recherche.strip()
    recherche_like = f"%{recherche}%"

    try:
        cursor.execute(
            """
            SELECT
                fi.id AS fiche_id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.statut_validation,
                fi.remarque_doyen,
                fi.date_generation,

                s.nom AS specialite_recommandee,

                e.id AS etudiant_id,
                e.id_universitaire,
                e.nom,
                e.prenom,
                e.email,
                e.promotion,

                sf.nom AS choix_final_etudiant,

                cfo.id AS choix_final_id,
                cfo.commentaire AS commentaire_choix_final,
                cfo.statut_choix,
                cfo.pdf_engagement_path,
                cfo.date_choix AS date_choix_final,
                cfo.date_confirmation_doyen,

                doc.id AS document_id,
                doc.nom_fichier_original AS document_nom,
                doc.statut_document,
                doc.verification_auto_statut,
                doc.verification_auto_message,
                doc.remarque_doyen AS remarque_document,
                doc.date_upload AS date_upload_document

            FROM fiches_intelligentes fi

            JOIN specialites s
                ON fi.specialite_recommandee_id = s.id

            JOIN tests_orientation t
                ON fi.test_orientation_id = t.id

            JOIN etudiants e
                ON t.etudiant_id = e.id

            LEFT JOIN choix_finaux_orientation cfo
                ON cfo.fiche_id = fi.id

            LEFT JOIN specialites sf
                ON cfo.specialite_id = sf.id

            LEFT JOIN documents_choix_final doc
                ON doc.id = (
                    SELECT d2.id
                    FROM documents_choix_final d2
                    WHERE d2.choix_final_id = cfo.id
                    ORDER BY d2.date_upload DESC, d2.id DESC
                    LIMIT 1
                )

            WHERE e.id_universitaire LIKE %s
               OR e.nom LIKE %s
               OR e.prenom LIKE %s
               OR CONCAT(e.prenom, ' ', e.nom) LIKE %s
               OR CONCAT(e.nom, ' ', e.prenom) LIKE %s

            ORDER BY fi.date_generation DESC, fi.id DESC
            """,
            (
                recherche_like,
                recherche_like,
                recherche_like,
                recherche_like,
                recherche_like
            )
        )

        fiches = cursor.fetchall()

        for fiche in fiches:
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

            fiche["scores"] = cursor.fetchall()

        return fiches

    finally:
        cursor.close()
        connection.close()


def autoriser_nouveau_test_pour_etudiant(utilisateur_id, id_universitaire):
    doyen_id = get_doyen_id_by_utilisateur_id(utilisateur_id)

    if doyen_id is None:
        return {
            "success": False,
            "message": "Aucun doyen trouvé pour cet utilisateur."
        }

    if id_universitaire is None or str(id_universitaire).strip() == "":
        return {
            "success": False,
            "message": "L'ID universitaire est obligatoire."
        }

    id_universitaire = str(id_universitaire).strip().upper()

    resultat = autoriser_nouveau_test_par_id_universitaire(
        id_universitaire,
        doyen_id
    )

    if not resultat["success"]:
        return resultat

    return {
        "success": True,
        "message": "Le doyen a autorisé cet étudiant à repasser le test.",
        "id_universitaire": id_universitaire,
        "doyen_id": doyen_id
    }