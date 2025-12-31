// api.js - API Service

import axios from 'axios'
import { API_BASE_URL, getAuthToken, removeAuthToken, removeUserId } from '../config'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeAuthToken()
      removeUserId()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth APIs
export const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password })
  return response.data
}

export const register = async (email, password) => {
  const response = await api.post('/auth/register', { email, password })
  return response.data
}

// Pet Profile APIs
export const checkPetProfileStatus = async (userId, petId) => {
  const response = await api.get(`/user/${userId}/pet/${petId}/profile/status`)
  return response.data
}

export const savePetProfile = async (userId, petId, profileData) => {
  const response = await api.post(`/user/${userId}/pet/${petId}/profile`, profileData)
  return response.data
}

// Chat APIs
export const sendChatMessage = async (userId, petId, question, petProfile, location = null) => {
  const response = await api.post(`/user/${userId}/pet/${petId}/chat`, {
    question,
    pet_profile: petProfile,
    location
  })
  return response.data
}

export const getChatMessages = async (userId, petId) => {
  const response = await api.get(`/user/${userId}/pet/${petId}/chat/messages`)
  return response.data
}

// Upload APIs
export const uploadImage = async (userId, petId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post(`/user/${userId}/pet/${petId}/upload/analyze`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const uploadDocument = async (userId, petId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post(`/user/${userId}/pet/${petId}/upload/analyze_document`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// Nutrition API
export const calculateNutrition = async (userId, petId, profileData) => {
  const response = await api.post(`/user/${userId}/pet/${petId}/nutrition/calculate`, profileData)
  return response.data
}

// Reports API
export const getReports = async (userId, petId) => {
  const response = await api.get(`/user/${userId}/pet/${petId}/reports`)
  return response.data
}

