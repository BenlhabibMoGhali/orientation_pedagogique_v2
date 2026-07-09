# Plateforme intelligente de recommandation pédagogique

Projet web développé avec **Flask**, **React/Vite** et **MySQL** pour accompagner l’orientation pédagogique des étudiants vers une spécialité.

> État actuel du projet : la gestion des places/capacités par filière a été retirée. Le test d’orientation peut être repassé librement par l’étudiant.

---

## 1. Fonctionnalités principales

- Authentification étudiant et doyen.
- Inscription étudiant avec confirmation par code email.
- Chatbot d’orientation pédagogique.
- Analyse des réponses et calcul de scores par spécialité.
- Affichage des pourcentages de recommandation.
- Choix final libre de la filière par l’étudiant.
- Génération d’une fiche d’engagement PDF.
- Import du document signé/scanné par l’étudiant.
- Consultation, validation ou refus du document par le doyen.
- Recherche doyen par ID universitaire, nom ou prénom.
- Tableau de bord administratif, notifications et exports.

---

## 2. Prérequis à installer

Avant de lancer le projet, il faut installer :

1. **Python 3.10 ou plus**  
   Vérification :
   ```bash
   python --version
   ```

2. **Node.js et npm**  
   Vérification :
   ```bash
   node -v
   npm -v
   ```

3. **MySQL Server**  
   Vérification :
   ```bash
   mysql --version
   ```

4. **Git Bash** si le projet est lancé sur Windows avec le fichier `run_project.sh`.

---

## 3. Remarque importante pour Windows

Sur Windows, le script `run_project.sh` doit être exécuté avec **Git Bash** ou **WSL**.

Il ne faut pas le lancer directement avec PowerShell.

Si la commande `mysql --version` ne fonctionne pas dans Git Bash, ajouter MySQL au PATH temporairement :

```bash
export PATH="$PATH:/c/Program Files/MySQL/MySQL Server 8.4/bin"
```

Puis revérifier :

```bash
mysql --version
```

---

## 4. Démarrage automatique du projet

Depuis la racine du projet, c’est-à-dire le dossier qui contient :

```text
backend/
frontend/
run_project.sh
README.md
```

exécuter :

```bash
chmod +x run_project.sh
./run_project.sh
```

Le script va demander :

```text
Utilisateur MySQL [root]:
```

Si l’utilisateur est `root`, appuyer directement sur **Entrée**.

Ensuite il demande :

```text
Mot de passe MySQL pour root:
```

Entrer le mot de passe MySQL local.

---

## 5. Ce que fait le script automatiquement

Le fichier `run_project.sh` effectue les étapes suivantes :

1. vérifie la présence de Python, npm et MySQL ;
2. crée le fichier local `backend/.env` ;
3. crée l’environnement virtuel Python `backend/venv` ;
4. installe les dépendances Python depuis `backend/requirements.txt` ;
5. installe les dépendances frontend avec `npm install` ;
6. crée la base MySQL `orientation_pedagogique` si elle n’existe pas ;
7. exécute le fichier SQL principal `backend/database/schema.sql` ;
8. applique les migrations avec `backend/run_migrations.py` ;
9. insère ou met à jour les questions finales ;
10. lance le backend Flask ;
11. lance le frontend React/Vite.

---

## 6. Liens après lancement

Une fois le projet lancé, ouvrir :

```text
Frontend React : http://127.0.0.1:5173
```

Le backend Flask tourne sur :

```text
Backend Flask : http://127.0.0.1:5000
```

Route simple de test backend :

```text
http://127.0.0.1:5000/
```

Route simple de test auth :

```text
http://127.0.0.1:5000/api/auth/test
```

---

## 7. Configuration locale `.env`

Le script crée automatiquement le fichier :

```text
backend/.env
```

Exemple de contenu :

```env
SECRET_KEY=orientation_pedagogique_secret_key_dev
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=mot_de_passe_mysql
DB_NAME=orientation_pedagogique
ADMIN_CREATION_KEY=ADMIN_ORIENTATION_2026
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_EXPEDITEUR=
EMAIL_DESTINATAIRE_DOCUMENTS=
```

Le fichier `.env` est volontairement ignoré par GitHub, car il contient des informations locales ou sensibles.

---

## 8. Configuration email

L’inscription étudiant utilise un code de confirmation envoyé par email.

Pour que l’envoi d’email fonctionne, il faut compléter dans `backend/.env` :

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=adresse_email_expediteur
SMTP_PASSWORD=mot_de_passe_ou_mot_de_passe_application
EMAIL_EXPEDITEUR=adresse_email_expediteur
EMAIL_DESTINATAIRE_DOCUMENTS=adresse_email_admin_ou_doyen
```

Si ces champs ne sont pas configurés, le projet peut démarrer, mais l’envoi du code de confirmation étudiant échouera.

---

## 9. Création d’un compte doyen

La création du compte doyen est protégée par une clé administrative.

Clé par défaut en local :

```text
ADMIN_ORIENTATION_2026
```

Exemple de création du doyen avec `curl` :

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register/doyen \
  -H "Content-Type: application/json" \
  -d '{
    "cle_admin": "ADMIN_ORIENTATION_2026",
    "identifiant_connexion": "doyen",
    "mot_de_passe": "doyen123",
    "nom": "Doyen",
    "prenom": "Admin",
    "email": "doyen@example.com"
  }'
```

