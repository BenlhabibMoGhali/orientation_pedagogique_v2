import json
import os
import unicodedata


SPECIALITES = [
    "Big Data",
    "Intelligence Artificielle",
    "Cybersécurité",
    "Développement Full Stack",
    "Robotique et Cobotique"
]


TYPES_MESSAGES_VALIDES = [
    "reponse_orientation",
    "demande_clarification",
    "demande_information_filiere",
    "hors_sujet"
]


def gemini_est_disponible():
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key is None or api_key.strip() == "":
        return False

    try:
        from google import genai  # noqa: F401
        return True
    except Exception:
        return False


def normaliser_texte(texte):
    if texte is None:
        return ""

    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = texte.encode("ascii", "ignore").decode("utf-8")
    texte = texte.replace("-", " ")
    texte = texte.replace("_", " ")
    texte = " ".join(texte.split())

    return texte


def extraire_json_depuis_texte(texte):
    if texte is None:
        return None

    try:
        return json.loads(texte)
    except Exception:
        pass

    debut = texte.find("{")
    fin = texte.rfind("}")

    if debut == -1 or fin == -1 or fin <= debut:
        return None

    morceau = texte[debut:fin + 1]

    try:
        return json.loads(morceau)
    except Exception:
        return None


def get_scores_vides():
    return {
        "Big Data": 0,
        "Intelligence Artificielle": 0,
        "Cybersécurité": 0,
        "Développement Full Stack": 0,
        "Robotique et Cobotique": 0
    }


def get_message_defaut_selon_type(type_message):
    if type_message == "demande_clarification":
        return (
            "Oui, vous pouvez demander une précision. "
            "Pour continuer le test, répondez ensuite à la question actuelle "
            "avec vos préférences personnelles."
        )

    if type_message == "demande_information_filiere":
        return (
            "Je peux vous donner des informations sur cette filière. "
            "Ensuite, vous pourrez répondre à la question actuelle pour continuer."
        )

    if type_message == "hors_sujet":
        return (
            "Votre message ne semble pas répondre directement à la question "
            "d’orientation. Veuillez reformuler ou répondre à la question actuelle."
        )

    return ""


def nettoyer_reponse_gemini(donnees):
    if donnees is None:
        return None

    type_message = donnees.get("type_message")

    if type_message not in TYPES_MESSAGES_VALIDES:
        type_message = "demande_clarification"

    donnees["type_message"] = type_message

    if "message_bot" not in donnees or donnees["message_bot"] is None:
        donnees["message_bot"] = ""

    if "scores" not in donnees or not isinstance(donnees["scores"], dict):
        donnees["scores"] = get_scores_vides()

    scores_corriges = get_scores_vides()

    for specialite in SPECIALITES:
        valeur = donnees["scores"].get(specialite, 0)

        try:
            valeur = int(valeur)
        except Exception:
            valeur = 0

        if valeur < 0:
            valeur = 0

        if valeur > 5:
            valeur = 5

        scores_corriges[specialite] = valeur

    donnees["scores"] = scores_corriges

    if type_message != "reponse_orientation":
        donnees["scores"] = get_scores_vides()

        if donnees["message_bot"].strip() == "":
            donnees["message_bot"] = get_message_defaut_selon_type(type_message)

    if type_message == "reponse_orientation":
        donnees["message_bot"] = ""

    if "domaines_detectes" not in donnees or not isinstance(donnees["domaines_detectes"], list):
        donnees["domaines_detectes"] = []

    if "hesitation_detectee" not in donnees:
        donnees["hesitation_detectee"] = False

    if "commentaire_analyse" not in donnees or donnees["commentaire_analyse"] is None:
        donnees["commentaire_analyse"] = ""

    donnees["source"] = "gemini"

    return donnees


