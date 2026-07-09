QUESTIONS_PROVISOIRES = [
    {
        "id": "q1",
        "texte": "Quel domaine vous intéresse le plus ?",
        "type": "choix_unique",
        "reponses": [
            {"id": "q1_data", "texte": "Analyse de données"},
            {"id": "q1_ai", "texte": "Intelligence artificielle"},
            {"id": "q1_cyber", "texte": "Cybersécurité"},
            {"id": "q1_fullstack", "texte": "Développement web et mobile"},
            {"id": "q1_robot", "texte": "Robotique et automatisation"}
        ]
    },
    {
        "id": "q2",
        "texte": "Quel type de projet préférez-vous réaliser ?",
        "type": "choix_unique",
        "reponses": [
            {"id": "q2_bigdata", "texte": "Analyser de grands volumes de données"},
            {"id": "q2_model", "texte": "Créer des modèles intelligents"},
            {"id": "q2_security", "texte": "Protéger des systèmes informatiques"},
            {"id": "q2_app", "texte": "Créer des applications complètes"},
            {"id": "q2_robot", "texte": "Créer des systèmes automatisés"}
        ]
    },
    {
        "id": "q3",
        "texte": "Comment évaluez-vous votre niveau en programmation ?",
        "type": "choix_unique",
        "reponses": [
            {"id": "q3_debutant", "texte": "Débutant"},
            {"id": "q3_moyen", "texte": "Moyen"},
            {"id": "q3_bon", "texte": "Bon"}
        ]
    },
    {
        "id": "q4",
        "texte": "Décrivez brièvement ce que vous aimez faire dans un projet.",
        "type": "texte_libre",
        "reponses": []
    }
]


def get_questions_provisoires():
    return QUESTIONS_PROVISOIRES