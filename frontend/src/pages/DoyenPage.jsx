import { useEffect, useState } from 'react'
import {
  rechercherFichesParIdUniversitaire,
  getDocumentsAConfirmer,
  getUrlVisualisationDocument,
  prendreDecisionDocument,
  getResumeReinitialisation,
  creerDemandeReinitialisation,
  confirmerReinitialisation,
  getDiscussionFiche,
  getUrlDiscussionFichePdf,
  getUrlDiscussionFicheTxt,
  getEtatNotificationEmail,
  getAnneeUniversitaireActive,
  getHistoriqueEtudiantFiche,
  getTableauBordDoyenAvance,
  getSuiviPromotionDoyen,
  importerListeOfficiellePromotion,
  getUrlExportSuiviPromotionExcel,
  getArchivesAdministratives,
  getUrlArchiveFicheVisualisation,
  getUrlArchiveFicheTelechargement,
  getUrlArchiveExportExcelTelechargement
} from '../services/doyenService'
import '../styles/LoginPage.css'

function DoyenPage({ utilisateur, onLogout }) {
  const [recherche, setRecherche] = useState('')
  const [fiches, setFiches] = useState([])
  const [ficheSelectionnee, setFicheSelectionnee] = useState(null)

  const [documentsAConfirmer, setDocumentsAConfirmer] = useState([])
  const [afficherListeDocumentsAConfirmer, setAfficherListeDocumentsAConfirmer] = useState(false)
  const [chargementTableau, setChargementTableau] = useState(false)
  const [derniereActualisation, setDerniereActualisation] = useState('')
  const [etatNotificationEmail, setEtatNotificationEmail] = useState(null)
  const [anneeUniversitaireActive, setAnneeUniversitaireActive] = useState(null)
  const [tableauBordAvance, setTableauBordAvance] = useState(null)
  const [suiviPromotion, setSuiviPromotion] = useState(null)
  const [texteListeOfficielle, setTexteListeOfficielle] = useState('')
  const [remplacerListeOfficielle, setRemplacerListeOfficielle] = useState(false)
  const [afficherImportListe, setAfficherImportListe] = useState(false)
  const [importListeEnCours, setImportListeEnCours] = useState(false)
  const [messageImportListe, setMessageImportListe] = useState('')
  const [archivesAdministratives, setArchivesAdministratives] = useState({ fiches: [], exports: [] })
  const [chargementArchives, setChargementArchives] = useState(false)
  const [erreurArchives, setErreurArchives] = useState('')

  const [message, setMessage] = useState('')
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)
  const [decisionEnCours, setDecisionEnCours] = useState(false)
  const [documentSelectionne, setDocumentSelectionne] = useState(null)
  const [remarqueDocument, setRemarqueDocument] = useState('')

  const [anneeReinitialisation, setAnneeReinitialisation] = useState('')
  const [resumeReinitialisation, setResumeReinitialisation] = useState(null)
  const [motDePasseDoyen, setMotDePasseDoyen] = useState('')
  const [phraseSecurite, setPhraseSecurite] = useState('')
  const [demandeReinitialisation, setDemandeReinitialisation] = useState(null)
  const [codeConfirmation, setCodeConfirmation] = useState('')
  const [reinitialisationEnCours, setReinitialisationEnCours] = useState(false)

  const [discussionDoyen, setDiscussionDoyen] = useState(null)
  const [chargementDiscussion, setChargementDiscussion] = useState(false)
  const [fenetreDiscussionOuverte, setFenetreDiscussionOuverte] = useState(false)
  const [erreurDiscussion, setErreurDiscussion] = useState('')

  const [historiqueEtudiant, setHistoriqueEtudiant] = useState([])
  const [chargementHistorique, setChargementHistorique] = useState(false)
  const [erreurHistorique, setErreurHistorique] = useState('')
  const [fenetreStatistiquesOuverte, setFenetreStatistiquesOuverte] = useState(false)

  useEffect(() => {
    chargerTableauDoyen()
  }, [])

  useEffect(() => {
    if (ficheSelectionnee && ficheSelectionnee.fiche_id) {
      chargerHistoriqueEtudiant(ficheSelectionnee.fiche_id)
    } else {
      setHistoriqueEtudiant([])
      setErreurHistorique('')
    }
  }, [ficheSelectionnee?.fiche_id])

  const chargerTableauDoyen = async (afficherMessageActualisation = false) => {
  setErreur('')
  setChargementTableau(true)

  try {
    const resultatDocuments = await getDocumentsAConfirmer()
    const resultatAnnee = await getAnneeUniversitaireActive()
    const resultatTableauBord = await getTableauBordDoyenAvance()
    const resultatSuiviPromotion = await getSuiviPromotionDoyen()
    const resultatArchives = await getArchivesAdministratives()

    setDocumentsAConfirmer(resultatDocuments.documents || [])
    setAnneeUniversitaireActive(resultatAnnee.annee_universitaire || null)
    setTableauBordAvance(resultatTableauBord || null)
    setSuiviPromotion(resultatSuiviPromotion || null)
    setArchivesAdministratives({
      fiches: resultatArchives.fiches || [],
      exports: resultatArchives.exports || []
    })

    if (resultatAnnee.annee_universitaire?.code) {
      setAnneeReinitialisation(resultatAnnee.annee_universitaire.code)
    }

    try {
      const resultatEtatEmail = await getEtatNotificationEmail()

      setEtatNotificationEmail(resultatEtatEmail)
    } catch (erreurEmail) {
      setEtatNotificationEmail({
        success: false,
        email_configure: false,
        message: (
          "Impossible de vérifier l’état des notifications email. " +
          "Les dépôts de documents restent fonctionnels."
        )
      })
    }

    setDerniereActualisation(new Date().toLocaleString('fr-FR'))

    if (afficherMessageActualisation) {
      setMessage('Tableau doyen actualisé avec succès.')
    }
  } catch (error) {
    setErreur(error.message)
  } finally {
    setChargementTableau(false)
  }
}

  const rechercherFiche = async (event) => {
    event.preventDefault()

    setErreur('')
    setMessage('')
    setFiches([])
    setFicheSelectionnee(null)
    setDiscussionDoyen(null)
    setFenetreDiscussionOuverte(false)
    setErreurDiscussion('')
    setHistoriqueEtudiant([])
    setErreurHistorique('')
    setHistoriqueEtudiant([])
    setErreurHistorique('')

    if (recherche.trim() === '') {
      setErreur('Veuillez saisir un ID universitaire ou un nom complet.')
      return
    }

    setChargement(true)

    try {
      const resultat = await rechercherFichesParIdUniversitaire(
        recherche.trim()
      )

      setFiches(resultat.fiches)

      if (resultat.fiches.length > 0) {
        setFicheSelectionnee(resultat.fiches[0])
      } else {
        setMessage('Aucun étudiant trouvé pour cette recherche.')
      }
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const changerFiche = (ficheId) => {
    const fiche = fiches.find((item) => item.fiche_id === Number(ficheId))

    setFicheSelectionnee(fiche)
    setMessage('')
    setErreur('')
    setDiscussionDoyen(null)
    setFenetreDiscussionOuverte(false)
    setErreurDiscussion('')
  }

  const parcourirDocumentsAConfirmer = () => {
    setAfficherListeDocumentsAConfirmer(true)

    setTimeout(() => {
      const zoneDocuments = document.getElementById('documents-a-confirmer-liste')

      if (zoneDocuments) {
        zoneDocuments.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }
    }, 100)
  }

  const ouvrirDocument = (documentId) => {
    window.open(
      getUrlVisualisationDocument(documentId),
      '_blank',
      'noopener,noreferrer'
    )
  }

  const preparerDecisionDocument = (document) => {
    setDocumentSelectionne(document)
    setRemarqueDocument('')
    setErreur('')
    setMessage('')
  }

  const fermerFenetreDecision = () => {
    if (decisionEnCours) {
      return
    }

    setDocumentSelectionne(null)
    setRemarqueDocument('')
    setErreur('')
  }

  const envoyerDecisionDocument = async (decision) => {
    if (!documentSelectionne) {
      setErreur('Aucun document sélectionné.')
      return
    }

    if (decision === 'refuser' && remarqueDocument.trim() === '') {
      setErreur('Veuillez ajouter une remarque pour expliquer le refus.')
      return
    }

    setErreur('')
    setMessage('')
    setDecisionEnCours(true)

    try {
      const resultat = await prendreDecisionDocument(
        utilisateur.id,
        documentSelectionne.choix_final_id,
        decision,
        remarqueDocument
      )

      setMessage(resultat.message)
      setDocumentSelectionne(null)
      setRemarqueDocument('')

      await chargerTableauDoyen()
      setAfficherListeDocumentsAConfirmer(true)

      if (ficheSelectionnee) {
        await rafraichirRechercheActuelle()
      }
    } catch (error) {
      setErreur(error.message)
    } finally {
      setDecisionEnCours(false)
    }
  }

  const rafraichirRechercheActuelle = async () => {
    if (recherche.trim() === '') {
      return
    }

    const resultat = await rechercherFichesParIdUniversitaire(
      recherche.trim()
    )

    setFiches(resultat.fiches)

    if (resultat.fiches.length > 0) {
      setFicheSelectionnee(resultat.fiches[0])
    }
  }

  const chargerResumeReinitialisation = async () => {
    setErreur('')
    setMessage('')
    setResumeReinitialisation(null)
    setDemandeReinitialisation(null)
    setCodeConfirmation('')
    setMotDePasseDoyen('')
    setPhraseSecurite('')

    if (anneeReinitialisation.trim() === '') {
      setErreur('Veuillez saisir une année universitaire.')
      return
    }

    try {
      const resultat = await getResumeReinitialisation(
        anneeReinitialisation.trim()
      )

      setResumeReinitialisation(resultat)
    } catch (error) {
      setErreur(error.message)
    }
  }

  const demanderReinitialisation = async () => {
    setErreur('')
    setMessage('')

    if (!resumeReinitialisation) {
      setErreur('Veuillez d’abord charger le résumé.')
      return
    }

    if (motDePasseDoyen.trim() === '') {
      setErreur('Veuillez saisir le mot de passe du doyen.')
      return
    }

    if (phraseSecurite.trim() === '') {
      setErreur('Veuillez recopier la phrase de sécurité.')
      return
    }

    setReinitialisationEnCours(true)

    try {
      const resultat = await creerDemandeReinitialisation(
        utilisateur.id,
        anneeReinitialisation.trim(),
        motDePasseDoyen,
        phraseSecurite.trim()
      )

      setDemandeReinitialisation(resultat)
      setMessage(resultat.message)
    } catch (error) {
      setErreur(error.message)
    } finally {
      setReinitialisationEnCours(false)
    }
  }

  const executerReinitialisation = async () => {
    setErreur('')
    setMessage('')

    if (!demandeReinitialisation) {
      setErreur('Aucune demande de réinitialisation créée.')
      return
    }

    if (codeConfirmation.trim() === '') {
      setErreur('Veuillez saisir le code de confirmation.')
      return
    }

    const confirmation = window.confirm(
      'Attention : cette action supprimera les étudiants et toutes leurs données liées pour cette année. Confirmez-vous ?'
    )

    if (!confirmation) {
      return
    }

    setReinitialisationEnCours(true)

    try {
      const resultat = await confirmerReinitialisation(
        utilisateur.id,
        demandeReinitialisation.reinitialisation_id,
        codeConfirmation.trim()
      )

      setMessage(resultat.message)
      setResumeReinitialisation(null)
      setDemandeReinitialisation(null)
      setMotDePasseDoyen('')
      setPhraseSecurite('')
      setCodeConfirmation('')

      await chargerTableauDoyen()
    } catch (error) {
      setErreur(error.message)
    } finally {
      setReinitialisationEnCours(false)
    }
  }


  const importerListeOfficielle = async () => {
    setErreur('')
    setMessage('')
    setMessageImportListe('')

    if (texteListeOfficielle.trim() === '') {
      setErreur(
        'Collez d’abord la liste officielle sous la forme : ID;Nom;Prénom;Email Outlook.'
      )
      return
    }

    setImportListeEnCours(true)

    try {
      const resultat = await importerListeOfficiellePromotion(
        texteListeOfficielle,
        remplacerListeOfficielle
      )

      setMessageImportListe(resultat.message)
      setTexteListeOfficielle('')
      setRemplacerListeOfficielle(false)
      await chargerTableauDoyen()
    } catch (error) {
      setErreur(error.message)
    } finally {
      setImportListeEnCours(false)
    }
  }

  const chargerArchivesAdministratives = async () => {
    setErreurArchives('')
    setChargementArchives(true)

    try {
      const resultat = await getArchivesAdministratives()

      setArchivesAdministratives({
        fiches: resultat.fiches || [],
        exports: resultat.exports || []
      })
    } catch (error) {
      setErreurArchives(error.message)
    } finally {
      setChargementArchives(false)
    }
  }

  const telechargerExportSuiviPromotion = () => {
    window.open(
      getUrlExportSuiviPromotionExcel(),
      '_blank',
      'noopener,noreferrer'
    )

    setTimeout(() => {
      chargerArchivesAdministratives()
    }, 1500)
  }

  const ouvrirDiscussionFiche = async () => {
    if (!ficheSelectionnee || !ficheSelectionnee.fiche_id) {
      setErreur('Aucune fiche sélectionnée.')
      return
    }

    setErreur('')
    setMessage('')
    setErreurDiscussion('')
    setChargementDiscussion(true)

    try {
      const discussion = await getDiscussionFiche(ficheSelectionnee.fiche_id)

      setDiscussionDoyen(discussion)
      setFenetreDiscussionOuverte(true)
    } catch (error) {
      setErreurDiscussion(error.message)
    } finally {
      setChargementDiscussion(false)
    }
  }

  const fermerDiscussionFiche = () => {
    if (chargementDiscussion) {
      return
    }

    setFenetreDiscussionOuverte(false)
  }

  const chargerHistoriqueEtudiant = async (ficheId) => {
    setErreurHistorique('')
    setChargementHistorique(true)

    try {
      const resultat = await getHistoriqueEtudiantFiche(ficheId)

      setHistoriqueEtudiant(resultat.historique || [])
    } catch (error) {
      setErreurHistorique(error.message)
      setHistoriqueEtudiant([])
    } finally {
      setChargementHistorique(false)
    }
  }

  const formaterDateHistorique = (date) => {
    if (!date) {
      return 'Date non disponible'
    }

    return date
  }

  const getHistoriqueBadgeClass = (statut) => {
    if (statut === 'success') {
      return 'timeline-badge timeline-success'
    }

    if (statut === 'warning') {
      return 'timeline-badge timeline-warning'
    }

    if (statut === 'danger') {
      return 'timeline-badge timeline-danger'
    }

    return 'timeline-badge timeline-info'
  }

  const getHistoriqueBadgeTexte = (statut) => {
    if (statut === 'success') {
      return 'Validé'
    }

    if (statut === 'warning') {
      return 'Attention'
    }

    if (statut === 'danger') {
      return 'Erreur'
    }

    return 'Info'
  }

  const getMeilleurScore = () => {
    if (!ficheSelectionnee || !ficheSelectionnee.scores) {
      return null
    }

    if (ficheSelectionnee.scores.length === 0) {
      return null
    }

    return ficheSelectionnee.scores[0]
  }

  const formatterStatutChoix = (statut) => {
    if (!statut) {
      return 'Choix non effectué'
    }

    if (statut === 'fiche_generee') {
      return 'Fiche générée'
    }

    if (statut === 'en_attente_confirmation_doyen') {
      return 'En attente de confirmation du doyen'
    }

    if (statut === 'choix_confirme') {
      return 'Choix confirmé'
    }

    if (statut === 'document_refuse') {
      return 'Document refusé'
    }

    return statut
  }

  const getBadgeStatutChoixClass = (statut) => {
    if (statut === 'choix_confirme') {
      return 'status-badge status-valid'
    }

    if (statut === 'document_refuse') {
      return 'status-badge status-danger'
    }

    if (statut === 'en_attente_confirmation_doyen') {
      return 'status-badge status-warning'
    }

    return 'status-badge status-pending'
  }

  const formaterRoleDiscussion = (role) => {
    if (role === 'assistant') {
      return 'Chatbot'
    }

    if (role === 'etudiant' || role === 'user') {
      return 'Étudiant'
    }

    if (role === 'bot') {
      return 'Chatbot'
    }

    return role || 'Message'
  }

  const getDateMessageDiscussion = (messageDiscussion) => {
    return (
      messageDiscussion.date_creation ||
      messageDiscussion.date_message ||
      messageDiscussion.created_at ||
      messageDiscussion.date_envoi ||
      ''
    )
  }

  const getMessagesDiscussion = () => {
    if (!discussionDoyen || !Array.isArray(discussionDoyen.messages)) {
      return []
    }

    return discussionDoyen.messages
  }



  const getIndicateursTableauBord = () => {
    return tableauBordAvance?.indicateurs || {}
  }

  const getRepartitionTableauBord = () => {
    return tableauBordAvance?.repartition_filieres || []
  }

  const getDocumentsRecentsTableauBord = () => {
    return tableauBordAvance?.documents_recents || []
  }

  const formaterNombreDashboard = (valeur) => {
    return Number(valeur || 0)
  }


  const getResumeSuiviPromotion = () => {
    return suiviPromotion?.resume || {}
  }

  const getRepartitionSuiviPromotion = () => {
    return suiviPromotion?.repartition_filieres || []
  }

  const getEtudiantsASuivre = () => {
    return suiviPromotion?.etudiants_a_suivre || []
  }

  const getStatutGlobalTexte = (statut) => {
    if (statut === 'dossier_complet') {
      return 'Dossier complet'
    }

    if (statut === 'non_inscrit') {
      return 'Non inscrit'
    }

    if (statut === 'test_non_fait') {
      return 'Test non fait'
    }

    if (statut === 'choix_non_fait') {
      return 'Choix non fait'
    }

    if (statut === 'document_non_depose') {
      return 'Document non déposé'
    }

    if (statut === 'document_en_attente') {
      return 'Document en attente'
    }

    if (statut === 'document_refuse') {
      return 'Document refusé'
    }

    return statut || 'Non défini'
  }

  const getStatutGlobalClass = (statut) => {
    if (statut === 'dossier_complet') {
      return 'status-badge status-valid'
    }

    if (statut === 'document_en_attente') {
      return 'status-badge status-warning'
    }

    if (statut === 'document_refuse' || statut === 'non_inscrit') {
      return 'status-badge status-danger'
    }

    return 'status-badge status-pending'
  }


  const meilleurScore = getMeilleurScore()

  return (
    <div className="dashboard-container">
      {fenetreDiscussionOuverte && discussionDoyen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.55)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '900px',
              maxHeight: '90vh',
              overflowY: 'auto',
              backgroundColor: '#ffffff',
              borderRadius: '22px',
              padding: '28px',
              boxShadow: '0 25px 70px rgba(15, 23, 42, 0.35)'
            }}
          >
            <div className="section-title-row">
              <div>
                <h2>Discussion chatbot de l’étudiant</h2>

                <p>
                  Visualisation complète de la discussion utilisée pour la
                  recommandation pédagogique.
                </p>
              </div>

              <button
                className="secondary-button small-button"
                onClick={fermerDiscussionFiche}
              >
                Fermer
              </button>
            </div>

            {discussionDoyen.fiche && (
              <div className="profile-summary-card">
                <div>
                  <span className="info-label">Étudiant</span>
                  <strong>
                    {discussionDoyen.fiche.prenom}{' '}
                    {discussionDoyen.fiche.nom}
                  </strong>
                </div>

                <div>
                  <span className="info-label">ID universitaire</span>
                  <strong>{discussionDoyen.fiche.id_universitaire}</strong>
                </div>

                <div>
                  <span className="info-label">Spécialité proposée</span>
                  <strong>
                    {discussionDoyen.fiche.specialite_recommandee}
                  </strong>
                </div>
              </div>
            )}

            <div className="discussion-actions">
              <a
                className="discussion-download-button"
                href={getUrlDiscussionFichePdf(
                  discussionDoyen.fiche?.fiche_id || ficheSelectionnee.fiche_id
                )}
                target="_blank"
                rel="noreferrer"
              >
                Télécharger en PDF
              </a>

              <a
                className="discussion-secondary-button"
                href={getUrlDiscussionFicheTxt(
                  discussionDoyen.fiche?.fiche_id || ficheSelectionnee.fiche_id
                )}
                target="_blank"
                rel="noreferrer"
              >
                Télécharger en TXT
              </a>
            </div>

            {discussionDoyen.session_chat && (
              <div className="document-status-box">
                <h4>Session chatbot</h4>

                <p>
                  <strong>Session ID :</strong>{' '}
                  {discussionDoyen.session_chat.id}
                </p>

                <p>
                  <strong>Statut :</strong>{' '}
                  {discussionDoyen.session_chat.statut}
                </p>

                <p>
                  <strong>Raison du droit :</strong>{' '}
                  {discussionDoyen.session_chat.raison_droit || 'Non renseignée'}
                </p>
              </div>
            )}

            <h3>Discussion complète</h3>

            {getMessagesDiscussion().length === 0 ? (
              <p className="info-message">
                Aucun message n’est disponible pour cette discussion.
              </p>
            ) : (
              <div className="chat-messages">
                {getMessagesDiscussion().map((messageDiscussion, index) => {
                  const role = messageDiscussion.role_message
                  const estChatbot =
                    role === 'assistant' || role === 'bot'

                  return (
                    <div
                      key={messageDiscussion.id || index}
                      className={
                        estChatbot
                          ? 'message-row bot-row'
                          : 'message-row user-row'
                      }
                    >
                      <div
                        className={
                          estChatbot
                            ? 'chat-bubble bot-bubble'
                            : 'chat-bubble user-bubble'
                        }
                      >
                        <strong>
                          {formaterRoleDiscussion(role)}
                        </strong>

                        {getDateMessageDiscussion(messageDiscussion) && (
                          <p style={{ fontSize: '0.78rem', opacity: 0.75 }}>
                            {getDateMessageDiscussion(messageDiscussion)}
                          </p>
                        )}

                        <p>{messageDiscussion.contenu}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {documentSelectionne && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.55)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '620px',
              maxHeight: '90vh',
              overflowY: 'auto',
              backgroundColor: '#ffffff',
              borderRadius: '22px',
              padding: '28px',
              boxShadow: '0 25px 70px rgba(15, 23, 42, 0.35)'
            }}
          >
            <div className="section-title-row">
              <div>
                <h2>Traiter le document</h2>

                <p>
                  Décision administrative concernant la fiche d’engagement signée.
                </p>
              </div>

              <button
                className="secondary-button small-button"
                onClick={fermerFenetreDecision}
                disabled={decisionEnCours}
              >
                Fermer
              </button>
            </div>

            <div className="profile-summary-card">
              <div>
                <span className="info-label">Étudiant</span>

                <strong>
                  {documentSelectionne.prenom} {documentSelectionne.nom}
                </strong>
              </div>

              <div>
                <span className="info-label">ID universitaire</span>
                <strong>{documentSelectionne.id_universitaire}</strong>
              </div>
            </div>

            <div className="profile-summary-card">
              <div>
                <span className="info-label">Filière choisie</span>
                <strong>{documentSelectionne.filiere_choisie}</strong>
              </div>

              <div>
                <span className="info-label">Document</span>
                <strong>{documentSelectionne.nom_fichier_original}</strong>
              </div>
            </div>

            {documentSelectionne.verification_auto_message && (
              <p className="info-message">
                {documentSelectionne.verification_auto_message}
              </p>
            )}

            <button
              className="secondary-button"
              onClick={() => ouvrirDocument(documentSelectionne.document_id)}
              disabled={decisionEnCours}
            >
              Visualiser le document
            </button>

            <label>Remarque du doyen</label>

            <textarea
              className="remark-textarea"
              value={remarqueDocument}
              onChange={(event) => setRemarqueDocument(event.target.value)}
              placeholder="Exemple : document lisible et signé / signature manquante / document illisible..."
            />

            <div className="validation-buttons">
              <button
                onClick={() => envoyerDecisionDocument('confirmer')}
                disabled={decisionEnCours}
              >
                {decisionEnCours
                  ? 'Traitement...'
                  : 'Confirmer le document'}
              </button>

              <button
                className="danger-button"
                onClick={() => envoyerDecisionDocument('refuser')}
                disabled={decisionEnCours}
              >
                Refuser le document
              </button>

              <button
                className="secondary-button"
                onClick={fermerFenetreDecision}
                disabled={decisionEnCours}
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}


      {fenetreStatistiquesOuverte && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.55)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '1050px',
              maxHeight: '90vh',
              overflowY: 'auto',
              backgroundColor: '#ffffff',
              borderRadius: '22px',
              padding: '28px',
              boxShadow: '0 25px 70px rgba(15, 23, 42, 0.35)'
            }}
          >
            <div className="section-title-row">
              <div>
                <h2>Statistiques de la promotion</h2>

                <p>
                  Cette page regroupe les indicateurs détaillés. Elle ne prend
                  aucune décision d’organisation pédagogique.
                </p>
              </div>

              <button
                className="secondary-button small-button"
                onClick={() => setFenetreStatistiquesOuverte(false)}
              >
                Fermer
              </button>
            </div>

            {tableauBordAvance && (
              <div className="admin-panel-card dashboard-advanced-card">
                <div className="section-title-row">
                  <div>
                    <h3>Tableau de bord avancé</h3>
                    <p>Vue globale de l’activité pour l’année universitaire active.</p>
                  </div>

                  <span className="status-badge status-pending">
                    {tableauBordAvance.annee_universitaire}
                  </span>
                </div>

                <div className="dashboard-metrics-grid">
                  <div className="dashboard-metric-card">
                    <span>Étudiants inscrits</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().total_etudiants)}</strong>
                  </div>

                  <div className="dashboard-metric-card">
                    <span>Tests passés</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().total_tests)}</strong>
                    <small>{formaterNombreDashboard(getIndicateursTableauBord().taux_tests)}% des étudiants</small>
                  </div>

                  <div className="dashboard-metric-card">
                    <span>Fiches générées</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().total_fiches)}</strong>
                  </div>

                  <div className="dashboard-metric-card">
                    <span>Choix finaux</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().total_choix_final)}</strong>
                    <small>{formaterNombreDashboard(getIndicateursTableauBord().taux_choix)}% des fiches</small>
                  </div>

                  <div className="dashboard-metric-card metric-warning">
                    <span>Documents en attente</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().documents_en_attente)}</strong>
                  </div>

                  <div className="dashboard-metric-card metric-success">
                    <span>Documents confirmés</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().documents_confirmes)}</strong>
                  </div>

                  <div className="dashboard-metric-card metric-danger">
                    <span>Documents refusés</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().documents_refuses)}</strong>
                  </div>

                  <div className="dashboard-metric-card">
                    <span>Notifications doyen non lues</span>
                    <strong>{formaterNombreDashboard(getIndicateursTableauBord().notifications_non_lues)}</strong>
                  </div>
                </div>

                <h3>Répartition des choix par filière</h3>

                <div className="dashboard-filiere-grid">
                  {getRepartitionTableauBord().map((filiere) => (
                    <div className="dashboard-filiere-card" key={filiere.specialite_id}>
                      <div className="dashboard-filiere-header">
                        <h4>{filiere.specialite}</h4>

                        <span className="status-badge status-pending">
                          {filiere.total_choix || 0} choix
                        </span>
                      </div>

                      <div className="dashboard-filiere-stats">
                        <p><strong>Choix enregistrés :</strong> {filiere.total_choix}</p>
                        <p><strong>Documents confirmés :</strong> {filiere.total_confirmes}</p>
                        <p><strong>Documents en attente :</strong> {filiere.total_en_attente}</p>
                        <p><strong>Documents refusés :</strong> {filiere.total_refuses}</p>
                        <p><strong>Fiches d’engagement générées :</strong> {filiere.fiches_engagement_generees || 0}</p>
                        <p><strong>Recommandations :</strong> {filiere.total_recommandations}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <h3>Derniers documents déposés</h3>

                {getDocumentsRecentsTableauBord().length === 0 ? (
                  <p className="info-message">
                    Aucun document récent pour cette année universitaire.
                  </p>
                ) : (
                  <div className="recent-documents-list">
                    {getDocumentsRecentsTableauBord().map((document) => (
                      <div className="recent-document-row" key={document.document_id}>
                        <div>
                          <strong>{document.prenom} {document.nom}</strong>
                          <p>{document.id_universitaire} — {document.filiere_choisie}</p>
                          <small>{document.nom_fichier_original}</small>
                        </div>

                        <span className="status-badge status-pending">
                          {document.statut_document}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {suiviPromotion && (
              <div className="admin-panel-card promotion-followup-card">
                <h3>Suivi de promotion</h3>

                <p className="info-message">
                  {suiviPromotion.message}
                </p>

                <div className="promotion-summary-grid">
                  <div className="promotion-summary-card">
                    <span>Total référence</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_reference)}</strong>
                  </div>

                  <div className="promotion-summary-card">
                    <span>Inscrits plateforme</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_inscrits)}</strong>
                  </div>

                  <div className="promotion-summary-card metric-danger">
                    <span>Non inscrits</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_non_inscrits)}</strong>
                  </div>

                  <div className="promotion-summary-card">
                    <span>Tests faits</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_tests_faits)}</strong>
                  </div>

                  <div className="promotion-summary-card metric-warning">
                    <span>Tests non faits</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_tests_non_faits)}</strong>
                  </div>

                  <div className="promotion-summary-card">
                    <span>Choix faits</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_choix_faits)}</strong>
                  </div>

                  <div className="promotion-summary-card metric-warning">
                    <span>Documents non déposés</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_documents_non_deposes)}</strong>
                  </div>

                  <div className="promotion-summary-card metric-success">
                    <span>Documents confirmés</span>
                    <strong>{formaterNombreDashboard(getResumeSuiviPromotion().total_documents_confirmes)}</strong>
                  </div>
                </div>

                <h3>Listes par filière choisie</h3>

                {getRepartitionSuiviPromotion().length === 0 ? (
                  <p className="info-message">
                    Aucun choix final enregistré pour le moment.
                  </p>
                ) : (
                  <div className="promotion-filiere-grid">
                    {getRepartitionSuiviPromotion().map((filiere) => (
                      <div className="promotion-filiere-card" key={filiere.filiere}>
                        <h4>{filiere.filiere}</h4>

                        <p><strong>Choix enregistrés :</strong> {filiere.total_choix}</p>
                        <p><strong>Documents déposés :</strong> {filiere.documents_deposes}</p>
                        <p><strong>Confirmés :</strong> {filiere.documents_confirmes}</p>
                        <p><strong>En attente :</strong> {filiere.documents_en_attente}</p>
                        <p><strong>Refusés :</strong> {filiere.documents_refuses}</p>
                      </div>
                    ))}
                  </div>
                )}

                <h3>Étudiants à suivre</h3>

                {getEtudiantsASuivre().length === 0 ? (
                  <p className="info-message">
                    Aucun étudiant incomplet dans la liste actuelle.
                  </p>
                ) : (
                  <div className="promotion-follow-table-wrapper">
                    <table className="promotion-follow-table">
                      <thead>
                        <tr>
                          <th>Étudiant</th>
                          <th>ID</th>
                          <th>Email Outlook</th>
                          <th>Filière</th>
                          <th>Statut</th>
                          <th>Action attendue</th>
                        </tr>
                      </thead>

                      <tbody>
                        {getEtudiantsASuivre().map((etudiant) => (
                          <tr key={`${etudiant.id_universitaire}-${etudiant.statut_global}`}>
                            <td>{etudiant.prenom} {etudiant.nom}</td>
                            <td>{etudiant.id_universitaire}</td>
                            <td>{etudiant.email_outlook || etudiant.email_plateforme}</td>
                            <td>{etudiant.filiere_choisie}</td>
                            <td>
                              <span className={getStatutGlobalClass(etudiant.statut_global)}>
                                {getStatutGlobalTexte(etudiant.statut_global)}
                              </span>
                            </td>
                            <td>{etudiant.action_attendue}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="dashboard-card large-card">
        <div className="interface-logo-header">
          <img
            src="/logos/LOGO-UEMF-HD.png"
            alt="Logo Université Euromed de Fès"
            className="interface-logo interface-logo-uemf"
          />
          <img
            src="/logos/logo-EIDIA.jpeg"
            alt="Logo EIDIA"
            className="interface-logo interface-logo-eidia"
          />
        </div>

        <div className="page-header">
          <div>
            <h1>Espace doyen</h1>

            <p>
              Bienvenue, <strong>{utilisateur.identifiant}</strong>.
            </p>
          </div>

          <button className="secondary-button small-button" onClick={onLogout}>
            Se déconnecter
          </button>
        </div>

        {anneeUniversitaireActive && (
          <div className="admin-panel-card academic-year-card">
            <div className="section-title-row">
              <div>
                <h2>Année universitaire active</h2>

                <p>
                  Les inscriptions, choix finaux, documents et statistiques sont
                  rattachés automatiquement à cette année universitaire.
                </p>
              </div>

              <span className="status-badge status-valid">
                {anneeUniversitaireActive.code}
              </span>
            </div>

            <div className="profile-summary-card">
              <div>
                <span className="info-label">Début</span>
                <strong>{anneeUniversitaireActive.date_debut}</strong>
              </div>

              <div>
                <span className="info-label">Fin</span>
                <strong>{anneeUniversitaireActive.date_fin}</strong>
              </div>

              <div>
                <span className="info-label">Statut</span>
                <strong>Active</strong>
              </div>
            </div>
          </div>
        )}

        <div className="admin-panel-card">
          <h2>Recherche d’un étudiant</h2>

          <p>
            Vous pouvez rechercher un étudiant par identifiant universitaire ou
            par nom complet.
          </p>

          <form onSubmit={rechercherFiche} className="search-form">
            <label>ID universitaire ou nom complet</label>

            <div className="search-row">
              <input
                type="text"
                value={recherche}
                onChange={(event) => setRecherche(event.target.value)}
                placeholder="Exemple : 1234567 ou Adam El Amrani"
              />

              <button type="submit" disabled={chargement}>
                {chargement ? 'Recherche...' : 'Rechercher'}
              </button>
            </div>
          </form>
        </div>

        {erreur && <p className="login-error">{erreur}</p>}
        {erreurDiscussion && <p className="login-error">{erreurDiscussion}</p>}
        {message && <p className="success-message">{message}</p>}

        {fiches.length > 0 && (
          <div className="result-count-card">
            <strong>{fiches.length}</strong>

            <span>
              fiche{fiches.length > 1 ? 's' : ''} trouvée
              {fiches.length > 1 ? 's' : ''}
            </span>
          </div>
        )}

        {fiches.length > 1 && (
          <div className="fiche-selector">
            <label>Choisir une fiche</label>

            <select
              value={ficheSelectionnee?.fiche_id || ''}
              onChange={(event) => changerFiche(event.target.value)}
            >
              {fiches.map((fiche) => (
                <option key={fiche.fiche_id} value={fiche.fiche_id}>
                  Fiche {fiche.fiche_id} - {fiche.specialite_recommandee}
                </option>
              ))}
            </select>
          </div>
        )}

        {ficheSelectionnee && (
          <div className="fiche-block">
            <div className="section-title-row">
              <div>
                <h2>Dossier étudiant</h2>

                <p>
                  Fiche numéro <strong>{ficheSelectionnee.fiche_id}</strong>
                </p>
              </div>

              <span className={getBadgeStatutChoixClass(ficheSelectionnee.statut_choix)}>
                {formatterStatutChoix(ficheSelectionnee.statut_choix)}
              </span>
            </div>

            <div className="profile-summary-card">
              <div>
                <span className="info-label">Étudiant</span>

                <strong>
                  {ficheSelectionnee.prenom} {ficheSelectionnee.nom}
                </strong>
              </div>

              <div>
                <span className="info-label">ID universitaire</span>
                <strong>{ficheSelectionnee.id_universitaire}</strong>
              </div>

              <div>
                <span className="info-label">Email</span>
                <strong>{ficheSelectionnee.email || 'Non renseigné'}</strong>
              </div>
            </div>

            <div className="profile-summary-card">
              <div>
                <span className="info-label">Recommandation système</span>
                <strong>{ficheSelectionnee.specialite_recommandee}</strong>
              </div>

              <div>
                <span className="info-label">Choix final étudiant</span>

                <strong>
                  {ficheSelectionnee.choix_final_etudiant || 'Non encore choisi'}
                </strong>
              </div>

              <div>
                <span className="info-label">Document signé</span>

                <strong>
                  {ficheSelectionnee.document_id ? 'Fourni' : 'Non fourni'}
                </strong>
              </div>
            </div>

            {ficheSelectionnee.document_id && (
              <div className="document-status-card">
                <h3>Document d’engagement</h3>

                <p>
                  <strong>Nom du fichier :</strong>{' '}
                  {ficheSelectionnee.document_nom}
                </p>

                <p>
                  <strong>Statut du document :</strong>{' '}
                  {formatterStatutChoix(ficheSelectionnee.statut_choix)}
                </p>

                {ficheSelectionnee.verification_auto_message && (
                  <p>
                    <strong>Vérification automatique :</strong>{' '}
                    {ficheSelectionnee.verification_auto_message}
                  </p>
                )}

                {ficheSelectionnee.remarque_document && (
                  <p>
                    <strong>Remarque du doyen :</strong>{' '}
                    {ficheSelectionnee.remarque_document}
                  </p>
                )}

                <button
                  className="secondary-button"
                  onClick={() => ouvrirDocument(ficheSelectionnee.document_id)}
                >
                  Visualiser le document
                </button>
              </div>
            )}

            {!ficheSelectionnee.document_id && (
              <p className="info-message">
                L’étudiant n’a pas encore déposé la fiche signée ou scannée.
              </p>
            )}

            <div className="student-history-card">
              <div className="section-title-row">
                <div>
                  <h3>Historique étudiant</h3>

                  <p>
                    Chronologie complète du parcours de l’étudiant dans la
                    plateforme.
                  </p>
                </div>

                <button
                  className="secondary-button small-button"
                  onClick={() => chargerHistoriqueEtudiant(ficheSelectionnee.fiche_id)}
                  disabled={chargementHistorique}
                >
                  {chargementHistorique ? 'Chargement...' : 'Actualiser'}
                </button>
              </div>

              {chargementHistorique && (
                <p className="info-message">
                  Chargement de l’historique étudiant...
                </p>
              )}

              {erreurHistorique && (
                <p className="login-error">
                  {erreurHistorique}
                </p>
              )}

              {!chargementHistorique && historiqueEtudiant.length === 0 && !erreurHistorique && (
                <p className="info-message">
                  Aucun historique détaillé n’est disponible pour cette fiche.
                </p>
              )}

              {historiqueEtudiant.length > 0 && (
                <div className="timeline-list">
                  {historiqueEtudiant.map((evenement) => (
                    <div className="timeline-item" key={`${evenement.ordre}-${evenement.type}`}>
                      <div className="timeline-marker">
                        <span>{evenement.ordre}</span>
                      </div>

                      <div className="timeline-content">
                        <div className="timeline-header">
                          <h4>{evenement.titre}</h4>

                          <span className={getHistoriqueBadgeClass(evenement.statut)}>
                            {getHistoriqueBadgeTexte(evenement.statut)}
                          </span>
                        </div>

                        <p>{evenement.description}</p>

                        <small>
                          {formaterDateHistorique(evenement.date)}
                        </small>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {meilleurScore && (
              <div className="result-highlight-card">
                <span className="info-label">Résultat principal proposé</span>

                <h2>{meilleurScore.specialite}</h2>

                <p>
                  Pourcentage obtenu :{' '}
                  <strong>{meilleurScore.pourcentage}%</strong>
                </p>
              </div>
            )}

            <h3>Scores par spécialité</h3>

            <div className="scores-list">
              {ficheSelectionnee.scores.map((score) => (
                <div className="score-card" key={score.specialite}>
                  <div className="score-card-header">
                    <span>{score.specialite}</span>
                    <strong>{score.pourcentage}%</strong>
                  </div>

                  <div className="score-progress">
                    <div
                      className="score-progress-fill"
                      style={{ width: `${score.pourcentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <h3>Résumé du profil</h3>

            <pre className="resume-box">
              {ficheSelectionnee.resume_profil}
            </pre>

            <div className="document-workflow-card">
              <h3>Trace de discussion chatbot</h3>

              <p>
                Le doyen peut visualiser directement la discussion complète de
                l’étudiant avec le chatbot. Le téléchargement PDF ou TXT reste
                disponible comme option d’archivage.
              </p>

              <div className="discussion-actions">
                <button
                  className="discussion-primary-button"
                  onClick={ouvrirDiscussionFiche}
                  disabled={chargementDiscussion}
                >
                  {chargementDiscussion
                    ? 'Chargement de la discussion...'
                    : 'Visualiser la discussion'}
                </button>

                <a
                  className="discussion-download-button"
                  href={getUrlDiscussionFichePdf(ficheSelectionnee.fiche_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Télécharger PDF
                </a>

                <a
                  className="discussion-secondary-button"
                  href={getUrlDiscussionFicheTxt(ficheSelectionnee.fiche_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Télécharger TXT
                </a>
              </div>
            </div>
          </div>
        )}


        <div className="admin-panel-card administrative-archives-card">
          <div className="section-title-row">
            <div>
              <h2>Archives administratives</h2>

              <p>
                Les documents signés validés et les exports Excel sont conservés
                sur le serveur du projet. Le doyen peut les consulter ou les
                télécharger depuis cette interface, même après la réinitialisation
                annuelle.
              </p>
            </div>

            <button
              className="secondary-button small-button"
              onClick={chargerArchivesAdministratives}
              disabled={chargementArchives}
            >
              {chargementArchives ? 'Actualisation...' : 'Actualiser archives'}
            </button>
          </div>

          {erreurArchives && (
            <p className="login-error">{erreurArchives}</p>
          )}

          <h3>Fiches d’engagement validées</h3>

          {archivesAdministratives.fiches.length === 0 ? (
            <p className="info-message">
              Aucune fiche d’engagement validée archivée pour le moment.
            </p>
          ) : (
            <div className="promotion-follow-table-wrapper">
              <table className="promotion-follow-table">
                <thead>
                  <tr>
                    <th>Matricule</th>
                    <th>Étudiant</th>
                    <th>Filière</th>
                    <th>Année</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {archivesAdministratives.fiches.map((archive) => (
                    <tr key={`fiche-${archive.id}`}>
                      <td>{archive.id_universitaire}</td>
                      <td>{archive.prenom} {archive.nom}</td>
                      <td>{archive.filiere_choisie}</td>
                      <td>{archive.annee_universitaire}</td>
                      <td>
                        <button
                          className="secondary-button small-button"
                          onClick={() => window.open(
                            getUrlArchiveFicheVisualisation(archive.id),
                            '_blank',
                            'noopener,noreferrer'
                          )}
                        >
                          Visualiser
                        </button>

                        <button
                          className="small-button"
                          onClick={() => window.open(
                            getUrlArchiveFicheTelechargement(archive.id),
                            '_blank',
                            'noopener,noreferrer'
                          )}
                        >
                          Télécharger
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h3>Exports Excel archivés</h3>

          {archivesAdministratives.exports.length === 0 ? (
            <p className="info-message">
              Aucun export Excel archivé pour le moment.
            </p>
          ) : (
            <div className="documents-list">
              {archivesAdministratives.exports.map((archive) => (
                <div className="document-card" key={`export-${archive.id}`}>
                  <div>
                    <h3>{archive.nom_fichier}</h3>
                    <p><strong>Année universitaire :</strong> {archive.annee_universitaire}</p>
                    <p><strong>Date de génération :</strong> {archive.date_generation}</p>
                  </div>

                  <div className="document-actions">
                    <button
                      className="small-button"
                      onClick={() => window.open(
                        getUrlArchiveExportExcelTelechargement(archive.id),
                        '_blank',
                        'noopener,noreferrer'
                      )}
                    >
                      Télécharger
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="admin-panel-card">
          <div className="section-title-row">
            <div>
              <h2>Documents à confirmer</h2>

              <p>
                Documents signés déposés par les étudiants et en attente de
                confirmation administrative.
              </p>
            </div>

            <div className="discussion-actions" style={{ margin: 0 }}>
              <span className="status-badge status-pending">
                {documentsAConfirmer.length} en attente
              </span>

              <button
                className="secondary-button small-button"
                onClick={() => chargerTableauDoyen(true)}
                disabled={chargementTableau}
              >
                {chargementTableau ? 'Actualisation...' : 'Actualiser'}
              </button>

              <button
                className="small-button"
                onClick={parcourirDocumentsAConfirmer}
                disabled={chargementTableau}
              >
                Parcourir
              </button>
            </div>
          </div>

          {derniereActualisation && (
            <p className="info-message">
              Dernière actualisation : {derniereActualisation}
            </p>
          )}

         {etatNotificationEmail && (
  <div
    className={
      etatNotificationEmail.email_configure
        ? 'email-status-card email-status-ok'
        : 'email-status-card email-status-warning'
    }
  >
    <strong>Notifications email</strong>

    <p>{etatNotificationEmail.message}</p>

    {!etatNotificationEmail.email_configure && (
      <small>
        Le dépôt des documents reste fonctionnel. La configuration SMTP
        sera faite à la fin des améliorations.
      </small>
    )}
  </div>
)}

          {!afficherListeDocumentsAConfirmer && (
            <p className="info-message">
              Cliquez sur “Parcourir” pour afficher les documents en attente directement dans cette rubrique.
            </p>
          )}

          {afficherListeDocumentsAConfirmer && (
            <div id="documents-a-confirmer-liste">
              {chargementTableau ? (
                <p className="info-message">
                  Chargement des documents à confirmer...
                </p>
              ) : documentsAConfirmer.length === 0 ? (
                <p className="info-message">
                  Aucun document n’est actuellement en attente de confirmation.
                </p>
              ) : (
                <div className="documents-list">
                  {documentsAConfirmer.map((document) => (
                    <div className="document-card" key={document.document_id}>
                      <div>
                        <h3>
                          {document.prenom} {document.nom}
                        </h3>

                        <p>
                          <strong>ID universitaire :</strong>{' '}
                          {document.id_universitaire}
                        </p>

                        <p>
                          <strong>Filière choisie :</strong>{' '}
                          {document.filiere_choisie}
                        </p>

                        <p>
                          <strong>Document :</strong>{' '}
                          {document.nom_fichier_original}
                        </p>

                        {document.verification_auto_message && (
                          <p>
                            <strong>Vérification automatique :</strong>{' '}
                            {document.verification_auto_message}
                          </p>
                        )}
                      </div>

                      <div className="document-actions">
                        <button
                          className="secondary-button small-button"
                          onClick={() => ouvrirDocument(document.document_id)}
                        >
                          Visualiser
                        </button>

                        <button
                          className="small-button"
                          onClick={() => preparerDecisionDocument(document)}
                        >
                          Traiter
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {suiviPromotion && (
          <div className="admin-panel-card promotion-followup-card">
            <div className="section-title-row">
              <div>
                <h2>Liste officielle et export Excel</h2>

                <p>
                  Cette rubrique sert uniquement à importer la liste officielle
                  de la promotion et à générer le fichier Excel simple par filière.
                </p>
              </div>

              <div className="discussion-actions" style={{ margin: 0 }}>
                <button
                  className="secondary-button small-button"
                  onClick={() => setAfficherImportListe(!afficherImportListe)}
                >
                  {afficherImportListe ? 'Masquer l’import' : 'Importer la liste'}
                </button>

                <button
                  className="small-button"
                  onClick={telechargerExportSuiviPromotion}
                >
                  Télécharger Excel
                </button>
              </div>
            </div>

            <p className="info-message">
              L’export Excel contient uniquement le nom, le prénom, l’ID universitaire
              et l’email Outlook des étudiants, avec une feuille par filière.
            </p>

            {afficherImportListe && (
              <div className="official-import-card">
                <h3>Importer la liste officielle de la promotion</h3>

                <p>
                  Collez les données depuis Excel avec l’ordre suivant :
                  <strong> ID universitaire ; Nom ; Prénom ; Email Outlook</strong>.
                </p>

                <textarea
                  className="official-import-textarea"
                  value={texteListeOfficielle}
                  onChange={(event) => setTexteListeOfficielle(event.target.value)}
                  placeholder={
                    'ID;Nom;Prénom;Email Outlook\n' +
                    '1234567;EL AMRANI;Adam;adam.elamrani@eidia.ueuromed.org\n' +
                    '7654321;BENALI;Sara;sara.benali@eidia.ueuromed.org'
                  }
                />

                <label className="checkbox-line">
                  <input
                    type="checkbox"
                    checked={remplacerListeOfficielle}
                    onChange={(event) => setRemplacerListeOfficielle(event.target.checked)}
                  />
                  Remplacer l’ancienne liste officielle de cette année
                </label>

                <button
                  className="small-button"
                  onClick={importerListeOfficielle}
                  disabled={importListeEnCours}
                >
                  {importListeEnCours ? 'Import en cours...' : 'Importer la liste'}
                </button>

                {messageImportListe && (
                  <p className="success-message">{messageImportListe}</p>
                )}
              </div>
            )}
          </div>
        )}


        <div className="admin-panel-card statistics-entry-card">
          <div className="section-title-row">
            <div>
              <h2>Statistiques</h2>

              <p>
                Les indicateurs détaillés sont masqués par défaut pour garder
                l’espace doyen simple et centré sur le traitement administratif.
              </p>
            </div>

            <button
              className="small-button"
              onClick={() => setFenetreStatistiquesOuverte(true)}
            >
              Voir les statistiques
            </button>
          </div>
        </div>


        <div className="danger-zone-card">
          <h2>Réinitialisation annuelle sécurisée</h2>

          <p>
            Cette action permet de supprimer les étudiants et leurs données
            liées pour une année donnée. Les spécialités, questions
            et comptes doyen ne seront pas supprimés.
          </p>

          <label>Année universitaire / promotion</label>

          <div className="search-row">
            <input
              type="text"
              value={anneeReinitialisation}
              onChange={(event) => setAnneeReinitialisation(event.target.value)}
              placeholder="Exemple : 2026"
            />

            <button
              className="warning-button"
              onClick={chargerResumeReinitialisation}
              disabled={reinitialisationEnCours}
            >
              Charger le résumé
            </button>
          </div>

          {resumeReinitialisation && (
            <div className="reset-summary-card">
              <h3>Résumé des données concernées</h3>

              <p>
                <strong>Étudiants :</strong>{' '}
                {resumeReinitialisation.resume.total_etudiants}
              </p>

              <p>
                <strong>Tests :</strong>{' '}
                {resumeReinitialisation.resume.total_tests}
              </p>

              <p>
                <strong>Fiches intelligentes :</strong>{' '}
                {resumeReinitialisation.resume.total_fiches}
              </p>

              <p>
                <strong>Choix finaux :</strong>{' '}
                {resumeReinitialisation.resume.total_choix}
              </p>

              <p>
                <strong>Documents déposés :</strong>{' '}
                {resumeReinitialisation.resume.total_documents}
              </p>

              <h4>Phrase de sécurité obligatoire</h4>

              <pre className="security-phrase-box">
                {resumeReinitialisation.phrase_attendue}
              </pre>

              <label>Mot de passe du doyen</label>

              <input
                type="password"
                value={motDePasseDoyen}
                onChange={(event) => setMotDePasseDoyen(event.target.value)}
                placeholder="Mot de passe du doyen"
              />

              <label>Recopier la phrase de sécurité</label>

              <input
                type="text"
                value={phraseSecurite}
                onChange={(event) => setPhraseSecurite(event.target.value)}
                placeholder="Exemple : SUPPRIMER LES ETUDIANTS 2026"
              />

              <button
                className="danger-button"
                onClick={demanderReinitialisation}
                disabled={reinitialisationEnCours}
              >
                Générer le code de confirmation
              </button>
            </div>
          )}

          {demandeReinitialisation && (
            <div className="reset-summary-card">
              <h3>Code de confirmation</h3>

              <p>
                Pour la démonstration, le code généré est :
              </p>

              <pre className="security-phrase-box">
                {demandeReinitialisation.code_demo}
              </pre>

              <label>Saisir le code de confirmation</label>

              <input
                type="text"
                value={codeConfirmation}
                onChange={(event) => setCodeConfirmation(event.target.value)}
                placeholder="Code à 6 chiffres"
              />

              <button
                className="danger-button"
                onClick={executerReinitialisation}
                disabled={
                  reinitialisationEnCours ||
                  !demandeReinitialisation ||
                  codeConfirmation.trim() === ''
                }
              >
                {reinitialisationEnCours
                  ? 'Réinitialisation en cours...'
                  : 'Exécuter la réinitialisation annuelle'}
              </button>
            </div>
          )}
        </div>


















      </div>
    </div>
  )
}

export default DoyenPage