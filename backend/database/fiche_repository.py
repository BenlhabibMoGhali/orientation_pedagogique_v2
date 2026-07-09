from database.db import get_db_connection


def get_meilleur_score(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                so.specialite_id,
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

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_scores_test(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
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
            (test_orientation_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_infos_etudiant_par_test(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                e.id AS etudiant_id,
                e.id_universitaire,
                e.nom,
                e.prenom,
                t.id AS test_orientation_id,
                t.date_test,
                t.statut
            FROM tests_orientation t
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE t.id = %s
            """,
            (test_orientation_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_reponses_test(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                q.texte AS question,
                cr.texte AS choix_reponse,
                re.reponse_libre
            FROM reponses_etudiants re
            JOIN questions q ON re.question_id = q.id
            LEFT JOIN choix_reponses cr ON re.choix_reponse_id = cr.id
            WHERE re.test_orientation_id = %s
            ORDER BY re.id ASC
            """,
            (test_orientation_id,)
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def construire_resume_profil(infos_etudiant, meilleur_score, scores, reponses):
    nom_complet = f"{infos_etudiant['prenom']} {infos_etudiant['nom']}"

    resume = f"Fiche intelligente de l'étudiant {nom_complet}.\n\n"

    resume += "Résumé général :\n"
    resume += (
        f"L'étudiant a passé un test d'orientation pédagogique. "
        f"L'analyse des réponses et des scores montre une compatibilité principale avec la spécialité "
        f"{meilleur_score['specialite']}, avec un pourcentage de {meilleur_score['pourcentage']}%.\n\n"
    )

    resume += "Scores obtenus :\n"

    for score in scores:
        resume += (
            f"- {score['specialite']} : "
            f"{score['pourcentage']}% "
            f"(score : {score['score']})\n"
        )

    resume += "\nInterprétation :\n"
    resume += (
        "La recommandation est générée à partir des réponses de l'étudiant, "
        "des choix effectués dans le chatbot, des pondérations associées aux spécialités "
        "et de l'analyse de la réponse libre lorsqu'elle existe. "
        "Cette recommandation constitue une aide à la décision et ne remplace pas la validation finale du doyen.\n"
    )

    reponses_libres = []

    for reponse in reponses:
        if reponse["reponse_libre"] is not None and reponse["reponse_libre"].strip() != "":
            reponses_libres.append(reponse["reponse_libre"])

    if len(reponses_libres) > 0:
        resume += "\nRéponse libre analysée :\n"
        for texte in reponses_libres:
            resume += f"- {texte}\n"

    return resume


def enregistrer_historique(fiche_id, action, description):
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
        print("Erreur historique :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def generer_fiche_intelligente(test_orientation_id):
    infos_etudiant = get_infos_etudiant_par_test(test_orientation_id)

    if infos_etudiant is None:
        return {
            "success": False,
            "message": "Test d'orientation introuvable."
        }

    meilleur_score = get_meilleur_score(test_orientation_id)

    if meilleur_score is None:
        return {
            "success": False,
            "message": "Aucun score trouvé pour ce test."
        }

    scores = get_scores_test(test_orientation_id)
    reponses = get_reponses_test(test_orientation_id)

    resume_profil = construire_resume_profil(
        infos_etudiant,
        meilleur_score,
        scores,
        reponses
    )

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
            INSERT INTO fiches_intelligentes
            (test_orientation_id, specialite_recommandee_id, resume_profil)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                specialite_recommandee_id = VALUES(specialite_recommandee_id),
                resume_profil = VALUES(resume_profil),
                statut_validation = 'en_attente',
                remarque_doyen = NULL
            """,
            (
                test_orientation_id,
                meilleur_score["specialite_id"],
                resume_profil
            )
        )

        connection.commit()

        if cursor.lastrowid != 0:
            fiche_id = cursor.lastrowid
        else:
            cursor.execute(
                """
                SELECT id
                FROM fiches_intelligentes
                WHERE test_orientation_id = %s
                """,
                (test_orientation_id,)
            )

            fiche = cursor.fetchone()
            fiche_id = fiche["id"]

        enregistrer_historique(
            fiche_id,
            "generation_fiche",
            "Fiche intelligente générée automatiquement après le calcul des scores."
        )

        return {
            "success": True,
            "message": "Fiche intelligente générée avec succès.",
            "fiche_id": fiche_id,
            "test_orientation_id": test_orientation_id,
            "specialite_recommandee": meilleur_score["specialite"],
            "pourcentage": float(meilleur_score["pourcentage"]),
            "resume_profil": resume_profil
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


def get_fiche_par_test(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                fi.id,
                fi.test_orientation_id,
                fi.resume_profil,
                fi.statut_validation,
                fi.remarque_doyen,
                fi.date_generation,
                s.nom AS specialite_recommandee
            FROM fiches_intelligentes fi
            JOIN specialites s ON fi.specialite_recommandee_id = s.id
            WHERE fi.test_orientation_id = %s
            """,
            (test_orientation_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()