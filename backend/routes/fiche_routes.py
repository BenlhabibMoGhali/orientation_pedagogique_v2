from flask import Blueprint, jsonify

from database.fiche_repository import (
    generer_fiche_intelligente,
    get_fiche_par_test
)


fiche_bp = Blueprint("fiche", __name__, url_prefix="/api/fiches")


@fiche_bp.route("/test", methods=["GET"])
def test_fiche():
    return jsonify({
        "module": "fiches intelligentes",
        "message": "Routes des fiches intelligentes fonctionnelles."
    })


@fiche_bp.route("/generer/<int:test_orientation_id>", methods=["POST"])
def generer_fiche(test_orientation_id):
    resultat = generer_fiche_intelligente(test_orientation_id)

    status_code = 201 if resultat["success"] else 400

    return jsonify(resultat), status_code


@fiche_bp.route("/test-orientation/<int:test_orientation_id>", methods=["GET"])
def afficher_fiche_par_test(test_orientation_id):
    fiche = get_fiche_par_test(test_orientation_id)

    if fiche is None:
        return jsonify({
            "success": False,
            "message": "Aucune fiche trouvée pour ce test."
        }), 404

    return jsonify({
        "success": True,
        "fiche": fiche
    })