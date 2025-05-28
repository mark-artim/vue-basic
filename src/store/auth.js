// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const sessionToken = ref('')
  const sessionId = ref('')
  const userName = ref('')
  const port = ref(localStorage.getItem('apiPort') || '5000')

  const portLabel = computed(() => {
    const labels = {
      '5000': 'Production',
      '5001': 'Train',
      '5002': 'ECOM',
      '5003': 'CONV1',
    }
    return labels[port.value] || 'Unknown'
  })

  function login(token, id, user) {
    isAuthenticated.value = true
    sessionToken.value = token
    sessionId.value = id
    userName.value = user

    localStorage.setItem('SessionToken', token)
    localStorage.setItem('SessionId', id)
    localStorage.setItem('userName', user)
    localStorage.setItem('apiPort', port.value)

    console.log('[auth.js] Login:', { token, id, user })
  }

  function logout() {
    isAuthenticated.value = false
    sessionToken.value = ''
    sessionId.value = ''
    userName.value = ''

    localStorage.removeItem('SessionToken')
    localStorage.removeItem('SessionId')
    localStorage.removeItem('userName')
  }

  function hydrate() {
    const token = localStorage.getItem('SessionToken')
    const id = localStorage.getItem('SessionId')
    const user = localStorage.getItem('userName')
    const savedPort = localStorage.getItem('apiPort') || '5000'

    if (token && id) {
      isAuthenticated.value = true
      sessionToken.value = token
      sessionId.value = id
      userName.value = user || ''
      port.value = savedPort
      console.log('[auth.js] Hydrated from localStorage')
    }
  }

  return {
    isAuthenticated,
    sessionToken,
    sessionId,
    userName,
    port,
    portLabel,
    login,
    logout,
    hydrate
  }
})
