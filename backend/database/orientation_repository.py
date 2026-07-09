from database.db import get_db_connection
import unicodedata


def get_etudiant_id_by_utilisateur_id(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM etudiants
            WHERE utilisateur_id = %s
            """,
            (utilisateur_id,)
        )

        etudiant = cursor.fetchone()

        if etudiant is None:
            return None

        return etudiant["id"]

    finally:
        cursor.close()
        connection.close()


def get_etudiant_by_id(etudiant_id):
    connection = get_db_connection()

    if connection is None:
        return None

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
                promotion,
                autorisation_nouveau_test
            FROM etudiants
            WHERE id = %s
            """,
            (etudiant_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_etudiant_by_id_universitaire(id_universitaire):
    connection = get_db_connection()

    if connection is None:
        return None

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
                promotion,
                autorisation_nouveau_test
            FROM etudiants
            WHERE id_universitaire = %s
            """,
            (id_universitaire,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_dernier_test_termine_etudiant(etudiant_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                t.id AS test_orientation_id,
                t.etudiant_id,
                t.date_test,
                t.statut AS statut_test,
                f.id AS fiche_id,
                f.statut_validation,
                s.nom AS specialite_recommandee
            FROM tests_orientation t
            LEFT JOIN fiches_intelligentes f 
                ON f.test_orientation_id = t.id
            LEFT JOIN specialites s 
                ON s.id = f.specialite_recommandee_id
            WHERE t.etudiant_id = %s
              AND t.statut = 'termine'
            ORDER BY t.date_test DESC, t.id DESC
            LIMIT 1
            """,
            (etudiant_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def verifier_droit_nouveau_test(etudiant_id):
    etudiant = get_etudiant_by_id(etudiant_id)

    if etudiant is None:
        return {
            "success": False,
            "peut_passer_test": False,
            "message": "Étudiant introuvable."
        }

    dernier_test = get_dernier_test_termine_etudiant(etudiant_id)

    if dernier_test is None:
        return {
            "success": True,
            "peut_passer_test": True,
            "raison": "premier_test",
            "message": "L'étudiant n'a pas encore passé de test."
        }

    autorisation = bool(etudiant.get("autorisation_nouveau_test"))

    if autorisation:
        return {
            "success": True,
            "peut_passer_test": True,
            "raison": "autorisation_doyen",
            "message": "L'étudiant est autorisé à repasser le test.",
            "dernier_test": dernier_test
        }

    return {
        "success": False,
        "peut_passer_test": False,
        "raison": "test_deja_effectue",
        "message": "Vous avez déjà passé le test d'orientation. Un nouveau passage nécessite une autorisation du doyen.",
        "dernier_test": dernier_test
    }


def autoriser_nouveau_test_etudiant(etudiant_id, doyen_id=None):
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
            UPDATE etudiants
            SET autorisation_nouveau_test = TRUE,
                date_autorisation_nouveau_test = NOW(),
                doyen_autorisation_id = %s
            WHERE id = %s
            """,
            (
                doyen_id,
                etudiant_id
            )
        )

        connection.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Aucun étudiant trouvé pour cette autorisation."
            }

        return {
            "success": True,
            "message": "L'étudiant est autorisé à repasser le test."
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


def autoriser_nouveau_test_par_id_universitaire(id_universitaire, doyen_id=None):
    etudiant = get_etudiant_by_id_universitaire(id_universitaire)

    if etudiant is None:
        return {
            "success": False,
            "message": "Aucun étudiant trouvé avec cet ID universitaire."
        }

    return autoriser_nouveau_test_etudiant(
        etudiant["id"],
        doyen_id
    )


def consommer_autorisation_nouveau_test(etudiant_id):
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
            UPDATE etudiants
            SET autorisation_nouveau_test = FALSE,
                date_autorisation_nouveau_test = NULL,
                doyen_autorisation_id = NULL
            WHERE id = %s
              AND autorisation_nouveau_test = TRUE
            """,
            (etudiant_id,)
        )

        connection.commit()

        return {
            "success": True,
            "message": "Autorisation consommée ou aucune autorisation active."
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


def creer_test_orientation(etudiant_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO tests_orientation (etudiant_id, statut)
            VALUES (%s, 'en_cours')
            """,
            (etudiant_id,)
        )

        connection.commit()

        return cursor.lastrowid

    except Exception as e:
        connection.rollback()
        print("Erreur création test orientation :", e)
        return None

    finally:
        cursor.close()
        connection.close()


def get_choix_reponse_by_code(code_reponse):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, question_id
            FROM choix_reponses
            WHERE code_reponse = %s
            """,
            (code_reponse,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_question_by_code(code_question):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM questions
            WHERE code_question = %s
            """,
            (code_question,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def enregistrer_reponse_choix(test_orientation_id, code_reponse):
    choix = get_choix_reponse_by_code(code_reponse)

    if choix is None:
        return {
            "success": False,
            "message": f"Choix de réponse introuvable : {code_reponse}"
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
            INSERT INTO reponses_etudiants
            (test_orientation_id, question_id, choix_reponse_id, reponse_libre)
            VALUES (%s, %s, %s, NULL)
            """,
            (
                test_orientation_id,
                choix["question_id"],
                choix["id"]
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Réponse enregistrée."
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


def enregistrer_reponse_libre(test_orientation_id, code_question, reponse_libre):
    question = get_question_by_code(code_question)

    if question is None:
        return {
            "success": False,
            "message": f"Question libre introuvable : {code_question}"
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
            INSERT INTO reponses_etudiants
            (test_orientation_id, question_id, choix_reponse_id, reponse_libre)
            VALUES (%s, %s, NULL, %s)
            """,
            (
                test_orientation_id,
                question["id"],
                reponse_libre
            )
        )

        connection.commit()

        return {
            "success": True,
            "message": "Réponse libre enregistrée.",
            "reponse_etudiant_id": cursor.lastrowid
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


def terminer_test_orientation(test_orientation_id):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE tests_orientation
            SET statut = 'termine'
            WHERE id = %s
            """,
            (test_orientation_id,)
        )

        connection.commit()
        return True

    except Exception as e:
        connection.rollback()
        print("Erreur terminaison test :", e)
        return False

    finally:
        cursor.close()
        connection.close()


def normaliser_texte(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = texte.encode("ascii", "ignore").decode("utf-8")
    texte = texte.replace("-", " ")
    texte = texte.replace("_", " ")
    texte = " ".join(texte.split())
    return texte


def get_specialites_dict():
    connection = get_db_connection()

    if connection is None:
        return {}

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, nom
            FROM specialites
            """
        )

        specialites = cursor.fetchall()

        dictionnaire = {}

        for specialite in specialites:
            nom_normalise = normaliser_texte(specialite["nom"])
            dictionnaire[nom_normalise] = specialite["id"]

        return dictionnaire

    finally:
        cursor.close()
        connection.close()


def extraire_scores_et_pourcentages(resultat_recommandation):
    scores = resultat_recommandation.get("scores", {})
    pourcentages = resultat_recommandation.get("pourcentages", {})

    if scores is None:
        scores = {}

    if pourcentages is None:
        pourcentages = {}

    if not isinstance(scores, dict):
        scores = {}

    if not isinstance(pourcentages, dict):
        pourcentages = {}

    if scores and not pourcentages:
        total = sum(scores.values())

        if total > 0:
            for nom_specialite, score in scores.items():
                pourcentage = (score / total) * 100
                pourcentages[nom_specialite] = round(pourcentage, 2)

    if pourcentages and not scores:
        for nom_specialite, pourcentage in pourcentages.items():
            scores[nom_specialite] = int(round(float(pourcentage)))

    return scores, pourcentages


def enregistrer_scores_orientation(test_orientation_id, resultat_recommandation):
    specialites_dict = get_specialites_dict()

    if not specialites_dict:
        return {
            "success": False,
            "message": "Aucune spécialité trouvée dans la base de données."
        }

    scores, pourcentages = extraire_scores_et_pourcentages(resultat_recommandation)

    if not scores and not pourcentages:
        return {
            "success": False,
            "message": "Aucun score à enregistrer."
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
            DELETE FROM scores_orientation
            WHERE test_orientation_id = %s
            """,
            (test_orientation_id,)
        )

        specialites_enregistrees = 0

        for nom_specialite, pourcentage in pourcentages.items():
            nom_normalise = normaliser_texte(nom_specialite)

            if nom_normalise not in specialites_dict:
                continue

            specialite_id = specialites_dict[nom_normalise]
            score = scores.get(nom_specialite, int(round(float(pourcentage))))

            cursor.execute(
                """
                INSERT INTO scores_orientation
                (test_orientation_id, specialite_id, score, pourcentage)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    test_orientation_id,
                    specialite_id,
                    int(score),
                    float(pourcentage)
                )
            )

            specialites_enregistrees += 1

        connection.commit()

        return {
            "success": True,
            "message": "Scores enregistrés avec succès.",
            "nombre_scores": specialites_enregistrees
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