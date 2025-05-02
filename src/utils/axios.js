import axios from 'axios';

// Check if env variable exists
const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com';
const port = localStorage.getItem('apiPort') || '5000';
const BASE_URL = `${host}:${port}`;


const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 20 seconds timeout
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

// Intercept any response errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    // If the server replied “419 Session timeout”, flip our reactive flag
    if (error.response?.status === 419) {
      authStatus.sessionExpired = true
    }
    // Always re-throw so your components can still handle it if they want
    return Promise.reject(error)
  }
)

export default apiClient;
