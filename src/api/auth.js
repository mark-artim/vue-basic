import axios from 'axios';

// const storedPort = localStorage.getItem('apiPort') || '5000'; // Default to 5000 if not set
// const BASE_URL = `https:eclipsemobile.wittichen-supply.com:${storedPort}`;

// Check if env variable exists
const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com';
const port = localStorage.getItem('apiPort') || '5000';
const BASE_URL = `${host}:${port}`;


export const createSession = async (username, password) => {
  try {
    console.log('Creating session: ', BASE_URL)
    const response = await axios.post(`${BASE_URL}/Sessions`, {
      username,
      password,
    });
    return response.data;
  } catch (error) {
    throw new Error('Invalid username or password');
  }
};

export const destroySession = async (sessionId, sessionToken) => {
  try {
    await axios.delete(`${BASE_URL}/Sessions/${sessionId}`, {
      headers: { sessionToken },
    });
  } catch (error) {
    console.error('Error logging out:', error);
  }
};
