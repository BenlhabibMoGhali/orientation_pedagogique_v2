import { useEffect, useState } from 'react'
import {
  demarrerChatOrientation,
  envoyerMessageChat,
  enregistrerChoixFinal,
  getUrlFicheEngagement,
  deposerDocumentSigne,
  getEtatOrientationEtudiant,
  getDiscussionEtudiant,
  getUrlDiscussionEtudiantTxt,
  getUrlDiscussionEtudiantPdf
} from '../services/chatbotService'
import '../styles/LoginPage.css'

const EXTENSIONS_DOCUMENTS_AUTORISEES = ['pdf', 'jpg', 'jpeg', 'png']
const TAILLE_MAX_DOCUMENT_SIGNE = 5 * 1024 * 1024

function EtudiantPage({ utilisateur, onLogout }) {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [messageActuel, setMessageActuel] = useState('')
  const [questionCourante, setQuestionCourante] = useState(null)
  const [reponsesSelectionnees, setReponsesSelectionnees] = useState([])
  const [niveauxDomaines, setNiveauxDomaines] = useState({})
  const [hesitationReponse, setHesitationReponse] = useState('')
  const [specialitesHesitees, setSpecialitesHesitees] = useState([])
  const [chargement, setChargement] = useState(true)
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const [droitTest, setDroitTest] = useState(null)
  const [terminee, setTerminee] = useState(false)
  const [resultat, setResultat] = useState(null)
  const [fiche, setFiche] = useState(null)
  const [etatEtudiant, setEtatEtudiant] = useState(null)

  const [specialiteChoisie, setSpecialiteChoisie] = useState('')
  const [commentaireChoix, setCommentaireChoix] = useState('')
  const [choixFinal, setChoixFinal] = useState(null)
  const [choixEnCours, setChoixEnCours] = useState(false)
  const [messageChoixFinal, setMessageChoixFinal] = useState('')
  const [alternatives, setAlternatives] = useState([])

  const [documentSigne, setDocumentSigne] = useState(null)
  const [documentAdministratif, setDocumentAdministratif] = useState(null)
  const [uploadEnCours, setUploadEnCours] = useState(false)
  const [messageUpload, setMessageUpload] = useState('')
  const [messageDocumentSelectionne, setMessageDocumentSelectionne] = useState('')
  const [erreurDocument, setErreurDocument] = useState('')
  const [resultatDepotDocument, setResultatDepotDocument] = useState(null)

  const [discussionEtudiant, setDiscussionEtudiant] = useState(null)
  const [chargementDiscussion, setChargementDiscussion] = useState(false)
  const [fenetreDiscussionOuverte, setFenetreDiscussionOuverte] = useState(false)
  const [erreurDiscussion, setErreurDiscussion] = useState('')

  useEffect(() => {
    initialiserEspaceEtudiant()
  }, [])

  const ajouterMessage = (role, contenu) => {
    setMessages((anciensMessages) => [
      ...anciensMessages,
      {
        role: role,
        contenu: contenu
      }
    ])
  }

  const afficherTexteAvecGras = (texte) => {
    if (!texte) {
      return ''
    }

    const lignes = String(texte).split('\n')

    return lignes.map((ligne, ligneIndex) => {
      const morceaux = ligne.split(/(\*\*.*?\*\*)/g)

      return (
        <span key={ligneIndex}>
          {morceaux.map((morceau, index) => {
            if (morceau.startsWith('**') && morceau.endsWith('**')) {
              return (
                <strong key={index}>
                  {morceau.replaceAll('**', '')}
                </strong>
              )
            }

            return morceau
          })}

          {ligneIndex < lignes.length - 1 && <br />}
        </span>
      )
    })
  }

  const convertirEtatEnResultat = (etat) => {
    const pourcentages = {}

    if (etat && Array.isArray(etat.scores)) {
      etat.scores
        .slice()
        .sort((a, b) => Number(b.pourcentage) - Number(a.pourcentage))
        .forEach((score) => {
          pourcentages[score.specialite] = Number(score.pourcentage)
        })
    }

    return {
      specialite_recommandee: etat?.fiche?.specialite_recommandee || '',
      pourcentages: pourcentages
    }
  }

  const chargerEtatEtudiant = async (afficherChargement = false) => {
    if (afficherChargement) {
      setChargement(true)
    }

    try {
      const etat = await getEtatOrientationEtudiant(utilisateur.id)

      setEtatEtudiant(etat)

      if (etat.a_passe_test) {
        const resultatReconstruit = convertirEtatEnResultat(etat)

        setTerminee(true)
        setResultat(resultatReconstruit)
        setFiche(etat.fiche || null)
        setChoixFinal(etat.choix_final || null)
        setDocumentAdministratif(etat.document || null)

        if (etat.choix_final) {
          setSpecialiteChoisie(
            etat.choix_final.filiere_choisie ||
              etat.fiche?.specialite_recommandee ||
              ''
          )

          setCommentaireChoix(etat.choix_final.commentaire || '')
        } else if (etat.fiche?.specialite_recommandee) {
          setSpecialiteChoisie(etat.fiche.specialite_recommandee)
        }
      }

      return etat
    } catch (error) {
      setErreur(error.message)
      return null
    } finally {
      if (afficherChargement) {
        setChargement(false)
      }
    }
  }

  const initialiserEspaceEtudiant = async () => {
    setErreur('')
    setChargement(true)

    const etat = await chargerEtatEtudiant(false)

    if (!etat || !etat.a_passe_test) {
      await demarrerConversation()
    } else {
      setChargement(false)
    }
  }

  const demarrerConversation = async () => {
    setErreur('')
    setChargement(true)

    try {
      const resultatDemarrage = await demarrerChatOrientation(utilisateur.id)

      setDroitTest(resultatDemarrage.droit_test || null)

      if (!resultatDemarrage.success) {
        setChargement(false)
        return
      }

      setSessionId(resultatDemarrage.session_id)
      setQuestionCourante(resultatDemarrage.question || null)
      reinitialiserReponseQuestion(resultatDemarrage.question || null)

      setMessages([
        {
          role: 'assistant',
          contenu: resultatDemarrage.message_bot
        }
      ])
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }


  const reinitialiserReponseQuestion = () => {
    setReponsesSelectionnees([])
    setMessageActuel('')
    setHesitationReponse('')
    setSpecialitesHesitees([])
    setNiveauxDomaines({})
  }

  const getOptionTexte = (option) => {
    if (typeof option === 'string') {
      return option
    }

    return option?.texte || ''
  }

  const basculerOption = (optionTexte) => {
    if (!questionCourante) {
      return
    }

    const optionExclusive = questionCourante.option_exclusive

    setReponsesSelectionnees((valeursActuelles) => {
      if (questionCourante.type_question === 'choix_unique') {
        return valeursActuelles.includes(optionTexte) ? [] : [optionTexte]
      }

      if (optionExclusive && optionTexte === optionExclusive) {
        return valeursActuelles.includes(optionTexte) ? [] : [optionTexte]
      }

      let nouvellesValeurs = valeursActuelles.filter(
        (valeur) => valeur !== optionExclusive
      )

      if (nouvellesValeurs.includes(optionTexte)) {
        return nouvellesValeurs.filter((valeur) => valeur !== optionTexte)
      }

      return [...nouvellesValeurs, optionTexte]
    })
  }

  const basculerSpecialiteHesitee = (specialite) => {
    setSpecialitesHesitees((valeursActuelles) => {
      if (valeursActuelles.includes(specialite)) {
        return valeursActuelles.filter((valeur) => valeur !== specialite)
      }

      return [...valeursActuelles, specialite]
    })
  }

  const construireReponseQuestion = () => {
    if (!questionCourante) {
      return messageActuel.trim()
    }

    if (
      questionCourante.type_question === 'choix_multiple' ||
      questionCourante.type_question === 'choix_unique'
    ) {
      return `Réponses sélectionnées : ${reponsesSelectionnees.join(' ; ')}`
    }

    if (questionCourante.type_question === 'hesitation') {
      if (hesitationReponse === 'Non') {
        return 'Non'
      }

      return `Oui, spécialités hésitées : ${specialitesHesitees.join(' ; ')}`
    }

    return messageActuel.trim()
  }

  const reponseQuestionValide = () => {
    if (!questionCourante) {
      return messageActuel.trim() !== ''
    }

    if (
      questionCourante.type_question === 'choix_multiple' ||
      questionCourante.type_question === 'choix_unique'
    ) {
      return reponsesSelectionnees.length > 0
    }

    if (questionCourante.type_question === 'hesitation') {
      if (hesitationReponse === 'Non') {
        return true
      }

      const minimum = questionCourante.min_specialites || 2
      return hesitationReponse === 'Oui' && specialitesHesitees.length >= minimum
    }

    return messageActuel.trim() !== ''
  }

  const repasserTest = async () => {
    const confirmation = window.confirm(
      'Voulez-vous démarrer un nouveau test d’orientation ? Votre ancienne trace restera consultable dans l’historique.'
    )

    if (!confirmation) {
      return
    }

    setSessionId(null)
    setMessages([])
    setMessageActuel('')
    setQuestionCourante(null)
    setReponsesSelectionnees([])
    setNiveauxDomaines({})
    setHesitationReponse('')
    setSpecialitesHesitees([])
    setDroitTest(null)
    setTerminee(false)
    setResultat(null)
    setFiche(null)
    setSpecialiteChoisie('')
    setCommentaireChoix('')
    setChoixFinal(null)
    setDocumentAdministratif(null)
    setMessageChoixFinal('')
    setAlternatives([])
    setDocumentSigne(null)
    setMessageUpload('')
    setErreurDocument('')
    setResultatDepotDocument(null)

    await demarrerConversation()
  }

  const envoyerMessage = async (event) => {
    event.preventDefault()

    if (!reponseQuestionValide()) {
      setErreur('Veuillez répondre à la question avant de continuer.')
      return
    }

    const contenu = construireReponseQuestion()

    setErreur('')
    ajouterMessage('etudiant', contenu)
    setEnvoi(true)

    try {
      const reponse = await envoyerMessageChat(sessionId, contenu)

      ajouterMessage('assistant', reponse.message_bot)

      if (reponse.terminee) {
        setTerminee(true)
        setResultat(reponse.resultat_recommandation)
        setFiche(reponse.fiche)
        setQuestionCourante(null)

        if (reponse.resultat_recommandation?.specialite_recommandee) {
          setSpecialiteChoisie(
            reponse.resultat_recommandation.specialite_recommandee
          )
        }
      } else {
        setQuestionCourante(reponse.question || questionCourante)
        reinitialiserReponseQuestion(reponse.question || questionCourante)
      }
    } catch (error) {
      setErreur(error.message)
    } finally {
      setEnvoi(false)
    }
  }

  const confirmerChoixFinal = async () => {
    if (!fiche || !fiche.fiche_id) {
      setErreur('Fiche introuvable.')
      return
    }

    if (specialiteChoisie.trim() === '') {
      setErreur('Veuillez choisir une spécialité finale.')
      return
    }

    setErreur('')
    setMessageChoixFinal('')
    setAlternatives([])
    setChoixEnCours(true)

    try {
      const resultatChoix = await enregistrerChoixFinal(
        utilisateur.id,
        fiche.fiche_id,
        specialiteChoisie,
        commentaireChoix
      )

      setChoixFinal(resultatChoix)
      setMessageChoixFinal(resultatChoix.message)

      await chargerEtatEtudiant(false)
    } catch (error) {
      setErreur(error.message)

      if (error.data && error.data.alternatives) {
        setAlternatives(error.data.alternatives)
      }
    } finally {
      setChoixEnCours(false)
    }
  }

  const formaterTailleFichier = (taille) => {
    if (!taille && taille !== 0) {
      return ''
    }

    const tailleMo = taille / (1024 * 1024)

    return `${tailleMo.toFixed(2)} Mo`
  }

  const validerDocumentSigne = (fichier) => {
    if (!fichier) {
      return {
        success: false,
        message: 'Veuillez sélectionner le document signé.'
      }
    }

    const nomFichier = fichier.name || ''

    if (!nomFichier.includes('.')) {
      return {
        success: false,
        message: 'Le fichier doit avoir une extension valide.'
      }
    }

    const extension = nomFichier.split('.').pop().toLowerCase()

    if (!EXTENSIONS_DOCUMENTS_AUTORISEES.includes(extension)) {
      return {
        success: false,
        message: 'Format non autorisé. Formats acceptés : PDF, JPG, JPEG, PNG.'
      }
    }

    if (fichier.size > TAILLE_MAX_DOCUMENT_SIGNE) {
      return {
        success: false,
        message: 'Le fichier est trop volumineux. Taille maximale autorisée : 5 Mo.'
      }
    }

    return {
      success: true,
      message: 'Document valide.'
    }
  }

  const selectionnerDocumentSigne = (event) => {
    const fichier = event.target.files[0]

    setErreur('')
    setErreurDocument('')
    setMessageUpload('')
    setMessageDocumentSelectionne('')
    setResultatDepotDocument(null)

    if (!fichier) {
      setDocumentSigne(null)
      return
    }

    const validation = validerDocumentSigne(fichier)

    if (!validation.success) {
      setDocumentSigne(null)
      setErreurDocument(validation.message)
      event.target.value = ''
      return
    }

    setDocumentSigne(fichier)

    setMessageDocumentSelectionne(
      `Fichier sélectionné : ${fichier.name} (${formaterTailleFichier(fichier.size)})`
    )
  }

  const construireMessageDepotDocument = (resultatUpload) => {
    if (!resultatUpload) {
      return ''
    }

    const notificationEmail = resultatUpload.notification_email

    if (notificationEmail && notificationEmail.success) {
      return (
        'Document signé déposé avec succès. ' +
        'Une notification email a été envoyée au service concerné. ' +
        'Votre document est maintenant en attente de confirmation du doyen.'
      )
    }

    return (
      'Document signé déposé avec succès. ' +
      'Votre document est maintenant en attente de confirmation du doyen. ' +
      'La notification email n’est pas encore configurée ou n’a pas pu être envoyée.'
    )
  }


  const getMessageNotificationDepot = () => {
    if (!resultatDepotDocument || !resultatDepotDocument.notification_email) {
      return ''
    }

    return resultatDepotDocument.notification_email.message || ''
  }


  const notificationEmailDepotEnvoyee = () => {
    return Boolean(
      resultatDepotDocument &&
        resultatDepotDocument.notification_email &&
        resultatDepotDocument.notification_email.success
    )
  }


  const envoyerDocumentSigne = async () => {
    if (!choixFinal || !choixFinal.choix_id) {
      setErreur('Veuillez d’abord confirmer votre choix final.')
      return
    }

    if (!documentSigne) {
      setErreurDocument('Veuillez sélectionner le document signé.')
      return
    }

    const validation = validerDocumentSigne(documentSigne)

    if (!validation.success) {
      setErreurDocument(validation.message)
      return
    }

    setErreur('')
    setErreurDocument('')
    setMessageUpload('')
    setMessageDocumentSelectionne('')
    setResultatDepotDocument(null)
    setUploadEnCours(true)

    try {
      const resultatUpload = await deposerDocumentSigne(
        choixFinal.choix_id,
        utilisateur.id,
        documentSigne
      )

      setResultatDepotDocument(resultatUpload)
      setMessageUpload(construireMessageDepotDocument(resultatUpload))
      setDocumentSigne(null)
      setErreurDocument('')

      await chargerEtatEtudiant(false)
    } catch (error) {
      setErreur(error.message)
    } finally {
      setUploadEnCours(false)
    }
  }

  const ouvrirDiscussionEtudiant = async () => {
    setErreur('')
    setErreurDiscussion('')
    setChargementDiscussion(true)

    try {
      const discussion = await getDiscussionEtudiant(utilisateur.id)

      setDiscussionEtudiant(discussion)
      setFenetreDiscussionOuverte(true)
    } catch (error) {
      setErreurDiscussion(error.message)
    } finally {
      setChargementDiscussion(false)
    }
  }

  const fermerDiscussionEtudiant = () => {
    if (chargementDiscussion) {
      return
    }

    setFenetreDiscussionOuverte(false)
  }

  const getProfilEtudiant = () => {
    return utilisateur.profil || null
  }

  const getNomComplet = () => {
    const profil = getProfilEtudiant()

    if (!profil) {
      return utilisateur.identifiant
    }

    return `${profil.prenom || ''} ${profil.nom || ''}`.trim()
  }

  const getSpecialites = () => {
    if (!resultat || !resultat.pourcentages) {
      return []
    }

    return Object.entries(resultat.pourcentages)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .map(([specialite]) => specialite)
  }

  const getPourcentagesTries = () => {
    if (!resultat || !resultat.pourcentages) {
      return []
    }

    return Object.entries(resultat.pourcentages)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
  }

  const getStatutDocument = () => {
    if (!documentAdministratif) {
      return 'Aucun document signé déposé'
    }

    const statutDocument = documentAdministratif.statut_document
    const statutChoix = choixFinal?.statut_choix

    if (
      statutDocument === 'en_attente' ||
      statutDocument === 'en_attente_confirmation_doyen' ||
      statutDocument === 'document_depose' ||
      statutChoix === 'document_depose' ||
      statutChoix === 'en_attente_confirmation_doyen'
    ) {
      return 'Document déposé — en attente de confirmation du doyen'
    }

    if (
      statutDocument === 'confirme' ||
      statutDocument === 'valide' ||
      statutDocument === 'confirme_par_doyen' ||
      statutChoix === 'document_confirme' ||
      statutChoix === 'confirme_par_doyen'
    ) {
      return 'Document confirmé par le doyen'
    }

    if (
      statutDocument === 'refuse' ||
      statutDocument === 'refuse_par_doyen' ||
      statutChoix === 'document_refuse' ||
      statutChoix === 'refuse_par_doyen'
    ) {
      return 'Document refusé par le doyen'
    }

    return 'Statut administratif en cours de traitement'
  }

  const documentEstRefuse = () => {
    if (!documentAdministratif) {
      return false
    }

    return (
      documentAdministratif.statut_document === 'refuse' ||
      documentAdministratif.statut_document === 'refuse_par_doyen' ||
      choixFinal?.statut_choix === 'document_refuse' ||
      choixFinal?.statut_choix === 'refuse_par_doyen'
    )
  }

  const documentEstConfirme = () => {
    if (!documentAdministratif) {
      return false
    }

    return (
      documentAdministratif.statut_document === 'confirme' ||
      documentAdministratif.statut_document === 'valide' ||
      documentAdministratif.statut_document === 'confirme_par_doyen' ||
      choixFinal?.statut_choix === 'document_confirme' ||
      choixFinal?.statut_choix === 'confirme_par_doyen'
    )
  }

  const peutDeposerDocument = () => {
    if (!choixFinal) {
      return false
    }

    if (!documentAdministratif) {
      return true
    }

    if (documentEstRefuse()) {
      return true
    }

    return false
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

  const getDateMessageDiscussion = (message) => {
    return (
      message.date_creation ||
      message.date_message ||
      message.created_at ||
      message.date_envoi ||
      ''
    )
  }

  const getMessagesDiscussion = () => {
    if (!discussionEtudiant || !Array.isArray(discussionEtudiant.messages)) {
      return []
    }

    return discussionEtudiant.messages
  }


  const afficherFormulaireQuestion = () => {
    if (!questionCourante || terminee) {
      return null
    }

    if (
      questionCourante.type_question === 'choix_multiple' ||
      questionCourante.type_question === 'choix_unique'
    ) {
      return (
        <form onSubmit={envoyerMessage} className="question-response-card">
          {questionCourante.consigne && (
            <p className="question-consigne">{questionCourante.consigne}</p>
          )}

          <div className="checkbox-options-grid">
            {(questionCourante.options || []).map((option) => {
              const optionTexte = getOptionTexte(option)

              return (
                <label className="checkbox-option-card" key={optionTexte}>
                  <input
                    type="checkbox"
                    checked={reponsesSelectionnees.includes(optionTexte)}
                    onChange={() => basculerOption(optionTexte)}
                    disabled={envoi}
                  />
                  <span>{optionTexte}</span>
                </label>
              )
            })}
          </div>

          <button type="submit" disabled={envoi || !reponseQuestionValide()}>
            Valider la réponse
          </button>
        </form>
      )
    }

    if (questionCourante.type_question === 'hesitation') {
      return (
        <form onSubmit={envoyerMessage} className="question-response-card">
          {questionCourante.consigne && (
            <p className="question-consigne">{questionCourante.consigne}</p>
          )}

          <div className="hesitation-choice-row">
            <label className="checkbox-option-card">
              <input
                type="radio"
                name="hesitation"
                checked={hesitationReponse === 'Non'}
                onChange={() => {
                  setHesitationReponse('Non')
                  setSpecialitesHesitees([])
                }}
                disabled={envoi}
              />
              <span>Non</span>
            </label>

            <label className="checkbox-option-card">
              <input
                type="radio"
                name="hesitation"
                checked={hesitationReponse === 'Oui'}
                onChange={() => setHesitationReponse('Oui')}
                disabled={envoi}
              />
              <span>Oui</span>
            </label>
          </div>

          {hesitationReponse === 'Oui' && (
            <div className="checkbox-options-grid">
              {(questionCourante.specialites || []).map((specialite) => (
                <label className="checkbox-option-card" key={specialite}>
                  <input
                    type="checkbox"
                    checked={specialitesHesitees.includes(specialite)}
                    onChange={() => basculerSpecialiteHesitee(specialite)}
                    disabled={envoi}
                  />
                  <span>{specialite}</span>
                </label>
              ))}
            </div>
          )}

          <button type="submit" disabled={envoi || !reponseQuestionValide()}>
            Valider la réponse
          </button>
        </form>
      )
    }

    return (
      <form onSubmit={envoyerMessage} className="chat-input-row text-question-row">
        <textarea
          className="chat-textarea"
          value={messageActuel}
          onChange={(event) => setMessageActuel(event.target.value)}
          placeholder="Écrivez votre réponse ici..."
          disabled={envoi}
        />

        <button type="submit" disabled={envoi || !reponseQuestionValide()}>
          Envoyer
        </button>
      </form>
    )
  }

  if (chargement) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-card">
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

          <h1>Espace étudiant</h1>
          <p>Préparation du chatbot d’orientation...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      {fenetreDiscussionOuverte && discussionEtudiant && (
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
              maxWidth: '850px',
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
                <h2>Ma discussion avec le chatbot</h2>
                <p>
                  Trace complète de votre échange avec le chatbot d’orientation.
                </p>
              </div>

              <button
                className="secondary-button small-button"
                onClick={fermerDiscussionEtudiant}
              >
                Fermer
              </button>
            </div>

            {discussionEtudiant.fiche && (
              <div className="profile-summary-card">
                <div>
                  <span className="info-label">Étudiant</span>
                  <strong>
                    {discussionEtudiant.fiche.prenom}{' '}
                    {discussionEtudiant.fiche.nom}
                  </strong>
                </div>

                <div>
                  <span className="info-label">ID universitaire</span>
                  <strong>{discussionEtudiant.fiche.id_universitaire}</strong>
                </div>

                <div>
                  <span className="info-label">Spécialité proposée</span>
                  <strong>
                    {discussionEtudiant.fiche.specialite_recommandee}
                  </strong>
                </div>
              </div>
            )}

            <div className="discussion-actions">
              <a
                className="discussion-download-button"
                href={getUrlDiscussionEtudiantPdf(utilisateur.id)}
                target="_blank"
                rel="noreferrer"
              >
                Télécharger en PDF
              </a>

              <a
                className="discussion-secondary-button"
                href={getUrlDiscussionEtudiantTxt(utilisateur.id)}
                target="_blank"
                rel="noreferrer"
              >
                Télécharger en TXT
              </a>
            </div>

            <h3>Discussion complète</h3>

            {getMessagesDiscussion().length === 0 ? (
              <p className="info-message">
                Aucun message n’est disponible pour cette discussion.
              </p>
            ) : (
              <div className="chat-messages">
                {getMessagesDiscussion().map((message, index) => {
                  const role = message.role_message
                  const estChatbot =
                    role === 'assistant' || role === 'bot'

                  return (
                    <div
                      key={message.id || index}
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

                        {getDateMessageDiscussion(message) && (
                          <p style={{ fontSize: '0.78rem', opacity: 0.75 }}>
                            {getDateMessageDiscussion(message)}
                          </p>
                        )}

                        <p>
                          {afficherTexteAvecGras(message.contenu)}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="dashboard-card chat-large-card">
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
            <h1>Chatbot d’orientation</h1>
            <p>
              Bienvenue, <strong>{getNomComplet()}</strong>.
            </p>
          </div>

          <button className="secondary-button small-button" onClick={onLogout}>
            Se déconnecter
          </button>
        </div>

        <div className="administrative-info-card">
          <h2>Information administrative importante</h2>

          <p>
            La fiche initiale d’engagement doit être fournie au début de
            l’année universitaire auprès de l’administration.
          </p>

          <p>
            La plateforme permet de générer, déposer et suivre la fiche
            d’engagement numérique, mais la remise du document initial reste
            obligatoire selon les procédures administratives de l’établissement.
          </p>
        </div>

        {sessionId && messages.length > 0 && (
          <div className="chat-shell">
            <div className="chat-messages">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.role === 'assistant'
                      ? 'message-row bot-row'
                      : 'message-row user-row'
                  }
                >
                  <div
                    className={
                      message.role === 'assistant'
                        ? 'chat-bubble bot-bubble'
                        : 'chat-bubble user-bubble'
                    }
                  >
                    {afficherTexteAvecGras(message.contenu)}
                  </div>
                </div>
              ))}

              {envoi && (
                <div className="message-row bot-row">
                  <div className="chat-bubble bot-bubble">
                    Analyse de votre réponse...
                  </div>
                </div>
              )}
            </div>

            {!terminee && afficherFormulaireQuestion()}
          </div>
        )}

        {terminee && resultat && (
          <div className="student-fiche-block">
            <h2>Résultat proposé par le système</h2>

            <div className="administrative-info-card">
              <h3>Repasser le test</h3>

              <p>
                Vous pouvez refaire le test d’orientation librement. Le nouveau
                passage créera une nouvelle trace de discussion et une nouvelle
                fiche de recommandation.
              </p>

              <button
                className="secondary-button small-button"
                onClick={repasserTest}
                disabled={chargement || envoi}
              >
                Refaire le test
              </button>
            </div>

            <div className="result-highlight-card">
              <span className="info-label">Recommandation principale</span>

              <h2>{resultat.specialite_recommandee}</h2>

              <p>
                Cette recommandation est une aide à la décision. Le choix final
                appartient à l’étudiant.
              </p>
            </div>

            <h3>Scores par spécialité</h3>

            <div className="scores-list">
              {getPourcentagesTries().map(
                ([specialite, pourcentage]) => (
                  <div className="score-card" key={specialite}>
                    <div className="score-card-header">
                      <span>{specialite}</span>
                      <strong>{pourcentage}%</strong>
                    </div>

                    <div className="score-progress">
                      <div
                        className="score-progress-fill"
                        style={{ width: `${pourcentage}%` }}
                      />
                    </div>
                  </div>
                )
              )}
            </div>

            {fiche && (
              <>
                <h3>Fiche intelligente</h3>

                <pre className="resume-box">
                  {fiche.resume_profil}
                </pre>

                <div className="document-workflow-card">
                  <h3>Trace de ma discussion avec le chatbot</h3>

                  <p>
                    Vous pouvez visualiser toute votre discussion avec le
                    chatbot. Le téléchargement PDF ou TXT est disponible comme
                    option d’archivage.
                  </p>

                  <div className="discussion-actions">
                    <button
                      className="discussion-primary-button"
                      onClick={ouvrirDiscussionEtudiant}
                      disabled={chargementDiscussion}
                    >
                      {chargementDiscussion
                        ? 'Chargement de la discussion...'
                        : 'Visualiser ma discussion'}
                    </button>

                    <a
                      className="discussion-download-button"
                      href={getUrlDiscussionEtudiantPdf(utilisateur.id)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Télécharger PDF
                    </a>

                    <a
                      className="discussion-secondary-button"
                      href={getUrlDiscussionEtudiantTxt(utilisateur.id)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Télécharger TXT
                    </a>
                  </div>

                  {erreurDiscussion && (
                    <p className="login-error">
                      {erreurDiscussion}
                    </p>
                  )}
                </div>
              </>
            )}

            <div className="final-choice-card">
              <h3>Choix final de la filière</h3>

              {!choixFinal && (
                <p>
                  Vous pouvez suivre la recommandation proposée ou choisir une
                  autre filière selon votre projet personnel.
                </p>
              )}

              {choixFinal && (
                <p className="success-message">
                  Choix final enregistré :{' '}
                  <strong>
                    {choixFinal.filiere_choisie || specialiteChoisie}
                  </strong>
                </p>
              )}

              <label>Filière choisie</label>

              <select
                value={specialiteChoisie}
                onChange={(event) => setSpecialiteChoisie(event.target.value)}
                disabled={choixFinal !== null}
              >
                {getSpecialites().map((specialite) => (
                  <option key={specialite} value={specialite}>
                    {specialite}
                  </option>
                ))}
              </select>

              <label>Commentaire personnel</label>

              <textarea
                className="remark-textarea"
                value={commentaireChoix}
                onChange={(event) => setCommentaireChoix(event.target.value)}
                placeholder="Expliquez brièvement votre choix final..."
                disabled={choixFinal !== null}
              />

              {!choixFinal && (
                <button
                  onClick={confirmerChoixFinal}
                  disabled={choixEnCours}
                >
                  {choixEnCours
                    ? 'Enregistrement du choix...'
                    : 'Confirmer mon choix et générer la fiche'}
                </button>
              )}

              {messageChoixFinal && (
                <p className="success-message">
                  {messageChoixFinal}
                </p>
              )}

              {alternatives.length > 0 && (
                <div className="alternatives-card">
                  <h4>Filières disponibles proches de votre profil</h4>

                  {alternatives.map((alternative) => (
                    <div
                      key={alternative.specialite}
                      className="alternative-line"
                    >
                      <span>
                        {alternative.specialite} — {alternative.pourcentage}%
                      </span>

                      <strong>
                        Proposition proche de votre profil
                      </strong>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {choixFinal && (
              <div className="document-workflow-card">
                <h3>Fiche d’engagement</h3>

                <p>
                  Votre fiche d’engagement est disponible. Téléchargez-la,
                  signez-la, puis déposez le document signé ou scanné.
                </p>

                <a
                  className="download-link-button"
                  href={getUrlFicheEngagement(choixFinal.choix_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Télécharger la fiche d’engagement PDF
                </a>

                <div className="document-status-box">
                  <h4>Statut administratif</h4>

                  <p>
                    <strong>{getStatutDocument()}</strong>
                  </p>

                  {documentAdministratif && (
                    <p>
                      Dernier document déposé :{' '}
                      <strong>
                        {documentAdministratif.nom_fichier_original}
                      </strong>
                    </p>
                  )}

                  {documentAdministratif?.verification_auto_message && (
                    <p className="info-message">
                      {documentAdministratif.verification_auto_message}
                    </p>
                  )}

                  {documentAdministratif?.remarque_doyen && (
                    <p className="login-error">
                      Remarque du doyen : {documentAdministratif.remarque_doyen}
                    </p>
                  )}

                  {documentEstConfirme() && (
                    <p className="success-message">
                      Votre document est confirmé. Votre choix de filière est enregistré administrativement.
                    </p>
                  )}

                  {documentEstRefuse() && (
                    <p className="login-error">
                      Votre document a été refusé. Veuillez déposer une nouvelle
                      version corrigée.
                    </p>
                  )}
                </div>

                {peutDeposerDocument() && (
                  <div className="upload-block">
                    <label>Déposer la fiche signée/scannée</label>

                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={selectionnerDocumentSigne}
                      disabled={uploadEnCours}
                    />

                    <p className="info-message">
                      Formats acceptés : PDF, JPG, JPEG, PNG. Taille maximale : 5 Mo.
                    </p>

                    {erreurDocument && (
                      <p className="login-error">
                        {erreurDocument}
                      </p>
                    )}

                    {messageDocumentSelectionne && (
                      <p className="info-message">
                        {messageDocumentSelectionne}
                      </p>
                    )}

                    <button
                      onClick={envoyerDocumentSigne}
                      disabled={uploadEnCours || !documentSigne}
                    >
                      {uploadEnCours
                        ? 'Dépôt en cours...'
                        : !documentSigne
                          ? 'Sélectionnez un fichier valide'
                          : documentEstRefuse()
                            ? 'Redéposer le document corrigé'
                            : 'Déposer le document signé'}
                    </button>
                  </div>
                )}

                {messageUpload && (
                  <div className="document-status-box">
                    <h4>Confirmation du dépôt</h4>

                    <p className="success-message">
                      {messageUpload}
                    </p>

                    <p>
                      <strong>Statut actuel :</strong>{' '}
                      document déposé et en attente de validation administrative
                      par le doyen.
                    </p>

                    {resultatDepotDocument?.notification_email && (
                      notificationEmailDepotEnvoyee() ? (
                        <p className="success-message">
                          Notification email : {getMessageNotificationDepot()}
                        </p>
                      ) : (
                        <p className="info-message">
                          Notification email : {getMessageNotificationDepot()}
                        </p>
                      )
                    )}

                    <p className="info-message">
                      Important : votre choix de filière sera enregistré
                      administrativement après confirmation du document par le
                      doyen.
                    </p>
                  </div>
                )}

                {!documentEstConfirme() && (
                  <p className="info-message">
                    Après dépôt, le document sera vérifié administrativement par
                    le doyen. Votre choix de filière sera enregistré après
                    confirmation du document.
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {erreur && <p className="login-error">{erreur}</p>}
      </div>
    </div>
  )
}

export default EtudiantPage