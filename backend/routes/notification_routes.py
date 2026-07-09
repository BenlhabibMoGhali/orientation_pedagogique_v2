from flask import Blueprint, jsonify, request

from database.notification_repository import (
    lister_notifications_utilisateur,
    compter_notifications_non_lues,
    marquer_notification_lue,
    marquer_toutes_notifications_lues
)
from services.jwt_service import token_requis, get_utilisateur_connecte_id, get_role_connecte


notification_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notifications"
)


@notification_bp.route("", methods=["GET"])
@token_requis(["etudiant", "doyen"])
def lister_notifications():
    utilisateur_id = get_utilisateur_connecte_id()
    role = get_role_connecte()

    limite = request.args.get("limite", 20)
    non_lues = request.args.get("non_lues", "0") == "1"

    try:
        limite = int(limite)
    except Exception:
        limite = 20

    notifications = lister_notifications_utilisateur(
        utilisateur_id,
        limite=limite,
        seulement_non_lues=non_lues
    )

    total_non_lues = compter_notifications_non_lues(utilisateur_id)

    return jsonify({
        "success": True,
        "role": role,
        "notifications": notifications,
        "total_non_lues": total_non_lues
    }), 200


@notification_bp.route("/non-lues/count", methods=["GET"])
@token_requis(["etudiant", "doyen"])
def compter_non_lues():
    utilisateur_id = get_utilisateur_connecte_id()

    return jsonify({
        "success": True,
        "total_non_lues": compter_notifications_non_lues(utilisateur_id)
    }), 200


@notification_bp.route("/<int:notification_id>/lire", methods=["PUT"])
@token_requis(["etudiant", "doyen"])
def lire_notification(notification_id):
    utilisateur_id = get_utilisateur_connecte_id()

    resultat = marquer_notification_lue(notification_id, utilisateur_id)
    status_code = 200 if resultat.get("success") else 404

    return jsonify(resultat), status_code


@notification_bp.route("/lire-toutes", methods=["PUT"])
@token_requis(["etudiant", "doyen"])
def lire_toutes_notifications():
    utilisateur_id = get_utilisateur_connecte_id()

    resultat = marquer_toutes_notifications_lues(utilisateur_id)
    status_code = 200 if resultat.get("success") else 400

    return jsonify(resultat), status_code
