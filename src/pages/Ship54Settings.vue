<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="mb-6">
          Ship54 Settings
        </h2>
        
        <!-- Shippo Integration -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="primary"
            >
              mdi-truck
            </v-icon>
            Shippo Integration
          </v-card-title>
          <v-card-text>
            <!-- Not Connected State -->
            <div v-if="!isShippoConnected">
              <v-alert
                type="info"
                class="mb-4"
              >
                <div class="d-flex align-center">
                  <v-icon class="me-2">
                    mdi-information
                  </v-icon>
                  <div>
                    <div class="font-weight-bold">
                      Connect Your Shippo Account
                    </div>
                    <div class="text-caption">
                      Enter your Shippo API token to enable shipping labels and rate quotes
                    </div>
                  </div>
                </div>
              </v-alert>
              
              <v-text-field
                v-model="shippoTokenInput"
                label="Shippo API Token"
                placeholder="shippo_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                hint="Get your API token from your Shippo dashboard → API"
                persistent-hint
                :type="showToken ? 'text' : 'password'"
                :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
                outlined
                class="mb-4"
                :error="tokenError !== null"
                :error-messages="tokenError"
                @click:append-inner="showToken = !showToken"
              />
              
              <div class="d-flex gap-2">
                <v-btn 
                  color="primary" 
                  :disabled="!shippoTokenInput || !isValidTokenFormat"
                  :loading="validating"
                  @click="validateAndSaveToken"
                >
                  <v-icon class="me-1">
                    mdi-check-circle
                  </v-icon>
                  Validate & Save Token
                </v-btn>
                
                <v-btn 
                  variant="outlined"
                  href="https://app.goshippo.com/api"
                  target="_blank"
                  rel="noopener"
                >
                  <v-icon class="me-1">
                    mdi-open-in-new
                  </v-icon>
                  Get Shippo Token
                </v-btn>
              </div>
            </div>
            
            <!-- Connected State -->
            <div v-else>
              <v-alert
                type="success"
                class="mb-4"
              >
                <div class="d-flex align-center">
                  <v-icon class="me-2">
                    mdi-check-circle
                  </v-icon>
                  <div>
                    <div class="font-weight-bold">
                      ✅ Shippo Connected
                    </div>
                    <div class="text-caption">
                      {{ shippoTokenEnvironment }} environment • Last tested: {{ formatLastTested }}
                    </div>
                    <div
                      v-if="settings.shippo.customerToken.testResults?.account"
                      class="text-caption mt-1"
                    >
                      Account: {{ settings.shippo.customerToken.testResults.account.email || settings.shippo.customerToken.testResults.account.name || 'Connected' }}
                    </div>
                  </div>
                </div>
              </v-alert>
              
              <div class="d-flex gap-2">
                <v-btn 
                  color="primary" 
                  variant="outlined"
                  :loading="testing"
                  @click="testTokenConnection"
                >
                  <v-icon class="me-1">
                    mdi-connection
                  </v-icon>
                  Test Connection
                </v-btn>
                
                <v-btn 
                  color="warning"
                  variant="outlined"
                  @click="showUpdateToken = true"
                >
                  <v-icon class="me-1">
                    mdi-key
                  </v-icon>
                  Update Token
                </v-btn>
                
                <v-btn 
                  color="error" 
                  variant="outlined"
                  :loading="removing"
                  @click="removeToken"
                >
                  <v-icon class="me-1">
                    mdi-delete
                  </v-icon>
                  Remove Token
                </v-btn>
              </div>
              
              <!-- Update Token Dialog -->
              <v-expand-transition>
                <div
                  v-if="showUpdateToken"
                  class="mt-4 pa-4"
                  style="border: 1px solid #e0e0e0; border-radius: 4px;"
                >
                  <h4 class="mb-3">
                    Update Shippo Token
                  </h4>
                  <v-text-field
                    v-model="shippoTokenInput"
                    label="New Shippo API Token"
                    placeholder="shippo_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    :type="showToken ? 'text' : 'password'"
                    :append-inner-icon="showToken ? 'mdi-eye-off' : 'mdi-eye'"
                    outlined
                    class="mb-3"
                    :error="tokenError !== null"
                    :error-messages="tokenError"
                    @click:append-inner="showToken = !showToken"
                  />
                  <div class="d-flex gap-2">
                    <v-btn 
                      color="primary"
                      :disabled="!shippoTokenInput || !isValidTokenFormat"
                      :loading="validating"
                      @click="validateAndSaveToken"
                    >
                      Update Token
                    </v-btn>
                    <v-btn 
                      variant="outlined"
                      @click="cancelUpdateToken"
                    >
                      Cancel
                    </v-btn>
                  </div>
                </div>
              </v-expand-transition>
            </div>
          </v-card-text>
        </v-card>

        <!-- Shipment Tracking Status -->
        <v-card
          v-if="isShippoConnected"
          class="mb-6"
        >
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="primary"
            >
              mdi-package-variant
            </v-icon>
            Shipment Tracking Status
          </v-card-title>
          <v-card-text>
            <div class="d-flex align-center mb-4">
              <!-- Webhook Status Indicator -->
              <div class="me-4">
                <v-chip
                  v-if="webhookStatus?.webhook?.isActive"
                  color="success"
                  size="large"
                >
                  <v-icon start>
                    mdi-check-circle
                  </v-icon>
                  Tracking Active
                </v-chip>
                <v-chip
                  v-else-if="webhookStatus?.webhook?.lastError"
                  color="error"
                  size="large"
                >
                  <v-icon start>
                    mdi-alert-circle
                  </v-icon>
                  Tracking Issue
                </v-chip>
                <v-chip
                  v-else
                  color="warning"
                  size="large"
                >
                  <v-icon start>
                    mdi-clock-outline
                  </v-icon>
                  Setting Up
                </v-chip>
              </div>
              
              <v-btn
                variant="outlined"
                size="small"
                :loading="trackingStatusLoading"
                @click="refreshTrackingStatus"
              >
                <v-icon start>
                  mdi-refresh
                </v-icon>
                Refresh Status
              </v-btn>
            </div>

            <!-- Status Details -->
            <div
              v-if="webhookStatus?.webhook?.isActive"
              class="mb-4"
            >
              <div class="d-flex align-center mb-2">
                <v-icon
                  color="success"
                  class="me-2"
                >
                  mdi-check
                </v-icon>
                <span class="text-body-2">Your shipment tracking is working correctly</span>
              </div>
              <div class="text-caption text-medium-emphasis ms-6">
                Shipments will automatically update with tracking information from carriers
              </div>
              <div
                v-if="webhookStatus.webhook.createdAt"
                class="text-caption text-medium-emphasis ms-6"
              >
                Tracking active since: {{ formatTrackingDate(webhookStatus.webhook.createdAt) }}
              </div>
            </div>

            <div
              v-else-if="webhookStatus?.webhook?.lastError"
              class="mb-4"
            >
              <div class="d-flex align-center mb-2">
                <v-icon
                  color="error"
                  class="me-2"
                >
                  mdi-alert
                </v-icon>
                <span class="text-body-2">There's an issue with your shipment tracking</span>
              </div>
              <v-alert
                type="error"
                density="compact"
                class="mb-2"
              >
                <div class="text-caption">
                  <strong>Error:</strong> {{ getCustomerFriendlyError(webhookStatus.webhook.lastError) }}
                </div>
              </v-alert>
              <div class="text-caption text-medium-emphasis">
                Your shipments may not receive automatic tracking updates. Please contact support if this persists.
              </div>
            </div>

            <div
              v-else
              class="mb-4"
            >
              <div class="d-flex align-center mb-2">
                <v-icon
                  color="warning"
                  class="me-2"
                >
                  mdi-clock-outline
                </v-icon>
                <span class="text-body-2">Shipment tracking is being set up</span>
              </div>
              <div class="text-caption text-medium-emphasis">
                Your tracking integration will be activated shortly. Contact support if this status doesn't change within 24 hours.
              </div>
            </div>

            <!-- Recent Activity (if available) -->
            <div
              v-if="recentShipmentStats"
              class="mb-4"
            >
              <h4 class="text-body-1 mb-2">
                Recent Activity
              </h4>
              <div class="d-flex flex-wrap gap-4">
                <div class="text-center">
                  <div class="text-h6 text-primary">
                    {{ recentShipmentStats.total || 0 }}
                  </div>
                  <div class="text-caption">
                    Tracked Shipments
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    (Last 30 days)
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-h6 text-success">
                    {{ recentShipmentStats.delivered || 0 }}
                  </div>
                  <div class="text-caption">
                    Delivered
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-h6 text-info">
                    {{ recentShipmentStats.inTransit || 0 }}
                  </div>
                  <div class="text-caption">
                    In Transit
                  </div>
                </div>
                <div
                  v-if="recentShipmentStats.needingAttention > 0"
                  class="text-center"
                >
                  <div class="text-h6 text-warning">
                    {{ recentShipmentStats.needingAttention }}
                  </div>
                  <div class="text-caption">
                    Need Attention
                  </div>
                </div>
              </div>
            </div>

            <!-- Customer Admin Webhook Controls -->
            <div
              v-if="canManageWebhook"
              class="mb-4"
            >
              <v-divider class="my-4" />
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="text-body-2 mb-1">
                    Webhook Management
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    Ship54 admins can manage webhook settings
                  </div>
                </div>
                <div class="d-flex gap-2">
                  <v-btn
                    v-if="!webhookStatus?.webhook?.isActive"
                    color="success"
                    size="small"
                    :loading="customerWebhookLoading"
                    @click="createCustomerWebhook"
                  >
                    <v-icon start>
                      mdi-plus
                    </v-icon>
                    Create Webhook
                  </v-btn>
                  
                  <v-btn
                    v-if="webhookStatus?.webhook?.isActive"
                    color="error"
                    variant="outlined"
                    size="small"
                    :loading="customerWebhookLoading"
                    @click="deleteCustomerWebhook"
                  >
                    <v-icon start>
                      mdi-delete
                    </v-icon>
                    Delete Webhook
                  </v-btn>
                </div>
              </div>
            </div>

            <!-- Help Section -->
            <v-divider class="my-4" />
            <div class="d-flex justify-space-between align-center">
              <div>
                <div class="text-body-2 mb-1">
                  Need Help with Shipment Tracking?
                </div>
                <div class="text-caption text-medium-emphasis">
                  Contact support if your shipments aren't receiving tracking updates
                </div>
              </div>
              <v-btn
                color="primary"
                variant="outlined"
                size="small"
                href="mailto:support@yourcompany.com?subject=Shipment Tracking Issue"
              >
                <v-icon start>
                  mdi-email
                </v-icon>
                Contact Support
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Freight Posting Settings -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="primary"
            >
              mdi-file-document
            </v-icon>
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
                <div
                  v-if="selectedProductInfo"
                  class="mt-2 pa-3"
                  style="background-color: #f5f5f5; border-radius: 4px; color: #333;"
                >
                  <div
                    class="text-body-2"
                    style="color: #333;"
                  >
                    <strong>Selected Product:</strong> {{ selectedProductInfo.id }} - {{ selectedProductInfo.description }}
                  </div>
                  <div
                    v-if="selectedProductInfo.category"
                    class="text-caption"
                    style="color: #666;"
                  >
                    Category: {{ selectedProductInfo.category }}
                  </div>
                </div>
              </div>
            </v-expand-transition>
          </v-card-text>
        </v-card>

        <!-- COD Terms Management -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="warning"
            >
              mdi-cash
            </v-icon>
            COD Terms Management
          </v-card-title>
          <v-card-text>
            <div class="mb-4">
              <h4>COD Terms Codes</h4>
              <p class="text-caption text-medium-emphasis mb-3">
                Specify which terms codes should be treated as Cash On Delivery (COD)
              </p>
              
              <v-autocomplete
                v-model="newCodTerm"
                :items="termsResults"
                item-title="id"
                item-value="id"
                label="Add COD Terms Code"
                placeholder="Search for terms codes..."
                :loading="termsSearchLoading"
                no-data-text="No matching terms codes found"
                hide-no-data
                clearable
                append-inner-icon="mdi-plus"
                class="mb-3"
                @click:append-inner="addCodTerm"
                @input="onTermsInput"
                @update:model-value="addCodTerm"
              >
                <template #item="{ props, item }">
                  <v-list-item v-bind="props">
                    <v-list-item-title>{{ item.raw.id }}</v-list-item-title>
                    <v-list-item-subtitle v-if="item.raw.description">
                      {{ item.raw.description }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-autocomplete>
              
              <div v-if="settings.cod.termsCodes.length > 0">
                <h5 class="mb-2">
                  Current COD Terms Codes:
                </h5>
                <div class="d-flex flex-wrap gap-2">
                  <v-chip
                    v-for="(term, index) in settings.cod.termsCodes"
                    :key="term"
                    color="warning"
                    closable
                    @click:close="removeCodTerm(index)"
                  >
                    {{ term }}
                  </v-chip>
                </div>
              </div>
            </div>
            
            <v-divider class="my-4" />
            
            <div>
              <h4 class="mb-3">
                COD Balance Due Policy
              </h4>
              <v-radio-group v-model="settings.cod.balancePolicy">
                <v-radio value="warn">
                  <template #label>
                    <div>
                      <strong>Warn Only</strong>
                      <div class="text-caption text-medium-emphasis">
                        Show warning for COD orders with outstanding balance, but allow shipment
                      </div>
                    </div>
                  </template>
                </v-radio>
                <v-radio value="prevent">
                  <template #label>
                    <div>
                      <strong>Prevent Shipment</strong>
                      <div class="text-caption text-medium-emphasis">
                        Block shipment of COD orders with outstanding balance
                      </div>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>
            </div>
          </v-card-text>
        </v-card>

        <!-- Shipping Preferences -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="primary"
            >
              mdi-cog
            </v-icon>
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
            
            <v-switch 
              v-model="settings.shipping.enableTrackingTestMode"
              label="Tracking Test Mode"
              color="orange"
              hint="Use real Shippo test API calls with test tracking numbers (SHIPPO_DELIVERED, SHIPPO_TRANSIT, etc.) to test various tracking scenarios"
              persistent-hint
              class="mb-4"
              @update:model-value="toggleTestMode"
            />

            <!-- User shipping preferences moved to individual user profiles -->
            <!-- Ship Via Keywords and Default Branch are now personal settings -->
          </v-card-text>
        </v-card>

        <!-- Save Button -->
        <v-card>
          <v-card-actions class="pa-4">
            <v-spacer />
            <v-btn
              color="primary"
              size="large"
              :loading="saving"
              @click="saveSettings"
            >
              <v-icon left>
                mdi-content-save
              </v-icon>
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
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'
// Branch and user imports removed - no longer needed for company-level settings
import { searchProducts, getProduct } from '@/api/products'
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'

const authStore = useAuthStore()

// Reactive state
const settings = ref({
  shippo: {
    connected: false,
    accountInfo: null,
    customerToken: {
      encrypted: null,
      isValid: false,
      lastTested: null,
      testResults: null,
      environment: 'test'
    }
  },
  freight: {
    defaultMethod: 'filedrop',
    productId: ''
  },
  shipping: {
    enableAutoSearch: true,
    enableTrackingTestMode: false,
    testMode: false
  },
  cod: {
    termsCodes: [],
    balancePolicy: 'warn'
  }
})

const connecting = ref(false)
const disconnecting = ref(false)
const testing = ref(false)
const saving = ref(false)
const showMessage = ref(false)
const message = ref('')
const messageType = ref('success')

// Shippo token management state
const shippoTokenInput = ref('')
const showToken = ref(false)
const validating = ref(false)
const removing = ref(false)
const showUpdateToken = ref(false)
const tokenError = ref(null)

// Product search state
const selectedProduct = ref('')
const selectedProductInfo = ref(null)

// COD state
const newCodTerm = ref('')
const termsResults = ref([])
const termsSearchLoading = ref(false)

// Webhook status state
const webhookStatus = ref(null)
const trackingStatusLoading = ref(false)
const recentShipmentStats = ref(null)
const customerWebhookLoading = ref(false)

// Terms search function
const fetchTermsCodes = async (query) => {
  if (!query || query.length < 1) return []
  
  try {
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'GET',
      url: '/Termslist',
      params: { keyword: query }
    })
    
    const results = response.data?.results || response.data || []
    console.log('[DEBUG TERMS] Terms fetched:', results)
    return results
  } catch (err) {
    console.error('Failed to fetch terms codes:', err)
    return []
  }
}

