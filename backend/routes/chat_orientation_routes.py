import os
import uuid
import unicodedata
from io import BytesIO
from html import escape

from flask import Blueprint, jsonify, request, send_file, Response
from werkzeug.utils import secure_filename

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from database.db import get_db_connection

from recommendation.chat_engine import (
    initialiser_scores,
    traiter_message_etudiant,
    appliquer_scores,
    construire_resultat_final,
    get_question_par_index,
    nombre_questions,
    get_question_clarification_si_necessaire
)

from ai.gemini_service import (
    traiter_message_chat_avec_gemini,
    repondre_clarification_avec_gemini
)

from database.chat_orientation_repository import (
    creer_session_chat,
    get_session_chat,
    ajouter_message_chat,
    mettre_a_jour_session_chat,
    terminer_session_chat,
    enregistrer_choix_final_etudiant,
    get_choix_final_details,
    enregistrer_pdf_engagement_choix,
    enregistrer_document_signe,
    get_etat_orientation_etudiant,
    get_discussion_chat_par_fiche,
    generer_contenu_txt_discussion
)

from database.orientation_repository import (
    creer_test_orientation,
    enregistrer_reponse_libre,
    enregistrer_scores_orientation,
    terminer_test_orientation
)

from database.fiche_repository import generer_fiche_intelligente
from services.pdf_engagement_service import generer_fiche_engagement_pdf
from services.email_notification_service import notifier_depot_document_signe
from database.notification_repository import notifier_doyens_nouveau_document
from services.jwt_service import etudiant_requis, get_utilisateur_connecte_id

chat_orientation_bp = Blueprint(
    "chat_orientation",
    __name__,
    url_prefix="/api/chat-orientation"
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_DOCUMENTS_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "documents_signes"
)


MESSAGE_ERREUR_IA = (
    "Le service d’intelligence artificielle est momentanément indisponible. "
    "Votre message a été enregistré, mais l’analyse n’a pas pu être effectuée. "
    "Veuillez réessayer dans quelques instants ou contacter l’administrateur."
)

EXTENSIONS_DOCUMENTS_AUTORISEES = {"pdf", "jpg", "jpeg", "png"}
TAILLE_MAX_DOCUMENT_SIGNE = 5 * 1024 * 1024


def normaliser_texte_detection(texte):
    texte = str(texte or "").lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )
    texte = texte.replace("’", "'")
    texte = texte.replace("-", " ")
    texte = " ".join(texte.split())
    return texte


def message_est_demande_aide_ou_proposition(question_actuelle, message_etudiant):
    """
    Détecte les messages qui ne doivent PAS faire avancer le questionnaire.

    Correction importante : la détection ne dépend plus uniquement de
    type_question = "texte_libre". Dans certains cas, après une première
    réponse d'aide, le frontend ou l'état de session peut renvoyer une question
    de clarification. Si l'étudiant écrit encore "donne-moi des exemples", le
    backend doit quand même répondre à la demande et rester sur la même étape.

    Le questionnaire avance seulement si le message ressemble réellement à une
    réponse d'orientation. Les demandes d'aide, d'exemples ou les questions
    restent bloquées sur la même question.
    """
    texte_original = str(message_etudiant or "").strip()
    texte = normaliser_texte_detection(texte_original)

    if texte == "":
        return False

    # Les réponses provenant des cases cochées sont déjà structurées par le
    # frontend. Elles doivent continuer normalement.
    if texte.startswith("reponses selectionnees"):
        return False

    # Les réponses de type hésitation sont de vraies réponses, pas des demandes
    # d'aide, même si elles contiennent plusieurs spécialités.
    if texte.startswith("oui, specialites hesitees"):
        return False

    marqueurs_question = [
        "?",
        "est ce que",
        "est-ce que",
        "puis je",
        "puis-je",
        "peux je",
        "peux-je",
        "peux tu",
        "peux-tu",
        "peut tu",
        "peut-tu",
        "pouvez vous",
        "pouvez-vous",
        "tu peux",
        "vous pouvez",
        "comment",
        "pourquoi",
        "combien",
        "quel ",
        "quelle ",
        "quels ",
        "quelles ",
        "quoi ",
        "c est quoi",
        "c'est quoi",
        "qu est ce que",
        "qu'est ce que",
        "quelle est la difference",
        "difference entre",
        "différence entre"
    ]

    motifs_assistance_forts = [
        "je ne sais pas",
        "j ne sais pas",
        "je sais pas",
        "je ne sais quoi",
        "je ne sais pas quoi",
        "aucune idee",
        "aucune ide",
        "aucune idée",
        "pas d idee",
        "pas d ide",
        "pas d'idée",
        "aide moi",
        "aidez moi",
        "aide-moi",
        "conseille moi",
        "conseillez moi",
        "conseille-moi",
        "propose moi",
        "proposes moi",
        "proposez moi",
        "propose-moi",
        "proposez-moi",
        "tu me propose",
        "tu me proposes",
        "vous me proposez",
        "propose",
        "proposer",
        "proposes",
        "donne moi",
        "donnez moi",
        "donne-moi",
        "donnez-moi",
        "des exemple",
        "des exemples",
        "exemple de projet",
        "exemples de projet",
        "exemple projet",
        "exemples projet",
        "idee de projet",
        "idees de projet",
        "idée de projet",
        "idées de projet",
        "des idees",
        "des idées",
        "des ide",
        "des idees de projet",
        "que choisir",
        "quoi choisir",
        "quel projet choisir",
        "quelle specialite choisir",
        "quoi ecrire",
        "que dois je ecrire",
        "que puis je ecrire",
        "je vais choisir",
        "je choisirai",
        "je choisirais"
    ]

    contient_question = any(marqueur in texte for marqueur in marqueurs_question)
    contient_assistance_forte = any(motif in texte for motif in motifs_assistance_forts)

    if not contient_question and not contient_assistance_forte:
        return False

    # Sur la question libre finale, toute question/demande d'aide doit bloquer
    # l'avancement.
    if isinstance(question_actuelle, dict) and question_actuelle.get("type_question") == "texte_libre":
        return True

    # Même si l'état courant n'est plus marqué texte_libre, une demande forte
    # comme "donne moi des exemples" doit rester une clarification.
    if contient_assistance_forte:
        return True

    # Pour une vraie question écrite manuellement, on répond aussi sans avancer.
    if contient_question:
        return True

    return False

