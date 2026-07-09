from werkzeug.security import generate_password_hash

from database.db import get_db_connection


def appliquer_migration():
    """Crée un compte étudiant de démonstration pour faciliter les tests locaux.

    Ce compte évite de bloquer la démonstration si la réception du code email
    Outlook/Gmail prend du temps. Il est destiné uniquement aux tests locaux.
    """
    connection = get_db_connection()

    if connection is None:
        print("Migration compte test étudiant ignorée : connexion MySQL impossible.")
        return

    cursor = connection.cursor(dictionary=True)

    try:
        identifiant = "2300259"
        mot_de_passe = "123456"

        cursor.execute(
            """
            SELECT id
            FROM utilisateurs
            WHERE identifiant_connexion = %s
            """,
            (identifiant,)
        )
        utilisateur = cursor.fetchone()

        if utilisateur is not None:
            print("Compte étudiant de test déjà présent.")
            return

        mot_de_passe_hash = generate_password_hash(mot_de_passe)

        cursor.execute(
            """
            INSERT INTO utilisateurs
            (identifiant_connexion, mot_de_passe_hash, role, actif)
            VALUES (%s, %s, 'etudiant', TRUE)
            """,
            (identifiant, mot_de_passe_hash)
        )

        utilisateur_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO etudiants
            (utilisateur_id, id_universitaire, nom, prenom, email, promotion)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                utilisateur_id,
                identifiant,
                "Test",
                "Etudiant",
                "etudiant.test@eidia.ueuromed.org",
                "2025-2026"
            )
        )

        connection.commit()
        print("Compte étudiant de test créé : 2300259 / 123456")

    except Exception as exc:
        connection.rollback()
        print(f"Erreur migration compte test étudiant : {exc}")

    finally:
        cursor.close()
        connection.close()