def construire_prompt_principal(
    question_actuelle,
    message_etudiant,
    scores_actuels,
    historique=None
):
    if historique is None:
        historique = []

    user_context = {
        "question_actuelle": question_actuelle,
        "message_etudiant": message_etudiant,
        "scores_actuels": scores_actuels,
        "historique_des_reponses": historique
    }

    return f"""
Tu es un assistant d’orientation pédagogique intégré dans une plateforme universitaire.

Ton rôle est d’analyser CHAQUE message de l’étudiant avec Gemini avant que le système décide de passer ou non à la question suivante.

Tu dois toujours faire deux choses :
1. Classifier le message de l’étudiant.
2. Retourner uniquement un JSON valide.

==================================================
RÈGLE PRINCIPALE
==================================================

Le questionnaire ne doit avancer que si :
type_message = "reponse_orientation"

Dans tous les autres cas, le système doit rester sur la même question.

==================================================
CLASSIFICATION OBLIGATOIRE
==================================================

Tu dois choisir exactement un seul type_message parmi :

1. "reponse_orientation"

Utilise ce type seulement si le message de l’étudiant répond réellement à la question actuelle avec :
- une préférence,
- un module,
- un domaine,
- une expérience,
- un niveau,
- un projet,
- un métier,
- une hésitation entre spécialités,
- ou une information utile pour l’orientation.

Dans ce cas :
- message_bot doit être une chaîne vide.
- scores doit contenir des valeurs entre 0 et 5.
- domaines_detectes doit contenir les spécialités ou domaines reconnus.
- Le système passera à la question suivante.

2. "demande_clarification"

Utilise ce type si l’étudiant :
- pose une question,
- demande une explication,
- demande s’il peut choisir plusieurs options,
- demande combien d’éléments il peut citer,
- demande s’il peut citer deux domaines,
- demande s’il peut donner plusieurs propositions,
- dit qu’il n’a pas compris,
- demande une précision sur le fonctionnement du test,
- dit qu’il ne sait pas quoi répondre et demande une proposition,
- demande au chatbot de proposer une idée de projet ou une piste.

Dans ce cas :
- scores doit être 0 pour toutes les spécialités.
- message_bot doit répondre clairement à la question de l’étudiant.
- Le système doit rester sur la même question.

3. "demande_information_filiere"

Utilise ce type si l’étudiant demande des informations sur :
- une filière,
- un métier,
- le marché du travail,
- les débouchés,
- une spécialité,
- la différence entre deux spécialités.

Dans ce cas :
- scores doit être 0 pour toutes les spécialités.
- message_bot doit répondre utilement.
- Le système doit rester sur la même question.

4. "hors_sujet"

Utilise ce type si le message n’a aucun rapport avec :
- la question actuelle,
- l’orientation,
- les filières,
- les modules,
- les études,
- le choix de spécialité.

Dans ce cas :
- scores doit être 0 pour toutes les spécialités.
- message_bot doit demander à l’étudiant de revenir à la question actuelle.
- Le système doit rester sur la même question.

==================================================
EXEMPLES IMPORTANTS
==================================================

Message étudiant :
"est ce que je peux choisir 2 domaines"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"est ce que je peux choisir plus que 3 propositions"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"je voulais dire est ce que je peux choisir 2 domaines"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"je peux citer python et analyse ?"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"combien de modules je peux citer ?"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"j’ai aimé Python et l’analyse parce que j’aime résoudre des problèmes"
Réponse attendue :
type_message = "reponse_orientation"

Message étudiant :
"j’ai bien réussi programmation python, analyse et statistiques"
Réponse attendue :
type_message = "reponse_orientation"

Message étudiant :
"j’ai apprécié Python, l’analyse et les statistiques"
Réponse attendue :
type_message = "reponse_orientation"

Message étudiant :
"c’est quoi la cybersécurité ?"
Réponse attendue :
type_message = "demande_information_filiere"

Message étudiant :
"quelle est la différence entre Big Data et IA ?"
Réponse attendue :
type_message = "demande_information_filiere"

Message étudiant :
"je n’ai pas compris la question"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"je ne sais pas, propose-moi un projet"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"j'aimerais bien que tu me proposes une idée"
Réponse attendue :
type_message = "demande_clarification"

Message étudiant :
"salut ça va ?"
Réponse attendue :
type_message = "hors_sujet"

==================================================
RÈGLES DE RÉPONSE POUR LES CLARIFICATIONS
==================================================

Si l’étudiant demande s’il peut citer plusieurs domaines, modules, options ou propositions, tu dois répondre clairement que oui.

Exemple de message_bot :
"Oui, vous pouvez citer plusieurs éléments dans votre réponse. Par exemple, vous pouvez mentionner deux modules, deux domaines ou plusieurs préférences si cela représente mieux votre profil. L’important est d’expliquer brièvement pourquoi. Ensuite, répondez à la question actuelle pour continuer."

==================================================
RÈGLES DE SCORING
==================================================

Tu dois attribuer des scores uniquement si :
type_message = "reponse_orientation"

Barème :
0 = aucun lien
1 = lien très faible
2 = lien faible
3 = lien moyen
4 = lien fort
5 = lien très fort

Exemples :
- Python, statistiques, analyse, données, SQL : Big Data
- IA, machine learning, deep learning, modèle, prédiction : Intelligence Artificielle
- sécurité, réseau, hacking, protection, systèmes : Cybersécurité
- web, application, frontend, backend, React, Flask : Développement Full Stack
- robotique, électronique, automatisation, capteurs, embarqué : Robotique et Cobotique

Si type_message est différent de "reponse_orientation", tous les scores doivent être 0.

==================================================
FORMAT JSON OBLIGATOIRE
==================================================

Tu dois retourner uniquement un JSON valide.
Ne mets aucun texte avant le JSON.
Ne mets aucun texte après le JSON.
Ne mets pas de bloc Markdown.

Le JSON doit respecter exactement cette structure :

{{
  "type_message": "reponse_orientation",
  "message_bot": "",
  "scores": {{
    "Big Data": 0,
    "Intelligence Artificielle": 0,
    "Cybersécurité": 0,
    "Développement Full Stack": 0,
    "Robotique et Cobotique": 0
  }},
  "domaines_detectes": [],
  "hesitation_detectee": false,
  "commentaire_analyse": ""
}}

==================================================
CONTEXTE ACTUEL
==================================================

Voici le contexte actuel au format JSON :

{json.dumps(user_context, ensure_ascii=False)}
"""


