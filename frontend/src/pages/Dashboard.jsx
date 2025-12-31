import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { checkPetProfileStatus } from '../services/api'
import { getPetId } from '../config'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [petProfile, setPetProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadProfile = async () => {
      if (!user?.id) {
        setLoading(false)
        return
      }

      try {
        const petId = getPetId()
        const response = await checkPetProfileStatus(user.id, petId)
        
        if (response.status === 'EXISTS' && response.profile_data) {
          setPetProfile(response.profile_data)
        } else {
          setError('Pet profile not found. Please complete your pet profile.')
        }
      } catch (err) {
        setError('Failed to load profile data.')
        console.error('Dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, [user])

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-content">
          <div className="loading-spinner">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-content">
        <h1 className="dashboard-title">📊 Pet Summary</h1>

        {error && (
          <div className="error-message">
            {error}
            <button 
              className="btn-link" 
              onClick={() => navigate('/pet-profile', { state: { userId: user?.id } })}
            >
              Complete Profile
            </button>
          </div>
        )}

        {petProfile && (
          <div className="dashboard-grid">
            <div className="dashboard-card profile-card">
              <h2>🐾 {petProfile.petName || 'Pet'}'s Profile</h2>
              <div className="profile-details">
                <div className="detail-row">
                  <span className="detail-label">Breed:</span>
                  <span className="detail-value">{petProfile.breed || 'Not specified'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Age:</span>
                  <span className="detail-value">{petProfile.age || 'Not specified'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Weight:</span>
                  <span className="detail-value">{petProfile.weight || 'Not specified'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Gender:</span>
                  <span className="detail-value">{petProfile.gender || 'Not specified'}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Activity Level:</span>
                  <span className="detail-value">{petProfile.activityLevel || 'Not specified'}</span>
                </div>
                {petProfile.medicalConditions && petProfile.medicalConditions.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Medical Conditions:</span>
                    <span className="detail-value">{petProfile.medicalConditions.join(', ')}</span>
                  </div>
                )}
                {petProfile.goals && petProfile.goals.length > 0 && (
                  <div className="detail-row">
                    <span className="detail-label">Goals:</span>
                    <span className="detail-value">{petProfile.goals.join(', ')}</span>
                  </div>
                )}
              </div>
              <button 
                className="btn-edit"
                onClick={() => navigate('/pet-profile', { state: { userId: user?.id } })}
              >
                Edit Profile
              </button>
            </div>

            <div className="dashboard-card">
              <h2>📈 Quick Actions</h2>
              <div className="action-buttons">
                <button className="action-btn" onClick={() => navigate('/chat')}>
                  💬 Start Chat
                </button>
                <button className="action-btn" onClick={() => navigate('/reports')}>
                  📄 View Reports
                </button>
                <button className="action-btn" onClick={() => navigate('/nutrient-calculator')}>
                  🥗 Calculate Nutrition
                </button>
              </div>
            </div>
          </div>
        )}

        {!petProfile && !error && (
          <div className="empty-state">
            <p>No profile data available.</p>
            <button 
              className="btn-primary"
              onClick={() => navigate('/pet-profile', { state: { userId: user?.id } })}
            >
              Create Pet Profile
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
