import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axiosPublic from '@/utils/axiosPublic'  // used only for unauthenticated login

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const jwt = ref('')
  const userName = ref('')
  const userType = ref('')
  const port = ref(localStorage.getItem('apiPort') || '5000')  // optional, only for UI display
  const userId = ref('')


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

      // Save to state
      isAuthenticated.value = true
      jwt.value = token
      userName.value = decoded.email || ''
      userType.value = decoded.userType || ''
      // port.value = localStorage.getItem('apiPort') || '5000'
      port.value = decoded.lastPort || '5000'  // Use lastPort from token if available

      // Save to localStorage
      localStorage.setItem('authToken', token)
      // localStorage.setItem('jwt', token)
      localStorage.setItem('userName', userName.value)
      localStorage.setItem('userType', userType.value)
      localStorage.setItem('apiPort', port.value)

      return { isAdmin: decoded.userType === 'admin' }
    } catch (err) {
      console.error('[authStore] Login failed:', err)
      throw err
    }
  }

  function logout() {
    isAuthenticated.value = false
    jwt.value = ''
    userName.value = ''
    userType.value = ''

    localStorage.removeItem('authToken')
    // localStorage.removeItem('jwt')
    localStorage.removeItem('userName')
    localStorage.removeItem('userType')
    localStorage.removeItem('apiPort')
  }

  function hydrate() {
    const token = localStorage.getItem('jwt')
    const user = localStorage.getItem('userName')
    const type = localStorage.getItem('userType')
    const savedPort = localStorage.getItem('apiPort') || '5000'

    if (token && user) {
      isAuthenticated.value = true
      jwt.value = token
      userName.value = user
      userType.value = type || ''
      port.value = savedPort
      console.log('[authStore] Hydrated from localStorage')
    }
  }

  return {
    isAuthenticated,
    jwt,
    userName,
    userType,
    userId,  
    port,
    portLabel,
    login,
    logout,
    hydrate,
  }
})