// Terms search setup using debounced search
const {
  searchTerm: termsKeyword,
  results: termsSearchResults,
  isLoading: termsSearchIsLoading,
  onSearch: onTermsInput
} = useDebouncedSearch(fetchTermsCodes, 500)

// Update reactive references for template
watch(termsSearchResults, (newResults) => {
  termsResults.value = newResults
})

watch(termsSearchIsLoading, (loading) => {
  termsSearchLoading.value = loading
})

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

// Load user settings on mount
onMounted(async () => {
  await loadSettings()
  await loadSelectedProductInfo()
  await loadWebhookStatus()
  await loadRecentShipmentStats()
  handleOAuthCallback()
})

const loadSettings = async () => {
  try {
    console.log('📥 Loading Ship54 settings...')
    const response = await apiClient.get('/ship54/settings')
    console.log('🔍 Raw settings response:', response.data)
    
    if (response.data) {
      settings.value = { ...settings.value, ...response.data }
      console.log('🔧 Settings after merge:', settings.value)
      console.log('🎯 COD settings after load:', settings.value.cod)
      
      // Set selected product if exists
      if (response.data.freight && response.data.freight.productId) {
        selectedProduct.value = response.data.freight.productId
      }
    }
  } catch (err) {
    console.error('Failed to load Ship54 settings:', err)
    console.log('🔧 Using default settings due to error')
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

const handleOAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search)
  const success = urlParams.get('success')
  const error = urlParams.get('error')
  
  if (success === 'connected') {
    showSuccess('Successfully connected to Shippo! Refreshing settings...')
    // Manually mark as connected since backend might not have updated yet
    settings.value.shippo.connected = true
    // Save this state and reload settings
    saveSettings().then(() => {
      setTimeout(() => {
        loadSettings()
      }, 1000)
    })
    
    // Clean up URL
    window.history.replaceState({}, document.title, window.location.pathname)
  } else if (error) {
    let errorMessage = 'Failed to connect to Shippo'
    switch (error) {
      case 'missing_parameters':
        errorMessage = 'OAuth flow incomplete - missing parameters'
        break
      case 'invalid_state':
        errorMessage = 'Security verification failed - please try again'
        break
      case 'token_exchange_failed':
        errorMessage = 'Failed to exchange authorization code for tokens'
        break
      case 'user_not_found':
        errorMessage = 'User session not found - please log in again'
        break
      case 'callback_failed':
        errorMessage = 'OAuth callback processing failed'
        break
      default:
        errorMessage = `OAuth error: ${error}`
    }
    showError(errorMessage)
    // Clean up URL
    window.history.replaceState({}, document.title, window.location.pathname)
  }
}

