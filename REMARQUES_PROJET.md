# Remarques techniques avant push GitHub

## Décisions fonctionnelles retenues

- La gestion des places/capacités par filière est retirée du projet.
- Le test d’orientation peut être repassé librement par l’étudiant.
- La validation du doyen concerne le document signé et le suivi administratif, pas une affectation selon capacité.

## Corrections appliquées

- Nettoyage du projet pour GitHub : suppression de `venv`, `node_modules`, `__pycache__` et des fichiers uploadés.
- Correction du script SQL principal.
- Conversion de `requirements.txt` en UTF-8.
- Ajout d’une configuration par fichier `.env`.
- Ajout d’un script unique `run_project.sh`.
- Ajout d’une base SQL plus complète pour éviter les tables manquantes.
- Ajout de migrations complémentaires pour les documents, notifications, archives et années universitaires.
- Retrait de la dépendance à la table `capacites_filieres`.

## Points à vérifier sur le PC de l’encadrant

- MySQL doit être installé et lancé.
- La commande `mysql` doit être disponible dans le terminal.
- Python et Node.js doivent être installés.
- Sous Windows, le fichier `.sh` peut être exécuté avec Git Bash ou WSL.

## Remarque sur l’IA

Les services Gemini/Claude sont présents comme extension possible. Si aucune clé API n’est configurée, le projet reste fonctionnel grâce au moteur local de scoring et d’analyse.
