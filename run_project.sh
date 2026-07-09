#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
ENV_FILE="$BACKEND_DIR/.env"
DB_NAME_DEFAULT="orientation_pedagogique"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

error_exit() {
  echo "Erreur: $1" >&2
  exit 1
}

if command_exists python3; then
  PYTHON_BIN="python3"
elif command_exists python; then
  PYTHON_BIN="python"
else
  error_exit "Python 3 est introuvable. Installe Python 3.10+ puis relance le script."
fi

command_exists npm || error_exit "npm est introuvable. Installe Node.js puis relance le script."
command_exists mysql || error_exit "La commande mysql est introuvable. Installe MySQL Server/Client et ajoute mysql au PATH."

# Crée le fichier .env seulement s'il n'existe pas déjà.
# Si backend/.env existe, le script le garde pour ne pas effacer les clés SMTP/Gemini.
if [ ! -f "$ENV_FILE" ]; then
  read -r -p "Utilisateur MySQL [root]: " DB_USER_INPUT
  DB_USER_INPUT=${DB_USER_INPUT:-root}
  read -r -s -p "Mot de passe MySQL pour $DB_USER_INPUT (laisser vide si aucun): " DB_PASSWORD_INPUT
  echo ""

  cat > "$ENV_FILE" <<EOF_ENV
SECRET_KEY=orientation_pedagogique_secret_key_dev
JWT_SECRET_KEY=orientation_pedagogique_jwt_secret_dev
DB_HOST=localhost
DB_PORT=3306
DB_USER=$DB_USER_INPUT
DB_PASSWORD=$DB_PASSWORD_INPUT
DB_NAME=$DB_NAME_DEFAULT
ADMIN_CREATION_KEY=ADMIN_ORIENTATION_2026
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_EXPEDITEUR=
EMAIL_DESTINATAIRE_DOCUMENTS=
EOF_ENV
  echo "Fichier backend/.env créé. Tu peux le modifier si tu veux ajouter SMTP/Gemini."
else
  echo "Fichier backend/.env déjà présent : il sera conservé."
fi

# Charge les variables du .env pour initialiser MySQL.
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-}
DB_NAME=${DB_NAME:-$DB_NAME_DEFAULT}

mkdir -p \
  "$BACKEND_DIR/uploads/documents_signes" \
  "$BACKEND_DIR/uploads/fiches_engagement" \
  "$BACKEND_DIR/uploads/archives"

if [ ! -d "$BACKEND_DIR/venv" ]; then
  echo "Création de l'environnement virtuel Python..."
  "$PYTHON_BIN" -m venv "$BACKEND_DIR/venv"
fi

if [ -f "$BACKEND_DIR/venv/Scripts/activate" ]; then
  # Git Bash / Windows
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/venv/Scripts/activate"
elif [ -f "$BACKEND_DIR/venv/bin/activate" ]; then
  # Linux / macOS / WSL
  # shellcheck disable=SC1091
  source "$BACKEND_DIR/venv/bin/activate"
else
  error_exit "Environnement virtuel incomplet. Supprime backend/venv puis relance le script."
fi

echo "Installation des dépendances Python..."
python -m pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

echo "Installation des dépendances frontend..."
cd "$FRONTEND_DIR"
npm install

echo "Initialisation de la base de données MySQL..."
if [ -z "$DB_PASSWORD" ]; then
  mysql -u "$DB_USER" < "$BACKEND_DIR/database/schema.sql"
else
  MYSQL_PWD="$DB_PASSWORD" mysql -u "$DB_USER" < "$BACKEND_DIR/database/schema.sql"
fi

cd "$BACKEND_DIR"
python run_migrations.py

echo "Lancement du backend Flask sur http://127.0.0.1:5000 ..."
python app.py &
BACKEND_PID=$!

cleanup() {
  echo "Arrêt du backend..."
  kill "$BACKEND_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 2

echo "Lancement du frontend React sur http://127.0.0.1:5173 ..."
cd "$FRONTEND_DIR"
npm run dev -- --host 127.0.0.1