// loadAvailableBranches removed - branch selection moved to user-specific settings

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
    
    // Save updated settings to backend
    await saveSettings()
    showSuccess('Shippo account disconnected successfully')
  } catch (err) {
    console.error('Failed to disconnect Shippo:', err)
    showError('Failed to disconnect Shippo account')
  } finally {
    disconnecting.value = false
  }
}

const toggleTestMode = async () => {
  const enabled = settings.value.shipping.enableTrackingTestMode
  console.log('🔥 toggleTestMode called, current value:', enabled)
  try {
    console.log('🔥 Making API call to toggle test mode')
    await apiClient.post('/ship54/toggle-test-mode', { enabled })
    console.log('🔥 API call succeeded')
    showSuccess('Test mode ' + (enabled ? 'enabled' : 'disabled'))
  } catch (err) {
    console.error('🔥 Failed to toggle test mode:', err)
    showError('Failed to toggle test mode')
    // Revert the switch
    settings.value.shipping.enableTrackingTestMode = !enabled
  }
}

// toggleSomething function removed - was unfinished demo code



const testShippoConnection = async () => {
  testing.value = true
  try {
    const response = await apiClient.get('/ship54/shippo/test')
    if (response.data.success) {
      showSuccess('Shippo connection test successful! API is working correctly.')
      // Update account info if retrieved
      if (response.data.accountInfo) {
        settings.value.shippo.accountInfo = response.data.accountInfo
        // Save updated settings to backend
        await saveSettings()
      }
    } else {
      showError(`Connection test failed: ${response.data.error}`)
    }
  } catch (err) {
    console.error('Failed to test Shippo connection:', err)
    showError(`Connection test failed: ${err.response?.data?.error || err.message}`)
  } finally {
    testing.value = false
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
    console.log('🎯 COD settings being saved:', settings.value.cod)
    
    const response = await apiClient.put('/ship54/settings', settings.value)
    console.log('💾 Save response:', response.data)
    
    // Verify the save by reloading settings
    const verifyResponse = await apiClient.get('/ship54/settings')
    console.log('🔍 Verification - settings after save:', verifyResponse.data)
    
    showSuccess('Settings saved successfully!')
    
    // localStorage updates removed - shipping preferences are now user-specific
  } catch (err) {
    console.error('❌ Failed to save settings:', err)
    console.error('Error details:', err.response?.data)
    showError(`Failed to save settings: ${err.response?.data?.error || err.message}`)
  } finally {
    saving.value = false
  }
}

