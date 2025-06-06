// src/utils/axios.js
import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/store/auth'
import { authStatus } from '@/utils/authStatus'

console.log('[axios.js] Loaded apiClient setup')

// Dynamic base URL based on current localStorage port
function getBaseURL() {
  const port = localStorage.getItem('apiPort') || '5000'
  const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com'
  const baseURL = `${host}:${port}`
  console.log(`[axios.js] getBaseURL() → ${baseURL}`)
  return baseURL
}

// Create Axios instance
const apiClient = axios.create({
  baseURL: getBaseURL(), // this gets overridden dynamically later anyway
  timeout: 60000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

// REQUEST INTERCEPTOR
apiClient.interceptors.request.use(
  config => {
    const port = localStorage.getItem('apiPort') || '5000'
    const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com'
    config.baseURL = `${host}:${port}`

    if (sessionStorage.getItem('apiLogging') === 'true') {
      const fullUrl = `${config.baseURL}${config.url}`
      console.log(`[INTERCEPTOR API Request] ${config.method?.toUpperCase()} ${fullUrl}`, {
        params: config.params,
        body: config.data,
      })
    }

    const sessionToken = localStorage.getItem('SessionToken')
    if (sessionToken) {
      config.headers['SessionToken'] = sessionToken
    }

    return config
  },
  error => Promise.reject(error)
)

// RESPONSE INTERCEPTOR
apiClient.interceptors.response.use(
  response => {
    if (sessionStorage.getItem('apiLogging') === 'true') {
      console.log(
        `[API Response] ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`,
        response.data
      )
    }
    return response;
  },
  async error => {
    const status = error.response?.status;
    const originalRequest = error.config;

    const isRefreshCall = originalRequest.url?.includes('/Sessions/refresh');
    const authStore = useAuthStore();

    // Prevent infinite loop: don't retry refresh call
    if (status === 419 && !originalRequest._retry && !isRefreshCall) {
      originalRequest._retry = true;

      try {
        const sessionId = authStore.sessionId;
        if (!sessionId) throw new Error('Missing session ID for refresh');

        const { data } = await apiClient.post('/Sessions/refresh', {
          sessionId: sessionId,
        });

        localStorage.setItem('SessionToken', data.SessionToken);
        apiClient.defaults.headers['SessionToken'] = data.SessionToken;
        originalRequest.headers['SessionToken'] = data.SessionToken;

        return apiClient(originalRequest);
      } catch (refreshErr) {
        console.warn('[Interceptor] Refresh failed. Logging out.');
        authStore.logout();
        router.replace({ path: '/' });
        return Promise.reject(refreshErr);
      }
    }

    return Promise.reject(error);
  }
);


export default apiClient