def obtenir_traitement_orientation(question_actuelle, message_etudiant, scores_actuels, historique):
    """
    Utilise Gemini en priorité pour analyser intelligemment l'intention.

    Objectif : laisser Gemini comprendre les fautes, les questions et les
    demandes d'aide. Si Gemini décide que le message est une demande
    d'assistance, le questionnaire reste sur la même question. Si Gemini décide
    que c'est une vraie réponse d'orientation, le questionnaire avance.

    Si Gemini est indisponible, on garde un secours local pour que le projet
    reste utilisable pendant la démonstration.
    """
    traitement_gemini = traiter_message_chat_avec_gemini(
        question_actuelle,
        message_etudiant,
        scores_actuels,
        historique
    )

    if traitement_gemini is not None:
        return traitement_gemini

    # Secours local seulement si Gemini n'a pas répondu.
    if message_est_demande_aide_ou_proposition(question_actuelle, message_etudiant):
        return repondre_clarification_avec_gemini(
            question_actuelle,
            message_etudiant,
            historique
        )

    return traiter_message_etudiant(
        question_actuelle,
        message_etudiant,
        scores_actuels,
        historique
    )


def code_question_dynamique_clarification(code_question):
    code = str(code_question or "").strip().lower()
    return code.startswith("qc") or code.startswith("clarification_")


