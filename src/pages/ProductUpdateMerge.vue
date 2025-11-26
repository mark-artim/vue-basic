<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="mb-6">
          Product Update Merge
        </h2>

        <!-- Product Selection Section -->
        <v-card class="mb-6">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="primary"
            >
              mdi-package-variant
            </v-icon>
            Product Selection
          </v-card-title>
          <v-card-text>
            <v-row>
              <!-- Keeper Product Search -->
              <v-col cols="12" md="6">
                <h4 class="mb-3">Keeper Product</h4>
                <v-autocomplete
                  v-model="selectedKeeperProduct"
                  :items="keeperProductResults"
                  item-title="title"
                  item-value="value"
                  label="Search Keeper Product"
                  placeholder="Type to search for keeper product..."
                  hint="Search and select the product to keep"
                  persistent-hint
                  :loading="keeperProductSearchLoading"
                  no-data-text="No matching products found"
                  clearable
                  @input="debugKeeperInput"
                  @update:model-value="onKeeperProductSelected"
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
              </v-col>

              <!-- Merge Product Search -->
              <v-col cols="12" md="6">
                <h4 class="mb-3">Merge Product</h4>
                <v-autocomplete
                  v-model="selectedMergeProduct"
                  :items="mergeProductResults"
                  item-title="title"
                  item-value="value"
                  label="Search Merge Product"
                  placeholder="Type to search for merge product..."
                  hint="Search and select the product to merge"
                  persistent-hint
                  :loading="mergeProductSearchLoading"
                  no-data-text="No matching products found"
                  hide-no-data
                  clearable
                  @input="onMergeProductInput"
                  @update:model-value="onMergeProductSelected"
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
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Selected Products Display -->
        <v-card
          v-if="keeperProductInfo || mergeProductInfo"
          class="mb-6"
        >
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="success"
            >
              mdi-check-circle
            </v-icon>
            Selected Products
          </v-card-title>
          <v-card-text>
            <v-row>
              <!-- Keeper Product Info -->
              <v-col cols="12" md="6">
                <div v-if="keeperProductInfo">
                  <h4 class="text-success mb-2">Keeper Product</h4>
                  <div class="product-info">
                    <div class="text-body-1 font-weight-bold">
                      ID: {{ keeperProductInfo.id }}
                    </div>
                    <div class="text-body-2">
                      Description: {{ keeperProductInfo.description }}
                    </div>
                    <div v-if="keeperProductInfo.keywords" class="text-caption mt-1">
                      Current Keywords: {{ keeperProductInfo.keywords }}
                    </div>
                  </div>
                </div>
                <div v-else class="text-disabled">
                  No keeper product selected
                </div>
              </v-col>

              <!-- Merge Product Info -->
              <v-col cols="12" md="6">
                <div v-if="mergeProductInfo">
                  <h4 class="text-warning mb-2">Merge Product</h4>
                  <div class="product-info">
                    <div class="text-body-1 font-weight-bold">
                      ID: {{ mergeProductInfo.id }}
                    </div>
                    <div class="text-body-2">
                      Description: {{ mergeProductInfo.description }}
                    </div>
                    <div v-if="mergeProductInfo.keywords" class="text-caption mt-1">
                      Current Keywords: {{ mergeProductInfo.keywords }}
                    </div>
                  </div>
                </div>
                <div v-else class="text-disabled">
                  No merge product selected
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Updated Keywords Section -->
        <v-card
          v-if="updatedKeywords"
          class="mb-6"
        >
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="info"
            >
              mdi-text-search
            </v-icon>
            Updated Keywords
          </v-card-title>
          <v-card-text>
            <div class="updated-keywords-container">
              <h4 class="mb-3">Merged Keywords for Keeper Product:</h4>
              <v-textarea
                v-model="updatedKeywords"
                label="Updated Keywords"
                rows="4"
                readonly
                variant="outlined"
                class="mb-3"
              />
              <div class="text-caption text-medium-emphasis">
                These keywords combine the existing keywords from the keeper product with keywords and description from the merge product, with duplicates removed.
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Action Buttons -->
        <v-card>
          <v-card-actions class="pa-4">
            <v-btn
              color="secondary"
              variant="outlined"
              @click="clearSelections"
            >
              <v-icon left>
                mdi-refresh
              </v-icon>
              Clear All
            </v-btn>

            <v-spacer />

            <v-btn
              color="primary"
              size="large"
              :disabled="!canSave"
              :loading="saving"
              @click="saveProductMerge"
            >
              <v-icon left>
                mdi-content-save
              </v-icon>
              Save Product Merge
            </v-btn>
          </v-card-actions>
        </v-card>

        <!-- Success/Error Messages -->
        <v-snackbar
          v-model="showMessage"
          :color="messageType"
          :timeout="5000"
        >
          {{ message }}
        </v-snackbar>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/utils/axios'