Ensuite, connexion avec :

```text
Identifiant : doyen
Mot de passe : doyen123
```

Il est conseillé de changer ces valeurs pour une vraie démonstration.

---

## 10. Compte étudiant de test

Pour faciliter les tests si le code de vérification email met du temps à arriver, une migration crée automatiquement un compte étudiant de démonstration lors du lancement du projet :

```text
Identifiant : 2300259
Mot de passe : 123456
```

Ce compte est prévu uniquement pour une démonstration locale. Pour un vrai déploiement, il faut le supprimer ou changer son mot de passe.

---

## 11. Informations pour l'encadrant

Les étapes de démarrage du projet sont détaillées dans ce fichier `README.md`.

Les vraies variables privées SMTP/Gemini ne doivent pas être publiées sur GitHub. Elles doivent être transmises séparément dans un fichier privé, puis copiées dans :

```text
backend/.env
```

---

## 10. Test conseillé après démarrage

Après lancement, tester dans cet ordre :

1. ouvrir `http://127.0.0.1:5173` ;
2. créer ou connecter un compte doyen ;
3. vérifier que le tableau de bord doyen s’ouvre ;
4. créer un compte étudiant ;
5. passer le test d’orientation ;
6. vérifier les résultats ;
7. choisir une filière finale ;
8. générer la fiche d’engagement PDF ;
9. importer le document signé/scanné ;
10. revenir dans l’espace doyen ;
11. rechercher l’étudiant ;
12. valider ou refuser le document.

---

## 11. Réinitialiser la base pour refaire un test propre

Si une ancienne version de la base existe déjà sur le PC, il est possible de supprimer la base locale avant de relancer le script :

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS orientation_pedagogique;"
```

Puis relancer :

```bash
./run_project.sh
```

Attention : cette commande supprime toutes les données locales de la base `orientation_pedagogique`.

---

## 12. Démarrage manuel sans le script

### Backend Flask

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Git Bash Windows
# ou : source venv/bin/activate    # Linux/macOS/WSL
pip install -r requirements.txt
mysql -u root -p < database/schema.sql
python run_migrations.py
python app.py
```

### Frontend React

Dans un deuxième terminal :

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

---

## 13. Commandes utiles de vérification

Vérifier les tables MySQL :

```bash
mysql -u root -p -e "USE orientation_pedagogique; SHOW TABLES;"
```

Vérifier les questions insérées :

```bash
mysql -u root -p -e "USE orientation_pedagogique; SELECT code_question, statut_question, active FROM questions LIMIT 10;"
```

Vérifier que le backend répond :

```bash
curl http://127.0.0.1:5000/api/auth/test
```

---

## 14. Problèmes fréquents

### Erreur : `mysql: command not found`

MySQL n’est pas accessible dans le terminal.

Sous Windows avec Git Bash :

```bash
export PATH="$PATH:/c/Program Files/MySQL/MySQL Server 8.4/bin"
```

### Erreur : `Access denied for user 'root'@'localhost'`

Le mot de passe MySQL saisi est incorrect ou l’utilisateur MySQL n’a pas les droits nécessaires.

### Erreur : port `5000` déjà utilisé

Un autre backend Flask est déjà lancé.

Fermer l’ancien terminal ou arrêter le processus qui utilise le port 5000.

### Erreur : port `5173` déjà utilisé

Un autre serveur Vite est déjà lancé.

Fermer l’ancien terminal ou utiliser un autre port.

### Erreur pendant `npm install`

Supprimer `frontend/node_modules` s’il existe, puis relancer :

```bash
cd frontend
npm install
```

### Erreur pendant `pip install`

Vérifier que Python est bien installé, puis relancer :

```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 15. Fichiers à ne pas pousser sur GitHub

Ne pas pousser :

```text
backend/venv/
frontend/node_modules/
backend/.env
backend/uploads/documents_signes/*
backend/uploads/fiches_engagement/*
backend/uploads/archives/*
__pycache__/
```

Ces fichiers sont normalement déjà ignorés dans `.gitignore`.

---

## 16. Commandes pour pousser sur GitHub

Après avoir testé le projet localement :

```bash
git init
git add .
git commit -m "Initial clean version of orientation pedagogique project"
git branch -M main
git remote add origin URL_DU_REPO_GITHUB
git push -u origin main
```

Avant de pousser, vérifier que `.env` n’est pas inclus :

```bash
git status
```

---

## 17. Technologies utilisées

- Backend : Python, Flask
- Frontend : React, Vite, JavaScript, HTML, CSS
- Base de données : MySQL
- PDF : ReportLab
- Export Excel : OpenPyXL
- Authentification : JWT
- Optionnel : Gemini / Claude pour l’analyse IA externe

## Configuration privée pour le professeur

Les clés email SMTP et Gemini ne doivent pas être publiées sur GitHub.
Le projet contient seulement `backend/.env.example` comme modèle.

Pour tester toutes les fonctionnalités :

1. créer le fichier `backend/.env` ;
2. y mettre les informations MySQL, SMTP et Gemini ;
3. lancer `./run_project.sh`.

Le script `run_project.sh` conserve maintenant `backend/.env` s'il existe déjà. Il ne l'écrase pas.
Ainsi, le professeur peut recevoir un fichier privé de configuration séparé, le placer dans `backend/.env`, puis lancer le projet.