def get_etudiant_id_by_utilisateur_id(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id
            FROM etudiants
            WHERE utilisateur_id = %s
            """,
            (utilisateur_id,)
        )

        etudiant = cursor.fetchone()

        if etudiant is None:
            return None

        return etudiant["id"]

    finally:
        cursor.close()
        connection.close()



def get_infos_etudiant_by_utilisateur_id(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, nom, prenom
            FROM etudiants
            WHERE utilisateur_id = %s
            """,
            (utilisateur_id,)
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def construire_message_accueil_chatbot(infos_etudiant, premiere_question):
    prenom = ""

    if infos_etudiant is not None:
        prenom = str(infos_etudiant.get("prenom") or "").strip()

    if prenom == "":
        salutation = "Bonjour."
    else:
        salutation = f"Bonjour {prenom}."

    return (
        f"{salutation} Je suis votre chatbot d’orientation pédagogique. "
        "Mon rôle est de vous aider à réfléchir à votre choix de filière en analysant vos préférences, "
        "vos modules réussis, vos centres d’intérêt et votre projet futur. "
        "La recommandation proposée est une aide à la décision : le choix final reste personnel.\n\n"
        f"{premiere_question['texte']}"
    )

def get_derniere_fiche_id_etudiant(utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return None

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                fi.id AS fiche_id
            FROM fiches_intelligentes fi
            JOIN tests_orientation t ON fi.test_orientation_id = t.id
            JOIN etudiants e ON t.etudiant_id = e.id
            WHERE e.utilisateur_id = %s
            ORDER BY fi.date_generation DESC, fi.id DESC
            LIMIT 1
            """,
            (utilisateur_id,)
        )

        fiche = cursor.fetchone()

        if fiche is None:
            return None

        return fiche["fiche_id"]

    finally:
        cursor.close()
        connection.close()




def normaliser_code_question_pour_db(code_question):
    """
    Convertit les codes longs du questionnaire final en codes courts compatibles
    avec la colonne code_question de la table reponses_etudiants.
    Cela évite les erreurs SQL du type Data too long for column code_question.
    """
    code = str(code_question or "").strip()

    correspondances = {
        "q1_projets_preferes": "q1",
        "q2_activites_motivantes": "q2",
        "q3_style_travail": "q3",
        "q4_modules_reussis": "q4",
        "q5_modules_apprecies": "q5",
        "q6_modules_difficiles": "q6",
        "q7_metiers_attirants": "q7",
        "q8_priorite_choix": "q8",
        "q9_hesitation": "q9",
        "q10_projet_futur": "q10"
    }

    if code in correspondances:
        return correspondances[code]

    if code_question_dynamique_clarification(code):
        # Les questions de clarification sont générées dynamiquement.
        # Elles influencent déjà les scores, mais ne sont pas stockées dans
        # reponses_etudiants car cette table référence uniquement les
        # questions fixes du questionnaire.
        return None

    if code == "":
        return "q"

    return code[:20]


def utilisateur_requete_autorise(utilisateur_id):
    utilisateur_connecte_id = get_utilisateur_connecte_id()

    if utilisateur_connecte_id is None:
        return False

    try:
        return int(utilisateur_connecte_id) == int(utilisateur_id)
    except Exception:
        return False


def session_appartient_utilisateur(session_id, utilisateur_id):
    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT sc.id
            FROM sessions_chat_orientation sc
            JOIN etudiants e ON sc.etudiant_id = e.id
            WHERE sc.id = %s
              AND e.utilisateur_id = %s
            LIMIT 1
            """,
            (session_id, utilisateur_id)
        )

        session = cursor.fetchone()

        return session is not None

    finally:
        cursor.close()
        connection.close()


def enregistrer_message_trace(session_id, role_message, contenu):
    """
    Enregistre un message dans la table messages_chat_orientation.
    Cette fonction assure la traçabilité complète de la discussion affichée.
    """
    resultat = ajouter_message_chat(session_id, role_message, contenu)

    if not resultat:
        print(
            "Attention : message non enregistré dans la trace chatbot.",
            "session_id =",
            session_id,
            "role =",
            role_message
        )

    return resultat


def traitement_ia_indisponible(traitement):
    """
    Détecte les cas où Gemini / IA n'a pas répondu correctement.
    """
    if traitement is None:
        return True

    if not isinstance(traitement, dict):
        return True

    if traitement.get("erreur_ia") is True:
        return True

    if traitement.get("ia_indisponible") is True:
        return True

    if traitement.get("gemini_indisponible") is True:
        return True

    if traitement.get("success") is False:
        return True

    code = str(traitement.get("code", "")).lower()
    message = str(traitement.get("message", "")).lower()

    mots_erreur = [
        "api key",
        "clé api",
        "cle api",
        "gemini",
        "quota",
        "timeout",
        "unauthorized",
        "permission",
        "indisponible",
        "api"
    ]

    for mot in mots_erreur:
        if mot in code or mot in message:
            return True

    if traitement.get("type_message") is None:
        return True

    return False


def construire_message_erreur_ia(traitement=None):
    if isinstance(traitement, dict):
        code = str(traitement.get("code", "")).lower()

        if code in [
            "gemini_api_key_absente",
            "gemini_api_key_invalide"
        ]:
            return (
                "Le service d’intelligence artificielle n’est pas configuré correctement. "
                "La clé API Gemini est absente ou invalide. "
                "Veuillez contacter l’administrateur de la plateforme."
            )

        if code == "gemini_bibliotheque_absente":
            return (
                "Le service d’intelligence artificielle n’est pas disponible sur le serveur. "
                "La bibliothèque Gemini n’est pas installée correctement."
            )

        if code == "gemini_quota_depasse":
            return (
                "Le service d’intelligence artificielle est momentanément indisponible "
                "car le quota Gemini est dépassé. Veuillez réessayer plus tard."
            )

        if code == "gemini_timeout":
            return (
                "Le service d’intelligence artificielle met trop de temps à répondre. "
                "Veuillez réessayer dans quelques instants."
            )

    return MESSAGE_ERREUR_IA


def reponse_erreur_ia(session_id, question_actuelle, index_question, traitement=None):
    """
    Retourne un message clair à l'étudiant si Gemini / IA ne répond pas.
    Le message est aussi enregistré dans la discussion.
    """
    message_erreur = construire_message_erreur_ia(traitement)

    enregistrer_message_trace(session_id, "assistant", message_erreur)

    return jsonify({
        "success": True,
        "terminee": False,
        "reste_sur_meme_question": True,
        "erreur_ia": True,
        "code": "service_ia_indisponible",
        "message": message_erreur,
        "message_bot": message_erreur,
        "question": question_actuelle,
        "index_question": index_question,
        "nombre_questions": nombre_questions()
    })


def trier_resultat_recommandation(resultat_recommandation):
    """
    Trie les pourcentages du plus grand au plus petit côté backend.
    """
    if not isinstance(resultat_recommandation, dict):
        return resultat_recommandation

    pourcentages = resultat_recommandation.get("pourcentages")

    if not isinstance(pourcentages, dict):
        return resultat_recommandation

    pourcentages_tries = dict(
        sorted(
            pourcentages.items(),
            key=lambda item: float(item[1]),
            reverse=True
        )
    )

    resultat_recommandation["pourcentages"] = pourcentages_tries

    return resultat_recommandation


def nettoyer_texte_pdf(texte):
    if texte is None:
        return ""

    return escape(str(texte)).replace("\n", "<br/>")


def formater_role_message_pdf(role_message):
    if role_message == "assistant":
        return "Chatbot"

    if role_message == "etudiant":
        return "Étudiant"

    if role_message == "user":
        return "Étudiant"

    if role_message == "bot":
        return "Chatbot"

    return role_message or "Message"


def recuperer_date_message_pdf(message):
    return (
        message.get("date_creation")
        or message.get("date_message")
        or message.get("created_at")
        or message.get("date_envoi")
        or ""
    )


def generer_pdf_discussion_buffer(discussion):
    fiche = discussion["fiche"]
    session_chat = discussion["session_chat"]
    scores = discussion["scores"]
    messages = discussion["messages"]

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm
    )

    styles = getSampleStyleSheet()

    titre_style = ParagraphStyle(
        "TitrePrincipal",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#1d4ed8"),
        spaceAfter=16
    )

    sous_titre_style = ParagraphStyle(
        "SousTitre",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=10,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "TexteNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=5
    )

    message_style = ParagraphStyle(
        "MessageStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        leftIndent=8,
        rightIndent=8,
        spaceBefore=4,
        spaceAfter=6
    )

    elements = []

    elements.append(Paragraph("Trace de discussion - Chatbot d’orientation", titre_style))

    elements.append(Paragraph("Informations étudiant", sous_titre_style))

    infos_etudiant = [
        ["Nom complet", f"{fiche.get('prenom', '')} {fiche.get('nom', '')}"],
        ["ID universitaire", fiche.get("id_universitaire", "")],
        ["Email", fiche.get("email", "")],
        ["Promotion", fiche.get("promotion", "")]
    ]

    table_infos = Table(infos_etudiant, colWidths=[5 * cm, 11 * cm])
    table_infos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e3a8a")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(table_infos)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Informations orientation", sous_titre_style))

    infos_orientation = [
        ["Fiche ID", fiche.get("fiche_id", "")],
        ["Test orientation ID", fiche.get("test_orientation_id", "")],
        ["Spécialité proposée", fiche.get("specialite_recommandee", "")],
        ["Date génération", fiche.get("date_generation", "")]
    ]

    table_orientation = Table(infos_orientation, colWidths=[5 * cm, 11 * cm])
    table_orientation.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6)
    ]))

    elements.append(table_orientation)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Scores par filière", sous_titre_style))

    if len(scores) == 0:
        elements.append(Paragraph("Aucun score enregistré.", normal_style))
    else:
        donnees_scores = [["Filière", "Score", "Pourcentage"]]

        for score in scores:
            donnees_scores.append([
                score.get("specialite", ""),
                str(score.get("score", "")),
                f"{score.get('pourcentage', '')}%"
            ])

        table_scores = Table(donnees_scores, colWidths=[9 * cm, 3 * cm, 4 * cm])
        table_scores.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6)
        ]))

        elements.append(table_scores)

    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Session chatbot", sous_titre_style))

    if session_chat is None:
        elements.append(Paragraph("Aucune session chat trouvée pour cette fiche.", normal_style))
    else:
        elements.append(Paragraph(
            f"<b>Session ID :</b> {session_chat.get('id', '')}<br/>"
            f"<b>Statut :</b> {session_chat.get('statut', '')}<br/>"
            f"<b>Raison droit :</b> {session_chat.get('raison_droit', '')}",
            normal_style
        ))

    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Discussion complète", sous_titre_style))

    if len(messages) == 0:
        elements.append(Paragraph("Aucun message enregistré pour cette discussion.", normal_style))
    else:
        for index, message in enumerate(messages, start=1):
            role = formater_role_message_pdf(message.get("role_message"))
            date_message = recuperer_date_message_pdf(message)
            contenu = nettoyer_texte_pdf(message.get("contenu") or "")

            elements.append(Paragraph(
                f"<b>Message {index} - {role}</b>",
                normal_style
            ))

            if date_message:
                elements.append(Paragraph(
                    f"<b>Date :</b> {nettoyer_texte_pdf(date_message)}",
                    normal_style
                ))

            elements.append(Paragraph(contenu, message_style))
            elements.append(Spacer(1, 4))

    document.build(elements)

    buffer.seek(0)
    return buffer


