from database.db import get_db_connection


def appliquer_migration():
    """Adapte la table questions au questionnaire réellement utilisé par le chatbot."""
    connection = get_db_connection()

    if connection is None:
        print("Migration questions chatbot : connexion impossible.")
        return

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            ALTER TABLE questions
            MODIFY type_question ENUM(
                'choix_unique',
                'choix_multiple',
                'texte_libre',
                'hesitation'
            ) NOT NULL
            """
        )
        connection.commit()
        print("Migration questions chatbot appliquée.")

    except Exception as e:
        connection.rollback()
        print("Migration questions chatbot ignorée ou déjà appliquée :", e)

    finally:
        cursor.close()
        connection.close()
