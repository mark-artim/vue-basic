<template>
  <v-container class="pa-4">
    <v-card
      class="pa-6 elevation-8"
      color="#0a0f1c"
    >
      <div class="d-flex align-center mb-4">
        <h1 class="flex-grow-1 text-white">
          {{ title }}
        </h1>
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
      <v-card
        v-if="authorizedProducts.length > 0"
        class="mb-4"
        variant="outlined"
      >
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="primary"
          >
            mdi-package-variant
          </v-icon>
          Authorized Products
        </v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-4">
            <div
              v-for="product in authorizedProducts"
              :key="product.code"
              class="glass-product-button"
            >
              <v-icon class="product-icon">
                mdi-package-variant
              </v-icon>
              <div class="product-content">
                <div class="product-name">
                  {{ product.name }}
                </div>
                <div
                  v-if="product.description"
                  class="product-description"
                >
                  {{ product.description }}
                </div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Available Products Section -->
      <v-card
        v-if="availableProducts.length > 0"
        class="mb-4"
        variant="outlined"
      >
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="success"
          >
            mdi-shopping
          </v-icon>
          Available Products
        </v-card-title>
        <v-card-text>
          <div class="d-flex flex-wrap gap-4">
            <div
              v-for="product in availableProducts"
              :key="product.code"
              class="glass-available-product"
            >
              <div class="product-header">
                <v-icon class="product-icon">
                  mdi-package-variant-plus
                </v-icon>
                <div class="product-content">
                  <div class="product-name">
                    {{ product.name }}
                  </div>
                  <div
                    v-if="product.longDescription"
                    class="product-long-description"
                  >
                    {{ product.longDescription }}
                  </div>
                </div>
              </div>
              
              <div
                v-if="product.features.length > 0"
                class="product-features"
              >
                <div class="features-title">
                  Features:
                </div>
                <ul class="features-list">
                  <li
                    v-for="feature in product.features"
                    :key="feature"
                  >
                    {{ feature }}
                  </li>
                </ul>
              </div>
              
              <v-btn
                class="signup-btn mt-3"
                color="success"
                variant="elevated"
                size="large"
                @click="signUpForProduct(product)"
              >
                <v-icon start>
                  mdi-plus-circle
                </v-icon>
                Sign Up
              </v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Collapsible Settings Section -->
      <v-expand-transition>
        <v-card
          v-if="showSettings"
          class="mb-4"
          variant="outlined"
        >
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="warning"
            >
              mdi-cog
            </v-icon>
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
                variant="outlined"
                density="compact"
                @update:model-value="savePort"
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
          <v-icon class="me-2">
            mdi-logout
          </v-icon>
          <div>
            <div class="font-weight-bold">
              {{ logoutMessage }}
            </div>
            <div class="text-caption">
              Logging out in {{ countdown }} seconds...
            </div>
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
const allProducts = ref([])

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

// Extract available products (not owned by user)
const availableProducts = computed(() => {
  const userProductCodes = authStore.decoded?.products || []
  return allProducts.value
    .filter(product => !userProductCodes.includes(product._id))
    .map(product => ({
      code: product._id,
      name: product.name || product._id,
      longDescription: product.longDescription || null,
      features: product.features || [],
      stripeProductId: product.stripeProductId || null
    }))
})

// Load product details from MongoDB
const loadProductDetails = async () => {
  try {
    const userProductCodes = authStore.decoded?.products || []
    console.log('Loading product details for user codes:', userProductCodes)
    
    // Get all products from MongoDB
    const response = await apiClient.get('/products')
    allProducts.value = response.data
    console.log('All products from MongoDB:', allProducts.value)
    
    // Filter to only user's authorized products
    productDetails.value = allProducts.value
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

function signUpForProduct(product) {
  console.log('Signing up for product:', product)
  // Navigate to product signup page with product details
  router.push({
    name: 'ProductSignup',
    params: { productId: product.code },
    query: { stripeProductId: product.stripeProductId }
  })
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

.glass-product-button {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px 24px;
  margin: 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.45) 0%,
    rgba(255, 255, 255, 0.35) 50%,
    rgba(255, 255, 255, 0.25) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  min-height: 60px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(255, 255, 255, 0.1);
}

.glass-product-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.3), 
    transparent);
  transition: left 0.6s ease;
}

.glass-product-button:hover::before {
  left: 100%;
}

.glass-product-button:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.3) 0%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.12) 100%);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(255, 255, 255, 0.15);
}

.product-icon {
  color: rgba(255, 255, 255, 0.9);
  margin-right: 12px;
  font-size: 24px;
}

.product-content {
  flex: 1;
}

.product-name {
  font-weight: bold;
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.product-description {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Available Products Styling */
.glass-available-product {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 24px;
  margin: 12px;
  border-radius: 20px;
  background: linear-gradient(135deg, 
    rgba(76, 175, 80, 0.15) 0%,
    rgba(255, 255, 255, 0.2) 30%,
    rgba(255, 255, 255, 0.1) 70%,
    rgba(76, 175, 80, 0.1) 100%);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: white;
  cursor: pointer;
  transition: all 0.4s ease;
  overflow: hidden;
  min-width: 280px;
  max-width: 350px;
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(76, 175, 80, 0.2);
}

.glass-available-product::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(255, 255, 255, 0.4), 
    transparent);
  transition: left 0.7s ease;
}

.glass-available-product:hover::before {
  left: 100%;
}

.glass-available-product:hover {
  transform: translateY(-4px);
  background: linear-gradient(135deg, 
    rgba(76, 175, 80, 0.2) 0%,
    rgba(255, 255, 255, 0.25) 30%,
    rgba(255, 255, 255, 0.15) 70%,
    rgba(76, 175, 80, 0.15) 100%);
  border-color: rgba(76, 175, 80, 0.4);
  box-shadow: 
    0 16px 50px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -1px 0 rgba(76, 175, 80, 0.3);
}

.product-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
}

.product-long-description {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8px;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.product-features {
  margin: 16px 0;
}

.features-title {
  font-weight: bold;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.75);
  margin-bottom: 4px;
  padding-left: 16px;
  position: relative;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.features-list li::before {
  content: '•';
  color: rgba(76, 175, 80, 0.8);
  font-weight: bold;
  position: absolute;
  left: 0;
}

.signup-btn {
  align-self: stretch;
  font-weight: bold;
  letter-spacing: 0.5px;
}
</style>