@chat_orientation_bp.route("/demarrer", methods=["POST"])
@etudiant_requis
def demarrer_chat_orientation():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    utilisateur_id = data.get("utilisateur_id")

    if utilisateur_id is None:
        return jsonify({
            "success": False,
            "message": "utilisateur_id obligatoire."
        }), 400

    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas utiliser le compte d’un autre étudiant."
        }), 403

    infos_etudiant = get_infos_etudiant_by_utilisateur_id(utilisateur_id)
    etudiant_id = infos_etudiant["id"] if infos_etudiant else None

    if etudiant_id is None:
        return jsonify({
            "success": False,
            "message": "Aucun étudiant trouvé pour cet utilisateur."
        }), 404

    droit = {
        "peut_passer_test": True,
        "raison": "passage_libre_etudiant",
        "message": (
            "L’étudiant peut passer ou repasser le test librement. "
            "Aucune autorisation du doyen n’est nécessaire."
        )
    }

    scores_initials = initialiser_scores()

    session_id = creer_session_chat(
        etudiant_id,
        droit.get("raison"),
        scores_initials
    )

    if session_id is None:
        return jsonify({
            "success": False,
            "message": "Impossible de créer la session de chat."
        }), 500

    premiere_question = get_question_par_index(0)

    if premiere_question is None:
        return jsonify({
            "success": False,
            "message": "Aucune question disponible pour le chatbot."
        }), 500

    message_bot = construire_message_accueil_chatbot(
        infos_etudiant,
        premiere_question
    )

    enregistrer_message_trace(session_id, "assistant", message_bot)

    return jsonify({
        "success": True,
        "peut_passer_test": True,
        "session_id": session_id,
        "droit_test": droit,
        "message_bot": message_bot,
        "question": premiere_question,
        "index_question": 0,
        "nombre_questions": nombre_questions()
    })


