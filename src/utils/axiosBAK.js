/ src/utils/axios.js
import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/store/auth'
import { authStatus } from '@/utils/authStatus'

console.log('[axios.js] Loaded apiClient setup')

// Determine API base URL
const host = import.meta.env.VITE_API_BASE_HOST
  || 'https://eclipsemobile.wittichen-supply.com'
const port     = localStorage.getItem('apiPort') || '5000'
const BASE_URL = `${host}:${port}`

// Create Axios instance
const apiClient = axios.create({
  // baseURL: BASE_URL,
  baseURL: getBaseURL(),
  timeout: 60000,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})

// This function always fetches the current port value from the store
function getBaseURL() {
  const port = localStorage.getItem('apiPort') || '5000'
  console.log(`Using API base URL: https://eclipsemobile.wittichen-supply.com:${port}`)
  return `https://eclipsemobile.wittichen-supply.com:${port}`
}

// REQUEST interceptor: attach token + log
apiClient.interceptors.request.use(
  config => {
    if (sessionStorage.getItem('apiLogging') === 'true') {
      console.log(
        `[API Request] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`,
        { params: config.params, body: config.data }
      )
    }
    const sessionToken = localStorage.getItem('SessionToken')
    if (sessionToken) {
      config.headers['SessionToken'] = sessionToken
      const port = localStorage.getItem('apiPort') || '5000'
      const host = import.meta.env.VITE_API_BASE_HOST || 'https://eclipsemobile.wittichen-supply.com'
      config.baseURL = `${host}:${port}`
      // ✅ Add this to see full URL being called
    const fullUrl = `${config.baseURL}${config.url}`
    console.log('[axios] Full request URL:', fullUrl)
    }
    return config
  },
  error => Promise.reject(error)
)

// RESPONSE interceptor: log + handle 419
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
    const status          = error.response?.status
    const originalRequest = error.config

    // retry once on 419
    if (status === 419 && !originalRequest._retry) {
      originalRequest._retry = true
      const authStore = useAuthStore()
      try {
        const { data } = await apiClient.post('/Sessions/refresh', {
          sessionId: authStore.sessionId,
        })
        localStorage.setItem('SessionToken', data.SessionToken)
        originalRequest.headers['SessionToken'] = data.SessionToken
        return apiClient(originalRequest)
      } catch (refreshErr) {
        authStore.logout()
        router.replace({ path: '/' })
      }
    }

    // **Here’s the missing closing brace for the error callback**  
    return Promise.reject(error)
  }  // ← **THIS brace closes the `async error => { … }`**
)    // ← closes interceptors.response.use(

export default apiClient
