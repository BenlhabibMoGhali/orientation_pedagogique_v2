import {
  getAuthorizationHeaders,
  ajouterTokenUrl
} from './authService'

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

export async function demarrerChatOrientation(utilisateurId) {
  const response = await fetch(`${API_BASE_URL}/chat-orientation/demarrer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthorizationHeaders()
    },
    body: JSON.stringify({
      utilisateur_id: utilisateurId
    })
  })

  return lireReponseJson(response)
}

export async function envoyerMessageChat(sessionId, message) {
  const response = await fetch(`${API_BASE_URL}/chat-orientation/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthorizationHeaders()
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message
    })
  })

  return lireReponseJson(response)
}

export async function enregistrerChoixFinal(
  utilisateurId,
  ficheId,
  specialiteChoisie,
  commentaire
) {
  const response = await fetch(`${API_BASE_URL}/chat-orientation/choix-final`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthorizationHeaders()
    },
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      fiche_id: ficheId,
      specialite_choisie: specialiteChoisie,
      commentaire: commentaire
    })
  })

  return lireReponseJson(response)
}

export function getUrlFicheEngagement(choixId) {
  return ajouterTokenUrl(
    `${API_BASE_URL}/chat-orientation/choix-final/${choixId}/pdf`
  )
}

export async function deposerDocumentSigne(choixId, utilisateurId, fichier) {
  const formData = new FormData()

  formData.append('utilisateur_id', utilisateurId)
  formData.append('document', fichier)

  const response = await fetch(
    `${API_BASE_URL}/chat-orientation/choix-final/${choixId}/document-signe`,
    {
      method: 'POST',
      headers: {
        ...getAuthorizationHeaders()
      },
      body: formData
    }
  )

  return lireReponseJson(response)
}

export async function getEtatOrientationEtudiant(utilisateurId) {
  const response = await fetch(
    `${API_BASE_URL}/chat-orientation/etat-etudiant/${utilisateurId}`,
    {
      headers: {
        ...getAuthorizationHeaders()
      }
    }
  )

  return lireReponseJson(response)
}

export async function getDiscussionEtudiant(utilisateurId) {
  const response = await fetch(
    `${API_BASE_URL}/chat-orientation/etat-etudiant/${utilisateurId}/discussion`,
    {
      headers: {
        ...getAuthorizationHeaders()
      }
    }
  )

  return lireReponseJson(response)
}

export function getUrlDiscussionEtudiantTxt(utilisateurId) {
  return ajouterTokenUrl(
    `${API_BASE_URL}/chat-orientation/etat-etudiant/${utilisateurId}/discussion/txt`
  )
}

export function getUrlDiscussionEtudiantPdf(utilisateurId) {
  return ajouterTokenUrl(
    `${API_BASE_URL}/chat-orientation/etat-etudiant/${utilisateurId}/discussion/pdf`
  )
}
