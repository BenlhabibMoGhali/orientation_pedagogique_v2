from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database.db import tester_connexion_db

from routes.auth_routes import auth_bp
from routes.etudiant_routes import etudiant_bp
from routes.doyen_routes import doyen_bp
from routes.chatbot_routes import chatbot_bp
from routes.chat_orientation_routes import chat_orientation_bp
from routes.fiche_routes import fiche_bp
from routes.question_routes import question_bp
from routes.notification_routes import notification_bp


app = Flask(__name__)
app.config.from_object(Config)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    }
)


@app.errorhandler(404)
def erreur_404(error):
    return jsonify({
        "success": False,
        "message": "Route API introuvable."
    }), 404


@app.errorhandler(500)
def erreur_500(error):
    return jsonify({
        "success": False,
        "message": "Erreur interne du serveur."
    }), 500


@app.route("/")
def home():
    return jsonify({
        "message": "Back-end Flask de la plateforme d'orientation pédagogique fonctionne correctement."
    })


@app.route("/api/database/test")
def test_database():
    resultat = tester_connexion_db()
    return jsonify(resultat)


app.register_blueprint(auth_bp)
app.register_blueprint(etudiant_bp)
app.register_blueprint(doyen_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(chat_orientation_bp)
app.register_blueprint(fiche_bp)
app.register_blueprint(question_bp)
app.register_blueprint(notification_bp)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)