def traiter_message_chat_avec_gemini(
    question_actuelle,
    message_etudiant,
    scores_actuels,
    historique=None
):
    if not gemini_est_disponible():
        return None

    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        client = genai.Client(api_key=api_key)

        prompt_complet = construire_prompt_principal(
            question_actuelle,
            message_etudiant,
            scores_actuels,
            historique
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt_complet
        )

        texte = response.text
        donnees = extraire_json_depuis_texte(texte)

        return nettoyer_reponse_gemini(donnees)

    except Exception as e:
        print("Erreur Gemini :", e)
        return None


def generer_reponse_clarification_locale(question_actuelle, message_etudiant):
    texte = normaliser_texte(message_etudiant)

    parle_de_plusieurs_choix = (
        "2" in texte
        or "deux" in texte
        or "plusieurs" in texte
        or "plus de" in texte
        or "plus que" in texte
        or "options" in texte
        or "propositions" in texte
        or "domaines" in texte
        or "choix" in texte
        or "modules" in texte
    )

    if parle_de_plusieurs_choix:
        return (
            "Oui, vous pouvez citer plusieurs éléments dans votre réponse. "
            "Par exemple, vous pouvez mentionner deux modules, deux domaines "
            "ou plusieurs préférences si cela représente mieux votre profil. "
            "L’important est d’expliquer brièvement pourquoi vous les avez appréciés. "
            "Vous pouvez donc répondre à la question actuelle en citant vos domaines "
            "ou modules préférés."
        )

    demande_proposition = (
        "propose" in texte
        or "proposer" in texte
        or "proposes" in texte
        or "je ne sais pas" in texte
        or "je sais pas" in texte
        or "quoi ecrire" in texte
        or "que choisir" in texte
        or "quel projet" in texte
    )

    if demande_proposition:
        return (
            "Je peux vous proposer des pistes, mais le choix doit rester basé sur "
            "vos préférences. Par exemple : si vous aimez analyser des données et "
            "faire des tableaux de bord, pensez à Big Data ; si vous aimez créer un "
            "modèle capable d’apprendre ou de prédire, pensez à Intelligence "
            "Artificielle ; si vous aimez sécuriser des systèmes, pensez à "
            "Cybersécurité ; si vous aimez créer une application complète, pensez à "
            "Développement Full Stack ; si vous aimez les capteurs, l’électronique "
            "ou l’automatisation, pensez à Robotique et Cobotique. Répondez ensuite "
            "avec la piste qui vous attire le plus et pourquoi."
        )

    if "pas compris" in texte or "comprends pas" in texte or "explique" in texte:
        return (
            "Bien sûr. La question actuelle vous demande simplement de parler "
            "des modules, domaines ou projets qui vous intéressent. Vous pouvez "
            "répondre naturellement, par exemple : “J’aimerais réaliser une "
            "application web intelligente” ou “J’aimerais analyser des données pour "
            "aider à la décision”."
        )

    return (
        "Oui, je peux vous aider. Pour continuer le test, répondez simplement "
        "à la question actuelle avec vos préférences personnelles. Vous pouvez "
        "donner une réponse courte ou détaillée."
    )