@chat_orientation_bp.route("/message", methods=["POST"])
@etudiant_requis
def envoyer_message_chat():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    session_id = data.get("session_id")
    message_etudiant = data.get("message")

    if session_id is None:
        return jsonify({
            "success": False,
            "message": "session_id obligatoire."
        }), 400

    if message_etudiant is None or str(message_etudiant).strip() == "":
        return jsonify({
            "success": False,
            "message": "Le message ne peut pas être vide."
        }), 400

    message_etudiant = str(message_etudiant).strip()

    utilisateur_connecte_id = get_utilisateur_connecte_id()

    if not session_appartient_utilisateur(session_id, utilisateur_connecte_id):
        return jsonify({
            "success": False,
            "message": "Cette session chatbot n’appartient pas à votre compte."
        }), 403

    session = get_session_chat(session_id)

    if session is None:
        return jsonify({
            "success": False,
            "message": "Session de chat introuvable."
        }), 404

    if session["statut"] == "termine":
        return jsonify({
            "success": False,
            "message": "Cette session est déjà terminée."
        }), 400

    index_question = session["index_question"]
    reponses = session["reponses"] or []

    question_actuelle = get_question_par_index(index_question)

    if question_actuelle is None:
        for element in reversed(reponses):
            if (
                element.get("type_ligne") == "question_clarification_posee"
                and element.get("repondue") is not True
            ):
                question_actuelle = element.get("question_obj")
                break

    if question_actuelle is None:
        return jsonify({
            "success": False,
            "message": "Question actuelle introuvable."
        }), 500

    enregistrer_message_trace(session_id, "etudiant", message_etudiant)

    try:
        traitement = obtenir_traitement_orientation(
            question_actuelle,
            message_etudiant,
            session["scores"],
            reponses
        )
    except Exception as e:
        print("Erreur moteur de recommandation :", e)
        return reponse_erreur_ia(session_id, question_actuelle, index_question), 200

    if traitement_ia_indisponible(traitement):
        print("Traitement IA invalide ou indisponible :", traitement)
        return reponse_erreur_ia(session_id, question_actuelle, index_question,traitement), 200

    if traitement.get("type_message") != "reponse_orientation":
        message_bot = traitement.get("message_bot")

        if message_bot is None or message_bot.strip() == "":
            message_bot = (
                "Je vous écoute. Vous pouvez poser une question ou répondre "
                "à la question actuelle avec vos préférences."
            )

        enregistrer_message_trace(session_id, "assistant", message_bot)

        return jsonify({
            "success": True,
            "terminee": False,
            "reste_sur_meme_question": True,
            "message_bot": message_bot,
            "question": question_actuelle,
            "index_question": index_question,
            "nombre_questions": nombre_questions(),
            "traitement": traitement
        })

    analyse = traitement

    nouveaux_scores = appliquer_scores(
        session["scores"],
        analyse.get("scores", {})
    )

    for element in reponses:
        if (
            element.get("type_ligne") == "question_clarification_posee"
            and element.get("repondue") is not True
            and element.get("question_obj", {}).get("code_question") == question_actuelle.get("code_question")
        ):
            element["repondue"] = True

    reponses.append({
        "code_question": question_actuelle["code_question"],
        "question": question_actuelle["texte"],
        "reponse": message_etudiant,
        "analyse": analyse
    })

    prochain_index = index_question + 1

    if prochain_index < nombre_questions():
        question_suivante = get_question_par_index(prochain_index)

        mettre_a_jour_session_chat(
            session_id,
            prochain_index,
            nouveaux_scores,
            reponses
        )

        message_bot = question_suivante["texte"]

        enregistrer_message_trace(session_id, "assistant", message_bot)

        return jsonify({
            "success": True,
            "terminee": False,
            "message_bot": message_bot,
            "question": question_suivante,
            "index_question": prochain_index,
            "nombre_questions": nombre_questions(),
            "analyse": analyse
        })

    question_clarification = get_question_clarification_si_necessaire(
        nouveaux_scores,
        reponses
    )

    if question_clarification is not None:
        reponses.append({
            "type_ligne": "question_clarification_posee",
            "question_obj": question_clarification,
            "repondue": False
        })

        mettre_a_jour_session_chat(
            session_id,
            nombre_questions() + 1,
            nouveaux_scores,
            reponses
        )

        message_bot = question_clarification["texte"]
        enregistrer_message_trace(session_id, "assistant", message_bot)

        return jsonify({
            "success": True,
            "terminee": False,
            "message_bot": message_bot,
            "question": question_clarification,
            "index_question": nombre_questions() + 1,
            "nombre_questions": nombre_questions(),
            "clarification": True,
            "analyse": analyse
        })

    resultat_recommandation = construire_resultat_final(nouveaux_scores)
    resultat_recommandation = trier_resultat_recommandation(resultat_recommandation)

    test_orientation_id = creer_test_orientation(session["etudiant_id"])

    if test_orientation_id is None:
        return jsonify({
            "success": False,
            "message": "Impossible de créer le test d'orientation."
        }), 500

    erreurs = []

    for reponse in reponses:
        if "code_question" not in reponse or "reponse" not in reponse:
            continue

        code_question_db = normaliser_code_question_pour_db(
            reponse.get("code_question")
        )

        if code_question_db is None:
            continue

        resultat_reponse = enregistrer_reponse_libre(
            test_orientation_id,
            code_question_db,
            reponse["reponse"]
        )

        if not resultat_reponse["success"]:
            erreurs.append(resultat_reponse["message"])

    if len(erreurs) > 0:
        return jsonify({
            "success": False,
            "message": "Certaines réponses n'ont pas été enregistrées.",
            "erreurs": erreurs
        }), 400

    resultat_scores = enregistrer_scores_orientation(
        test_orientation_id,
        resultat_recommandation
    )

    if not resultat_scores["success"]:
        return jsonify({
            "success": False,
            "message": "Scores non sauvegardés.",
            "erreur_scores": resultat_scores["message"]
        }), 500

    terminer_test_orientation(test_orientation_id)

    fiche = generer_fiche_intelligente(test_orientation_id)
    fiche_id = fiche.get("fiche_id") if fiche else None

    if fiche_id is None:
        message_bot = (
            "Le test est terminé, mais la fiche intelligente n’a pas pu être "
            "générée correctement. Veuillez contacter l’administrateur."
        )

        enregistrer_message_trace(session_id, "assistant", message_bot)

        return jsonify({
            "success": False,
            "terminee": False,
            "message": "Fiche intelligente non générée.",
            "message_bot": message_bot
        }), 500

    message_bot = (
        "Merci pour vos réponses. J’ai terminé l’analyse de votre profil. "
        "Vous pouvez maintenant consulter la recommandation proposée, puis "
        "choisir librement votre spécialité finale."
    )

    enregistrer_message_trace(session_id, "assistant", message_bot)

    mettre_a_jour_session_chat(
        session_id,
        prochain_index,
        nouveaux_scores,
        reponses
    )

    terminer_session_chat(
        session_id,
        test_orientation_id,
        fiche_id
    )

    return jsonify({
        "success": True,
        "terminee": True,
        "message_bot": message_bot,
        "test_orientation_id": test_orientation_id,
        "fiche": fiche,
        "resultat_recommandation": resultat_recommandation,
        "scores_enregistres": resultat_scores
    })


