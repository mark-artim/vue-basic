import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

console.log('[axios.js] Loaded Axios instance')

// Create Axios instance 1234
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3001',
  timeout: 60000,
  headers: {
    Accept: 'application/json',
    // 'Content-Type': 'application/json',
  },
})

// ✅ REQUEST INTERCEPTOR: Add JWT to headers
apiClient.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    if (authStore.apiLogging) {
      console.log('[API] Request:', config)
    }
    // const jwt = authStore.jwt
    const jwt = localStorage.getItem('jwt') || sessionStorage.getItem('jwt')
    // console.log('[Axios] Request Interceptor: JWT from store:', jwt)
    const logging = sessionStorage.getItem('apiLogging') === 'true';

    
    if (jwt) {
      config.headers['Authorization'] = `Bearer ${jwt}`;
      if (authStore.apiLogging) {
            console.log('[Axios] Request Interceptor: Adding JWT to headers, authToken: ', jwt.substring(0, 5) + '...')
      } else if (logging) {
        console.log('[Axios] Request Interceptor: JWT is present, but not logging token value');
      }

      if (!jwt) {
        console.warn('[Axios] No JWT found in store, request may fail')  
      }
      // TEMPORARILY Turn on this log all the time
      console.log(`[axios API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
        headers: config.headers,
      })

    if (authStore.apiLogging) {
        console.log(`[axios API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      })
    } 
    }

    return config
  },
  error => Promise.reject(error)
)

// ✅ RESPONSE INTERCEPTOR: Log or handle 401
apiClient.interceptors.response.use(
  response => {
    if (sessionStorage.getItem('apiLogging') === 'true') {
      console.log(
        `[API Response] ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`,
        response.data
      )
    }
    return response
  },
  async error => {
    const status = error.response?.status

    if (status === 401) {
      console.warn('[Axios] Unauthorized. Redirecting to login...')
      router.replace({ path: '/' })
    }

    return Promise.reject(error)
  }
)

export default apiClient
