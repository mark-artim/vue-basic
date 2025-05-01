import axios from 'axios';

// Create an Axios instance
const storedPort = localStorage.getItem('apiPort') || '5000'; // Default to 5000 if not set
const BASE_URL = `https:eclipsemobile.wittichen-supply.com:${storedPort}`;

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 20 seconds timeout
  // baseURL: 'https://eclipsemobile.wittichen-supply.com:5003',
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

// Add an interceptor to include the session token
apiClient.interceptors.request.use((config) => {
  const sessionToken = localStorage.getItem('SessionToken');
  if (sessionToken) {
    config.headers['SessionToken'] = sessionToken;
  }
  return config;
}, (error) => Promise.reject(error));

export default apiClient;
