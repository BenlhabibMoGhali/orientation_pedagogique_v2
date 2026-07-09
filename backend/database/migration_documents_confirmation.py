from database.db import get_db_connection


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS count_col
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name)
    )

    result = cursor.fetchone()
    return result["count_col"] > 0


def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


def appliquer_migration():
    connection = get_db_connection()

    if connection is None:
        print("Connexion à la base impossible.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "annee_universitaire",
            "VARCHAR(20) NOT NULL DEFAULT '2026/2027'"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "statut_choix",
            "VARCHAR(50) NOT NULL DEFAULT 'fiche_generee'"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "pdf_engagement_path",
            "VARCHAR(500) NULL"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "date_generation_pdf",
            "DATETIME NULL"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "date_confirmation_doyen",
            "DATETIME NULL"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "doyen_confirmation_id",
            "INT NULL"
        )

        add_column_if_not_exists(
            cursor,
            "choix_finaux_orientation",
            "remarque_doyen",
            "TEXT NULL"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents_choix_final (
                id INT AUTO_INCREMENT PRIMARY KEY,
                choix_final_id INT NOT NULL,
                etudiant_id INT NOT NULL,
                nom_fichier_original VARCHAR(255) NOT NULL,
                nom_fichier_stocke VARCHAR(255) NOT NULL,
                chemin_fichier VARCHAR(500) NOT NULL,
                type_fichier VARCHAR(100) NOT NULL,
                taille_fichier INT NOT NULL,
                statut_document VARCHAR(50) NOT NULL DEFAULT 'en_attente_confirmation_doyen',
                verification_auto_statut VARCHAR(50) NULL,
                verification_auto_message TEXT NULL,
                remarque_doyen TEXT NULL,
                date_upload DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                date_decision_doyen DATETIME NULL,
                doyen_id INT NULL,
                archive_document_valide_path VARCHAR(500) NULL,
                FOREIGN KEY (choix_final_id) REFERENCES choix_finaux_orientation(id) ON DELETE CASCADE,
                FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
            )
            """
        )

        add_column_if_not_exists(
            cursor,
            "documents_choix_final",
            "archive_document_valide_path",
            "VARCHAR(500) NULL"
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historique_admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                utilisateur_id INT NULL,
                action VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                date_action DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()
        print("Migration documents et confirmation doyen terminée.")

    except Exception as e:
        connection.rollback()
        print("Erreur migration documents :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    appliquer_migration()
