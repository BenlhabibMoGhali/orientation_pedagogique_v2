import { useState } from 'react'
import {
  loginUtilisateur,
  demanderCodeInscriptionEtudiant,
  confirmerInscriptionEtudiant,
  demanderReinitialisationMotDePasse,
  reinitialiserMotDePasse
} from '../services/authService'
import '../styles/LoginPage.css'

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('connexion')

  const [identifiant, setIdentifiant] = useState('')
  const [motDePasse, setMotDePasse] = useState('')

  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [idUniversitaire, setIdUniversitaire] = useState('')
  const [email, setEmail] = useState('')
  const [motDePasseInscription, setMotDePasseInscription] = useState('')
  const [confirmationMotDePasse, setConfirmationMotDePasse] = useState('')
  const [codeConfirmationInscription, setCodeConfirmationInscription] = useState('')
  const [codeInscriptionEnvoye, setCodeInscriptionEnvoye] = useState(false)

  const [identifiantOuEmail, setIdentifiantOuEmail] = useState('')
  const [tokenDemo, setTokenDemo] = useState('')

  const [token, setToken] = useState('')
  const [nouveauMotDePasse, setNouveauMotDePasse] = useState('')
  const [confirmationNouveauMotDePasse, setConfirmationNouveauMotDePasse] = useState('')

  const [erreur, setErreur] = useState('')
  const [message, setMessage] = useState('')
  const [chargement, setChargement] = useState(false)

  const EMAIL_DOMAINE_EIDIA = '@eidia.ueuromed.org'
  const EMAIL_ETUDIANT_REGEX = /^[a-z]+\.[a-z]+@eidia\.ueuromed\.org$/
  const ID_UNIVERSITAIRE_REGEX = /^\d{7}$/

  const changerMode = (nouveauMode) => {
    setMode(nouveauMode)
    setErreur('')
    setMessage('')

    if (nouveauMode !== 'inscription') {
      setCodeConfirmationInscription('')
      setCodeInscriptionEnvoye(false)
    }
  }

  const calculerAnneeUniversitaireAutomatique = () => {
    const dateActuelle = new Date()
    const mois = dateActuelle.getMonth() + 1
    const annee = dateActuelle.getFullYear()

    const anneeDebut = mois >= 7 ? annee : annee - 1
    const anneeFin = anneeDebut + 1

    return `${anneeDebut}/${anneeFin}`
  }

  const normaliserIdUniversitaire = (valeur) => {
    return valeur.replace(/\D/g, '').slice(0, 7)
  }

  const idUniversitaireValide = () => {
    return ID_UNIVERSITAIRE_REGEX.test(idUniversitaire)
  }

  const normaliserPartieEmail = (valeur) => {
    if (!valeur) {
      return ''
    }

    return valeur
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z]/g, '')
  }

  const construireEmailAttendu = () => {
    const prenomNormalise = normaliserPartieEmail(prenom)
    const nomNormalise = normaliserPartieEmail(nom)

    if (!prenomNormalise || !nomNormalise) {
      return ''
    }

    return `${prenomNormalise}.${nomNormalise}${EMAIL_DOMAINE_EIDIA}`
  }

  const normaliserEmailEtudiant = (emailEtudiant) => {
    return emailEtudiant.trim().toLowerCase()
  }

  const emailEtudiantValide = (emailEtudiant) => {
    if (!emailEtudiant) {
      return false
    }

    const emailNormalise = normaliserEmailEtudiant(emailEtudiant)
    const emailAttendu = construireEmailAttendu()

    if (!EMAIL_ETUDIANT_REGEX.test(emailNormalise)) {
      return false
    }


    if (!emailAttendu) {
      return false
    }

    return emailNormalise === emailAttendu
  }

  const handleConnexion = async (event) => {
    event.preventDefault()
    setErreur('')
    setMessage('')
    setChargement(true)

    try {
      const resultat = await loginUtilisateur(identifiant, motDePasse)

      localStorage.setItem('utilisateur', JSON.stringify(resultat.utilisateur))

      onLogin(resultat.utilisateur)
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const validerChampsInscription = () => {
    const emailNormalise = normaliserEmailEtudiant(email)
    const emailAttendu = construireEmailAttendu()

    if (!idUniversitaireValide()) {
      setErreur(
        'ID universitaire invalide. Il doit contenir exactement 7 chiffres, sans lettres ni espaces.'
      )
      return null
    }

    if (!emailAttendu) {
      setErreur(
        'Veuillez saisir correctement votre nom et votre prénom avant de valider l’email.'
      )
      return null
    }

    if (!emailEtudiantValide(emailNormalise)) {
      setErreur(
        `Email étudiant invalide. L'adresse attendue selon le nom et prénom saisis est : ${emailAttendu}`
      )
      return null
    }

    if (motDePasseInscription.length < 6) {
      setErreur('Le mot de passe doit contenir au moins 6 caractères.')
      return null
    }

    if (motDePasseInscription !== confirmationMotDePasse) {
      setErreur('Les mots de passe ne correspondent pas.')
      return null
    }

    return {
      emailNormalise,
      anneeUniversitaireAutomatique: calculerAnneeUniversitaireAutomatique()
    }
  }

  const handleDemanderCodeInscription = async (event) => {
    event.preventDefault()
    setErreur('')
    setMessage('')

    const donneesValidees = validerChampsInscription()

    if (!donneesValidees) {
      return
    }

    setChargement(true)

    try {
      const resultat = await demanderCodeInscriptionEtudiant(
        nom,
        prenom,
        idUniversitaire,
        donneesValidees.emailNormalise,
        donneesValidees.anneeUniversitaireAutomatique,
        motDePasseInscription,
        confirmationMotDePasse
      )

      setCodeInscriptionEnvoye(true)
      setMessage(resultat.message)
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const handleConfirmerInscription = async (event) => {
    event.preventDefault()
    setErreur('')
    setMessage('')

    const donneesValidees = validerChampsInscription()

    if (!donneesValidees) {
      return
    }

    if (!/^\d{6}$/.test(codeConfirmationInscription.trim())) {
      setErreur('Le code de confirmation doit contenir 6 chiffres.')
      return
    }

    setChargement(true)

    try {
      const resultat = await confirmerInscriptionEtudiant(
        nom,
        prenom,
        idUniversitaire,
        donneesValidees.emailNormalise,
        donneesValidees.anneeUniversitaireAutomatique,
        motDePasseInscription,
        confirmationMotDePasse,
        codeConfirmationInscription.trim()
      )

      setMessage(
        `${resultat.message} Vous pouvez maintenant vous connecter avec votre ID universitaire.`
      )

      setIdentifiant(idUniversitaire)
      setMotDePasse('')
      setCodeConfirmationInscription('')
      setCodeInscriptionEnvoye(false)
      setMode('connexion')
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const handleMotDePasseOublie = async (event) => {
    event.preventDefault()
    setErreur('')
    setMessage('')
    setTokenDemo('')
    setChargement(true)

    try {
      const resultat = await demanderReinitialisationMotDePasse(
        identifiantOuEmail
      )

      setMessage(resultat.message)

      if (resultat.token_demo) {
        setTokenDemo(resultat.token_demo)
        setToken(resultat.token_demo)
      }
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const handleReinitialisation = async (event) => {
    event.preventDefault()
    setErreur('')
    setMessage('')
    setChargement(true)

    try {
      const resultat = await reinitialiserMotDePasse(
        token,
        nouveauMotDePasse,
        confirmationNouveauMotDePasse
      )

      setMessage(resultat.message)
      setMotDePasse('')
      setMode('connexion')
    } catch (error) {
      setErreur(error.message)
    } finally {
      setChargement(false)
    }
  }

  const emailAttendu = construireEmailAttendu()
  const anneeUniversitaireAutomatique = calculerAnneeUniversitaireAutomatique()

  return (
    <div className="login-container">
      <div className="login-card">
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

        <h1>Plateforme d’orientation pédagogique</h1>

        {mode === 'connexion' && (
          <>
            <p className="login-subtitle">
              Connexion étudiant / doyen
            </p>

            <form onSubmit={handleConnexion} className="login-form">
              <label>Identifiant</label>
              <input
                type="text"
                value={identifiant}
                onChange={(event) => setIdentifiant(event.target.value)}
                placeholder="ID universitaire ou identifiant doyen"
                required
              />

              <label>Mot de passe</label>
              <input
                type="password"
                value={motDePasse}
                onChange={(event) => setMotDePasse(event.target.value)}
                placeholder="Mot de passe"
                required
              />

              {erreur && <p className="login-error">{erreur}</p>}
              {message && <p className="login-success">{message}</p>}

              <button type="submit" disabled={chargement}>
                {chargement ? 'Connexion...' : 'Se connecter'}
              </button>
            </form>

            <div className="login-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => changerMode('inscription')}
              >
                Créer un compte étudiant
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() => changerMode('motDePasseOublie')}
              >
                Mot de passe oublié ?
              </button>
            </div>

            <div className="login-help">
              <p>Connexion étudiant : ID universitaire + mot de passe</p>
              <p>Compte doyen test : doyen001 / 123456</p>
            </div>
          </>
        )}

        {mode === 'inscription' && (
          <>
            <p className="login-subtitle">
              Inscription étudiant
            </p>

            <form onSubmit={handleDemanderCodeInscription} className="login-form">
              <label>Nom</label>
              <input
                type="text"
                value={nom}
                onChange={(event) => setNom(event.target.value)}
                placeholder="Votre nom"
                required
              />

              <label>Prénom</label>
              <input
                type="text"
                value={prenom}
                onChange={(event) => setPrenom(event.target.value)}
                placeholder="Votre prénom"
                required
              />

              <label>ID universitaire</label>
              <input
                type="text"
                value={idUniversitaire}
                onChange={(event) =>
                  setIdUniversitaire(normaliserIdUniversitaire(event.target.value))
                }
                placeholder="Exemple : 1234567"
                inputMode="numeric"
                pattern="[0-9]{7}"
                maxLength="7"
                required
              />

              <p className="info-message">
                L’ID universitaire doit contenir exactement
                <strong> 7 chiffres</strong>, sans lettres ni espaces.
              </p>

              <label>Email universitaire EIDIA</label>
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value.trim().toLowerCase())
                }
                placeholder="prenom.nom@eidia.ueuromed.org"
                required
              />

              <p className="info-message">
                L’email doit respecter exactement le format :
                <strong> prenom.nom@eidia.ueuromed.org</strong>
                <br />
                Si le nom ou le prénom contient plusieurs mots, ils doivent être
                écrits collés dans l’adresse email.
                <br />
                Exemple : <strong>mohamed hamza</strong> devient{' '}
                <strong>mohamedhamza</strong>.
              </p>

              {emailAttendu && (
                <p className="info-message">
                  Adresse attendue selon le nom et prénom saisis :
                  <br />
                  <strong>{emailAttendu}</strong>
                </p>
              )}

              <label>Année universitaire</label>
              <input
                type="text"
                value={anneeUniversitaireAutomatique}
                readOnly
                disabled
              />

              <p className="info-message">
                L’année universitaire est générée automatiquement par le système :
                <strong> {anneeUniversitaireAutomatique}</strong>.
                <br />
                Elle commence en septembre et se termine fin juin de l’année suivante.
              </p>

              <label>Mot de passe</label>
              <input
                type="password"
                value={motDePasseInscription}
                onChange={(event) => setMotDePasseInscription(event.target.value)}
                placeholder="Minimum 6 caractères"
                required
              />

              <label>Confirmation du mot de passe</label>
              <input
                type="password"
                value={confirmationMotDePasse}
                onChange={(event) => setConfirmationMotDePasse(event.target.value)}
                placeholder="Confirmez le mot de passe"
                required
              />

              {codeInscriptionEnvoye && (
                <>
                  <label>Code de confirmation reçu par email Outlook</label>
                  <input
                    type="text"
                    value={codeConfirmationInscription}
                    onChange={(event) =>
                      setCodeConfirmationInscription(
                        event.target.value.replace(/\D/g, '').slice(0, 6)
                      )
                    }
                    placeholder="Code à 6 chiffres"
                    inputMode="numeric"
                    maxLength="6"
                  />

                  <p className="info-message">
                    Le code est envoyé à votre email Outlook universitaire.
                    Cette étape permet de confirmer que c’est bien l’étudiant
                    concerné qui crée le compte.
                  </p>
                </>
              )}

              {erreur && <p className="login-error">{erreur}</p>}
              {message && <p className="login-success">{message}</p>}

              {!codeInscriptionEnvoye ? (
                <button type="submit" disabled={chargement}>
                  {chargement ? 'Envoi du code...' : 'Recevoir le code de confirmation'}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    disabled={chargement}
                    onClick={handleConfirmerInscription}
                  >
                    {chargement ? 'Confirmation...' : 'Confirmer mon inscription'}
                  </button>

                  <button
                    type="submit"
                    className="secondary-button"
                    disabled={chargement}
                  >
                    Renvoyer le code
                  </button>
                </>
              )}
            </form>

            <button
              type="button"
              className="secondary-button"
              onClick={() => changerMode('connexion')}
            >
              Retour à la connexion
            </button>
          </>
        )}

        {mode === 'motDePasseOublie' && (
          <>
            <p className="login-subtitle">
              Récupération du mot de passe
            </p>

            <form onSubmit={handleMotDePasseOublie} className="login-form">
              <label>ID universitaire ou email universitaire</label>
              <input
                type="text"
                value={identifiantOuEmail}
                onChange={(event) => setIdentifiantOuEmail(event.target.value)}
                placeholder="Exemple : 1234567 ou prenom.nom@eidia.ueuromed.org"
                required
              />

              {erreur && <p className="login-error">{erreur}</p>}
              {message && <p className="login-success">{message}</p>}

              {tokenDemo && (
                <div className="token-demo-box">
                  <p>Token de démonstration :</p>
                  <pre>{tokenDemo}</pre>
                  <p>
                    En version finale, ce token sera envoyé par email universitaire.
                  </p>
                </div>
              )}

              <button type="submit" disabled={chargement}>
                {chargement ? 'Demande en cours...' : 'Demander la réinitialisation'}
              </button>
            </form>

            {tokenDemo && (
              <button
                type="button"
                className="secondary-button"
                onClick={() => changerMode('reinitialisation')}
              >
                Réinitialiser le mot de passe
              </button>
            )}

            <button
              type="button"
              className="secondary-button"
              onClick={() => changerMode('connexion')}
            >
              Retour à la connexion
            </button>
          </>
        )}

        {mode === 'reinitialisation' && (
          <>
            <p className="login-subtitle">
              Nouveau mot de passe
            </p>

            <form onSubmit={handleReinitialisation} className="login-form">
              <label>Token de réinitialisation</label>
              <input
                type="text"
                value={token}
                onChange={(event) => setToken(event.target.value)}
                placeholder="Collez le token reçu"
                required
              />

              <label>Nouveau mot de passe</label>
              <input
                type="password"
                value={nouveauMotDePasse}
                onChange={(event) => setNouveauMotDePasse(event.target.value)}
                placeholder="Nouveau mot de passe"
                required
              />

              <label>Confirmation du nouveau mot de passe</label>
              <input
                type="password"
                value={confirmationNouveauMotDePasse}
                onChange={(event) => setConfirmationNouveauMotDePasse(event.target.value)}
                placeholder="Confirmez le nouveau mot de passe"
                required
              />

              {erreur && <p className="login-error">{erreur}</p>}
              {message && <p className="login-success">{message}</p>}

              <button type="submit" disabled={chargement}>
                {chargement ? 'Réinitialisation...' : 'Changer le mot de passe'}
              </button>
            </form>

            <button
              type="button"
              className="secondary-button"
              onClick={() => changerMode('connexion')}
            >
              Retour à la connexion
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default LoginPage
