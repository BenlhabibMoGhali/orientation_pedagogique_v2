CREATE DATABASE IF NOT EXISTS orientation_pedagogique
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE orientation_pedagogique;

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identifiant_connexion VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role ENUM('etudiant', 'doyen') NOT NULL,
    actif BOOLEAN DEFAULT TRUE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS etudiants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL UNIQUE,
    id_universitaire VARCHAR(50) NOT NULL UNIQUE,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    email VARCHAR(150),
    promotion VARCHAR(20) NULL,
    autorisation_nouveau_test BOOLEAN NOT NULL DEFAULT FALSE,
    date_autorisation_nouveau_test DATETIME NULL,
    doyen_autorisation_id INT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_etudiants_email (email),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS doyens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL UNIQUE,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    email VARCHAR(150),
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS specialites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code_question VARCHAR(50) NOT NULL UNIQUE,
    texte TEXT NOT NULL,
    type_question ENUM('choix_unique', 'choix_multiple', 'texte_libre', 'hesitation') NOT NULL,
    statut_question ENUM('provisoire', 'finale') DEFAULT 'provisoire',
    ordre INT,
    active BOOLEAN DEFAULT TRUE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS choix_reponses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    code_reponse VARCHAR(50) NOT NULL UNIQUE,
    texte TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS poids_reponses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    choix_reponse_id INT NOT NULL,
    specialite_id INT NOT NULL,
    poids INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_poids_reponse_specialite (choix_reponse_id, specialite_id),
    FOREIGN KEY (choix_reponse_id) REFERENCES choix_reponses(id) ON DELETE CASCADE,
    FOREIGN KEY (specialite_id) REFERENCES specialites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tests_orientation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    date_test DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    statut ENUM('en_cours', 'termine') DEFAULT 'en_cours',
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reponses_etudiants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_orientation_id INT NOT NULL,
    question_id INT NOT NULL,
    choix_reponse_id INT NULL,
    reponse_libre TEXT NULL,
    date_reponse DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_orientation_id) REFERENCES tests_orientation(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (choix_reponse_id) REFERENCES choix_reponses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analyses_reponses_libres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reponse_etudiant_id INT NOT NULL,
    mots_cles_detectes TEXT,
    scores_detectes TEXT,
    commentaire_analyse TEXT,
    date_analyse DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reponse_etudiant_id) REFERENCES reponses_etudiants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scores_orientation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_orientation_id INT NOT NULL,
    specialite_id INT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    pourcentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    UNIQUE KEY uq_score_test_specialite (test_orientation_id, specialite_id),
    FOREIGN KEY (test_orientation_id) REFERENCES tests_orientation(id) ON DELETE CASCADE,
    FOREIGN KEY (specialite_id) REFERENCES specialites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fiches_intelligentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_orientation_id INT NOT NULL UNIQUE,
    specialite_recommandee_id INT NOT NULL,
    resume_profil TEXT,
    statut_validation ENUM('en_attente', 'validee', 'a_revoir') DEFAULT 'en_attente',
    remarque_doyen TEXT,
    date_generation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_orientation_id) REFERENCES tests_orientation(id) ON DELETE CASCADE,
    FOREIGN KEY (specialite_recommandee_id) REFERENCES specialites(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS validations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fiche_id INT NOT NULL,
    doyen_id INT NOT NULL,
    statut ENUM('validee', 'a_revoir') NOT NULL,
    remarque TEXT,
    date_validation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES fiches_intelligentes(id) ON DELETE CASCADE,
    FOREIGN KEY (doyen_id) REFERENCES doyens(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historique_orientations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fiche_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES fiches_intelligentes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sessions_chat_orientation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'en_cours',
    raison_droit VARCHAR(100) NULL,
    index_question INT NOT NULL DEFAULT 0,
    scores_json TEXT NULL,
    reponses_json TEXT NULL,
    test_orientation_id INT NULL,
    fiche_id INT NULL,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (test_orientation_id) REFERENCES tests_orientation(id) ON DELETE SET NULL,
    FOREIGN KEY (fiche_id) REFERENCES fiches_intelligentes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS messages_chat_orientation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_chat_id INT NOT NULL,
    role_message VARCHAR(20) NOT NULL,
    contenu TEXT NOT NULL,
    date_message DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_chat_id) REFERENCES sessions_chat_orientation(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS choix_finaux_orientation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fiche_id INT NOT NULL UNIQUE,
    etudiant_id INT NOT NULL,
    specialite_id INT NOT NULL,
    commentaire TEXT NULL,
    annee_universitaire VARCHAR(20) NOT NULL DEFAULT '2026/2027',
    statut_choix VARCHAR(50) NOT NULL DEFAULT 'fiche_generee',
    pdf_engagement_path VARCHAR(500) NULL,
    date_generation_pdf DATETIME NULL,
    date_confirmation_doyen DATETIME NULL,
    doyen_confirmation_id INT NULL,
    remarque_doyen TEXT NULL,
    date_choix DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fiche_id) REFERENCES fiches_intelligentes(id) ON DELETE CASCADE,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (specialite_id) REFERENCES specialites(id) ON DELETE CASCADE,
    FOREIGN KEY (doyen_confirmation_id) REFERENCES doyens(id) ON DELETE SET NULL,
    INDEX idx_choix_annee_statut (annee_universitaire, statut_choix),
    INDEX idx_choix_specialite_annee (specialite_id, annee_universitaire)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documents_choix_final (
    id INT AUTO_INCREMENT PRIMARY KEY,
    choix_final_id INT NOT NULL,
    etudiant_id INT NOT NULL,
    nom_fichier_original VARCHAR(255) NOT NULL,
    nom_fichier_stocke VARCHAR(255) NOT NULL,
    chemin_fichier VARCHAR(500) NOT NULL,
    type_fichier VARCHAR(100) NOT NULL,
    taille_fichier INT NOT NULL,
    statut_document VARCHAR(50) NOT NULL DEFAULT 'en_attente_confirmation_doyen',
    verification_auto_statut VARCHAR(50) NULL,
    verification_auto_message TEXT NULL,
    remarque_doyen TEXT NULL,
    date_upload DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_decision_doyen DATETIME NULL,
    doyen_id INT NULL,
    archive_document_valide_path VARCHAR(500) NULL,
    FOREIGN KEY (choix_final_id) REFERENCES choix_finaux_orientation(id) ON DELETE CASCADE,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    FOREIGN KEY (doyen_id) REFERENCES doyens(id) ON DELETE SET NULL,
    INDEX idx_documents_statut (statut_document),
    INDEX idx_documents_choix_date (choix_final_id, date_upload)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historique_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    date_action DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS annees_universitaires (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    annee_debut INT NOT NULL,
    annee_fin INT NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS confirmations_inscription_email (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    id_universitaire VARCHAR(50) NOT NULL,
    email VARCHAR(150) NOT NULL,
    annee_universitaire VARCHAR(20) NULL,
    code_hash VARCHAR(255) NOT NULL,
    date_expiration DATETIME NOT NULL,
    utilise TINYINT(1) NOT NULL DEFAULT 0,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_utilisation DATETIME NULL,
    INDEX idx_confirmation_identite (id_universitaire, email, utilise)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reinitialisations_mots_de_passe (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    date_expiration DATETIME NOT NULL,
    utilise BOOLEAN NOT NULL DEFAULT FALSE,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reinitialisations_annuelles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    annee_universitaire VARCHAR(20) NOT NULL,
    phrase_securite VARCHAR(255) NOT NULL,
    code_confirmation VARCHAR(20) NOT NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'en_attente',
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_expiration DATETIME NOT NULL,
    date_execution DATETIME NULL,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notifications_internes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    role_destinataire VARCHAR(30) NOT NULL,
    titre VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type_notification VARCHAR(80) NOT NULL,
    lien_action VARCHAR(255) NULL,
    lue TINYINT(1) NOT NULL DEFAULT 0,
    date_lecture DATETIME NULL,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    INDEX idx_notifications_user_lue (utilisateur_id, lue),
    INDEX idx_notifications_role_lue (role_destinataire, lue)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS archives_fiches_engagement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL UNIQUE,
    choix_final_id INT NOT NULL,
    etudiant_id INT NOT NULL,
    id_universitaire VARCHAR(100) NOT NULL,
    nom VARCHAR(150) NULL,
    prenom VARCHAR(150) NULL,
    email_outlook VARCHAR(255) NULL,
    filiere_choisie VARCHAR(150) NULL,
    annee_universitaire VARCHAR(20) NULL,
    nom_fichier_archive VARCHAR(255) NOT NULL,
    chemin_archive VARCHAR(500) NOT NULL,
    type_fichier VARCHAR(100) NULL,
    date_archivage DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents_choix_final(id) ON DELETE CASCADE,
    FOREIGN KEY (choix_final_id) REFERENCES choix_finaux_orientation(id) ON DELETE CASCADE,
    FOREIGN KEY (etudiant_id) REFERENCES etudiants(id) ON DELETE CASCADE,
    INDEX idx_archives_fiches_annee (annee_universitaire),
    INDEX idx_archives_fiches_filiere (filiere_choisie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS archives_exports_excel (
    id INT AUTO_INCREMENT PRIMARY KEY,
    annee_universitaire VARCHAR(20) NOT NULL,
    nom_fichier VARCHAR(255) NOT NULL,
    chemin_archive VARCHAR(500) NOT NULL,
    date_generation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_export_excel_annee_nom (annee_universitaire, nom_fichier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS etudiants_officiels_promotion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    annee_universitaire VARCHAR(20) NOT NULL,
    id_universitaire VARCHAR(100) NOT NULL,
    nom VARCHAR(150) NOT NULL,
    prenom VARCHAR(150) NOT NULL,
    email_outlook VARCHAR(255) NULL,
    source_import VARCHAR(80) NULL,
    active TINYINT(1) NOT NULL DEFAULT 1,
    date_import DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_officiel_annee_id (annee_universitaire, id_universitaire),
    INDEX idx_officiel_annee_active (annee_universitaire, active),
    INDEX idx_officiel_id_universitaire (id_universitaire)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO specialites (nom, description) VALUES
('Big Data', 'Spécialité orientée vers l’analyse, le traitement et l’exploitation de grandes quantités de données.'),
('Intelligence Artificielle', 'Spécialité orientée vers les modèles intelligents, l’apprentissage automatique et les systèmes capables d’apprendre.'),
('Cybersécurité', 'Spécialité orientée vers la protection des systèmes, des réseaux et des données.'),
('Développement Full Stack', 'Spécialité orientée vers la création d’applications web et mobiles complètes.'),
('Robotique et Cobotique', 'Spécialité orientée vers la robotique, l’automatisation et les systèmes intelligents physiques.');
