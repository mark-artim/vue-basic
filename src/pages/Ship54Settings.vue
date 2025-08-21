<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="mb-6">Ship54 Settings</h2>
        
        <!-- Shippo Account Connection -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-truck</v-icon>
            Shippo Account Connection
          </v-card-title>
          <v-card-text>
            <div v-if="!settings.shippo.connected">
              <v-alert type="info" class="mb-4">
                Connect your Shippo account to enable shipping label creation and tracking.
              </v-alert>
              <v-btn 
                color="primary" 
                size="large"
                @click="connectShippo"
                :loading="connecting"
              >
                <v-icon left>mdi-link</v-icon>
                Connect Your Shippo Account
              </v-btn>
            </div>
            <div v-else>
              <v-alert type="success" class="mb-4">
                <v-icon left>mdi-check-circle</v-icon>
                Successfully connected to Shippo
                <div class="mt-2" v-if="settings.shippo.accountInfo">
                  <small>Account: {{ settings.shippo.accountInfo.email || 'Connected' }}</small>
                </div>
              </v-alert>
              <v-btn 
                color="error" 
                variant="outlined"
                @click="disconnectShippo"
                :loading="disconnecting"
              >
                <v-icon left>mdi-link-off</v-icon>
                Disconnect Account
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Freight Posting Settings -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-file-document</v-icon>
            Freight Posting Method
          </v-card-title>
          <v-card-text>
            <v-radio-group v-model="settings.freight.defaultMethod">
              <v-radio 
                label="Starship File Drop (Current Method)" 
                value="filedrop"
              >
                <template #label>
                  <div>
                    <strong>Starship File Drop</strong>
                    <div class="text-caption text-medium-emphasis">
                      Exports freight information to a file for processing
                    </div>
                  </div>
                </template>
              </v-radio>
              <v-radio 
                label="Invoice Line Item (New Method)" 
                value="lineitem"
              >
                <template #label>
                  <div>
                    <strong>Invoice Line Item</strong>
                    <div class="text-caption text-medium-emphasis">
                      Adds freight charge directly to the invoice and updates print status
                    </div>
                  </div>
                </template>
              </v-radio>
            </v-radio-group>
            
            <v-expand-transition>
              <div v-if="settings.freight.defaultMethod === 'lineitem'">
                <v-autocomplete
                  v-model="selectedProduct"
                  :items="productResults"
                  item-title="displayText" 
                  item-value="id"
                  label="Search Freight Product"
                  placeholder="Type to search for freight product..."
                  hint="Search and select the Eclipse product for freight charges"
                  persistent-hint
                  :loading="productSearchLoading"
                  no-data-text="No matching products found"
                  hide-no-data
                  clearable
                  @input="onProductInput"
                  @update:model-value="onProductSelected"
                >
                  <template #item="{ props, item }">
                    <v-list-item v-bind="props">
                      <v-list-item-title>{{ item.raw.id }} - {{ item.raw.description }}</v-list-item-title>
                      <v-list-item-subtitle v-if="item.raw.category">
                        Category: {{ item.raw.category }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-autocomplete>
                
                <!-- Show selected product info -->
                <div v-if="selectedProductInfo" class="mt-2 pa-3" style="background-color: #f5f5f5; border-radius: 4px; color: #333;">
                  <div class="text-body-2" style="color: #333;">
                    <strong>Selected Product:</strong> {{ selectedProductInfo.id }} - {{ selectedProductInfo.description }}
                  </div>
                  <div v-if="selectedProductInfo.category" class="text-caption" style="color: #666;">
                    Category: {{ selectedProductInfo.category }}
                  </div>
                </div>
              </div>
            </v-expand-transition>
          </v-card-text>
        </v-card>

        <!-- Shipping Preferences -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon class="me-2" color="primary">mdi-cog</v-icon>
            Shipping Preferences
          </v-card-title>
          <v-card-text>
            <v-switch 
              v-model="settings.shipping.enableAutoSearch"
              label="Auto-search orders when page loads"
              color="primary"
              hint="Automatically load orders when you visit Ship Station if a default branch is saved"
              persistent-hint
              class="mb-4"
            />
            
            <v-text-field
              v-model="settings.shipping.defaultShipViaKeywords"
              label="Default Ship Via Keywords"
              placeholder="e.g., UPS, FEDEX, DHL"
              hint="Comma-separated keywords for filtering shipping methods"
              persistent-hint
              class="mb-4"
            />
            
            <v-select
              v-model="settings.shipping.defaultBranch"
              :items="availableBranches"
              label="Default Shipping Branch"
              hint="The branch that will be automatically selected in Ship Station"
              persistent-hint
              clearable
            />
          </v-card-text>
        </v-card>

        <!-- Save Button -->
        <v-card>
          <v-card-actions class="pa-4">
            <v-spacer />
            <v-btn
              color="primary"
              size="large"
              @click="saveSettings"
              :loading="saving"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Settings
            </v-btn>
          </v-card-actions>
        </v-card>

        <!-- Success/Error Messages -->
        <v-snackbar
          v-model="showMessage"
          :color="messageType"
          :timeout="3000"
        >
          {{ message }}
        </v-snackbar>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'
import { getBranch } from '@/api/branches'
import { getUser } from '@/api/users'
import { searchProducts, getProduct } from '@/api/products'
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'

const authStore = useAuthStore()

// Reactive state
const settings = ref({
  shippo: {
    connected: false,
    accountInfo: null
  },
  freight: {
    defaultMethod: 'filedrop',
    productId: ''
  },
  shipping: {
    enableAutoSearch: true,
    defaultShipViaKeywords: 'UPS, FEDEX',
    defaultBranch: ''
  }
})

const availableBranches = ref([])
const connecting = ref(false)
const disconnecting = ref(false)
const saving = ref(false)
const showMessage = ref(false)
const message = ref('')
const messageType = ref('success')

// Product search state
const selectedProduct = ref('')
const selectedProductInfo = ref(null)

// Product search setup - simplified to match InvoiceLookup pattern
const fetchProducts = async (query) => {
  const result = await searchProducts(query)
  const products = result.results || result || []
  console.log('[DEBUG SHIP54] Products fetched:', products)
  
  // Format products for autocomplete - same as InvoiceLookup does with customers
  return products.map(product => ({
    id: product.productId || product.id,
    description: product.description || product.name || 'No description',
    category: product.category,
    displayText: `${product.productId || product.id} - ${product.description || product.name || 'No description'}`
  }))
}

const {
  searchTerm: productKeyword,
  results: productResults,
  isLoading: productSearchLoading,
  onSearch: onProductInput
} = useDebouncedSearch(fetchProducts, 800)

// Load user settings and available branches on mount
onMounted(async () => {
  await loadSettings()
  await loadAvailableBranches()
  await loadSelectedProductInfo()
})

const loadSettings = async () => {
  try {
    const response = await apiClient.get('/ship54/settings')
    if (response.data) {
      settings.value = { ...settings.value, ...response.data }
      
      // Set selected product if exists
      if (response.data.freight && response.data.freight.productId) {
        selectedProduct.value = response.data.freight.productId
      }
    }
  } catch (err) {
    console.error('Failed to load Ship54 settings:', err)
    // If settings don't exist yet, that's okay - use defaults
  }
}

const loadSelectedProductInfo = async () => {
  if (selectedProduct.value) {
    try {
      const product = await getProduct(selectedProduct.value)
      selectedProductInfo.value = {
        id: product.productId || product.id,
        description: product.description || product.name || 'No description',
        category: product.category
      }
    } catch (err) {
      console.error('Failed to load product info:', err)
      selectedProductInfo.value = {
        id: selectedProduct.value,
        description: 'Product ID: ' + selectedProduct.value,
        category: null
      }
    }
  }
}

const loadAvailableBranches = async () => {
  try {
    const jwt = authStore.jwt
    const payload = JSON.parse(atob(jwt.split('.')[1]))
    const erpUserName = (payload.erpUserName || payload.erpLogin).toUpperCase()
    
    const userData = await getUser(erpUserName)
    const branchesArray = userData.accessibleBranches || []
    availableBranches.value = branchesArray.map(b => b.branchId)
  } catch (err) {
    console.error('Failed to load available branches:', err)
  }
}

const connectShippo = async () => {
  connecting.value = true
  try {
    // This will initiate the OAuth flow
    const response = await apiClient.post('/ship54/shippo/connect')
    if (response.data.authUrl) {
      // Redirect to Shippo OAuth
      window.location.href = response.data.authUrl
    }
  } catch (err) {
    console.error('Failed to initiate Shippo connection:', err)
    showError('Failed to connect to Shippo. Please try again.')
  } finally {
    connecting.value = false
  }
}

const disconnectShippo = async () => {
  disconnecting.value = true
  try {
    await apiClient.delete('/ship54/shippo/disconnect')
    settings.value.shippo.connected = false
    settings.value.shippo.accountInfo = null
    showSuccess('Shippo account disconnected successfully')
  } catch (err) {
    console.error('Failed to disconnect Shippo:', err)
    showError('Failed to disconnect Shippo account')
  } finally {
    disconnecting.value = false
  }
}

const onProductSelected = async (productId) => {
  console.log('🎯 Product selected event fired with:', productId)
  console.log('🎯 Type of productId:', typeof productId)
  if (productId) {
    selectedProduct.value = productId
    settings.value.freight.productId = productId
    await loadSelectedProductInfo()
    console.log('✅ Settings after product selection:', settings.value)
    console.log('✅ selectedProduct.value is now:', selectedProduct.value)
  } else {
    console.log('⚠️ No product ID provided, clearing selection')
    selectedProduct.value = ''
    selectedProductInfo.value = null
    settings.value.freight.productId = ''
  }
}

const clearProductSelection = () => {
  selectedProduct.value = ''
  selectedProductInfo.value = null
  settings.value.freight.productId = ''
}

const saveSettings = async () => {
  saving.value = true
  try {
    console.log('🔄 Starting save process...')
    console.log('Selected product value:', selectedProduct.value)
    console.log('Settings before save:', JSON.stringify(settings.value, null, 2))
    
    // Ensure the freight.productId is properly set
    if (selectedProduct.value) {
      settings.value.freight.productId = selectedProduct.value
      console.log('✅ Updated freight.productId to:', settings.value.freight.productId)
    }
    
    console.log('Final settings to save:', JSON.stringify(settings.value, null, 2))
    
    const response = await apiClient.put('/ship54/settings', settings.value)
    console.log('💾 Save response:', response.data)
    
    // Verify the save by reloading settings
    const verifyResponse = await apiClient.get('/ship54/settings')
    console.log('🔍 Verification - settings after save:', verifyResponse.data)
    
    showSuccess('Settings saved successfully!')
    
    // Update localStorage for immediate use
    if (settings.value.shipping.defaultShipViaKeywords) {
      localStorage.setItem('defaultShipViaKeywords', settings.value.shipping.defaultShipViaKeywords)
    }
    if (settings.value.shipping.defaultBranch) {
      localStorage.setItem('defaultShippingBranch', settings.value.shipping.defaultBranch)
    }
  } catch (err) {
    console.error('❌ Failed to save settings:', err)
    console.error('Error details:', err.response?.data)
    showError(`Failed to save settings: ${err.response?.data?.error || err.message}`)
  } finally {
    saving.value = false
  }
}

const showSuccess = (msg) => {
  message.value = msg
  messageType.value = 'success'
  showMessage.value = true
}

const showError = (msg) => {
  message.value = msg
  messageType.value = 'error'
  showMessage.value = true
}
</script>

<style scoped>
.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>