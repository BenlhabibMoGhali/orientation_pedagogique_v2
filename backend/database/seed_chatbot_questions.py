from database.db import get_db_connection
from recommendation.chat_engine import QUESTIONS


def inserer_questions_chatbot():
    """
    Insère les questions q1 à q10 réellement utilisées par le chatbot.

    Cela permet à la sauvegarde finale des réponses de retrouver les questions
    par code_question dans la table reponses_etudiants.
    """
    connection = get_db_connection()

    if connection is None:
        print("Erreur : impossible de se connecter à la base de données.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        for ordre, question in enumerate(QUESTIONS, start=1):
            cursor.execute(
                """
                INSERT INTO questions
                (code_question, texte, type_question, statut_question, ordre, active)
                VALUES (%s, %s, %s, 'finale', %s, TRUE)
                ON DUPLICATE KEY UPDATE
                    texte = VALUES(texte),
                    type_question = VALUES(type_question),
                    statut_question = VALUES(statut_question),
                    ordre = VALUES(ordre),
                    active = TRUE
                """,
                (
                    question["code_question"],
                    question["texte"],
                    question["type_question"],
                    ordre
                )
            )

            cursor.execute(
                "SELECT id FROM questions WHERE code_question = %s",
                (question["code_question"],)
            )
            question_db = cursor.fetchone()

            if question_db is None:
                continue

            question_id = question_db["id"]

            for index, option in enumerate(question.get("options", []), start=1):
                texte_option = option.get("texte", "")
                if texte_option == "":
                    continue

                code_reponse = f"{question['code_question']}_opt_{index}"

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
                    (question_id, code_reponse, texte_option)
                )

        connection.commit()
        print("Questions du chatbot insérées avec succès.")

    except Exception as e:
        connection.rollback()
        print("Erreur insertion questions chatbot :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    inserer_questions_chatbot()
