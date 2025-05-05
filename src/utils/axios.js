// src/utils/axios.js
import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/store/auth'
import { authStatus } from '@/utils/authStatus'

// Determine API base URL
const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com'
const port = localStorage.getItem('apiPort') || '5000'
const BASE_URL = `${host}:${port}`

// Create Axios instance
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

// Attach session token to every request
apiClient.interceptors.request.use(
  config => {
    const sessionToken = localStorage.getItem('SessionToken')
    if (sessionToken) {
      config.headers['SessionToken'] = sessionToken
    }
    return config
  },
  error => Promise.reject(error)
)

// Handle responses and catch 419 Session Timeout
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const status = error.response?.status;
    const originalRequest = error.config;

    // Only handle 419 once per request
    if (status === 419 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();

      // Try to refresh
      try {
        const { data } = await apiClient.post('/Sessions/refresh', {
          sessionId: authStore.sessionId,
        });
        // Persist new token
        localStorage.setItem('SessionToken', data.SessionToken);

        // Update headers and re-fire the original request
        originalRequest.headers['SessionToken'] = data.SessionToken;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        // Refresh failed → log out + redirect once
        authStore.logout();
        router.replace({ path: '/' });
        // Don’t alert in a loop; you could show a toast here instead if you like
      }
    }

    // For all other errors (or if _retry was already true), reject
    return Promise.reject(error);
  }
);


export default apiClient
