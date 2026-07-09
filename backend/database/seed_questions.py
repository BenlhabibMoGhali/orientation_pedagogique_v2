from database.db import get_db_connection
from recommendation.question_bank import get_questions_provisoires
from recommendation.weights import POIDS_REPONSES


def get_specialite_id(cursor, nom_specialite):
    cursor.execute(
        "SELECT id FROM specialites WHERE nom = %s",
        (nom_specialite,)
    )

    resultat = cursor.fetchone()

    if resultat:
        return resultat[0]

    return None


def get_question_id(cursor, code_question):
    cursor.execute(
        "SELECT id FROM questions WHERE code_question = %s",
        (code_question,)
    )

    resultat = cursor.fetchone()

    if resultat:
        return resultat[0]

    return None


def get_choix_reponse_id(cursor, code_reponse):
    cursor.execute(
        "SELECT id FROM choix_reponses WHERE code_reponse = %s",
        (code_reponse,)
    )

    resultat = cursor.fetchone()

    if resultat:
        return resultat[0]

    return None


def enregistrer_poids(cursor, choix_reponse_id, specialite_id, poids):
    cursor.execute(
        """
        SELECT id
        FROM poids_reponses
        WHERE choix_reponse_id = %s AND specialite_id = %s
        """,
        (choix_reponse_id, specialite_id)
    )

    resultat = cursor.fetchone()

    if resultat:
        cursor.execute(
            """
            UPDATE poids_reponses
            SET poids = %s
            WHERE id = %s
            """,
            (poids, resultat[0])
        )
    else:
        cursor.execute(
            """
            INSERT INTO poids_reponses
            (choix_reponse_id, specialite_id, poids)
            VALUES (%s, %s, %s)
            """,
            (choix_reponse_id, specialite_id, poids)
        )


def inserer_questions_provisoires():
    connection = get_db_connection()

    if connection is None:
        print("Erreur : impossible de se connecter à la base de données.")
        return

    cursor = connection.cursor()

    questions = get_questions_provisoires()

    for index, question in enumerate(questions, start=1):
        cursor.execute(
            """
            INSERT INTO questions
            (code_question, texte, type_question, statut_question, ordre, active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                texte = VALUES(texte),
                type_question = VALUES(type_question),
                statut_question = VALUES(statut_question),
                ordre = VALUES(ordre),
                active = TRUE
            """,
            (
                question["id"],
                question["texte"],
                question["type"],
                "provisoire",
                index
            )
        )

        question_id = get_question_id(cursor, question["id"])

        for reponse in question["reponses"]:
            cursor.execute(
                """
                INSERT INTO choix_reponses
                (question_id, code_reponse, texte, active)
                VALUES (%s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE
                    question_id = VALUES(question_id),
                    texte = VALUES(texte),
                    active = TRUE
                """,
                (
                    question_id,
                    reponse["id"],
                    reponse["texte"]
                )
            )

            choix_reponse_id = get_choix_reponse_id(cursor, reponse["id"])

            poids_reponse = POIDS_REPONSES.get(reponse["id"], {})

            for nom_specialite, poids in poids_reponse.items():
                specialite_id = get_specialite_id(cursor, nom_specialite)

                if specialite_id is not None:
                    enregistrer_poids(
                        cursor,
                        choix_reponse_id,
                        specialite_id,
                        poids
                    )

    connection.commit()
    cursor.close()
    connection.close()

    print("Questions provisoires, choix de réponses et poids insérés avec succès.")


if __name__ == "__main__":
    inserer_questions_provisoires()