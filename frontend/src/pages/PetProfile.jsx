import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { savePetProfile, checkPetProfileStatus } from '../services/api'
import { getPetId, setPetId, getUserId } from '../config'
import './Login.css'

function PetProfile() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userId, setUserIdState] = useState(null)
  const [petId, setPetIdState] = useState('your_dog_buddy_id')
  
  // Form fields
  const [formData, setFormData] = useState({
    petName: '',
    breed: '',
    weight: '',
    age: '',
    gender: '',
    season: '',
    activityLevel: '',
    behaviorNotes: '',
    medicalConditions: [],
    goals: []
  })
  
  const [medicalConditionInput, setMedicalConditionInput] = useState('')
  const [goalInput, setGoalInput] = useState('')

  useEffect(() => {
    // Get userId from location state or auth context
    const userIdFromState = location.state?.userId
    const userIdFromAuth = user?.id
    const userIdFromStorage = getUserId()
    
    const currentUserId = userIdFromState || userIdFromAuth || userIdFromStorage
    if (currentUserId) {
      setUserIdState(parseInt(currentUserId))
    }
    
    // Get petId from storage or use default
    const currentPetId = getPetId()
    setPetIdState(currentPetId)
    
    // Check if profile already exists and load it
    if (currentUserId && currentPetId) {
      loadExistingProfile(currentUserId, currentPetId)
    }
  }, [location.state, user])

  const loadExistingProfile = async (userId, petId) => {
    try {
      const response = await checkPetProfileStatus(userId, petId)
      if (response.status === 'EXISTS' && response.profile_data) {
        const profile = response.profile_data
        setFormData({
          petName: profile.petName || '',
          breed: profile.breed || '',
          weight: profile.weight || '',
          age: profile.age || '',
          gender: profile.gender || '',
          season: profile.season || '',
          activityLevel: profile.activityLevel || '',
          behaviorNotes: profile.behaviorNotes || '',
          medicalConditions: profile.medicalConditions || [],
          goals: profile.goals || []
        })
      }
    } catch (err) {
      // Profile doesn't exist yet, that's fine
      console.log('No existing profile found')
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const addMedicalCondition = () => {
    if (medicalConditionInput.trim()) {
      setFormData(prev => ({
        ...prev,
        medicalConditions: [...prev.medicalConditions, medicalConditionInput.trim()]
      }))
      setMedicalConditionInput('')
    }
  }

  const removeMedicalCondition = (index) => {
    setFormData(prev => ({
      ...prev,
      medicalConditions: prev.medicalConditions.filter((_, i) => i !== index)
    }))
  }

  const addGoal = () => {
    if (goalInput.trim()) {
      setFormData(prev => ({
        ...prev,
        goals: [...prev.goals, goalInput.trim()]
      }))
      setGoalInput('')
    }
  }

  const removeGoal = (index) => {
    setFormData(prev => ({
      ...prev,
      goals: prev.goals.filter((_, i) => i !== index)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    if (!userId) {
      setError('User ID not found. Please try logging in again.')
      return
    }

    // Validate required fields
    if (!formData.petName || !formData.breed || !formData.weight || !formData.age || 
        !formData.gender || !formData.season || !formData.activityLevel) {
      setError('Please fill in all required fields')
      return
    }

    setLoading(true)

    try {
      const response = await savePetProfile(userId, petId, formData)
      // Update pet_id in localStorage if it was changed by backend
      if (response.pet_id && response.pet_id !== petId) {
        setPetId(response.pet_id)
      }
      // Navigate to dashboard after successful save
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box" style={{ maxWidth: '600px' }}>
        <h1>🐾 Dog Health AI</h1>
        <h2>Pet Profile</h2>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Please provide your pet's information to get started
        </p>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Pet Name *</label>
            <input
              type="text"
              name="petName"
              value={formData.petName}
              onChange={handleInputChange}
              required
              placeholder="Enter your pet's name"
            />
          </div>

          <div className="form-group">
            <label>Breed *</label>
            <input
              type="text"
              name="breed"
              value={formData.breed}
              onChange={handleInputChange}
              required
              placeholder="e.g., Golden Retriever, German Shepherd"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="form-group">
              <label>Weight *</label>
              <input
                type="text"
                name="weight"
                value={formData.weight}
                onChange={handleInputChange}
                required
                placeholder="e.g., 25 kg"
              />
            </div>

            <div className="form-group">
              <label>Age *</label>
              <input
                type="text"
                name="age"
                value={formData.age}
                onChange={handleInputChange}
                required
                placeholder="e.g., 3 years"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="form-group">
              <label>Gender *</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1em'
                }}
              >
                <option value="">Select gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Season *</label>
              <select
                name="season"
                value={formData.season}
                onChange={handleInputChange}
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1em'
                }}
              >
                <option value="">Select season</option>
                <option value="Spring">Spring</option>
                <option value="Summer">Summer</option>
                <option value="Autumn">Autumn</option>
                <option value="Winter">Winter</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Activity Level *</label>
            <select
              name="activityLevel"
              value={formData.activityLevel}
              onChange={handleInputChange}
              required
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1em'
              }}
            >
              <option value="">Select activity level</option>
              <option value="Low">Low</option>
              <option value="Moderate">Moderate</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>

          <div className="form-group">
            <label>Behavior Notes</label>
            <textarea
              name="behaviorNotes"
              value={formData.behaviorNotes}
              onChange={handleInputChange}
              placeholder="Describe your pet's behavior, habits, etc."
              rows="4"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1em',
                fontFamily: 'inherit',
                resize: 'vertical'
              }}
            />
          </div>

          <div className="form-group">
            <label>Medical Conditions</label>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
              <input
                type="text"
                value={medicalConditionInput}
                onChange={(e) => setMedicalConditionInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addMedicalCondition()
                  }
                }}
                placeholder="Add a medical condition"
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1em'
                }}
              />
              <button
                type="button"
                onClick={addMedicalCondition}
                style={{
                  padding: '12px 20px',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '1em'
                }}
              >
                Add
              </button>
            </div>
            {formData.medicalConditions.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {formData.medicalConditions.map((condition, index) => (
                  <span
                    key={index}
                    style={{
                      background: '#f0f0f0',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '0.9em',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    {condition}
                    <button
                      type="button"
                      onClick={() => removeMedicalCondition(index)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '1.2em',
                        color: '#666'
                      }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Goals</label>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
              <input
                type="text"
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addGoal()
                  }
                }}
                placeholder="Add a goal (e.g., Weight loss, Muscle gain)"
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  fontSize: '1em'
                }}
              />
              <button
                type="button"
                onClick={addGoal}
                style={{
                  padding: '12px 20px',
                  background: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '1em'
                }}
              >
                Add
              </button>
            </div>
            {formData.goals.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {formData.goals.map((goal, index) => (
                  <span
                    key={index}
                    style={{
                      background: '#f0f0f0',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '0.9em',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    {goal}
                    <button
                      type="button"
                      onClick={() => removeGoal(index)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '1.2em',
                        color: '#666'
                      }}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default PetProfile