// COD terms management functions
const addCodTerm = async () => {
  const term = newCodTerm.value.trim().toUpperCase()
  
  if (!term) {
    showError('Please enter a terms code')
    return
  }
  
  if (settings.value.cod.termsCodes.includes(term)) {
    showError('Terms code already exists')
    return
  }
  
  // Validate against ERP system
  try {
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'GET',
      url: '/Termslist',
      params: { keyword: term }
    })
    
    const results = response.data?.results || response.data || []
    const validTerm = results.find(t => t.id?.toUpperCase() === term)
    
    if (validTerm) {
      settings.value.cod.termsCodes.push(term)
      newCodTerm.value = ''
      showSuccess(`Added COD term: ${term} (${validTerm.description || 'No description'})`)
    } else {
      showError(`Terms code "${term}" not found in ERP system. Please verify the terms code exists.`)
    }
  } catch (err) {
    console.error('Failed to validate terms code:', err)
    // Allow adding if validation fails but warn user
    settings.value.cod.termsCodes.push(term)
    newCodTerm.value = ''
    showSuccess(`Added COD term: ${term} (Warning: Could not validate with ERP system)`)
  }
}

const removeCodTerm = (index) => {
  const removedTerm = settings.value.cod.termsCodes[index]
  settings.value.cod.termsCodes.splice(index, 1)
  showSuccess(`Removed COD term: ${removedTerm}`)
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

// Webhook status functions
const loadWebhookStatus = async () => {
  if (!isShippoConnected.value) {
    webhookStatus.value = null
    return
  }
  
  try {
    // Get company ID from decoded JWT token
    const decodedToken = authStore.decoded
    const companyId = decodedToken?.companyId?._id || decodedToken?.companyId
    
    console.log('[WEBHOOK STATUS] Raw decoded token:', decodedToken)
    console.log('[WEBHOOK STATUS] CompanyId field:', decodedToken?.companyId)
    console.log('[WEBHOOK STATUS] CompanyId type:', typeof decodedToken?.companyId)
    console.log('[WEBHOOK STATUS] Extracted company ID:', companyId)
    
    if (!companyId || companyId === 'undefined') {
      console.error('[WEBHOOK STATUS] No valid company ID found in token')
      console.error('[WEBHOOK STATUS] Available token fields:', Object.keys(decodedToken || {}))
      webhookStatus.value = null
      return
    }
    
    const response = await apiClient.get(`/admin/companies/${companyId}/webhook/status`)
    webhookStatus.value = response.data
  } catch (error) {
    console.error('Failed to load webhook status:', error)
    webhookStatus.value = null
  }
}

const loadRecentShipmentStats = async () => {
  if (!isShippoConnected.value) {
    recentShipmentStats.value = null
    return
  }
  
  try {
    const response = await apiClient.get('/api/shipments/summary/stats?days=30')
    recentShipmentStats.value = {
      total: response.data.total_shipments || 0,
      delivered: response.data.status_breakdown?.DELIVERED || 0,
      inTransit: (response.data.status_breakdown?.IN_TRANSIT || 0) + (response.data.status_breakdown?.SHIPPED || 0),
      needingAttention: response.data.needing_attention || 0
    }
  } catch (error) {
    console.error('Failed to load recent shipment stats:', error)
    recentShipmentStats.value = null
  }
}

const refreshTrackingStatus = async () => {
  trackingStatusLoading.value = true
  try {
    await Promise.all([
      loadWebhookStatus(),
      loadRecentShipmentStats()
    ])
    showSuccess('Tracking status refreshed')
  } catch (error) {
    console.error('Failed to refresh tracking status:', error)
    showError('Failed to refresh tracking status')
  } finally {
    trackingStatusLoading.value = false
  }
}

const getCustomerFriendlyError = (error) => {
  if (!error) return 'Unknown error'
  
  // Convert technical errors to customer-friendly messages
  if (error.includes('No valid Shippo API token')) {
    return 'Shippo integration needs to be reconnected'
  }
  if (error.includes('Failed to decrypt')) {
    return 'Authentication issue - please contact support'
  }
  if (error.includes('Network')) {
    return 'Connection issue - please try again later'
  }
  if (error.includes('Rate limit')) {
    return 'Too many requests - please wait a moment'
  }
  if (error.includes('404')) {
    return 'Webhook configuration issue - contact support'
  }
  
  // If it's a short, user-friendly error already, return it
  if (error.length < 100 && !error.includes('Error:') && !error.includes('Failed to')) {
    return error
  }
  
  // Default fallback
  return 'Integration issue - please contact support if this persists'
}

const formatTrackingDate = (dateString) => {
  if (!dateString) return 'Unknown'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  
  return date.toLocaleDateString()
}

// Automatic webhook creation for new token validations
const createWebhookAutomatically = async () => {
  try {
    console.log('[AUTO WEBHOOK] Attempting to create webhook automatically...')
    
    const companyId = authStore.decoded?.companyId?._id || authStore.decoded?.companyId
    if (!companyId) {
      console.warn('[AUTO WEBHOOK] No company ID found, skipping webhook creation')
      return
    }

    // Check if webhook already exists
    const statusResponse = await apiClient.get(`/admin/companies/${companyId}/webhook/status`)
    if (statusResponse.data?.webhook?.isActive) {
      console.log('[AUTO WEBHOOK] Webhook already active, skipping creation')
      showSuccess('🎯 Webhook already active - shipment tracking ready!')
      return
    }

    // Create webhook
    const createResponse = await apiClient.post(`/admin/companies/${companyId}/webhook/create`)
    
    if (createResponse.data) {
      console.log('[AUTO WEBHOOK] Webhook created successfully:', createResponse.data)
      showSuccess('🚀 Webhook created automatically! Shipment tracking is now active.')
      
      // Refresh status to show updated state
      await loadWebhookStatus()
    }
    
  } catch (error) {
    console.error('[AUTO WEBHOOK] Failed to create webhook automatically:', error)
    
    // Don't show error to user for auto-creation - just log it
    // They can manually create later if needed
    console.warn('[AUTO WEBHOOK] Auto webhook creation failed, user can create manually later')
  }
}

// Customer-facing webhook management functions
const createCustomerWebhook = async () => {
  if (!canManageWebhook.value) {
    showError('You need Ship54 admin permissions to manage webhooks')
    return
  }

  customerWebhookLoading.value = true
  try {
    const companyId = authStore.decoded?.companyId?._id || authStore.decoded?.companyId
    if (!companyId) {
      showError('Company ID not found')
      return
    }

    const response = await apiClient.post(`/admin/companies/${companyId}/webhook/create`)
    
    if (response.data) {
      showSuccess('✅ Webhook created successfully! Shipment tracking is now active.')
      await refreshTrackingStatus()
    }
    
  } catch (error) {
    console.error('Failed to create webhook:', error)
    showError(`Failed to create webhook: ${error.response?.data?.error || error.message}`)
  } finally {
    customerWebhookLoading.value = false
  }
}

const deleteCustomerWebhook = async () => {
  if (!canManageWebhook.value) {
    showError('You need Ship54 admin permissions to manage webhooks')
    return
  }

  if (!confirm('Are you sure you want to delete the webhook? This will stop automatic shipment tracking.')) {
    return
  }

  customerWebhookLoading.value = true
  try {
    const companyId = authStore.decoded?.companyId?._id || authStore.decoded?.companyId
    if (!companyId) {
      showError('Company ID not found')
      return
    }

    const response = await apiClient.delete(`/admin/companies/${companyId}/webhook`)
    
    if (response.status === 200) {
      showSuccess('🗑️ Webhook deleted successfully. Shipment tracking is now disabled.')
      await refreshTrackingStatus()
    }
    
  } catch (error) {
    console.error('Failed to delete webhook:', error)
    showError(`Failed to delete webhook: ${error.response?.data?.error || error.message}`)
  } finally {
    customerWebhookLoading.value = false
  }
}

// Role-based permissions computed properties
const canManageWebhook = computed(() => {
  // Check if user has admin role for Ship54 product
  // The roles are stored in the decoded JWT token
  const decodedToken = authStore.decoded
  const userRoles = decodedToken?.roles || {}
  
  console.log('[WEBHOOK PERMISSIONS] Checking permissions...')
  console.log('[WEBHOOK PERMISSIONS] User roles:', userRoles)
  console.log('[WEBHOOK PERMISSIONS] Decoded token:', decodedToken)
  
  // Check if user has Ship54 admin role
  const ship54Roles = userRoles.ship54 || []
  const hasShip54Admin = Array.isArray(ship54Roles) && ship54Roles.includes('admin')
  
  console.log('[WEBHOOK PERMISSIONS] Ship54 roles:', ship54Roles)
  console.log('[WEBHOOK PERMISSIONS] Has Ship54 admin:', hasShip54Admin)
  return hasShip54Admin
})

// Shippo token management computed properties
const isShippoConnected = computed(() => {
  return settings.value.shippo.customerToken?.isValid || false
})

const isValidTokenFormat = computed(() => {
  if (!shippoTokenInput.value) return false
  return /^shippo_(test|live)_[a-f0-9]{40}$/.test(shippoTokenInput.value)
})

const shippoTokenEnvironment = computed(() => {
  const env = settings.value.shippo.customerToken?.environment
  return env ? env.charAt(0).toUpperCase() + env.slice(1) : 'Unknown'
})

const formatLastTested = computed(() => {
  const lastTested = settings.value.shippo.customerToken?.lastTested
  if (!lastTested) return 'Never'
  
  const date = new Date(lastTested)
  const now = new Date()
  const diffMinutes = Math.floor((now - date) / (1000 * 60))
  
  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes} min ago`
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} hr ago`
  return date.toLocaleDateString()
})