@chat_orientation_bp.route("/choix-final", methods=["POST"])
@etudiant_requis
def enregistrer_choix_final():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    utilisateur_id = data.get("utilisateur_id")
    fiche_id = data.get("fiche_id")
    specialite = data.get("specialite")

    if specialite is None:
        specialite = data.get("specialite_choisie")

    commentaire = data.get("commentaire")

    if utilisateur_id is None:
        return jsonify({
            "success": False,
            "message": "utilisateur_id obligatoire."
        }), 400

    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas enregistrer un choix final pour un autre étudiant."
        }), 403

    if fiche_id is None:
        return jsonify({
            "success": False,
            "message": "fiche_id obligatoire."
        }), 400

    if specialite is None or str(specialite).strip() == "":
        return jsonify({
            "success": False,
            "message": "Veuillez choisir une spécialité."
        }), 400

    specialite = str(specialite).strip()

    etudiant_id = get_etudiant_id_by_utilisateur_id(utilisateur_id)

    if etudiant_id is None:
        return jsonify({
            "success": False,
            "message": "Aucun étudiant trouvé pour cet utilisateur."
        }), 404

    resultat = enregistrer_choix_final_etudiant(
        fiche_id,
        etudiant_id,
        specialite,
        commentaire
    )

    if not resultat["success"]:
        return jsonify(resultat), 400

    choix_id = resultat["choix_id"]
    details_choix = get_choix_final_details(choix_id)

    if details_choix is None:
        return jsonify({
            "success": False,
            "message": "Choix enregistré, mais détails introuvables."
        }), 500

    chemin_pdf = generer_fiche_engagement_pdf(details_choix)
    enregistrer_pdf_engagement_choix(choix_id, chemin_pdf)

    resultat["pdf_engagement_url"] = (
        f"/api/chat-orientation/choix-final/{choix_id}/pdf"
    )

    resultat["message"] = (
        "Choix enregistré et fiche d’engagement générée. "
        "Veuillez télécharger la fiche, la signer, puis déposer le document signé."
    )

    return jsonify(resultat), 200


