import base64
import functools
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta

from flask import jsonify, request, g


JWT_ALGORITHME = "HS256"
JWT_DUREE_HEURES = int(os.getenv("JWT_DUREE_HEURES", "8"))
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    os.getenv("SECRET_KEY", "orientation_pedagogique_secret_dev")
)


def encoder_base64url(donnees):
    if isinstance(donnees, str):
        donnees = donnees.encode("utf-8")

    return base64.urlsafe_b64encode(donnees).rstrip(b"=").decode("utf-8")


def decoder_base64url(texte):
    padding = "=" * (-len(texte) % 4)
    return base64.urlsafe_b64decode((texte + padding).encode("utf-8"))


def signer(contenu):
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        contenu.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return encoder_base64url(signature)


def generer_token_jwt(utilisateur):
    maintenant = int(time.time())
    expiration = maintenant + (JWT_DUREE_HEURES * 60 * 60)

    header = {
        "typ": "JWT",
        "alg": JWT_ALGORITHME
    }

    payload = {
        "utilisateur_id": utilisateur.get("id"),
        "identifiant": utilisateur.get("identifiant_connexion"),
        "role": utilisateur.get("role"),
        "iat": maintenant,
        "exp": expiration
    }

    header_encode = encoder_base64url(
        json.dumps(header, ensure_ascii=False, separators=(",", ":"))
    )
    payload_encode = encoder_base64url(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )

    contenu = f"{header_encode}.{payload_encode}"
    signature = signer(contenu)

    return f"{contenu}.{signature}"


def verifier_token_jwt(token):
    try:
        morceaux = token.split(".")

        if len(morceaux) != 3:
            return {
                "success": False,
                "message": "Token JWT invalide."
            }

        header_encode, payload_encode, signature_recue = morceaux
        contenu = f"{header_encode}.{payload_encode}"
        signature_attendue = signer(contenu)

        if not hmac.compare_digest(signature_recue, signature_attendue):
            return {
                "success": False,
                "message": "Signature du token invalide."
            }

        header = json.loads(decoder_base64url(header_encode).decode("utf-8"))
        payload = json.loads(decoder_base64url(payload_encode).decode("utf-8"))

        if header.get("alg") != JWT_ALGORITHME:
            return {
                "success": False,
                "message": "Algorithme JWT non autorisé."
            }

        expiration = payload.get("exp")

        if expiration is None or int(expiration) < int(time.time()):
            return {
                "success": False,
                "message": "Session expirée. Veuillez vous reconnecter."
            }

        return {
            "success": True,
            "payload": payload
        }

    except Exception as erreur:
        return {
            "success": False,
            "message": "Token JWT impossible à vérifier.",
            "erreur": str(erreur)
        }


def recuperer_token_requete():
    authorization = request.headers.get("Authorization", "")

    if authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "", 1).strip()

    token_url = request.args.get("token")

    if token_url:
        return token_url.strip()

    return None


def token_requis(roles_autorises=None):
    if roles_autorises is None:
        roles_autorises = []

    def decorateur(fonction):
        @functools.wraps(fonction)
        def wrapper(*args, **kwargs):
            token = recuperer_token_requete()

            if token is None:
                return jsonify({
                    "success": False,
                    "message": "Authentification obligatoire. Token manquant."
                }), 401

            verification = verifier_token_jwt(token)

            if not verification.get("success"):
                return jsonify({
                    "success": False,
                    "message": verification.get(
                        "message",
                        "Token invalide."
                    )
                }), 401

            payload = verification["payload"]
            role = payload.get("role")

            if roles_autorises and role not in roles_autorises:
                return jsonify({
                    "success": False,
                    "message": "Accès non autorisé pour ce rôle."
                }), 403

            g.utilisateur_auth = payload

            return fonction(*args, **kwargs)

        return wrapper

    return decorateur


def doyen_requis(fonction):
    return token_requis(["doyen"])(fonction)


def etudiant_requis(fonction):
    return token_requis(["etudiant"])(fonction)


def get_utilisateur_connecte_id():
    payload = getattr(g, "utilisateur_auth", {})
    return payload.get("utilisateur_id")


def get_role_connecte():
    payload = getattr(g, "utilisateur_auth", {})
    return payload.get("role")