// Shippo token management functions
async function validateAndSaveToken() {
  validating.value = true
  tokenError.value = null
  
  try {
    if (!isValidTokenFormat.value) {
      tokenError.value = 'Invalid token format. Token should start with shippo_test_ or shippo_live_'
      return
    }
    
    // Test token with Shippo API
    const response = await apiClient.post('/ship54/shippo/validate-token', {
      token: shippoTokenInput.value
    })
    
    if (response.data.success) {
      // Update settings with validated token info
      settings.value.shippo.customerToken = {
        encrypted: response.data.encrypted, // Backend returns encrypted version
        isValid: true,
        lastTested: new Date().toISOString(),
        testResults: response.data.accountInfo,
        environment: response.data.environment
      }
      settings.value.shippo.connected = true
      
      await saveSettings()
      showSuccess(`✅ Shippo token validated and saved! Environment: ${response.data.environment}`)
      
      // Auto-create webhook for new token
      await createWebhookAutomatically()
      
      shippoTokenInput.value = ''
      showUpdateToken.value = false
    } else {
      tokenError.value = response.data.error || 'Token validation failed'
    }
  } catch (err) {
    console.error('Token validation failed:', err)
    tokenError.value = err.response?.data?.error || 'Failed to validate token'
  } finally {
    validating.value = false
  }
}

