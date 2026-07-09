from flask import Blueprint, jsonify


etudiant_bp = Blueprint("etudiant", __name__, url_prefix="/api/etudiant")


@etudiant_bp.route("/test", methods=["GET"])
def test_etudiant():
    return jsonify({
        "module": "espace étudiant",
        "message": "Routes étudiant fonctionnelles."
    })