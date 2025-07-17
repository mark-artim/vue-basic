<template>
  <v-container class="pa-4">
    <v-card class="pa-6 elevation-4">
      <h1>{{ title }}</h1>

      <div class="form-group">
        <label for="port">Select the port you'd like to use for API calls.</label>
        <select
          id="port"
          v-model="selectedPort"
          @change="savePort"
          :disabled="allowedPorts.length === 1"
        >
          <option disabled value="">-- Select a port --</option>
          <option v-for="port in allowedPorts" :key="port.value" :value="port.value">
            {{ port.value }} - {{ port.label }}
          </option>
        </select>
      </div>

      <v-checkbox
        v-model="authStore.apiLogging"
        label="API call logging enabled"
        hide-details
        @change="authStore.setApiLogging(authStore.apiLogging)"
      />
      <div>Logging: {{ authStore.apiLogging ? 'ON' : 'OFF' }}</div>

      <h3 v-if="logoutMessage" class="logout-warning">
        {{ logoutMessage }} Logging out in {{ countdown }} seconds...
      </h3>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'

const authStore = useAuthStore()
const router = useRouter()

// Extract allowed ports from JWT
const allowedPorts = computed(() => {
  const portList = authStore.decoded?.companyId?.apiPorts || []
  const labels = {
    '5000': 'Heritage Production',
    '5001': 'Heritage Train',
    '5002': 'Heritage ECOM',
    '5003': 'Heritage CONV1'
  }
  return portList.map(port => ({
    value: port,
    label: labels[port] || `Port ${port}`
  }))
})

// Initial selected port
const selectedPort = ref(localStorage.getItem('apiPort') || allowedPorts.value[0]?.value || '')

const logoutMessage = ref('')
const countdown = ref(5)
let countdownTimer = null

const title = computed(() => {
  return authStore.companyCode === 'heritage'
    ? 'Welcome to Heritage ERP Portal'
    : 'Welcome to emp54'
})

const selectedPortLabel = computed(() => {
  const match = allowedPorts.value.find(p => p.value === selectedPort.value)
  return match ? match.label : ''
})

async function savePort() {
  try {
    // const userId = authStore.userId
    const userId = authStore.userId;
    const port = selectedPort.value
    console.log('Saving port:', port, 'for user:', userId)

    await apiClient.put(`/admin/users/${userId}/port`, { port })

    logoutMessage.value = 'Port changed. Please log in again.'
    countdown.value = 5

    if (countdownTimer) clearInterval(countdownTimer)

    countdownTimer = setInterval(() => {
      if (countdown.value <= 1) {
        clearInterval(countdownTimer)
        logoutNow()
      } else {
        countdown.value--
      }
    }, 1000)
  } catch (err) {
    console.error('Failed to save port:', err.message, err.response?.data || err)
    alert('Could not save your selected port. Please try again.')
  }
}


function logoutNow() {
  console.log('Logging out...')
  authStore.logout()
  router.push('/')
}

onBeforeUnmount(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>


<style scoped>
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  min-height: 100vh;
  background-color: black;
  font-family: 'Segoe UI', sans-serif;
}

.card {
  color: orange;
  background-color: white;
  padding: 2rem 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.card h1 {
  margin-bottom: 0.5rem;
  font-size: 1.75rem;
  color: #333;
}

.card p {
  margin-bottom: 1.5rem;
  color: #666;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
  color: #007bff;
}

label {
  font-weight: 500;
  color: #555;
  color: white;

}

select {
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 1rem;
  color: #007bff
}

.current-port {
  margin-top: 1.5rem;
  font-size: 1rem;
  color: #007bff;
}

.logout-warning {
  color: #dc3545;
  font-weight: bold;
  margin-top: 1rem;
}
</style>
