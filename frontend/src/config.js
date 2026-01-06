// config.js - API Configuration

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

export const setAuthToken = (token) => {
  localStorage.setItem('auth_token', token);
};

export const removeAuthToken = () => {
  localStorage.removeItem('auth_token');
};

export const getUserId = () => {
  return localStorage.getItem('user_id');
};

export const setUserId = (userId) => {
  localStorage.setItem('user_id', userId);
};

export const removeUserId = () => {
  localStorage.removeItem('user_id');
};

export const getPetId = () => {
  return localStorage.getItem('pet_id') || 'your_dog_buddy_id';
};

export const setPetId = (petId) => {
  localStorage.setItem('pet_id', petId);
};





