import unicodedata

from database.db import get_db_connection


def normaliser(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = texte.encode("ascii", "ignore").decode("utf-8")
    texte = texte.replace("-", " ")
    texte = " ".join(texte.split())
    return texte


questions_finales = [
    {
        "code": "qf1",
        "texte": "Quels modules avez-vous le mieux réussis pendant le cycle préparatoire ?",
        "type": "choix_unique",
        "ordre": 1,
        "choix": [
            {
                "code": "qf1_prog",
                "texte": "Algorithmique, programmation C ou C++",
                "poids": {
                    "developpement full stack": 4,
                    "intelligence artificielle": 2,
                    "cybersecurite": 2
                }
            },
            {
                "code": "qf1_data",
                "texte": "Python, probabilités, statistiques ou analyse de données",
                "poids": {
                    "big data": 5,
                    "intelligence artificielle": 4
                }
            },
            {
                "code": "qf1_systeme",
                "texte": "Architecture des ordinateurs ou système d'exploitation",
                "poids": {
                    "cybersecurite": 5,
                    "developpement full stack": 2
                }
            },
            {
                "code": "qf1_electronique",
                "texte": "Électronique, électronique embarquée, Matlab ou Simulink",
                "poids": {
                    "robotique et cobotique": 5,
                    "intelligence artificielle": 2
                }
            },
            {
                "code": "qf1_math",
                "texte": "Analyse, algèbre ou analyse numérique",
                "poids": {
                    "intelligence artificielle": 4,
                    "big data": 3,
                    "robotique et cobotique": 2
                }
            }
        ]
    },
    {
        "code": "qf2",
        "texte": "Quels modules avez-vous le plus appréciés ?",
        "type": "choix_unique",
        "ordre": 2,
        "choix": [
            {
                "code": "qf2_data",
                "texte": "Statistiques, Python et analyse de données",
                "poids": {
                    "big data": 5,
                    "intelligence artificielle": 3
                }
            },
            {
                "code": "qf2_ia",
                "texte": "Algorithmes, mathématiques et modèles intelligents",
                "poids": {
                    "intelligence artificielle": 5,
                    "big data": 2
                }
            },
            {
                "code": "qf2_dev",
                "texte": "Programmation et développement d'applications",
                "poids": {
                    "developpement full stack": 5,
                    "intelligence artificielle": 2
                }
            },
            {
                "code": "qf2_cyber",
                "texte": "Systèmes, réseaux et sécurité",
                "poids": {
                    "cybersecurite": 5,
                    "developpement full stack": 2
                }
            },
            {
                "code": "qf2_robot",
                "texte": "Électronique, robotique et automatisation",
                "poids": {
                    "robotique et cobotique": 5,
                    "intelligence artificielle": 2
                }
            }
        ]
    },
    {
        "code": "qf3",
        "texte": "Quel domaine vous semble le plus difficile actuellement ?",
        "type": "choix_unique",
        "ordre": 3,
        "choix": [
            {
                "code": "qf3_math",
                "texte": "Mathématiques et statistiques",
                "poids": {}
            },
            {
                "code": "qf3_prog",
                "texte": "Programmation",
                "poids": {}
            },
            {
                "code": "qf3_systeme",
                "texte": "Systèmes et architecture",
                "poids": {}
            },
            {
                "code": "qf3_electronique",
                "texte": "Électronique et embarqué",
                "poids": {}
            },
            {
                "code": "qf3_aucun",
                "texte": "Aucun domaine en particulier",
                "poids": {
                    "big data": 1,
                    "intelligence artificielle": 1,
                    "cybersecurite": 1,
                    "developpement full stack": 1,
                    "robotique et cobotique": 1
                }
            }
        ]
    },
    {
        "code": "qf4",
        "texte": "Quel est votre niveau réel dans les domaines principaux ?",
        "type": "choix_unique",
        "ordre": 4,
        "choix": [
            {
                "code": "qf4_prog",
                "texte": "Bon niveau en programmation",
                "poids": {
                    "developpement full stack": 5,
                    "intelligence artificielle": 3,
                    "cybersecurite": 2
                }
            },
            {
                "code": "qf4_math",
                "texte": "Bon niveau en mathématiques et statistiques",
                "poids": {
                    "big data": 5,
                    "intelligence artificielle": 5
                }
            },
            {
                "code": "qf4_systeme",
                "texte": "Bon niveau en systèmes, architecture ou réseaux",
                "poids": {
                    "cybersecurite": 5,
                    "developpement full stack": 2
                }
            },
            {
                "code": "qf4_embarque",
                "texte": "Bon niveau en électronique ou systèmes embarqués",
                "poids": {
                    "robotique et cobotique": 5,
                    "intelligence artificielle": 2
                }
            }
        ]
    },
    {
        "code": "qf5",
        "texte": "Quel type de projet préférez-vous réaliser ?",
        "type": "choix_unique",
        "ordre": 5,
        "choix": [
            {
                "code": "qf5_data",
                "texte": "Analyser de grandes quantités de données",
                "poids": {
                    "big data": 5,
                    "intelligence artificielle": 2
                }
            },
            {
                "code": "qf5_ia",
                "texte": "Créer des modèles intelligents capables d'apprendre",
                "poids": {
                    "intelligence artificielle": 5,
                    "big data": 2
                }
            },
            {
                "code": "qf5_dev",
                "texte": "Développer une application web ou mobile complète",
                "poids": {
                    "developpement full stack": 5
                }
            },
            {
                "code": "qf5_cyber",
                "texte": "Sécuriser des systèmes ou détecter des failles",
                "poids": {
                    "cybersecurite": 5
                }
            },
            {
                "code": "qf5_robot",
                "texte": "Automatiser un système physique ou travailler sur un robot",
                "poids": {
                    "robotique et cobotique": 5,
                    "intelligence artificielle": 2
                }
            }
        ]
    },
    {
        "code": "qf6",
        "texte": "Quelle activité vous motive le plus ?",
        "type": "choix_unique",
        "ordre": 6,
        "choix": [
            {
                "code": "qf6_analyse",
                "texte": "Analyser et interpréter des informations",
                "poids": {
                    "big data": 5
                }
            },
            {
                "code": "qf6_innovation",
                "texte": "Faire de la recherche et créer des solutions intelligentes",
                "poids": {
                    "intelligence artificielle": 5
                }
            },
            {
                "code": "qf6_conception",
                "texte": "Concevoir et développer des plateformes",
                "poids": {
                    "developpement full stack": 5
                }
            },
            {
                "code": "qf6_protection",
                "texte": "Protéger les données, les réseaux et les systèmes",
                "poids": {
                    "cybersecurite": 5
                }
            },
            {
                "code": "qf6_auto",
                "texte": "Automatiser, expérimenter et contrôler des systèmes",
                "poids": {
                    "robotique et cobotique": 5
                }
            }
        ]
    },
    {
        "code": "qf7",
        "texte": "Quel métier vous attire le plus ?",
        "type": "choix_unique",
        "ordre": 7,
        "choix": [
            {
                "code": "qf7_data_engineer",
                "texte": "Data Analyst ou Data Engineer",
                "poids": {
                    "big data": 5
                }
            },
            {
                "code": "qf7_ai_engineer",
                "texte": "AI Engineer ou Machine Learning Engineer",
                "poids": {
                    "intelligence artificielle": 5
                }
            },
            {
                "code": "qf7_fullstack",
                "texte": "Développeur Full Stack",
                "poids": {
                    "developpement full stack": 5
                }
            },
            {
                "code": "qf7_cyber",
                "texte": "Ingénieur Cybersécurité",
                "poids": {
                    "cybersecurite": 5
                }
            },
            {
                "code": "qf7_robot",
                "texte": "Ingénieur Robotique ou Automatisation",
                "poids": {
                    "robotique et cobotique": 5
                }
            },
            {
                "code": "qf7_indecis",
                "texte": "Je ne sais pas encore",
                "poids": {
                    "big data": 1,
                    "intelligence artificielle": 1,
                    "cybersecurite": 1,
                    "developpement full stack": 1,
                    "robotique et cobotique": 1
                }
            }
        ]
    },
    {
        "code": "qf8",
        "texte": "Quel type de projet avez-vous déjà réalisé ou aimé réaliser ?",
        "type": "choix_unique",
        "ordre": 8,
        "choix": [
            {
                "code": "qf8_data",
                "texte": "Projet d'analyse de données",
                "poids": {
                    "big data": 5
                }
            },
            {
                "code": "qf8_ia",
                "texte": "Projet IA ou machine learning",
                "poids": {
                    "intelligence artificielle": 5
                }
            },
            {
                "code": "qf8_web",
                "texte": "Projet web ou mobile",
                "poids": {
                    "developpement full stack": 5
                }
            },
            {
                "code": "qf8_securite",
                "texte": "Projet sécurité ou systèmes",
                "poids": {
                    "cybersecurite": 5
                }
            },
            {
                "code": "qf8_robot",
                "texte": "Projet électronique, robotique ou automatisation",
                "poids": {
                    "robotique et cobotique": 5
                }
            },
            {
                "code": "qf8_aucun",
                "texte": "Aucun projet précis pour le moment",
                "poids": {}
            }
        ]
    },
    {
        "code": "qf9",
        "texte": "Ressentez-vous une hésitation entre plusieurs spécialités ?",
        "type": "choix_unique",
        "ordre": 9,
        "choix": [
            {
                "code": "qf9_bigdata_ia",
                "texte": "J'hésite entre Big Data et Intelligence Artificielle",
                "poids": {
                    "big data": 2,
                    "intelligence artificielle": 2
                }
            },
            {
                "code": "qf9_ia_robot",
                "texte": "J'hésite entre Intelligence Artificielle et Robotique",
                "poids": {
                    "intelligence artificielle": 2,
                    "robotique et cobotique": 2
                }
            },
            {
                "code": "qf9_full_cyber",
                "texte": "J'hésite entre Développement Full Stack et Cybersécurité",
                "poids": {
                    "developpement full stack": 2,
                    "cybersecurite": 2
                }
            },
            {
                "code": "qf9_bigdata_full",
                "texte": "J'hésite entre Big Data et Développement Full Stack",
                "poids": {
                    "big data": 2,
                    "developpement full stack": 2
                }
            },
            {
                "code": "qf9_aucune",
                "texte": "Je n'ai pas d'hésitation précise",
                "poids": {}
            }
        ]
    },
    {
        "code": "qf10",
        "texte": "Décrivez brièvement votre profil, vos intérêts et ce que vous attendez de votre future spécialité.",
        "type": "texte_libre",
        "ordre": 10,
        "choix": []
    }
]


def get_specialites():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT id, nom FROM specialites WHERE active = TRUE")
    specialites = cursor.fetchall()

    cursor.close()
    connection.close()

    dictionnaire = {}

    for specialite in specialites:
        dictionnaire[normaliser(specialite["nom"])] = specialite["id"]

    return dictionnaire


def inserer_ou_modifier_question(cursor, question):
    cursor.execute(
        """
        SELECT id
        FROM questions
        WHERE code_question = %s
        """,
        (question["code"],)
    )

    existante = cursor.fetchone()

    if existante:
        cursor.execute(
            """
            UPDATE questions
            SET texte = %s,
                type_question = %s,
                statut_question = 'finale',
                ordre = %s,
                active = TRUE
            WHERE id = %s
            """,
            (
                question["texte"],
                question["type"],
                question["ordre"],
                existante["id"]
            )
        )

        return existante["id"]

    cursor.execute(
        """
        INSERT INTO questions
        (code_question, texte, type_question, statut_question, ordre, active)
        VALUES (%s, %s, %s, 'finale', %s, TRUE)
        """,
        (
            question["code"],
            question["texte"],
            question["type"],
            question["ordre"]
        )
    )

    return cursor.lastrowid


def inserer_ou_modifier_choix(cursor, question_id, choix):
    cursor.execute(
        """
        SELECT id
        FROM choix_reponses
        WHERE code_reponse = %s
        """,
        (choix["code"],)
    )

    existant = cursor.fetchone()

    if existant:
        cursor.execute(
            """
            UPDATE choix_reponses
            SET question_id = %s,
                texte = %s,
                active = TRUE
            WHERE id = %s
            """,
            (
                question_id,
                choix["texte"],
                existant["id"]
            )
        )

        return existant["id"]

    cursor.execute(
        """
        INSERT INTO choix_reponses
        (question_id, code_reponse, texte, active)
        VALUES (%s, %s, %s, TRUE)
        """,
        (
            question_id,
            choix["code"],
            choix["texte"]
        )
    )

    return cursor.lastrowid


def inserer_poids(cursor, choix_reponse_id, poids, specialites):
    cursor.execute(
        """
        DELETE FROM poids_reponses
        WHERE choix_reponse_id = %s
        """,
        (choix_reponse_id,)
    )

    for nom_specialite, valeur in poids.items():
        nom_normalise = normaliser(nom_specialite)

        if nom_normalise not in specialites:
            print(f"Spécialité introuvable : {nom_specialite}")
            continue

        cursor.execute(
            """
            INSERT INTO poids_reponses
            (choix_reponse_id, specialite_id, poids)
            VALUES (%s, %s, %s)
            """,
            (
                choix_reponse_id,
                specialites[nom_normalise],
                valeur
            )
        )


def inserer_questions_finales():
    specialites = get_specialites()
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        for question in questions_finales:
            question_id = inserer_ou_modifier_question(cursor, question)

            for choix in question["choix"]:
                choix_id = inserer_ou_modifier_choix(
                    cursor,
                    question_id,
                    choix
                )

                inserer_poids(
                    cursor,
                    choix_id,
                    choix["poids"],
                    specialites
                )

        connection.commit()

        print("Questions finales insérées avec succès.")

    except Exception as e:
        connection.rollback()
        print("Erreur :", e)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    inserer_questions_finales()