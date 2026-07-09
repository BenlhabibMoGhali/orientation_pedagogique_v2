import mysql.connector
from mysql.connector import Error

from config import Config


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        return connection

    except Error as erreur:
        print("Erreur de connexion à MySQL :", erreur)
        return None


def tester_connexion_db():
    connection = get_db_connection()

    if connection is None:
        return {
            "status": "error",
            "message": "Connexion à la base de données échouée."
        }

    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        database_name = cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Connexion à la base de données réussie.",
            "database": database_name[0]
        }

    return {
        "status": "error",
        "message": "Connexion non active."
    }