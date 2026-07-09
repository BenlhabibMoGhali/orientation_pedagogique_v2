from flask import Blueprint, jsonify, request

from database.question_repository import get_questions_par_statut
from database.orientation_repository import (
    get_etudiant_id_by_utilisateur_id,
    creer_test_orientation,
    enregistrer_reponse_choix,
    enregistrer_reponse_libre,
    terminer_test_orientation,
    enregistrer_scores_orientation,
    verifier_droit_nouveau_test,
    consommer_autorisation_nouveau_test
)
from recommendation.scoring import calculer_recommandation


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("/test", methods=["GET"])
def test_chatbot():
    return jsonify({
        "module": "chatbot d'orientation",
        "message": "Routes chatbot fonctionnelles."
    })


@chatbot_bp.route("/questions", methods=["GET"])
def afficher_questions():
    questions = get_questions_par_statut("finale")

    if len(questions) == 0:
        questions = get_questions_par_statut("provisoire")
        statut = "provisoire"
    else:
        statut = "finale"

    return jsonify({
        "type": f"questions {statut}",
        "source": "base de données MySQL",
        "message": "Ces questions servent au workflow du chatbot.",
        "questions": questions
    })


@chatbot_bp.route("/droit-test/<int:utilisateur_id>", methods=["GET"])
def verifier_droit_test(utilisateur_id):
    etudiant_id = get_etudiant_id_by_utilisateur_id(utilisateur_id)

    if etudiant_id is None:
        return jsonify({
            "success": False,
            "peut_passer_test": False,
            "message": "Aucun étudiant trouvé pour cet utilisateur."
        }), 404

    droit = verifier_droit_nouveau_test(etudiant_id)

    return jsonify({
        "success": True,
        "etudiant_id": etudiant_id,
        "droit_test": droit
    })


@chatbot_bp.route("/demo", methods=["GET"])
def demo_recommandation():
    reponses_demo = [
        "qf1_data",
        "qf2_data",
        "qf4_math",
        "qf5_data",
        "qf6_analyse",
        "qf7_data_engineer",
        "qf8_data",
        "qf9_bigdata_ia"
    ]

    reponse_libre_demo = (
        "J'aime Python, les statistiques, l'analyse de donnees "
        "et les projets lies au Big Data."
    )

    resultat = calculer_recommandation(
        reponses_demo,
        reponse_libre_demo
    )

    return jsonify(resultat)


@chatbot_bp.route("/recommandation", methods=["POST"])
def recommandation():
    data = request.get_json()

    if data is None:
        return jsonify({
            "erreur": "Aucune donnée reçue."
        }), 400

    reponses = data.get("reponses", [])
    reponse_libre = data.get("reponse_libre", "")

    if not isinstance(reponses, list):
        return jsonify({
            "erreur": "Le champ 'reponses' doit être une liste."
        }), 400

    resultat = calculer_recommandation(
        reponses,
        reponse_libre
    )

    return jsonify(resultat)


@chatbot_bp.route("/soumettre-test", methods=["POST"])
def soumettre_test_orientation():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    utilisateur_id = data.get("utilisateur_id")
    reponses = data.get("reponses", [])
    reponse_libre = data.get("reponse_libre", "")
    code_question_libre = data.get("code_question_libre", "qf10")

    if utilisateur_id is None:
        return jsonify({
            "success": False,
            "message": "utilisateur_id obligatoire."
        }), 400

    if not isinstance(reponses, list):
        return jsonify({
            "success": False,
            "message": "Le champ reponses doit être une liste."
        }), 400

    etudiant_id = get_etudiant_id_by_utilisateur_id(utilisateur_id)

    if etudiant_id is None:
        return jsonify({
            "success": False,
            "message": "Aucun étudiant trouvé pour cet utilisateur."
        }), 404

    droit_test = verifier_droit_nouveau_test(etudiant_id)

    if not droit_test.get("peut_passer_test"):
        return jsonify({
            "success": False,
            "message": droit_test.get(
                "message",
                "Vous n'êtes pas autorisé à passer ce test."
            ),
            "droit_test": droit_test
        }), 403

    test_orientation_id = creer_test_orientation(etudiant_id)

    if test_orientation_id is None:
        return jsonify({
            "success": False,
            "message": "Impossible de créer le test d'orientation."
        }), 500

    erreurs = []

    for code_reponse in reponses:
        resultat_reponse = enregistrer_reponse_choix(
            test_orientation_id,
            code_reponse
        )

        if not resultat_reponse["success"]:
            erreurs.append(resultat_reponse["message"])

    if reponse_libre.strip() != "":
        resultat_libre = enregistrer_reponse_libre(
            test_orientation_id,
            code_question_libre,
            reponse_libre
        )

        if not resultat_libre["success"]:
            erreurs.append(resultat_libre["message"])

    if len(erreurs) > 0:
        return jsonify({
            "success": False,
            "message": "Test créé, mais certaines réponses n'ont pas été enregistrées.",
            "test_orientation_id": test_orientation_id,
            "erreurs": erreurs
        }), 400

    resultat_recommandation = calculer_recommandation(
        reponses,
        reponse_libre
    )

    resultat_scores = enregistrer_scores_orientation(
        test_orientation_id,
        resultat_recommandation
    )

    if not resultat_scores["success"]:
        return jsonify({
            "success": False,
            "message": "Les réponses ont été enregistrées, mais les scores n'ont pas été sauvegardés.",
            "test_orientation_id": test_orientation_id,
            "erreur_scores": resultat_scores["message"],
            "resultat_recommandation": resultat_recommandation
        }), 500

    terminer_test_orientation(test_orientation_id)

    consommation_autorisation = None

    if droit_test.get("raison") == "autorisation_doyen":
        consommation_autorisation = consommer_autorisation_nouveau_test(
            etudiant_id
        )

    return jsonify({
        "success": True,
        "message": "Test d'orientation enregistré avec réponses et scores.",
        "test_orientation_id": test_orientation_id,
        "etudiant_id": etudiant_id,
        "nombre_reponses_choix": len(reponses),
        "reponse_libre_enregistree": reponse_libre.strip() != "",
        "code_question_libre": code_question_libre,
        "droit_test_utilise": droit_test,
        "autorisation_consommee": consommation_autorisation,
        "scores_enregistres": resultat_scores,
        "resultat_recommandation": resultat_recommandation
    })