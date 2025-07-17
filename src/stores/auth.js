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
  const companyCode = ref('')
  const decoded = ref(null)

  const apiLogging = ref(localStorage.getItem('apiLogging') === 'true')

  function setApiLogging(enabled) {
    apiLogging.value = enabled
    localStorage.setItem('apiLogging', String(enabled))
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

      decoded.value = parseJwt(token) // ✅ set the store-level ref
      console.log('[authStore] Decoded token:', decoded.value)

      // console.log('[authStore] Decoded token:', decoded)

      // Set state
      isAuthenticated.value = true
      jwt.value = token
      localStorage.setItem('jwt', token)
      userId.value = decoded.value.userId || ''
      console.log('[authStore] User ID:', userId.value)
      userName.value = decoded.email || ''
      console.log('[authStore] User Name:', userName.value)
      userType.value = decoded.value.userType || ''
      console.log('[authStore] User Type:', userType.value)
      port.value = decoded.value.lastPort || '5000'
      console.log('[authStore] Port:', port.value)
      localStorage.setItem('apiPort', port.value)
      erpUserName.value = (decoded.value.erpUserName || decoded.erpLogin || '').toUpperCase()
      console.log('[authStore] ERP User Name:', erpUserName.value)
      companyCode.value = decoded.value.companyCode || ''
      console.log('[authStore] Company Code:', companyCode.value)

      return { isAdmin: decoded.value.userType === 'admin' }
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
    erpUserName.value = ''
    companyCode.value = ''
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
    companyCode,
    decoded,
  }
})
