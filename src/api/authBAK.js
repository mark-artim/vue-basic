// import apiClient from 'axios';
import apiClient from '@/utils/axios';

// Check if env variable exists
const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com';
const port = localStorage.getItem('apiPort') || '5000';
const BASE_URL = `${host}:${port}`;


export const createSession = async (username, password) => {
  try {
    console.log('Creating session: ', BASE_URL)
    const response = await apiClient.post(`${BASE_URL}/Sessions`, {
      username,
      password,
    });
    console.log('Session created: ', response.data);
    return response.data;
  } catch (error) {
    throw new Error('Invalid username or password');
  }
};

export const destroySession = async (sessionId, sessionToken) => {
  try {
    await apiClient.delete(`${BASE_URL}/Sessions/${sessionId}`, {
      headers: { sessionToken },
    });
  } catch (error) {
    console.error('Error logging out:', error);
  }
};
