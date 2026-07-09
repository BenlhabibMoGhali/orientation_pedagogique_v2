import os
from pathlib import Path


def _charger_env_local():
    """Charge backend/.env si le fichier existe, sans dépendance externe."""
    chemins = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]

    for chemin in chemins:
        if not chemin.exists():
            continue

        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue

            cle, valeur = ligne.split("=", 1)
            cle = cle.strip()
            valeur = valeur.strip().strip('"').strip("'")

            if cle and cle not in os.environ:
                os.environ[cle] = valeur


_charger_env_local()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "orientation_pedagogique_secret_key_dev")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "orientation_pedagogique")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