def repondre_clarification_avec_gemini(question_actuelle, message_etudiant, historique=None):
    if historique is None:
        historique = []

    reponse_locale = generer_reponse_clarification_locale(
        question_actuelle,
        message_etudiant
    )

    if not gemini_est_disponible():
        return {
            "type_message": "demande_clarification",
            "message_bot": reponse_locale,
            "scores": get_scores_vides(),
            "domaines_detectes": [],
            "hesitation_detectee": False,
            "commentaire_analyse": "Clarification détectée localement.",
            "source": "locale"
        }

    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        client = genai.Client(api_key=api_key)

        prompt = f"""
Tu es un assistant d’orientation pédagogique dans une plateforme universitaire.

L’étudiant vient de poser une question ou une demande de clarification.
Tu dois répondre précisément à sa question, mais tu ne dois PAS considérer son message comme une réponse au questionnaire.

Question actuelle du questionnaire :
{question_actuelle}

Message de l’étudiant :
{message_etudiant}

Règles obligatoires :
- Ne fais pas avancer le questionnaire.
- Ne donne aucun score d’orientation.
- Ne choisis aucune spécialité à la place de l’étudiant.
- Réponds précisément à la question de l’étudiant.
- Si l’étudiant demande s’il peut choisir plusieurs options, domaines, modules ou propositions, réponds clairement que oui.
- À la fin, invite l’étudiant à répondre à la question actuelle pour continuer.

Tu dois retourner uniquement un JSON valide au format suivant :

{{
  "type_message": "demande_clarification",
  "message_bot": "ta réponse naturelle ici",
  "scores": {{
    "Big Data": 0,
    "Intelligence Artificielle": 0,
    "Cybersécurité": 0,
    "Développement Full Stack": 0,
    "Robotique et Cobotique": 0
  }},
  "domaines_detectes": [],
  "hesitation_detectee": false,
  "commentaire_analyse": "Question de clarification détectée. Le questionnaire ne doit pas avancer."
}}
"""

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )

        texte = response.text
        data = extraire_json_depuis_texte(texte)

        if data is None:
            return {
                "type_message": "demande_clarification",
                "message_bot": reponse_locale,
                "scores": get_scores_vides(),
                "domaines_detectes": [],
                "hesitation_detectee": False,
                "commentaire_analyse": "Réponse Gemini non JSON pour clarification.",
                "source": "locale"
            }

        data["type_message"] = "demande_clarification"
        data["scores"] = get_scores_vides()

        return nettoyer_reponse_gemini(data)

    except Exception as e:
        print("Erreur Gemini clarification :", e)

        return {
            "type_message": "demande_clarification",
            "message_bot": reponse_locale,
            "scores": get_scores_vides(),
            "domaines_detectes": [],
            "hesitation_detectee": False,
            "commentaire_analyse": "Erreur Gemini pendant la clarification.",
            "source": "locale"
        }