import { searchProducts, getProduct } from '@/api/products'
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'

const authStore = useAuthStore()

// Reactive state for keeper product
const selectedKeeperProduct = ref('')
const keeperProductInfo = ref(null)
const keeperProductData = ref(null) // Store full product data for save

// Reactive state for merge product
const selectedMergeProduct = ref('')
const mergeProductInfo = ref(null)
const mergeProductData = ref(null) // Store full product data

// UI state
const saving = ref(false)
const showMessage = ref(false)
const message = ref('')
const messageType = ref('success')

// Computed updated keywords
const updatedKeywords = computed(() => {
  if (!keeperProductInfo.value || !mergeProductInfo.value) {
    return null
  }

  // Get existing keywords from keeper product
  const keeperKeywords = keeperProductInfo.value.keywords || ''

  // Get keywords and description from merge product
  const mergeKeywords = mergeProductInfo.value.keywords || ''
  const mergeDescription = mergeProductInfo.value.description || ''

  // Combine all text sources
  const allText = [keeperKeywords, mergeKeywords, mergeDescription]
    .filter(text => text && text.trim())
    .join(' ')

  // Split into words, remove duplicates, filter out short words
  const words = allText
    .toLowerCase()
    .replace(/[^\w\s]/g, ' ') // Replace punctuation with spaces
    .split(/\s+/)
    .filter(word => word.length > 2) // Only words longer than 2 characters
    .filter((word, index, arr) => arr.indexOf(word) === index) // Remove duplicates

  return words.join(' ')
})

// Check if save is allowed
const canSave = computed(() => {
  return keeperProductInfo.value &&
         mergeProductInfo.value &&
         updatedKeywords.value &&
         !saving.value
})

// Product search functions
const fetchProducts = async (query) => {
  console.log('[PRODUCT SEARCH] Starting search for:', query)

  if (!query || query.length < 2) {
    console.log('[PRODUCT SEARCH] Query too short, returning empty')
    return []
  }

  try {
    console.log('[PRODUCT SEARCH] Calling searchProducts API...')
    const result = await searchProducts(query)
    console.log('[PRODUCT SEARCH] Raw API result:', result)

    const products = result.results || result || []
    console.log('[PRODUCT SEARCH] Extracted products array:', products)
    console.log('[PRODUCT SEARCH] Number of products:', products.length)

    // Simple mapping - just return the product ID for dropdown display
    const mappedProducts = products.map(product => {
      const productId = product.id || product.productId
      console.log('[PRODUCT SEARCH] Mapping product ID:', productId)

      return {
        value: productId,
        title: productId  // Vuetify's default property for display
      }
    })

    console.log('[PRODUCT SEARCH] Final mapped products:', mappedProducts)
    return mappedProducts
  } catch (error) {
    console.error('[PRODUCT SEARCH] Failed to fetch products:', error)
    return []
  }
}

// Keeper product search setup
const {
  results: keeperProductResults,
  isLoading: keeperProductSearchLoading,
  onSearch: onKeeperProductInput
} = useDebouncedSearch(fetchProducts, 800)

// Debug keeper product results
watch(keeperProductResults, (newResults) => {
  console.log('[KEEPER AUTOCOMPLETE] Results updated:', newResults)
  console.log('[KEEPER AUTOCOMPLETE] Results length:', newResults?.length)
})

