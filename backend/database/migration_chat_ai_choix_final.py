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
            CREATE TABLE IF NOT EXISTS sessions_chat_orientation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                etudiant_id INT NOT NULL,
                statut VARCHAR(30) NOT NULL DEFAULT 'en_cours',
                raison_droit VARCHAR(100) NULL,
                index_question INT NOT NULL DEFAULT 0,
                scores_json TEXT NULL,
                reponses_json TEXT NULL,
                test_orientation_id INT NULL,
                fiche_id INT NULL,
                date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                date_modification DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (etudiant_id)
                    REFERENCES etudiants(id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages_chat_orientation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_chat_id INT NOT NULL,
                role_message VARCHAR(20) NOT NULL,
                contenu TEXT NOT NULL,
                date_message DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_chat_id)
                    REFERENCES sessions_chat_orientation(id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS choix_finaux_orientation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fiche_id INT NOT NULL UNIQUE,
                etudiant_id INT NOT NULL,
                specialite_id INT NOT NULL,
                commentaire TEXT NULL,
                date_choix DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fiche_id)
                    REFERENCES fiches_intelligentes(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (etudiant_id)
                    REFERENCES etudiants(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (specialite_id)
                    REFERENCES specialites(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

        print("Migration chat IA et choix final terminée avec succès.")

    except Exception as e:
        connection.rollback()
        print("Erreur migration :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    appliquer_migration()