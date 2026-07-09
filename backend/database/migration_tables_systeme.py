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
            CREATE TABLE IF NOT EXISTS annees_universitaires (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(20) NOT NULL UNIQUE,
                annee_debut INT NOT NULL,
                annee_fin INT NOT NULL,
                date_debut DATE NOT NULL,
                date_fin DATE NOT NULL,
                active TINYINT(1) NOT NULL DEFAULT 1,
                date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS confirmations_inscription_email (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                prenom VARCHAR(100) NOT NULL,
                id_universitaire VARCHAR(50) NOT NULL,
                email VARCHAR(150) NOT NULL,
                annee_universitaire VARCHAR(20) NULL,
                code_hash VARCHAR(255) NOT NULL,
                date_expiration DATETIME NOT NULL,
                utilise TINYINT(1) NOT NULL DEFAULT 0,
                date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                date_utilisation DATETIME NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications_internes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                utilisateur_id INT NOT NULL,
                role_destinataire VARCHAR(30) NOT NULL,
                titre VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                type_notification VARCHAR(80) NOT NULL,
                lien_action VARCHAR(255) NULL,
                lue TINYINT(1) NOT NULL DEFAULT 0,
                date_lecture DATETIME NULL,
                date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS archives_fiches_engagement (
                id INT AUTO_INCREMENT PRIMARY KEY,
                document_id INT NOT NULL UNIQUE,
                choix_final_id INT NOT NULL,
                etudiant_id INT NOT NULL,
                id_universitaire VARCHAR(100) NOT NULL,
                nom VARCHAR(150) NULL,
                prenom VARCHAR(150) NULL,
                email_outlook VARCHAR(255) NULL,
                filiere_choisie VARCHAR(150) NULL,
                annee_universitaire VARCHAR(20) NULL,
                nom_fichier_archive VARCHAR(255) NOT NULL,
                chemin_archive VARCHAR(500) NOT NULL,
                type_fichier VARCHAR(100) NULL,
                date_archivage DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents_choix_final(id) ON DELETE CASCADE,
                FOREIGN KEY (choix_final_id) REFERENCES choix_finaux_orientation(id) ON DELETE CASCADE,
                FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS archives_exports_excel (
                id INT AUTO_INCREMENT PRIMARY KEY,
                annee_universitaire VARCHAR(20) NOT NULL,
                nom_fichier VARCHAR(255) NOT NULL,
                chemin_archive VARCHAR(500) NOT NULL,
                date_generation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_export_excel_annee_nom (annee_universitaire, nom_fichier)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS etudiants_officiels_promotion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                annee_universitaire VARCHAR(20) NOT NULL,
                id_universitaire VARCHAR(100) NOT NULL,
                nom VARCHAR(150) NOT NULL,
                prenom VARCHAR(150) NOT NULL,
                email_outlook VARCHAR(255) NULL,
                source_import VARCHAR(80) NULL,
                active TINYINT(1) NOT NULL DEFAULT 1,
                date_import DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_officiel_annee_id (annee_universitaire, id_universitaire),
                INDEX idx_officiel_annee_active (annee_universitaire, active),
                INDEX idx_officiel_id_universitaire (id_universitaire)
            )
            """
        )

        connection.commit()
        print("Migration tables système terminée.")

    except Exception as e:
        connection.rollback()
        print("Erreur migration tables système :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    appliquer_migration()
