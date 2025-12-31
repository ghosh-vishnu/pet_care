import { createContext, useContext, useState, useEffect } from 'react'
import { login as loginAPI, register as registerAPI } from '../services/api'
import { setAuthToken, getAuthToken, removeAuthToken, setUserId, getUserId, removeUserId } from '../config'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getAuthToken()
    const userId = getUserId()
    
    if (token && userId) {
      setUser({ id: parseInt(userId) })
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      const response = await loginAPI(email, password)
      setAuthToken(response.access_token)
      setUserId(response.user_id)
      const userObj = { id: response.user_id }
      setUser(userObj)
      return { user: userObj }
    } catch (error) {
      throw error
    }
  }

  const signup = async (email, password) => {
    try {
      const response = await registerAPI(email, password)
      setAuthToken(response.access_token)
      setUserId(response.user_id)
      const userObj = { id: response.user_id }
      setUser(userObj)
      return { user: userObj }
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    removeAuthToken()
    removeUserId()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