@chat_orientation_bp.route("/choix-final/<int:choix_id>/pdf", methods=["GET"])
@etudiant_requis
def telecharger_fiche_engagement(choix_id):
    details_choix = get_choix_final_details(choix_id)

    if details_choix is None:
        return jsonify({
            "success": False,
            "message": "Choix final introuvable."
        }), 404

    etudiant_id_connecte = get_etudiant_id_by_utilisateur_id(
        get_utilisateur_connecte_id()
    )

    if etudiant_id_connecte is None or int(details_choix["etudiant_id"]) != int(etudiant_id_connecte):
        return jsonify({
            "success": False,
            "message": "Cette fiche d’engagement n’appartient pas à votre compte."
        }), 403

    chemin_pdf = details_choix.get("pdf_engagement_path")

    if chemin_pdf is None or not os.path.exists(chemin_pdf):
        chemin_pdf = generer_fiche_engagement_pdf(details_choix)
        enregistrer_pdf_engagement_choix(choix_id, chemin_pdf)

    return send_file(
        chemin_pdf,
        as_attachment=True,
        download_name=f"fiche_engagement_{choix_id}.pdf",
        mimetype="application/pdf"
    )


@chat_orientation_bp.route("/choix-final/<int:choix_id>/document-signe", methods=["POST"])
@etudiant_requis
def deposer_document_signe(choix_id):
    utilisateur_id = request.form.get("utilisateur_id")

    if utilisateur_id is None:
        return jsonify({
            "success": False,
            "message": "utilisateur_id obligatoire."
        }), 400

    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas déposer un document pour un autre étudiant."
        }), 403

    etudiant_id = get_etudiant_id_by_utilisateur_id(utilisateur_id)

    if etudiant_id is None:
        return jsonify({
            "success": False,
            "message": "Aucun étudiant trouvé pour cet utilisateur."
        }), 404

    details_choix = get_choix_final_details(choix_id)

    if details_choix is None:
        return jsonify({
            "success": False,
            "message": "Choix final introuvable."
        }), 404

    if int(details_choix["etudiant_id"]) != int(etudiant_id):
        return jsonify({
            "success": False,
            "message": "Ce choix final n’appartient pas à cet étudiant."
        }), 403

    statut_choix = str(details_choix.get("statut_choix", "") or "").lower()
    statut_document = str(details_choix.get("statut_document", "") or "").lower()
    document_id = details_choix.get("document_id")

    statuts_confirmes = {
        "choix_confirme",
        "document_confirme",
        "confirme",
        "valide",
        "confirme_par_doyen"
    }

    statuts_en_attente = {
        "document_depose",
        "en_attente",
        "en_attente_confirmation_doyen"
    }

    statuts_refus = {
        "document_refuse",
        "refuse",
        "refuse_par_doyen"
    }

    if statut_choix in statuts_confirmes or statut_document in statuts_confirmes:
        return jsonify({
            "success": False,
            "message": (
                "Le document de ce choix final est déjà confirmé. "
                "Aucun nouveau dépôt n’est autorisé."
            )
        }), 400

    if document_id and (
        statut_choix in statuts_en_attente or statut_document in statuts_en_attente
    ):
        return jsonify({
            "success": False,
            "message": (
                "Un document est déjà déposé et en attente de confirmation du doyen. "
                "Veuillez attendre la décision administrative."
            )
        }), 400

    if document_id and not (
        statut_choix in statuts_refus or statut_document in statuts_refus
    ):
        return jsonify({
            "success": False,
            "message": (
                "Un document existe déjà pour ce choix final. "
                "Un nouveau dépôt est autorisé uniquement si le document précédent a été refusé."
            )
        }), 400

    if "document" not in request.files:
        return jsonify({
            "success": False,
            "message": "Aucun document reçu."
        }), 400

    fichier = request.files["document"]

    if fichier.filename is None or fichier.filename.strip() == "":
        return jsonify({
            "success": False,
            "message": "Nom de fichier invalide."
        }), 400

    nom_original = secure_filename(fichier.filename)

    if nom_original == "":
        return jsonify({
            "success": False,
            "message": "Nom de fichier invalide après sécurisation."
        }), 400

    if "." not in nom_original:
        return jsonify({
            "success": False,
            "message": "Le fichier doit avoir une extension valide."
        }), 400

    extension = nom_original.rsplit(".", 1)[-1].lower()

    if extension not in EXTENSIONS_DOCUMENTS_AUTORISEES:
        return jsonify({
            "success": False,
            "message": (
                "Format de fichier non autorisé. "
                "Formats acceptés : PDF, JPG, JPEG, PNG."
            )
        }), 400

    fichier.seek(0, os.SEEK_END)
    taille_fichier = fichier.tell()
    fichier.seek(0)

    if taille_fichier <= 0:
        return jsonify({
            "success": False,
            "message": "Le fichier sélectionné est vide."
        }), 400

    if taille_fichier > TAILLE_MAX_DOCUMENT_SIGNE:
        return jsonify({
            "success": False,
            "message": "Le fichier est trop volumineux. Taille maximale autorisée : 5 Mo."
        }), 400

    os.makedirs(UPLOAD_DOCUMENTS_DIR, exist_ok=True)

    nom_stocke = f"document_signe_{choix_id}_{uuid.uuid4().hex}.{extension}"
    chemin_fichier = os.path.join(UPLOAD_DOCUMENTS_DIR, nom_stocke)

    try:
        fichier.save(chemin_fichier)
    except Exception as erreur:
        print("Erreur sauvegarde document signé :", erreur)

        return jsonify({
            "success": False,
            "message": "Erreur lors de la sauvegarde du document signé.",
            "erreur": str(erreur)
        }), 500

    type_fichier = fichier.mimetype or extension

    resultat = enregistrer_document_signe(
        choix_id,
        etudiant_id,
        nom_original,
        nom_stocke,
        chemin_fichier,
        type_fichier,
        taille_fichier
    )

    if not resultat["success"]:
        return jsonify(resultat), 400

    details_notification = dict(details_choix)

    details_notification["nom_fichier_original"] = nom_original
    details_notification["nom_fichier_stocke"] = nom_stocke
    details_notification["chemin_fichier"] = chemin_fichier
    details_notification["type_fichier"] = type_fichier
    details_notification["taille_fichier"] = taille_fichier

    try:
        resultat_notification = notifier_depot_document_signe(
            details_notification
        )
    except Exception as erreur:
        print("Erreur notification email document signé :", erreur)

        resultat_notification = {
            "success": False,
            "message": (
                "Le document a été déposé, mais la notification email "
                "n’a pas pu être envoyée."
            ),
            "erreur": str(erreur)
        }

    resultat["notification_email"] = resultat_notification

    total_notifications_internes = notifier_doyens_nouveau_document(
        details_notification
    )

    resultat["notification_interne"] = {
        "success": total_notifications_internes > 0,
        "total_doyens_notifies": total_notifications_internes,
        "message": (
            f"{total_notifications_internes} notification(s) interne(s) "
            "envoyée(s) au doyen."
        )
    }

    if resultat_notification.get("success"):
        resultat["message"] = (
            resultat.get("message", "Document signé déposé avec succès.")
            + " Une notification email a été envoyée au service concerné."
        )
    else:
        resultat["message"] = (
            resultat.get("message", "Document signé déposé avec succès.")
            + " La notification email n’a pas été envoyée, mais le document est bien déposé."
        )

    return jsonify(resultat), 200


