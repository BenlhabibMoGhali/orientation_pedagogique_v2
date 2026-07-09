from database.db import get_db_connection


def get_specialites_actives():
    connection = get_db_connection()

    if connection is None:
        return []

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, nom
            FROM specialites
            WHERE active = TRUE
            ORDER BY id ASC
            """
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def initialiser_scores():
    specialites = get_specialites_actives()
    scores = {}

    for specialite in specialites:
        scores[specialite["nom"]] = 0

    return scores


def ajouter_scores_reponse(scores, code_reponse):
    connection = get_db_connection()

    if connection is None:
        return scores

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 
                s.nom AS specialite,
                pr.poids
            FROM choix_reponses cr
            JOIN poids_reponses pr ON cr.id = pr.choix_reponse_id
            JOIN specialites s ON pr.specialite_id = s.id
            WHERE cr.code_reponse = %s
              AND cr.active = TRUE
              AND s.active = TRUE
            """,
            (code_reponse,)
        )

        poids = cursor.fetchall()

        for ligne in poids:
            specialite = ligne["specialite"]
            valeur = ligne["poids"]

            if specialite not in scores:
                scores[specialite] = 0

            scores[specialite] += valeur

        return scores

    finally:
        cursor.close()
        connection.close()


def analyser_reponse_libre(scores, reponse_libre):
    if reponse_libre is None:
        return scores, []

    texte = reponse_libre.lower()
    mots_detectes = []

    mots_big_data = [
        "data", "donnees", "données", "statistique", "statistiques",
        "analyse", "analyser", "python", "visualisation", "tableau",
        "base de donnees", "base de données", "big data"
    ]

    mots_ia = [
        "ia", "intelligence artificielle", "machine learning",
        "apprentissage", "modele", "modèle", "modeles", "modèles",
        "prediction", "prédiction", "algorithme intelligent"
    ]

    mots_cyber = [
        "cyber", "cybersecurite", "cybersécurité", "securite",
        "sécurité", "protection", "piratage", "attaque",
        "reseau", "réseau", "faille", "vulnerabilite", "vulnérabilité"
    ]

    mots_full_stack = [
        "web", "site", "application", "frontend", "backend",
        "react", "flask", "developpement", "développement",
        "interface", "plateforme"
    ]

    mots_robotique = [
        "robot", "robotique", "automatisation", "automatique",
        "embarque", "embarqué", "electronique", "électronique",
        "matlab", "simulink", "capteur"
    ]

    for mot in mots_big_data:
        if mot in texte:
            scores["Big Data"] = scores.get("Big Data", 0) + 2
            mots_detectes.append(mot)

    for mot in mots_ia:
        if mot in texte:
            scores["Intelligence Artificielle"] = scores.get("Intelligence Artificielle", 0) + 2
            mots_detectes.append(mot)

    for mot in mots_cyber:
        if mot in texte:
            scores["Cybersécurité"] = scores.get("Cybersécurité", 0) + 2
            mots_detectes.append(mot)

    for mot in mots_full_stack:
        if mot in texte:
            scores["Développement Full Stack"] = scores.get("Développement Full Stack", 0) + 2
            mots_detectes.append(mot)

    for mot in mots_robotique:
        if mot in texte:
            scores["Robotique et Cobotique"] = scores.get("Robotique et Cobotique", 0) + 2
            mots_detectes.append(mot)

    return scores, list(set(mots_detectes))


def calculer_pourcentages(scores):
    total = sum(scores.values())

    pourcentages = {}

    if total == 0:
        nombre_specialites = len(scores)

        if nombre_specialites == 0:
            return {}

        pourcentage_egal = round(100 / nombre_specialites, 2)

        for specialite in scores:
            pourcentages[specialite] = pourcentage_egal

        return pourcentages

    for specialite, score in scores.items():
        pourcentages[specialite] = round((score / total) * 100, 2)

    return pourcentages


def trouver_specialite_recommandee(pourcentages):
    if not pourcentages:
        return None

    return max(pourcentages, key=pourcentages.get)


def trouver_specialites_proches(pourcentages, specialite_recommandee):
    if not pourcentages or specialite_recommandee is None:
        return []

    meilleur_pourcentage = pourcentages[specialite_recommandee]
    specialites_proches = []

    for specialite, pourcentage in pourcentages.items():
        if specialite != specialite_recommandee:
            difference = meilleur_pourcentage - pourcentage

            if difference <= 10:
                specialites_proches.append({
                    "specialite": specialite,
                    "pourcentage": pourcentage,
                    "difference": round(difference, 2)
                })

    return specialites_proches


def calculer_recommandation(reponses, reponse_libre=""):
    scores = initialiser_scores()

    for code_reponse in reponses:
        scores = ajouter_scores_reponse(scores, code_reponse)

    scores, mots_detectes = analyser_reponse_libre(
        scores,
        reponse_libre
    )

    pourcentages = calculer_pourcentages(scores)

    specialite_recommandee = trouver_specialite_recommandee(
        pourcentages
    )

    specialites_proches = trouver_specialites_proches(
        pourcentages,
        specialite_recommandee
    )

    return {
        "scores": scores,
        "pourcentages": pourcentages,
        "specialite_recommandee": specialite_recommandee,
        "specialites_proches": specialites_proches,
        "analyse_reponse_libre": {
            "reponse_libre": reponse_libre,
            "mots_detectes": mots_detectes
        },
        "source": "Calcul dynamique basé sur MySQL et analyse simple de la réponse libre."
    }