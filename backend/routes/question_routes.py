from flask import Blueprint, jsonify

from database.question_repository import get_questions_par_statut


question_bp = Blueprint("question", __name__, url_prefix="/api/questions")


@question_bp.route("/test", methods=["GET"])
def test_questions():
    return jsonify({
        "module": "gestion des questions",
        "message": "Routes de gestion des questions fonctionnelles."
    })


@question_bp.route("/provisoires", methods=["GET"])
def afficher_questions_provisoires():
    questions = get_questions_par_statut("provisoire")

    return jsonify({
        "type": "questions provisoires",
        "source": "base de données MySQL",
        "questions": questions
    })


@question_bp.route("/finales", methods=["GET"])
def afficher_questions_finales():
    questions = get_questions_par_statut("finale")

    return jsonify({
        "type": "questions finales",
        "source": "base de données MySQL",
        "questions": questions
    })