from datetime import date

from database.db import get_db_connection


def calculer_annee_universitaire_depuis_date(date_reference=None):
    """
    Calcule l'année universitaire selon la règle :
    - septembre à décembre : année actuelle / année suivante
    - janvier à juin : année précédente / année actuelle
    - juillet et août : préparation de l'année qui commence en septembre
    Exemple : juillet 2026 -> 2026/2027
    """
    if date_reference is None:
        date_reference = date.today()

    mois = date_reference.month
    annee = date_reference.year

    if mois >= 7:
        annee_debut = annee
    else:
        annee_debut = annee - 1

    annee_fin = annee_debut + 1

    return {
        "code": f"{annee_debut}/{annee_fin}",
        "annee_debut": annee_debut,
        "annee_fin": annee_fin,
        "date_debut": f"{annee_debut}-09-01",
        "date_fin": f"{annee_fin}-06-30"
    }


def assurer_annee_universitaire_active():
    """
    Garantit qu'une année universitaire active existe en base.
    Si aucune année active n'existe, le système crée ou active l'année calculée.
    """
    annee_calculee = calculer_annee_universitaire_depuis_date()

    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible.",
            "annee_universitaire": annee_calculee
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM annees_universitaires
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        )

        annee_active = cursor.fetchone()

        if annee_active is not None:
            return {
                "success": True,
                "message": "Année universitaire active récupérée.",
                "annee_universitaire": annee_active
            }

        cursor.execute(
            """
            INSERT INTO annees_universitaires
            (code, annee_debut, annee_fin, date_debut, date_fin, active)
            VALUES (%s, %s, %s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
                annee_debut = VALUES(annee_debut),
                annee_fin = VALUES(annee_fin),
                date_debut = VALUES(date_debut),
                date_fin = VALUES(date_fin),
                active = 1
            """,
            (
                annee_calculee["code"],
                annee_calculee["annee_debut"],
                annee_calculee["annee_fin"],
                annee_calculee["date_debut"],
                annee_calculee["date_fin"]
            )
        )

        connection.commit()

        cursor.execute(
            """
            SELECT *
            FROM annees_universitaires
            WHERE code = %s
            LIMIT 1
            """,
            (annee_calculee["code"],)
        )

        annee_active = cursor.fetchone()

        return {
            "success": True,
            "message": "Année universitaire active créée automatiquement.",
            "annee_universitaire": annee_active
        }

    except Exception as erreur:
        connection.rollback()

        return {
            "success": False,
            "message": "Erreur lors de la récupération de l'année universitaire active.",
            "erreur": str(erreur),
            "annee_universitaire": annee_calculee
        }

    finally:
        cursor.close()
        connection.close()


def get_annee_universitaire_active():
    resultat = assurer_annee_universitaire_active()

    if resultat.get("success"):
        return resultat["annee_universitaire"]

    return resultat.get("annee_universitaire")


def get_code_annee_universitaire_active():
    annee = get_annee_universitaire_active()

    if annee is None:
        return calculer_annee_universitaire_depuis_date()["code"]

    return annee.get("code")


def lister_annees_universitaires():
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible.",
            "annees": []
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT *
            FROM annees_universitaires
            ORDER BY annee_debut DESC
            """
        )

        return {
            "success": True,
            "annees": cursor.fetchall()
        }

    finally:
        cursor.close()
        connection.close()
