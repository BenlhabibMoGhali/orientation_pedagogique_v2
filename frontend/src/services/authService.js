const API_BASE_URL = 'http://127.0.0.1:5000/api'

async function lireReponseJson(response) {
  const texte = await response.text()

  let data = null

  try {
    data = JSON.parse(texte)
  } catch (error) {
    console.error('Réponse non JSON reçue :', texte)

    throw new Error(
      "Le frontend a reçu une réponse HTML au lieu d'une réponse JSON. Vérifiez que le backend Flask est bien lancé sur http://127.0.0.1:5000."
    )
  }

  if (!response.ok) {
    const erreur = new Error(data.message || 'Erreur serveur.')
    erreur.data = data
    throw erreur
  }

  return data
}

export function enregistrerSessionUtilisateur(resultatConnexion) {
  if (resultatConnexion.utilisateur) {
    localStorage.setItem(
      'utilisateur',
      JSON.stringify(resultatConnexion.utilisateur)
    )
  }

  if (resultatConnexion.access_token) {
    localStorage.setItem('access_token', resultatConnexion.access_token)
  }
}

export function getAccessToken() {
  return localStorage.getItem('access_token') || ''
}

export function getAuthorizationHeaders() {
  const token = getAccessToken()

  if (!token) {
    return {}
  }

  return {
    Authorization: `Bearer ${token}`
  }
}

export function ajouterTokenUrl(url) {
  const token = getAccessToken()

  if (!token) {
    return url
  }

  const separateur = url.includes('?') ? '&' : '?'

  return `${url}${separateur}token=${encodeURIComponent(token)}`
}

export function supprimerSessionUtilisateur() {
  localStorage.removeItem('utilisateur')
  localStorage.removeItem('access_token')
}

export async function loginUtilisateur(identifiantConnexion, motDePasse) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      identifiant_connexion: identifiantConnexion,
      mot_de_passe: motDePasse
    })
  })

  const resultat = await lireReponseJson(response)

  enregistrerSessionUtilisateur(resultat)

  return resultat
}

function construirePayloadInscription(
  nom,
  prenom,
  idUniversitaire,
  email,
  promotion,
  motDePasse,
  confirmationMotDePasse
) {
  return {
    nom: nom,
    prenom: prenom,
    id_universitaire: idUniversitaire,
    email: email,
    promotion: promotion,
    mot_de_passe: motDePasse,
    confirmation_mot_de_passe: confirmationMotDePasse
  }
}

export async function demanderCodeInscriptionEtudiant(
  nom,
  prenom,
  idUniversitaire,
  email,
  promotion,
  motDePasse,
  confirmationMotDePasse
) {
  const response = await fetch(`${API_BASE_URL}/auth/register/etudiant/demander-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(
      construirePayloadInscription(
        nom,
        prenom,
        idUniversitaire,
        email,
        promotion,
        motDePasse,
        confirmationMotDePasse
      )
    )
  })

  return lireReponseJson(response)
}

export async function confirmerInscriptionEtudiant(
  nom,
  prenom,
  idUniversitaire,
  email,
  promotion,
  motDePasse,
  confirmationMotDePasse,
  codeConfirmation
) {
  const payload = construirePayloadInscription(
    nom,
    prenom,
    idUniversitaire,
    email,
    promotion,
    motDePasse,
    confirmationMotDePasse
  )

  payload.code_confirmation = codeConfirmation

  const response = await fetch(`${API_BASE_URL}/auth/register/etudiant/confirmer-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  return lireReponseJson(response)
}

export async function inscrireEtudiant(
  nom,
  prenom,
  idUniversitaire,
  email,
  promotion,
  motDePasse,
  confirmationMotDePasse
) {
  return demanderCodeInscriptionEtudiant(
    nom,
    prenom,
    idUniversitaire,
    email,
    promotion,
    motDePasse,
    confirmationMotDePasse
  )
}

export async function demanderReinitialisationMotDePasse(identifiantOuEmail) {
  const response = await fetch(`${API_BASE_URL}/auth/password/forgot`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      identifiant_ou_email: identifiantOuEmail
    })
  })

  return lireReponseJson(response)
}

export async function reinitialiserMotDePasse(
  token,
  nouveauMotDePasse,
  confirmationMotDePasse
) {
  const response = await fetch(`${API_BASE_URL}/auth/password/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      token: token,
      nouveau_mot_de_passe: nouveauMotDePasse,
      confirmation_mot_de_passe: confirmationMotDePasse
    })
  })

  return lireReponseJson(response)
}
