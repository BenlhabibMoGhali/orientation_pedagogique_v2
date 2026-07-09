from database.migration_chat_ai_choix_final import appliquer_migration as migration_chat
from database.migration_documents_confirmation import appliquer_migration as migration_documents
from database.migration_inscription_securite import appliquer_migration as migration_inscription
from database.migration_reinitialisation_annuelle import appliquer_migration as migration_reinitialisation
from database.migration_tables_systeme import appliquer_migration as migration_tables_systeme
from database.migration_questions_chatbot import appliquer_migration as migration_questions_chatbot
from database.migration_compte_test_etudiant import appliquer_migration as migration_compte_test_etudiant
from database.seed_final_questions import inserer_questions_finales
from database.seed_chatbot_questions import inserer_questions_chatbot
from services.annee_universitaire_service import assurer_annee_universitaire_active


def main():
    print("Application des migrations...")
    migration_tables_systeme()
    migration_questions_chatbot()
    migration_chat()
    migration_documents()
    migration_inscription()
    migration_reinitialisation()
    assurer_annee_universitaire_active()

    print("Insertion/mise à jour des questions finales...")
    inserer_questions_finales()

    print("Insertion/mise à jour des questions utilisées par le chatbot...")
    inserer_questions_chatbot()

    print("Création/vérification du compte étudiant de test...")
    migration_compte_test_etudiant()

    print("Base de données initialisée avec succès.")


if __name__ == "__main__":
    main()
