<template>
  <v-container class="pa-4">
    <v-card class="pa-6 elevation-8" color="#0a0f1c">
      <div class="d-flex align-center mb-4">
        <h1 class="flex-grow-1 text-white">{{ title }}</h1>
        <v-btn
          icon
          variant="outlined"
          size="small"
          @click="showSettings = !showSettings"
        >
          <v-icon>{{ showSettings ? 'mdi-cog' : 'mdi-cog-outline' }}</v-icon>
        </v-btn>
      </div>

      <!-- User Products Section -->
      <v-card v-if="authorizedProducts.length > 0" class="mb-4" variant="outlined">
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2" color="primary">mdi-package-variant</v-icon>
          Authorized Products
        </v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-3">
            <v-chip
              v-for="product in authorizedProducts"
              :key="product.code"
              color="primary"
              variant="elevated"
              size="large"
              class="text-h6 pa-4"
              style="height: auto; min-height: 48px;"
            >
              <v-icon start>mdi-package-variant</v-icon>
              <div>
                <div class="font-weight-bold">{{ product.name }}</div>
                <div v-if="product.description" class="text-caption">{{ product.description }}</div>
              </div>
            </v-chip>
          </div>
        </v-card-text>
      </v-card>

      <!-- Collapsible Settings Section -->
      <v-expand-transition>
        <v-card v-if="showSettings" class="mb-4" variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="warning">mdi-cog</v-icon>
            System Settings
          </v-card-title>
          <v-card-text>
            <div class="mb-4">
              <v-select
                v-model="selectedPort"
                :items="allowedPorts"
                item-title="label"
                item-value="value"
                label="API Port"
                hint="Select the port for API calls"
                persistent-hint
                :disabled="allowedPorts.length === 1"
                @update:model-value="savePort"
                variant="outlined"
                density="compact"
              />
            </div>

            <div class="d-flex align-center justify-space-between">
              <v-switch
                v-model="authStore.apiLogging"
                label="API Call Logging"
                color="primary"
                hide-details
                @change="authStore.setApiLogging(authStore.apiLogging)"
              />
              <v-chip
                :color="authStore.apiLogging ? 'success' : 'error'"
                size="small"
                variant="flat"
              >
                {{ authStore.apiLogging ? 'ON' : 'OFF' }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>
      </v-expand-transition>

      <!-- Logout Warning -->
      <v-alert
        v-if="logoutMessage"
        type="warning"
        variant="outlined"
        class="mt-4"
      >
        <div class="d-flex align-center">
          <v-icon class="me-2">mdi-logout</v-icon>
          <div>
            <div class="font-weight-bold">{{ logoutMessage }}</div>
            <div class="text-caption">Logging out in {{ countdown }} seconds...</div>
          </div>
        </div>
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'

const authStore = useAuthStore()
const router = useRouter()

// Settings toggle state
const showSettings = ref(false)

// Product data state
const productDetails = ref([])

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

// Extract authorized products using MongoDB data
const authorizedProducts = computed(() => {
  return productDetails.value
})

// Load product details from MongoDB
const loadProductDetails = async () => {
  try {
    const userProductCodes = authStore.decoded?.products || []
    console.log('Loading product details for user codes:', userProductCodes)
    
    // Get all products from MongoDB
    const response = await apiClient.get('/products')
    const allProducts = response.data
    console.log('All products from MongoDB:', allProducts)
    
    // Filter to only user's authorized products
    productDetails.value = allProducts
      .filter(product => userProductCodes.includes(product._id))
      .map(product => ({
        code: product._id,
        name: product.name || product._id,
        description: product.description || null
      }))
    
    console.log('Filtered authorized products:', productDetails.value)
  } catch (err) {
    console.error('Failed to load product details:', err)
    // Fallback to product codes
    const products = authStore.decoded?.products || []
    productDetails.value = products.map(code => ({
      code,
      name: code.charAt(0).toUpperCase() + code.slice(1),
      description: null
    }))
  }
}

onMounted(() => {
  loadProductDetails()
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
.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
