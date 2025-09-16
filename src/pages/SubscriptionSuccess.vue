<template>
  <v-container class="pa-4">
    <v-card
      class="pa-6 elevation-8"
      color="#0a0f1c"
    >
      <div class="text-center">
        <v-icon
          color="success"
          size="80"
          class="mb-4"
        >
          mdi-check-circle
        </v-icon>
        <h1 class="text-white mb-4">
          Subscription Successful!
        </h1>
        
        <v-card
          variant="outlined"
          class="mb-6"
        >
          <v-card-text>
            <div class="text-h6 mb-2">
              Welcome to {{ productName }}!
            </div>
            <div class="text-body-1 mb-4">
              Your subscription has been activated and you now have access to all features.
            </div>
            
            <v-chip
              color="success"
              variant="elevated"
              size="large"
              class="mb-4"
            >
              <v-icon start>
                mdi-check
              </v-icon>
              Access Granted
            </v-chip>
          </v-card-text>
        </v-card>

        <div class="d-flex gap-4 justify-center">
          <v-btn
            color="primary"
            variant="elevated"
            size="large"
            @click="goHome"
          >
            <v-icon start>
              mdi-home
            </v-icon>
            Go to Dashboard
          </v-btn>
          
          <v-btn
            color="success"
            variant="outlined"
            size="large"
            @click="goToProduct"
          >
            <v-icon start>
              mdi-rocket-launch
            </v-icon>
            Start Using {{ productName }}
          </v-btn>
        </div>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const productDetails = ref(null)
const sessionId = computed(() => route.query.session_id)
const productName = computed(() => productDetails.value?.name || 'New Product')

const loadProductFromSession = async () => {
  try {
    if (sessionId.value) {
      // Verify session and get product details
      const response = await apiClient.get(`/stripe/session/${sessionId.value}`)
      productDetails.value = response.data.product
    }
  } catch (err) {
    console.error('Failed to load session details:', err)
  }
}

const goHome = () => {
  router.push('/home')
}

const goToProduct = () => {
  // Navigate to the specific product page
  if (productDetails.value?._id === 'ship54') {
    router.push('/ship54-settings')
  } else {
    router.push('/home')
  }
}

onMounted(() => {
  loadProductFromSession()
  // Refresh auth store to get updated product access
  authStore.refreshUserData()
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