import { useEffect, useState } from 'react'
import LoginPage from './pages/LoginPage'
import EtudiantPage from './pages/EtudiantPage'
import DoyenPage from './pages/DoyenPage'
import './styles/LoginPage.css'

function App() {
  const [utilisateur, setUtilisateur] = useState(null)

  useEffect(() => {
    const utilisateurSauvegarde = localStorage.getItem('utilisateur')

    if (utilisateurSauvegarde) {
      setUtilisateur(JSON.parse(utilisateurSauvegarde))
    }
  }, [])

  const handleLogin = (utilisateurConnecte) => {
    setUtilisateur(utilisateurConnecte)
  }

  const handleLogout = () => {
    localStorage.removeItem('utilisateur')
    setUtilisateur(null)
  }

  if (!utilisateur) {
    return <LoginPage onLogin={handleLogin} />
  }

  if (utilisateur.role === 'etudiant') {
    return (
      <EtudiantPage
        utilisateur={utilisateur}
        onLogout={handleLogout}
      />
    )
  }

  if (utilisateur.role === 'doyen') {
    return (
      <DoyenPage
        utilisateur={utilisateur}
        onLogout={handleLogout}
      />
    )
  }

  return (
    <div>
      <h1>Rôle inconnu</h1>
      <button onClick={handleLogout}>Se déconnecter</button>
    </div>
  )
}

export default App