@chat_orientation_bp.route("/etat-etudiant/<int:utilisateur_id>", methods=["GET"])
@etudiant_requis
def etat_orientation_etudiant(utilisateur_id):
    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas consulter l’état d’un autre étudiant."
        }), 403

    resultat = get_etat_orientation_etudiant(utilisateur_id)

    status_code = 200 if resultat.get("success") else 404

    return jsonify(resultat), status_code


@chat_orientation_bp.route("/etat-etudiant/<int:utilisateur_id>/discussion", methods=["GET"])
@etudiant_requis
def discussion_etudiant(utilisateur_id):
    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas consulter la discussion d’un autre étudiant."
        }), 403

    fiche_id = get_derniere_fiche_id_etudiant(utilisateur_id)

    if fiche_id is None:
        return jsonify({
            "success": False,
            "message": "Aucune fiche trouvée pour cet étudiant."
        }), 404

    resultat = get_discussion_chat_par_fiche(fiche_id)

    status_code = 200 if resultat.get("success") else 404

    return jsonify(resultat), status_code


@chat_orientation_bp.route("/etat-etudiant/<int:utilisateur_id>/discussion/txt", methods=["GET"])
@etudiant_requis
def telecharger_discussion_etudiant_txt(utilisateur_id):
    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas télécharger la discussion d’un autre étudiant."
        }), 403

    fiche_id = get_derniere_fiche_id_etudiant(utilisateur_id)

    if fiche_id is None:
        return jsonify({
            "success": False,
            "message": "Aucune fiche trouvée pour cet étudiant."
        }), 404

    resultat = generer_contenu_txt_discussion(fiche_id)

    if not resultat.get("success"):
        return jsonify(resultat), 404

    contenu = resultat["contenu"]
    nom_fichier = resultat["nom_fichier"]

    return Response(
        contenu,
        mimetype="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={nom_fichier}"
        }
    )


@chat_orientation_bp.route("/etat-etudiant/<int:utilisateur_id>/discussion/pdf", methods=["GET"])
@etudiant_requis
def telecharger_discussion_etudiant_pdf(utilisateur_id):
    if not utilisateur_requete_autorise(utilisateur_id):
        return jsonify({
            "success": False,
            "message": "Vous ne pouvez pas télécharger la discussion d’un autre étudiant."
        }), 403

    fiche_id = get_derniere_fiche_id_etudiant(utilisateur_id)

    if fiche_id is None:
        return jsonify({
            "success": False,
            "message": "Aucune fiche trouvée pour cet étudiant."
        }), 404

    resultat = get_discussion_chat_par_fiche(fiche_id)

    if not resultat.get("success"):
        return jsonify(resultat), 404

    fiche = resultat["fiche"]

    nom_fichier = (
        f"discussion_chat_"
        f"{fiche.get('id_universitaire', 'etudiant')}_"
        f"fiche_{fiche_id}.pdf"
    )

    buffer_pdf = generer_pdf_discussion_buffer(resultat)

    return send_file(
        buffer_pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nom_fichier
    )
