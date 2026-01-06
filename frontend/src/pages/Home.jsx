import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Home.css'

function Home() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="home-container">
      <div className="home-header">
        <h1>🐾 Dog Health AI</h1>
        <button onClick={handleLogout} className="btn-logout">Logout</button>
      </div>
      <div className="home-grid">
        <div className="home-card" onClick={() => navigate('/chat')}>
          <div className="card-icon">💬</div>
          <h2>Chat</h2>
          <p>Ask questions about your dog's health</p>
        </div>
        <div className="home-card" onClick={() => navigate('/dashboard')}>
          <div className="card-icon">📊</div>
          <h2>Dashboard</h2>
          <p>View your pet's profile and summary</p>
        </div>
        <div className="home-card" onClick={() => navigate('/reports')}>
          <div className="card-icon">📄</div>
          <h2>Reports</h2>
          <p>View health reports and analysis</p>
        </div>
        <div className="home-card" onClick={() => navigate('/nutrient-calculator')}>
          <div className="card-icon">🥗</div>
          <h2>Nutrition</h2>
          <p>Calculate nutritional requirements</p>
        </div>
      </div>
    </div>
  )
}

export default Home





