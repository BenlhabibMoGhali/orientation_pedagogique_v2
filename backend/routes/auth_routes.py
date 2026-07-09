import re
import unicodedata

import os

from flask import Blueprint, jsonify, request

from database.auth_repository import (
    creer_etudiant,
    creer_doyen,
    verifier_connexion,
    demander_reinitialisation_mot_de_passe,
    reinitialiser_mot_de_passe
)
from database.inscription_confirmation_repository import (
    creer_confirmation_inscription_email,
    verifier_code_confirmation_inscription,
    marquer_confirmation_inscription_utilisee
)
from services.annee_universitaire_service import get_code_annee_universitaire_active
from services.jwt_service import generer_token_jwt
from services.email_confirmation_service import envoyer_email_confirmation_inscription


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


EMAIL_DOMAINE_EIDIA = "@eidia.ueuromed.org"
EMAIL_ETUDIANT_REGEX = r"^[a-z]+\.[a-z]+@eidia\.ueuromed\.org$"
ID_UNIVERSITAIRE_REGEX = r"^\d{7}$"


def normaliser_partie_email(valeur):
    if valeur is None:
        return ""

    texte = str(valeur).strip().lower()
    texte = unicodedata.normalize("NFD", texte)

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    texte = re.sub(r"[^a-z]", "", texte)

    return texte


def construire_email_attendu(nom, prenom):
    nom_normalise = normaliser_partie_email(nom)
    prenom_normalise = normaliser_partie_email(prenom)

    if nom_normalise == "" or prenom_normalise == "":
        return ""

    return f"{prenom_normalise}.{nom_normalise}{EMAIL_DOMAINE_EIDIA}"


def email_etudiant_valide(email, nom=None, prenom=None):
    if email is None:
        return False

    email = str(email).strip().lower()

    if email == "":
        return False

    if re.match(EMAIL_ETUDIANT_REGEX, email) is None:
        return False

    if nom is None or prenom is None:
        return True

    email_attendu = construire_email_attendu(nom, prenom)

    if email_attendu == "":
        return False

    return email == email_attendu


def id_universitaire_valide(id_universitaire):
    if id_universitaire is None:
        return False

    id_normalise = str(id_universitaire).strip()

    if re.match(ID_UNIVERSITAIRE_REGEX, id_normalise) is None:
        return False

    return True


def verifier_donnees_inscription_etudiant(data):
    if data is None:
        return {
            "success": False,
            "message": "Aucune donnée reçue."
        }

    nom = data.get("nom")
    prenom = data.get("prenom")
    email = data.get("email")
    id_universitaire = str(data.get("id_universitaire", "")).strip()
    mot_de_passe = data.get("mot_de_passe")
    confirmation_mot_de_passe = data.get("confirmation_mot_de_passe")

    if not id_universitaire_valide(id_universitaire):
        return {
            "success": False,
            "message": (
                "ID universitaire invalide. "
                "Il doit contenir exactement 7 chiffres, sans lettres ni espaces."
            )
        }

    email_attendu = construire_email_attendu(nom, prenom)

    if not email_etudiant_valide(email, nom, prenom):
        return {
            "success": False,
            "message": (
                "Email étudiant invalide. "
                "L'adresse doit correspondre exactement au nom et prénom saisis. "
                f"Adresse attendue : {email_attendu}"
            )
        }

    if mot_de_passe is None or str(mot_de_passe).strip() == "":
        return {
            "success": False,
            "message": "Mot de passe obligatoire."
        }

    if len(str(mot_de_passe)) < 6:
        return {
            "success": False,
            "message": "Le mot de passe doit contenir au moins 6 caractères."
        }

    if mot_de_passe != confirmation_mot_de_passe:
        return {
            "success": False,
            "message": "Les mots de passe ne correspondent pas."
        }

    return {
        "success": True,
        "nom": str(nom).strip(),
        "prenom": str(prenom).strip(),
        "email": str(email).strip().lower(),
        "id_universitaire": id_universitaire,
        "mot_de_passe": mot_de_passe,
        "confirmation_mot_de_passe": confirmation_mot_de_passe,
        "promotion": get_code_annee_universitaire_active()
    }


@auth_bp.route("/test", methods=["GET"])
def test_auth():
    return jsonify({
        "module": "authentification",
        "message": "Routes auth fonctionnelles."
    })


