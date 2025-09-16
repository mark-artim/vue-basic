<template>
  <v-container class="pa-4">
    <v-card
      class="pa-6 elevation-8"
      color="#0a0f1c"
    >
      <div class="d-flex align-center mb-4">
        <v-btn
          icon
          variant="text"
          class="me-3"
          @click="$router.back()"
        >
          <v-icon color="white">
            mdi-arrow-left
          </v-icon>
        </v-btn>
        <h1 class="flex-grow-1 text-white">
          Subscribe to {{ productName }}
        </h1>
      </div>

      <!-- Product Details Card -->
      <v-card
        v-if="productDetails"
        class="mb-6"
        variant="outlined"
      >
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="success"
          >
            mdi-package-variant-plus
          </v-icon>
          {{ productDetails.name }}
        </v-card-title>
        <v-card-text>
          <div
            v-if="productDetails.longDescription"
            class="product-description mb-4"
          >
            {{ productDetails.longDescription }}
          </div>
          
          <div
            v-if="productDetails.features?.length > 0"
            class="features-section"
          >
            <h3 class="features-title mb-2">
              Features Included:
            </h3>
            <v-chip-group column>
              <v-chip
                v-for="feature in productDetails.features"
                :key="feature"
                color="success"
                variant="outlined"
                size="small"
              >
                <v-icon
                  start
                  size="small"
                >
                  mdi-check
                </v-icon>
                {{ feature }}
              </v-chip>
            </v-chip-group>
          </div>
        </v-card-text>
      </v-card>

      <!-- Stripe Embedded Form -->
      <v-card
        variant="outlined"
        class="stripe-form-container"
      >
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="primary"
          >
            mdi-credit-card
          </v-icon>
          Complete Your Subscription
        </v-card-title>
        <v-card-text>
          <div
            v-if="loading"
            class="text-center pa-8"
          >
            <v-progress-circular
              indeterminate
              color="primary"
              size="50"
            />
            <div class="mt-4 text-body-1">
              Loading subscription form...
            </div>
          </div>
          
          <div
            v-else-if="error"
            class="text-center pa-8"
          >
            <v-alert
              type="error"
              variant="outlined"
            >
              <div class="font-weight-bold">
                Unable to load subscription form
              </div>
              <div class="text-caption mt-2">
                {{ error }}
              </div>
            </v-alert>
            <v-btn 
              color="primary" 
              variant="outlined" 
              class="mt-4"
              @click="initializeStripe"
            >
              Try Again
            </v-btn>
          </div>

          <!-- Stripe Elements will be mounted here -->
          <div 
            v-else 
            id="checkout" 
            class="stripe-checkout-container"
          />
        </v-card-text>
      </v-card>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// State
const loading = ref(true)
const error = ref(null)
const stripe = ref(null)
const elements = ref(null)
const productDetails = ref(null)

// Computed
const productId = computed(() => route.params.productId)
const stripeProductId = computed(() => route.query.stripeProductId)
const productName = computed(() => productDetails.value?.name || productId.value)

// Load product details
const loadProductDetails = async () => {
  try {
    const response = await apiClient.get('/products')
    const products = response.data
    productDetails.value = products.find(p => p._id === productId.value)
    
    if (!productDetails.value) {
      error.value = 'Product not found'
      return
    }
    
    console.log('Product details loaded:', productDetails.value)
  } catch (err) {
    console.error('Failed to load product details:', err)
    error.value = 'Failed to load product information'
  }
}

// Initialize Stripe
const initializeStripe = async () => {
  try {
    loading.value = true
    error.value = null
    
    // Load Stripe.js if not already loaded
    if (!window.Stripe) {
      const script = document.createElement('script')
      script.src = 'https://js.stripe.com/v3/'
      document.head.appendChild(script)
      
      await new Promise((resolve, reject) => {
        script.onload = resolve
        script.onerror = reject
      })
    }

    // Get Stripe publishable key from backend
    const configResponse = await apiClient.get('/stripe/config')
    const { publishableKey } = configResponse.data
    
    // Initialize Stripe instance
    stripe.value = window.Stripe(publishableKey)
    
    // Create checkout session
    const sessionResponse = await apiClient.post('/stripe/create-checkout-session', {
      productId: productId.value,
      stripeProductId: stripeProductId.value
    })
    
    const { clientSecret } = sessionResponse.data
    
    // Initialize Stripe Elements with embedded form
    const checkout = await stripe.value.initEmbeddedCheckout({
      clientSecret: clientSecret
    })
    
    // Mount the embedded checkout form
    checkout.mount('#checkout')
    
    loading.value = false
    
  } catch (err) {
    console.error('Stripe initialization failed:', err)
    error.value = err.response?.data?.error || 'Failed to initialize payment form'
    loading.value = false
  }
}

onMounted(async () => {
  await loadProductDetails()
  if (productDetails.value && !error.value) {
    await initializeStripe()
  }
})

onBeforeUnmount(() => {
  // Cleanup Stripe elements if they exist
  if (elements.value) {
    elements.value.destroy()
  }
})
</script>

<style scoped>
.product-description {
  font-size: 1.1rem;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.8);
}

.features-section {
  margin-top: 20px;
}

.features-title {
  color: rgba(0, 0, 0, 0.87);
  font-weight: 600;
}

.stripe-form-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.stripe-checkout-container {
  min-height: 400px;
  width: 100%;
}

.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>