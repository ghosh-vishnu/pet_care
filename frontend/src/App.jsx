import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import PetProfile from './pages/PetProfile'
import PetProfileStepTwo from './pages/PetProfileStepTwo'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import NutrientCalculator from './pages/NutrientCalculator'
import ProfileChoice from './pages/ProfileChoice'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading...</div>
  }
  
  return user ? children : <Navigate to="/login" />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
      <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/pet-profile" element={<PrivateRoute><PetProfile /></PrivateRoute>} />
      <Route path="/pet-profile-step-two" element={<PrivateRoute><PetProfileStepTwo /></PrivateRoute>} />
      <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
      <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
      <Route path="/nutrient-calculator" element={<PrivateRoute><NutrientCalculator /></PrivateRoute>} />
      <Route path="/profile-choice" element={<PrivateRoute><ProfileChoice /></PrivateRoute>} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