async function testTokenConnection() {
  testing.value = true
  
  try {
    const response = await apiClient.post('/ship54/shippo/test-token')
    
    if (response.data.success) {
      // Update last tested time and results
      settings.value.shippo.customerToken.lastTested = new Date().toISOString()
      settings.value.shippo.customerToken.testResults = response.data.accountInfo
      
      await saveSettings()
      showSuccess('✅ Shippo connection test successful!')
    } else {
      showError(`❌ Connection test failed: ${response.data.error}`)
    }
  } catch (err) {
    console.error('Token test failed:', err)
    showError(`❌ Connection test failed: ${err.response?.data?.error || err.message}`)
  } finally {
    testing.value = false
  }
}

async function removeToken() {
  removing.value = true
  
  try {
    await apiClient.delete('/ship54/shippo/remove-token')
    
    // Reset token state
    settings.value.shippo.customerToken = {
      encrypted: null,
      isValid: false,
      lastTested: null,
      testResults: null,
      environment: 'test'
    }
    settings.value.shippo.connected = false
    
    await saveSettings()
    showSuccess('🗑️ Shippo token removed successfully')
  } catch (err) {
    console.error('Failed to remove token:', err)
    showError(`Failed to remove token: ${err.response?.data?.error || err.message}`)
  } finally {
    removing.value = false
  }
}

function cancelUpdateToken() {
  showUpdateToken.value = false
  shippoTokenInput.value = ''
  tokenError.value = null
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