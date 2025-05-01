import axios from 'axios';

// const BASE_URL = 'https://eclipsemobile.wittichen-supply.com:5003';
const storedPort = localStorage.getItem('apiPort') || '5000'; // Default to 5000 if not set
const BASE_URL = `https:eclipsemobile.wittichen-supply.com:${storedPort}`;

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
