def analyser_reponse_libre(texte):
    texte = texte.lower()

    scores = {
        "Big Data": 0,
        "Intelligence Artificielle": 0,
        "Cybersécurité": 0,
        "Développement Full Stack": 0,
        "Robotique et Cobotique": 0
    }

    mots_cles = {
        "Big Data": ["donnée", "données", "data", "analyse", "statistique", "tableau", "volume"],
        "Intelligence Artificielle": ["ia", "intelligence", "modèle", "machine learning", "apprendre", "prédiction"],
        "Cybersécurité": ["sécurité", "cyber", "attaque", "protection", "réseau", "système"],
        "Développement Full Stack": ["application", "web", "mobile", "site", "interface", "frontend", "backend"],
        "Robotique et Cobotique": ["robot", "robotique", "automatisation", "capteur", "objet", "système intelligent"]
    }

    for specialite, liste_mots in mots_cles.items():
        for mot in liste_mots:
            if mot in texte:
                scores[specialite] += 2

    return scores