import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axiosPublic from '@/utils/axiosPublic' // unauthenticated

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const jwt = ref('')
  const userName = ref('')
  const userType = ref('')
  const port = ref('5000') // start with a default
  const userId = ref('')
  const erpUserName = ref('')

  const apiLogging = ref(sessionStorage.getItem('apiLogging') === 'true')
  function setApiLogging(enabled) {
  apiLogging.value = enabled
  sessionStorage.setItem('apiLogging', String(enabled))
}


  const portLabel = computed(() => {
    const labels = {
      '5000': 'Production',
      '5001': 'Train',
      '5002': 'ECOM',
      '5003': 'CONV1',
    }
    return labels[port.value] || 'Unknown'
  })

  function parseJwt(token) {
    try {
      return JSON.parse(atob(token.split('.')[1]))
    } catch {
      return {}
    }
  }

  async function login(email, password) {
    try {
      const response = await axiosPublic.post('/auth/login', { email, password })
      const token = response.data.token
      const decoded = parseJwt(token)

      console.log('[authStore] Decoded token:', decoded)

      // Set state
      isAuthenticated.value = true
      jwt.value = token
      userId.value = decoded.userId || ''
      userName.value = decoded.email || ''
      userType.value = decoded.userType || ''
      port.value = decoded.lastPort || '5000'
      erpUserName.value = (decoded.erpUserName || decoded.erpLogin || '').toUpperCase()

      return { isAdmin: decoded.userType === 'admin' }
    } catch (err) {
      console.error('[authStore] Login failed:', err)
      throw err
    }
  }

  function logout() {
    isAuthenticated.value = false
    jwt.value = ''
    userId.value = ''
    userName.value = ''
    userType.value = ''
    port.value = '5000'
  }

  return {
    isAuthenticated,
    jwt,
    userId,
    userName,
    userType,
    port,
    portLabel,
    login,
    logout,
    apiLogging,
    setApiLogging,
    erpUserName,
  }
})