@auth_bp.route("/register/etudiant/demander-code", methods=["POST"])
def demander_code_inscription_etudiant():
    data = request.get_json()
    verification = verifier_donnees_inscription_etudiant(data)

    if not verification.get("success"):
        return jsonify(verification), 400

    resultat_code = creer_confirmation_inscription_email(
        nom=verification["nom"],
        prenom=verification["prenom"],
        id_universitaire=verification["id_universitaire"],
        email=verification["email"],
        annee_universitaire=verification["promotion"]
    )

    if not resultat_code.get("success"):
        return jsonify(resultat_code), 400

    resultat_email = envoyer_email_confirmation_inscription(
        email_destinataire=verification["email"],
        nom=verification["nom"],
        prenom=verification["prenom"],
        id_universitaire=verification["id_universitaire"],
        code=resultat_code["code"],
        expiration_minutes=resultat_code.get("expiration_minutes", 10)
    )

    if not resultat_email.get("success"):
        return jsonify(resultat_email), 500

    return jsonify({
        "success": True,
        "message": (
            "Un code de confirmation a été envoyé à votre email Outlook. "
            "Saisissez ce code pour confirmer votre inscription."
        ),
        "expiration_minutes": resultat_code.get("expiration_minutes", 10)
    }), 200


@auth_bp.route("/register/etudiant/confirmer-code", methods=["POST"])
def confirmer_code_inscription_etudiant():
    data = request.get_json()
    verification = verifier_donnees_inscription_etudiant(data)

    if not verification.get("success"):
        return jsonify(verification), 400

    code_confirmation = str(data.get("code_confirmation", "")).strip()

    if not re.match(r"^\d{6}$", code_confirmation):
        return jsonify({
            "success": False,
            "message": "Le code de confirmation doit contenir 6 chiffres."
        }), 400

    verification_code = verifier_code_confirmation_inscription(
        id_universitaire=verification["id_universitaire"],
        email=verification["email"],
        code=code_confirmation
    )

    if not verification_code.get("success"):
        return jsonify(verification_code), 400

    resultat = creer_etudiant(
        nom=verification["nom"],
        prenom=verification["prenom"],
        id_universitaire=verification["id_universitaire"],
        email=verification["email"],
        mot_de_passe=verification["mot_de_passe"],
        confirmation_mot_de_passe=verification["confirmation_mot_de_passe"],
        promotion=verification["promotion"]
    )

    if resultat.get("success"):
        confirmation = verification_code.get("confirmation")
        if confirmation is not None:
            marquer_confirmation_inscription_utilisee(confirmation["id"])

    status_code = 201 if resultat["success"] else 400

    return jsonify(resultat), status_code


@auth_bp.route("/register/etudiant", methods=["POST"])
def register_etudiant():
    return jsonify({
        "success": False,
        "message": (
            "L’inscription étudiant nécessite maintenant une confirmation "
            "par email Outlook. Veuillez d’abord demander un code de confirmation."
        )
    }), 400


@auth_bp.route("/register/doyen", methods=["POST"])
def register_doyen():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    cle_admin = data.get("cle_admin")

    cle_admin_attendue = os.getenv("ADMIN_CREATION_KEY", "ADMIN_ORIENTATION_2026")

    if cle_admin != cle_admin_attendue:
        return jsonify({
            "success": False,
            "message": "La création du compte doyen est réservée à l'administration."
        }), 403

    resultat = creer_doyen(
        identifiant_connexion=data.get("identifiant_connexion"),
        mot_de_passe=data.get("mot_de_passe"),
        nom=data.get("nom"),
        prenom=data.get("prenom"),
        email=data.get("email")
    )

    status_code = 201 if resultat["success"] else 400

    return jsonify(resultat), status_code


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    identifiant_connexion = data.get("identifiant_connexion")
    mot_de_passe = data.get("mot_de_passe")

    resultat = verifier_connexion(
        identifiant_connexion,
        mot_de_passe
    )

    if resultat.get("success") and resultat.get("utilisateur"):
        resultat["access_token"] = generer_token_jwt(resultat["utilisateur"])
        resultat["token_type"] = "Bearer"

    status_code = 200 if resultat["success"] else 401

    return jsonify(resultat), status_code


@auth_bp.route("/password/forgot", methods=["POST"])
def password_forgot():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    identifiant_ou_email = data.get("identifiant_ou_email")

    resultat = demander_reinitialisation_mot_de_passe(
        identifiant_ou_email
    )

    status_code = 200 if resultat["success"] else 400

    return jsonify(resultat), status_code


@auth_bp.route("/password/reset", methods=["POST"])
def password_reset():
    data = request.get_json()

    if data is None:
        return jsonify({
            "success": False,
            "message": "Aucune donnée reçue."
        }), 400

    resultat = reinitialiser_mot_de_passe(
        token=data.get("token"),
        nouveau_mot_de_passe=data.get("nouveau_mot_de_passe"),
        confirmation_mot_de_passe=data.get("confirmation_mot_de_passe")
    )

    status_code = 200 if resultat["success"] else 400

    return jsonify(resultat), status_code