// Debug the search input - prevent clearing results when empty
const debugKeeperInput = (input) => {
  console.log('[KEEPER INPUT] Input received:', input)
  console.log('[KEEPER INPUT] Input type:', typeof input)

  // Don't clear results if input is empty but we have results
  if (!input && keeperProductResults.value.length > 0) {
    console.log('[KEEPER INPUT] Preventing clear of existing results')
    return
  }

  onKeeperProductInput(input)
}

// Merge product search setup
const {
  results: mergeProductResults,
  isLoading: mergeProductSearchLoading,
  onSearch: onMergeProductInput
} = useDebouncedSearch(fetchProducts, 800)

// Product selection handlers
const onKeeperProductSelected = async (productId) => {
  console.log('[KEEPER SELECTION] Selected:', productId)

  if (productId) {
    selectedKeeperProduct.value = productId
    await loadKeeperProductInfo(productId)
  } else {
    selectedKeeperProduct.value = ''
    keeperProductInfo.value = null
    keeperProductData.value = null
  }
}

const onMergeProductSelected = async (productId) => {
  if (productId) {
    selectedMergeProduct.value = productId
    await loadMergeProductInfo(productId)
  } else {
    selectedMergeProduct.value = ''
    mergeProductInfo.value = null
    mergeProductData.value = null
  }
}

// Load detailed product information
const loadKeeperProductInfo = async (productId) => {
  try {
    const product = await getProduct(productId)
    keeperProductData.value = product // Store full data for save

    keeperProductInfo.value = {
      id: product.productId || product.id,
      description: product.description || product.name || 'No description',
      keywords: product.keywords || product['DESC.OVRD.NUC'] || '', // Check both possible keyword fields
      category: product.category
    }
  } catch (error) {
    console.error('Failed to load keeper product info:', error)
    showError('Failed to load keeper product details')
    keeperProductInfo.value = {
      id: productId,
      description: 'Product ID: ' + productId,
      keywords: '',
      category: null
    }
  }
}

const loadMergeProductInfo = async (productId) => {
  try {
    const product = await getProduct(productId)
    mergeProductData.value = product // Store full data

    mergeProductInfo.value = {
      id: product.productId || product.id,
      description: product.description || product.name || 'No description',
      keywords: product.keywords || product['DESC.OVRD.NUC'] || '', // Check both possible keyword fields
      category: product.category
    }
  } catch (error) {
    console.error('Failed to load merge product info:', error)
    showError('Failed to load merge product details')
    mergeProductInfo.value = {
      id: productId,
      description: 'Product ID: ' + productId,
      keywords: '',
      category: null
    }
  }
}

// Save product merge
const saveProductMerge = async () => {
  if (!canSave.value) {
    showError('Please select both keeper and merge products first')
    return
  }

  saving.value = true

  try {
    // First, we need to get the full product data with update key
    const keeperProductId = keeperProductInfo.value.id

    // Get the keeper product with full data needed for update
    const fullKeeperProduct = keeperProductData.value

    if (!fullKeeperProduct) {
      throw new Error('Keeper product data not available')
    }

    // Update the keywords field in the full product object
    const updatedProduct = {
      ...fullKeeperProduct,
      'DESC.OVRD.NUC': updatedKeywords.value
    }

    // Make the API call to update the product
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'PUT',
      url: `/UserDefined/PROD.CLASS?id=${keeperProductId}`,
      data: updatedProduct
    })

    if (response.data) {
      showSuccess(`Successfully updated keywords for product ${keeperProductId}`)

      // Optionally reload the keeper product to show updated info
      await loadKeeperProductInfo(keeperProductId)
    } else {
      throw new Error('No response data received')
    }

  } catch (error) {
    console.error('Failed to save product merge:', error)
    showError(`Failed to save product merge: ${error.response?.data?.error || error.message}`)
  } finally {
    saving.value = false
  }
}

// Utility functions
const clearSelections = () => {
  selectedKeeperProduct.value = ''
  selectedMergeProduct.value = ''
  keeperProductInfo.value = null
  mergeProductInfo.value = null
  keeperProductData.value = null
  mergeProductData.value = null
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
.product-info {
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  border-left: 4px solid #1976d2;
}

.updated-keywords-container {
  background-color: #e3f2fd;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #90caf9;
}

.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.text-disabled {
  color: #9e9e9e;
  font-style: italic;
}
</style>