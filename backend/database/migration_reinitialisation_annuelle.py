from database.db import get_db_connection


def appliquer_migration():
    connection = get_db_connection()

    if connection is None:
        print("Connexion à la base impossible.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reinitialisations_annuelles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                utilisateur_id INT NOT NULL,
                annee_universitaire VARCHAR(20) NOT NULL,
                phrase_securite VARCHAR(255) NOT NULL,
                code_confirmation VARCHAR(20) NOT NULL,
                statut VARCHAR(30) NOT NULL DEFAULT 'en_attente',
                date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                date_expiration DATETIME NOT NULL,
                date_execution DATETIME NULL
            )
            """
        )

        connection.commit()

        print("Migration réinitialisation annuelle terminée avec succès.")

    except Exception as e:
        connection.rollback()
        print("Erreur migration :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    appliquer_migration()