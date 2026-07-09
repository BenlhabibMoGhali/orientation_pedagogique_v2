from database.db import get_db_connection


def colonne_existe(cursor, table, colonne):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table, colonne)
    )

    resultat = cursor.fetchone()
    return resultat["total"] > 0


def index_existe(cursor, table, index_name):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND INDEX_NAME = %s
        """,
        (table, index_name)
    )

    resultat = cursor.fetchone()
    return resultat["total"] > 0


def valeurs_dupliquees(cursor, table, colonne):
    cursor.execute(
        f"""
        SELECT {colonne}, COUNT(*) AS total
        FROM {table}
        WHERE {colonne} IS NOT NULL
          AND {colonne} <> ''
        GROUP BY {colonne}
        HAVING COUNT(*) > 1
        """
    )

    return cursor.fetchall()


def ajouter_colonne_si_absente(cursor, table, colonne, definition):
    if not colonne_existe(cursor, table, colonne):
        cursor.execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {colonne} {definition}
            """
        )

        print(f"Colonne ajoutée : {table}.{colonne}")
    else:
        print(f"Colonne déjà existante : {table}.{colonne}")


def ajouter_index_unique_si_absent(cursor, table, colonne, index_name):
    if index_existe(cursor, table, index_name):
        print(f"Index déjà existant : {index_name}")
        return

    doublons = valeurs_dupliquees(cursor, table, colonne)

    if len(doublons) > 0:
        print(f"Impossible d'ajouter l'index unique sur {table}.{colonne}.")
        print("Valeurs dupliquées trouvées :")
        for doublon in doublons:
            print(doublon)
        return

    cursor.execute(
        f"""
        ALTER TABLE {table}
        ADD UNIQUE INDEX {index_name} ({colonne})
        """
    )

    print(f"Index unique ajouté : {index_name}")


def creer_table_reinitialisation(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reinitialisations_mots_de_passe (
            id INT AUTO_INCREMENT PRIMARY KEY,
            utilisateur_id INT NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            date_expiration DATETIME NOT NULL,
            utilise BOOLEAN NOT NULL DEFAULT FALSE,
            date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilisateur_id)
                REFERENCES utilisateurs(id)
                ON DELETE CASCADE
        )
        """
    )

    print("Table vérifiée/créée : reinitialisations_mots_de_passe")


def appliquer_migration():
    connection = get_db_connection()

    if connection is None:
        print("Impossible de se connecter à la base de données.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        ajouter_colonne_si_absente(
            cursor,
            "etudiants",
            "promotion",
            "VARCHAR(20) NULL"
        )

        ajouter_colonne_si_absente(
            cursor,
            "etudiants",
            "autorisation_nouveau_test",
            "BOOLEAN NOT NULL DEFAULT FALSE"
        )

        ajouter_colonne_si_absente(
            cursor,
            "etudiants",
            "date_autorisation_nouveau_test",
            "DATETIME NULL"
        )

        ajouter_colonne_si_absente(
            cursor,
            "etudiants",
            "doyen_autorisation_id",
            "INT NULL"
        )

        ajouter_index_unique_si_absent(
            cursor,
            "utilisateurs",
            "identifiant_connexion",
            "uk_utilisateurs_identifiant_connexion"
        )

        ajouter_index_unique_si_absent(
            cursor,
            "etudiants",
            "id_universitaire",
            "uk_etudiants_id_universitaire"
        )

        ajouter_index_unique_si_absent(
            cursor,
            "etudiants",
            "email",
            "uk_etudiants_email"
        )

        creer_table_reinitialisation(cursor)

        connection.commit()

        print("")
        print("Migration terminée avec succès.")

    except Exception as e:
        connection.rollback()
        print("Erreur pendant la migration :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    appliquer_migration()