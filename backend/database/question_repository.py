from database.db import get_db_connection


def get_questions_par_statut(statut_question="provisoire"):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, code_question, texte, type_question, statut_question, ordre
        FROM questions
        WHERE statut_question = %s AND active = TRUE
        ORDER BY ordre ASC
        """,
        (statut_question,)
    )

    questions_db = cursor.fetchall()
    questions = []

    for question in questions_db:
        cursor.execute(
            """
            SELECT code_reponse, texte
            FROM choix_reponses
            WHERE question_id = %s AND active = TRUE
            ORDER BY id ASC
            """,
            (question["id"],)
        )

        reponses_db = cursor.fetchall()

        reponses = []

        for reponse in reponses_db:
            reponses.append({
                "id": reponse["code_reponse"],
                "texte": reponse["texte"]
            })

        questions.append({
            "id": question["code_question"],
            "texte": question["texte"],
            "type": question["type_question"],
            "statut": question["statut_question"],
            "ordre": question["ordre"],
            "reponses": reponses
        })

    cursor.close()
    connection.close()

    return questions