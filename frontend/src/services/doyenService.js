import {
  getAuthorizationHeaders,
  ajouterTokenUrl
} from './authService'

const API_BASE_URL = 'http://127.0.0.1:5000/api'

async function lireReponseJson(response, messageErreur) {
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
    throw new Error(data.message || messageErreur || 'Erreur serveur.')
  }

  return data
}

function headersJsonAutorises() {
  return {
    'Content-Type': 'application/json',
    ...getAuthorizationHeaders()
  }
}

export async function rechercherFichesParIdUniversitaire(recherche) {
  const response = await fetch(
    `${API_BASE_URL}/doyen/fiches/rechercher/${encodeURIComponent(recherche)}`,
    {
      headers: {
        ...getAuthorizationHeaders()
      }
    }
  )

  return lireReponseJson(response, 'Erreur lors de la recherche.')
}


export async function autoriserNouveauTest(utilisateurId, idUniversitaire) {
  const response = await fetch(`${API_BASE_URL}/doyen/autoriser-nouveau-test`, {
    method: 'POST',
    headers: headersJsonAutorises(),
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      id_universitaire: idUniversitaire
    })
  })

  return lireReponseJson(response, 'Erreur lors de l’autorisation.')
}


export async function getRepartitionChoixFilieres() {
  const response = await fetch(`${API_BASE_URL}/doyen/repartition-choix-filieres`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(response, 'Erreur lors du chargement de la répartition des choix.')
}


export async function getDocumentsAConfirmer() {
  const response = await fetch(`${API_BASE_URL}/doyen/documents/a-confirmer`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(response, 'Erreur lors du chargement des documents.')
}


export function getUrlVisualisationDocument(documentId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/documents/${documentId}/visualiser`)
}


export async function prendreDecisionDocument(
  utilisateurId,
  choixId,
  decision,
  remarque
) {
  const response = await fetch(`${API_BASE_URL}/doyen/documents/decision`, {
    method: 'POST',
    headers: headersJsonAutorises(),
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      choix_id: choixId,
      decision: decision,
      remarque: remarque
    })
  })

  return lireReponseJson(response, 'Erreur lors de la décision.')
}


export async function getResumeReinitialisation(anneeUniversitaire) {
  const response = await fetch(
    `${API_BASE_URL}/doyen/reinitialisation/resume/${encodeURIComponent(anneeUniversitaire)}`,
    {
      headers: {
        ...getAuthorizationHeaders()
      }
    }
  )

  return lireReponseJson(response, 'Erreur lors du chargement du résumé.')
}


export async function creerDemandeReinitialisation(
  utilisateurId,
  anneeUniversitaire,
  motDePasse,
  phraseSecurite
) {
  const response = await fetch(`${API_BASE_URL}/doyen/reinitialisation/demande`, {
    method: 'POST',
    headers: headersJsonAutorises(),
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      annee_universitaire: anneeUniversitaire,
      mot_de_passe: motDePasse,
      phrase_securite: phraseSecurite
    })
  })

  return lireReponseJson(response, 'Erreur lors de la demande de réinitialisation.')
}


export async function confirmerReinitialisation(
  utilisateurId,
  reinitialisationId,
  codeConfirmation
) {
  const response = await fetch(`${API_BASE_URL}/doyen/reinitialisation/confirmer`, {
    method: 'POST',
    headers: headersJsonAutorises(),
    body: JSON.stringify({
      utilisateur_id: utilisateurId,
      reinitialisation_id: reinitialisationId,
      code_confirmation: codeConfirmation
    })
  })

  return lireReponseJson(response, 'Erreur lors de la confirmation.')
}


export async function getDiscussionFiche(ficheId) {
  const response = await fetch(`${API_BASE_URL}/doyen/fiches/${ficheId}/discussion`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(response, 'Erreur lors du chargement de la discussion.')
}


export function getUrlDiscussionFichePdf(ficheId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/fiches/${ficheId}/discussion/pdf`)
}


export function getUrlDiscussionFicheTxt(ficheId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/fiches/${ficheId}/discussion/txt`)
}


export async function getEtatNotificationEmail() {
  const response = await fetch(`${API_BASE_URL}/doyen/notifications/email/etat`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    "Erreur lors du chargement de l’état des notifications email."
  )
}

export async function getAnneeUniversitaireActive() {
  const response = await fetch(`${API_BASE_URL}/doyen/annee-universitaire/active`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    "Erreur lors du chargement de l’année universitaire active."
  )
}


export async function getAnneesUniversitaires() {
  const response = await fetch(`${API_BASE_URL}/doyen/annees-universitaires`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    "Erreur lors du chargement des années universitaires."
  )
}

export async function getHistoriqueEtudiantFiche(ficheId) {
  const response = await fetch(`${API_BASE_URL}/doyen/fiches/${ficheId}/historique`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    "Erreur lors du chargement de l’historique étudiant."
  )
}



export async function getTableauBordDoyenAvance() {
  const response = await fetch(`${API_BASE_URL}/doyen/tableau-bord/avance`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    'Erreur lors du chargement du tableau de bord avancé.'
  )
}


export async function getSuiviPromotionDoyen() {
  const response = await fetch(`${API_BASE_URL}/doyen/promotion/suivi`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    'Erreur lors du chargement du suivi de promotion.'
  )
}


export async function importerListeOfficiellePromotion(texteCsv, remplacer = false) {
  const response = await fetch(`${API_BASE_URL}/doyen/promotion/liste-officielle/importer`, {
    method: 'POST',
    headers: headersJsonAutorises(),
    body: JSON.stringify({
      texte_csv: texteCsv,
      remplacer: remplacer
    })
  })

  return lireReponseJson(
    response,
    'Erreur lors de l’import de la liste officielle.'
  )
}


export function getUrlExportSuiviPromotionExcel() {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/promotion/export-excel`)
}


export async function getArchivesAdministratives() {
  const response = await fetch(`${API_BASE_URL}/doyen/archives/administratives`, {
    headers: {
      ...getAuthorizationHeaders()
    }
  })

  return lireReponseJson(
    response,
    'Erreur lors du chargement des archives administratives.'
  )
}


export function getUrlArchiveFicheVisualisation(archiveId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/archives/fiches/${archiveId}/visualiser`)
}


export function getUrlArchiveFicheTelechargement(archiveId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/archives/fiches/${archiveId}/telecharger`)
}


export function getUrlArchiveExportExcelTelechargement(archiveId) {
  return ajouterTokenUrl(`${API_BASE_URL}/doyen/archives/exports/${archiveId}/telecharger`)
}
