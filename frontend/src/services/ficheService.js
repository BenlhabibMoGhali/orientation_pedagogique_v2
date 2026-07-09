export async function genererFicheIntelligente(testOrientationId) {
  const response = await fetch(`/api/fiches/generer/${testOrientationId}`, {
    method: 'POST'
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Erreur lors de la génération de la fiche.')
  }

  return data
}


export async function getFicheParTest(testOrientationId) {
  const response = await fetch(`/api/fiches/test-orientation/${testOrientationId}`)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.message || 'Erreur lors du chargement de la fiche.')
  }

  return data.fiche
}