import json
import os


SPECIALITES = [
    "Big Data",
    "Intelligence Artificielle",
    "Cybersécurité",
    "Développement Full Stack",
    "Robotique et Cobotique"
]


def claude_est_disponible():
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key is None or api_key.strip() == "":
        return False

    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def extraire_json_depuis_texte(texte):
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


def traiter_message_chat_avec_claude(
    question_actuelle,
    message_etudiant,
    scores_actuels,
    historique=None
):
    if not claude_est_disponible():
        return None

    try:
        from anthropic import Anthropic

        client = Anthropic()
        model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

        system_prompt = """
Tu es un chatbot intelligent d'orientation pédagogique pour une école d'ingénieurs.

L'étudiant répond dans une interface de chat.
Ton rôle est de comprendre chaque message.

Tu dois déterminer si le message de l'étudiant est :
1. une vraie réponse exploitable à la question d'orientation actuelle
2. une demande de clarification
3. une demande d'information sur une filière, les métiers, le marché du travail, les débouchés ou les compétences
4. un message hors sujet

Les filières possibles sont :
- Big Data
- Intelligence Artificielle
- Cybersécurité
- Développement Full Stack
- Robotique et Cobotique

Règles très importantes :
- Si le message est une vraie réponse à la question actuelle, mets type_message = "reponse_orientation".
- Dans ce cas, analyse la réponse et donne des scores entre 0 et 5 pour chaque filière.
- Si le message est une question de l'étudiant, une demande d'explication, une demande sur les métiers, le marché du travail ou une filière, ne le considère pas comme une réponse au test.
- Dans ce cas, mets le bon type_message, rédige toi-même la réponse dans message_bot, puis invite l'étudiant à répondre à la question actuelle.
- Ne passe jamais à la question suivante si le message n'est pas une vraie réponse d'orientation.
- Tu dois être naturel, pédagogique et utile.
- Tu peux donner des informations sur les filières, les postes possibles, les compétences et le marché du travail.
- Tu ne dois pas imposer une orientation à l'étudiant.
- Le choix final reste libre.

Tu dois répondre uniquement avec un JSON valide.
Ne donne aucun texte hors JSON.

Format obligatoire :
{
  "type_message": "reponse_orientation",
  "message_bot": "",
  "scores": {
    "Big Data": 0,
    "Intelligence Artificielle": 0,
    "Cybersécurité": 0,
    "Développement Full Stack": 0,
    "Robotique et Cobotique": 0
  },
  "domaines_detectes": [],
  "hesitation_detectee": false,
  "commentaire_analyse": ""
}

Valeurs possibles pour type_message :
- "reponse_orientation"
- "demande_clarification"
- "demande_information_filiere"
- "hors_sujet"
"""

        user_prompt = {
            "question_actuelle": question_actuelle,
            "message_etudiant": message_etudiant,
            "scores_actuels": scores_actuels,
            "historique": historique or []
        }

        response = client.messages.create(
            model=model,
            max_tokens=1200,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": json.dumps(user_prompt, ensure_ascii=False)
                }
            ]
        )

        texte = response.content[0].text
        donnees = extraire_json_depuis_texte(texte)

        if donnees is None:
            return None

        if "scores" not in donnees:
            donnees["scores"] = get_scores_vides()

        if "message_bot" not in donnees:
            donnees["message_bot"] = ""

        if "type_message" not in donnees:
            donnees["type_message"] = "demande_clarification"

        donnees["source"] = "claude"

        return donnees

    except Exception as e:
        print("Erreur Claude :", e)
        return None