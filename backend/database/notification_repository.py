from database.db import get_db_connection


def creer_notification(
    utilisateur_id,
    role_destinataire,
    titre,
    message,
    type_notification,
    lien_action=None
):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO notifications_internes
            (utilisateur_id, role_destinataire, titre, message,
             type_notification, lien_action, lue)
            VALUES (%s, %s, %s, %s, %s, %s, 0)
            """,
            (
                utilisateur_id,
                role_destinataire,
                titre,
                message,
                type_notification,
                lien_action
            )
        )

        connection.commit()
        return True

    except Exception as erreur:
        connection.rollback()
        print("Erreur création notification interne :", erreur)
        return False

    finally:
        cursor.close()
        connection.close()


def get_utilisateurs_doyens_actifs():
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, identifiant_connexion
            FROM utilisateurs
            WHERE role = 'doyen'
              AND actif = 1
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_utilisateur_id_par_etudiant_id(etudiant_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT utilisateur_id
            FROM etudiants
            WHERE id = %s
            """,
            (etudiant_id,)
        )

        ligne = cursor.fetchone()

        if ligne is None:
            return None

        return ligne["utilisateur_id"]

    finally:
        cursor.close()
        connection.close()


def get_utilisateur_id_par_id_universitaire(id_universitaire):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT utilisateur_id
            FROM etudiants
            WHERE id_universitaire = %s
            """,
            (id_universitaire,)
        )

        ligne = cursor.fetchone()

        if ligne is None:
            return None

        return ligne["utilisateur_id"]

    finally:
        cursor.close()
        connection.close()


def notifier_tous_les_doyens(titre, message, type_notification, lien_action=None):
    doyens = get_utilisateurs_doyens_actifs()
    total = 0

    for doyen in doyens:
        notification_creee = creer_notification(
            doyen["id"],
            "doyen",
            titre,
            message,
            type_notification,
            lien_action
        )

        if notification_creee:
            total += 1

    return total


def notifier_doyens_nouveau_document(details_document):
    prenom = details_document.get("prenom", "")
    nom = details_document.get("nom", "")
    id_universitaire = details_document.get("id_universitaire", "")
    filiere = details_document.get("filiere_choisie", "")
    nom_fichier = details_document.get("nom_fichier_original", "")

    titre = "Nouveau document signé à confirmer"
    message = (
        f"{prenom} {nom} ({id_universitaire}) a déposé un document signé "
        f"pour la filière {filiere}. Document : {nom_fichier}."
    )

    return notifier_tous_les_doyens(
        titre,
        message,
        "nouveau_document_signe",
        "/doyen/documents"
    )


def notifier_etudiant_decision_document(details_choix, decision, remarque=None):
    etudiant_id = details_choix.get("etudiant_id")
    utilisateur_id = get_utilisateur_id_par_etudiant_id(etudiant_id)

    if utilisateur_id is None:
        return False

    filiere = details_choix.get("filiere_choisie", "")

    if decision == "confirmer":
        titre = "Document confirmé"
        message = (
            "Votre document signé a été confirmé par le doyen. "
            f"Votre choix de filière ({filiere}) est maintenant enregistré "
            "administrativement."
        )
        type_notification = "document_confirme"
    else:
        titre = "Document refusé"
        message = (
            "Votre document signé a été refusé par le doyen. "
            "Veuillez déposer une nouvelle version corrigée."
        )

        if remarque:
            message += f" Remarque : {remarque}"

        type_notification = "document_refuse"

    return creer_notification(
        utilisateur_id,
        "etudiant",
        titre,
        message,
        type_notification,
        "/etudiant/document"
    )


def notifier_etudiant_autorisation_test(id_universitaire):
    utilisateur_id = get_utilisateur_id_par_id_universitaire(id_universitaire)

    if utilisateur_id is None:
        return False

    return creer_notification(
        utilisateur_id,
        "etudiant",
        "Nouveau test autorisé",
        "Le doyen vous a autorisé à repasser le test d’orientation.",
        "autorisation_nouveau_test",
        "/etudiant/chatbot"
    )


def lister_notifications_utilisateur(utilisateur_id, limite=20, seulement_non_lues=False):
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        condition_lue = "AND lue = 0" if seulement_non_lues else ""

        cursor.execute(
            f"""
            SELECT
                id,
                utilisateur_id,
                role_destinataire,
                titre,
                message,
                type_notification,
                lien_action,
                lue,
                date_lecture,
                date_creation
            FROM notifications_internes
            WHERE utilisateur_id = %s
            {condition_lue}
            ORDER BY date_creation DESC, id DESC
            LIMIT %s
            """,
            (utilisateur_id, int(limite))
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def compter_notifications_non_lues(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return 0

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM notifications_internes
            WHERE utilisateur_id = %s
              AND lue = 0
            """,
            (utilisateur_id,)
        )

        ligne = cursor.fetchone()
        return ligne["total"] if ligne else 0

    finally:
        cursor.close()
        connection.close()


def marquer_notification_lue(notification_id, utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE notifications_internes
            SET lue = 1,
                date_lecture = CURRENT_TIMESTAMP
            WHERE id = %s
              AND utilisateur_id = %s
            """,
            (notification_id, utilisateur_id)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "Notification introuvable."
            }

        return {
            "success": True,
            "message": "Notification marquée comme lue."
        }

    except Exception as erreur:
        connection.rollback()
        return {
            "success": False,
            "message": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()


def marquer_toutes_notifications_lues(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return {
            "success": False,
            "message": "Connexion à la base impossible."
        }

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE notifications_internes
            SET lue = 1,
                date_lecture = CURRENT_TIMESTAMP
            WHERE utilisateur_id = %s
              AND lue = 0
            """,
            (utilisateur_id,)
        )

        total = cursor.rowcount
        connection.commit()

        return {
            "success": True,
            "message": f"{total} notification(s) marquée(s) comme lue(s).",
            "total": total
        }

    except Exception as erreur:
        connection.rollback()
        return {
            "success": False,
            "message": str(erreur)
        }

    finally:
        cursor.close()
        connection.close()
