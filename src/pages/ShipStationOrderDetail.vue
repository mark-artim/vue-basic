<template>
  <v-container
    fluid
    class="pa-4"
  >
    <v-card
      max-width="800"
      class="mx-auto"
    >
      <v-card-title class="ma-4 text-h5" style="color: orangered;">
        <strong>{{ isManualMode ? 'Manual Shipment Creation' : `Shipment Preparation for: ${invoice} - ${shipVia}` }}</strong><br>
      </v-card-title>
      <v-card-text class="text-uppercase">
        <v-row dense>
          <v-row class="mt-6" dense>
            <v-col cols="3">
              Ship Branch:<strong>{{ shipBranchName }} </strong>
            </v-col>
            <v-col cols="3">
              Ship Date: <strong> {{ shipDate }} </strong>
            </v-col>
            <v-col cols="5">
              PO Number:<strong> {{ poNumber }} </strong> 
            </v-col>
          </v-row>
          <v-row class="mb-6" dense>
            <v-col cols="3">
              Sales Amount: <strong>
              {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
                .format(salesTotal) }}
            </strong></v-col>
            <v-col cols="3">
              Balance Due:<strong>
              {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
                .format(balanceDue) }}</strong>
            </v-col>
            <v-col cols="3">
              Order Writer: <strong>{{ writer }}</strong>
            </v-col>
          </v-row>
          <v-col cols="6">
            <strong>Ship From:</strong>
          </v-col>
          <v-col cols="6">
            <strong>Ship To:</strong>
          </v-col>
          <v-col cols="6">
            {{ shipFrom.name }}
          </v-col>
          <v-col cols="6">
            {{ shippingName }}
          </v-col>
          <v-col cols="6">
            {{ shipFrom.addressLine1 }}<br>
            <span v-if="shipFrom.addressLine2">{{ shipFrom.addressLine2 }}<br></span>
            {{ shipFrom.city }}, {{ shipFrom.state }} {{ shipFrom.postalCode }}<br>
            {{ shipFrom.phone }} | {{ shipFrom.email }}
          </v-col>
          
        </v-row>

        <v-divider class="my-4" />

        <v-row dense>
          <v-col cols="12">
            <v-textarea
              v-model="shippingInstructions"
              label="Shipping Instructions"
              readonly
              rows="2"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="shippingName"
              label="Name"
              :readonly="!isManualMode"
              :variant="isManualMode ? 'outlined' : 'filled'"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="shippingAddressLine1"
              label="Ship To Address Line 1"
              :readonly="!isManualMode"
              :variant="isManualMode ? 'outlined' : 'filled'"
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="shippingAddressLine2"
              label="Ship To Address Line 2"
              :readonly="!isManualMode"
              :variant="isManualMode ? 'outlined' : 'filled'"
            />
          </v-col>
          <v-col
            v-if="isManualMode"
            cols="4"
          >
            <v-text-field
              v-model="shippingCity"
              label="City"
              variant="outlined"
            />
          </v-col>
          <v-col
            v-if="isManualMode"
            cols="4"
          >
            <v-text-field
              v-model="shippingState"
              label="State"
              variant="outlined"
            />
          </v-col>
          <v-col
            v-if="isManualMode"
            cols="4"
          >
            <v-text-field
              v-model="postalCode"
              label="ZIP"
              variant="outlined"
            />
          </v-col>
          <v-col
            v-if="isManualMode"
            cols="12"
          >
            <v-btn
              color="primary"
              variant="text"
              size="small"
              :loading="addressValidating"
              class="mb-2"
              @click="validateAddress"
            >
              <v-icon
                start
                size="small"
              >
                mdi-check-circle
              </v-icon>
              Validate Address
            </v-btn>
            
            <!-- Address Validation Results -->
            <v-card
              v-if="addressValidationResult"
              variant="outlined"
              class="mt-4"
            >
              <v-card-title class="d-flex align-center">
                <v-icon
                  :color="addressValidationResult.is_valid ? 'success' : 'warning'"
                  class="me-2"
                >
                  {{ addressValidationResult.is_valid ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
                Address Validation Results
              </v-card-title>
              <v-card-text>
                <v-alert 
                  :type="addressValidationResult.is_valid ? 'success' : 'warning'" 
                  class="mb-2"
                >
                  {{ addressValidationResult.is_valid ? 'Address is valid' : 'Address validation warnings found' }}
                </v-alert>
                
                <div v-if="addressValidationResult.messages?.length">
                  <v-chip
                    v-for="message in addressValidationResult.messages"
                    :key="message.text"
                    :color="message.type === 'warning' ? 'warning' : 'info'"
                    class="me-2 mb-2"
                    size="small"
                  >
                    {{ message.text }}
                  </v-chip>
                </div>

                <div
                  v-if="addressValidationResult.suggested_address"
                  class="mt-4"
                >
                  <div class="text-subtitle-2 mb-2">
                    Suggested Address:
                  </div>
                  <v-card
                    variant="tonal"
                    color="info"
                  >
                    <v-card-text>
                      <div>{{ addressValidationResult.suggested_address.name }}</div>
                      <div>{{ addressValidationResult.suggested_address.street1 }}</div>
                      <div v-if="addressValidationResult.suggested_address.street2">
                        {{ addressValidationResult.suggested_address.street2 }}
                      </div>
                      <div>{{ addressValidationResult.suggested_address.city }}, {{ addressValidationResult.suggested_address.state }} {{ addressValidationResult.suggested_address.zip }}</div>
                      <v-btn
                        color="info"
                        variant="text"
                        size="small"
                        class="mt-2"
                        @click="useSuggestedAddress"
                      >
                        Use Suggested Address
                      </v-btn>
                    </v-card-text>
                  </v-card>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col
            v-if="!isManualMode"
            cols="6"
          >
            <v-text-field
              v-model="cityStateZip"
              label="City, State, ZIP"
              readonly
            />
          </v-col>
        </v-row>
        
        <v-divider class="my-4" />

        <v-expansion-panels class="my-4">
          <v-expansion-panel>
            <v-expansion-panel-title>
              Freight Posting Method
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row dense>
                <v-col cols="12">
                  <v-radio-group
                    v-model="shippingMethod"
                    row
                  >
                    <v-radio
                      label="Starship File Drop"
                      value="filedrop"
                    />
                    <v-radio
                      label="Invoice Line Item"
                      value="lineitem"
                    />
            </v-radio-group>
          </v-col>
          <v-col
            v-if="shippingMethod === 'lineitem'"
            cols="12"
          >
            <v-text-field
              v-model="freightProductId"
              label="Freight Product ID"
              placeholder="Enter Eclipse product ID for freight charges"
              required
              readonly
            />
            <div
              v-if="freightProductInfo"
              class="mt-2 pa-3"
              style="background-color: #f5f5f5; border-radius: 4px; color: #333;"
            >
              <div
                class="text-body-2"
                style="color: #333;"
              >
                <strong>Product:</strong> {{ freightProductInfo.id }} - {{ freightProductInfo.description }}
              </div>
              <div
                v-if="freightProductInfo.category"
                class="text-caption"
                style="color: #666;"
              >
                Category: {{ freightProductInfo.category }}
              </div>
            </div>
          </v-col>
        </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <v-divider class="my-4" />

        <v-row dense>
          <v-col cols="3">
            <v-text-field
              v-model="length"
              label="Length"
              suffix="in"
              type="number"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="width"
              label="Width"
              suffix="in"
              type="number"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="height"
              label="Height"
              suffix="in"
              type="number"
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="weight"
              label="Weight"
              suffix="lb"
              type="number"
            >
              <template #append>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="primary"
                  :disabled="!scaleSupported"
                  :loading="connectingToScale"
                  @click="connectToScale"
                  title="Connect to digital scale"
                >
                  <v-icon>mdi-scale</v-icon>
                </v-btn>
              </template>
            </v-text-field>
            <div v-if="scaleConnected" class="text-caption text-success">
              <v-icon size="small">mdi-check-circle</v-icon>
              Scale connected - weight auto-updating
            </div>
            <div v-else-if="!scaleSupported" class="text-caption text-warning">
              <v-icon size="small">mdi-alert</v-icon>
              Scale connection requires Chrome/Edge browser
            </div>
          </v-col>
        </v-row>

        <v-card-actions class="mt-4">
          <v-btn
            color="primary"
            size="large"
            variant="elevated"
            prepend-icon="mdi-calculator"
            :disabled="!canGetRates"
            class="font-weight-bold"
            @click="getRates"
          >
            Get Rates
          </v-btn>
          <v-btn
            color="success"
            size="large"
            variant="elevated"
            prepend-icon="mdi-package-variant"
            :disabled="!selectedRateId"
            class="font-weight-bold"
            @click="shipPackage"
          >
            Ship Package
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>

    <v-card
      v-if="rates.length"
      class="mt-6 pa-4 mx-auto"
      max-width="800"
      outlined
    >
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Available Shipping Rates</span>
        <span
          v-if="shipVia"
          class="font-weight-bold text-body-1 text-orange-accent-4"
        >
          Requested Ship Via: {{ shipVia }}
        </span>
      </v-card-title>
      <v-data-table
        v-model="selectedRates"
        :headers="rateHeaders"
        :items="rates"
        item-value="object_id"
        show-select
        single-select
        return-object
        density="compact"
        class="elevation-1"
      >
        <template #item.provider="{ item }">
          <div class="d-flex align-center ga-2">
            <img 
              v-if="item.provider_image_75" 
              :src="item.provider_image_75" 
              :alt="item.provider"
              height="24"
              style="max-width: 60px; object-fit: contain;"
            >
            <span class="font-weight-medium">{{ item.provider }}</span>
          </div>
        </template>
        <template #item.amount="{ item }">
          {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.amount) }}
        </template>
        <template #header.data-table-select>
          <!-- Empty template to hide select all checkbox -->
        </template>
        <template #no-data>
          No rates returned.
        </template>
      </v-data-table>
      <pre class="mt-4">Selected Rate: {{ selectedRateId }}</pre>
    </v-card>

    <!-- Success Modal -->
    <v-dialog
      v-model="showSuccessModal"
      max-width="500"
      persistent
    >
      <v-card>
        <v-card-title class="text-h5 text-center pa-6">
          <v-icon
            color="success"
            size="48"
            class="mb-4"
          >
            mdi-check-circle
          </v-icon>
          <div>Shipment Successful!</div>
        </v-card-title>
        
        <v-card-text class="text-center pb-2">
          <p
            v-if="!isManualMode"
            class="text-body-1 mb-2"
          >
            Freight line item has been added to the invoice and print status updated to "P".
          </p>
          <p
            v-if="isManualMode"
            class="text-body-1 mb-2"
          >
            Manual shipment has been created successfully with tracking number {{ lastLabelTracking }}.
          </p>
          <p class="text-body-2 text-medium-emphasis">
            Your shipping label opened in a new tab.
          </p>
        </v-card-text>
        
        <v-card-actions class="justify-center pb-6">
          <v-btn
            color="primary"
            size="large"
            @click="returnToShipStation"
          >
            Return to Ship54
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/utils/axios'
import { useShipFromStore } from '@/stores/useShipFromStore'
import { getOrder } from '@/api/orders'
import { getProduct } from '@/api/products'
const shipFrom = useShipFromStore()

const route = useRoute()
const router = useRouter()
const invoice = route.params.invoice

// Manual mode detection
const isManualMode = computed(() => invoice === 'MANUAL' && route.query.manual === 'true')

// Address validation state
const addressValidating = ref(false)
const addressValidationResult = ref(null)

const cityStateZip = computed(() => `${shippingCity.value}, ${shippingState.value} ${postalCode.value}`.trim())
const canGetRates = computed(() => length.value > 0 && width.value > 0 && height.value > 0 && weight.value > 0)

const shipDate = ref('')
const poNumber = ref('')
const balanceDue = ref(0)
const salesTotal = ref(0)
const writer = ref('')
const shippingInstructions = ref('')
const shippingAddressLine1 = ref('')
const shippingAddressLine2 = ref('')
const shippingCity = ref('')
const shippingState = ref('')
const postalCode = ref('')
const shippingName = ref('')
const shipVia = ref('')
const rates = ref([])
const selectedRates = ref([])
const lastLabelTracking = ref('');

// Scale connection state
const scaleSupported = ref(false)
const scaleConnected = ref(false)
const connectingToScale = ref(false)
let scalePort = null
let scaleReader = null


const selectedRateId = computed({
  get() {
    return selectedRates.value[0] ?? null
  },
  set(val) {
    selectedRates.value = val ? [val] : []
  }
})

const length = ref(null)
const width = ref(null)
const height = ref(null)
const weight = ref(null)

const shippingMethod = ref('filedrop')
const freightProductId = ref('')
const freightProductInfo = ref(null)
const showSuccessModal = ref(false)

const rateHeaders = [
  { title: 'Provider', key: 'provider' },
  { title: 'Service Level', key: 'serviceLevelName' },
  { title: 'Est. Days', key: 'estimatedDays' },
  { title: 'Duration Terms', key: 'durationTerms' },
  { title: 'Amount (USD)', key: 'amount' }
]

const shippoToken = import.meta.env.VITE_SHIPPO_API_KEY

const exportFreightFile = async (labelResponse) => {
  try {
    await apiClient.post('/postFreight', {
      invoiceNumber: invoice,
      totalFreight: selectedRateId.value.amount,
      shipVia: shipVia.value,
      trackingNumber: labelResponse.tracking_number,
      weight: weight.value,
      actualWeight: weight.value
    });
    console.log('📄 Freight info exported to ADEOUT.0');
  } catch (err) {
    console.error('❌ Failed to export freight file:', err);
  }
};

const addInvoiceLineItem = async (labelResponse) => {
  try {
    if (!freightProductId.value) {
      throw new Error('Freight Product ID is required for Invoice Line Item method');
    }

    console.log('📝 Adding freight line item to invoice...');
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'POST',
      url: `/SalesOrders/${invoice}/LineItems`,
      data: [
        {
          lineItemProduct: {
            productId: parseInt(freightProductId.value),
            quantity: 1,
            um: 'ea',
            umQuantity: 1,
            unitPrice: parseFloat(selectedRateId.value.amount),
            comments: `Carrier: ${labelResponse.rate?.provider || selectedRateId.value.provider || 'N/A'} Ship Method: ${labelResponse.rate?.servicelevel?.name || selectedRateId.value.serviceLevelName || 'N/A'} Tracking: ${labelResponse.tracking_number || 'N/A'}`,
            commentsId: '1'
          }
        }
      ]
    });

    console.log('✅ Freight line item added to invoice');
    return response.data;
  } catch (err) {
    console.error('❌ Failed to add freight line item:', err);
    throw err;
  }
};

const updatePrintStatus = async () => {
  try {
    console.log('📄 Updating print status to P...');
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'PUT',
      url: `/SalesOrders/${invoice}/PrintStatus`,
      params: {
        printStatus: 'P'
      }
    });
    console.log('✅ Print status updated to P');
    return response.data;
  } catch (err) {
    console.error('❌ Failed to update print status:', err);
    throw err;
  }
};

const returnToShipStation = () => {
  showSuccessModal.value = false;
  router.push({ name: 'Ship Station' });
};

const loadShip54Settings = async () => {
  try {
    const response = await apiClient.get('/ship54/settings')
    if (response.data && response.data.freight) {
      // Set freight posting method from user settings
      shippingMethod.value = response.data.freight.defaultMethod || 'filedrop'
      
      // Set product ID if using lineitem method
      if (response.data.freight.productId) {
        freightProductId.value = response.data.freight.productId
        
        // Load product information for display
        await loadFreightProductInfo()
      }
      
      console.log('📋 Loaded Ship54 settings:', {
        method: shippingMethod.value,
        productId: freightProductId.value
      })
    }
  } catch (err) {
    console.error('Failed to load Ship54 settings:', err)
    // Use defaults if settings can't be loaded
    shippingMethod.value = 'filedrop'
    freightProductId.value = ''
  }
};

const loadFreightProductInfo = async () => {
  if (freightProductId.value) {
    try {
      console.log('📦 Loading product info for ID:', freightProductId.value)
      const product = await getProduct(freightProductId.value)
      freightProductInfo.value = {
        id: product.productId || product.id,
        description: product.description || product.name || 'No description',
        category: product.category
      }
      console.log('✅ Loaded product info:', freightProductInfo.value)
    } catch (err) {
      console.error('Failed to load freight product info:', err)
      freightProductInfo.value = {
        id: freightProductId.value,
        description: 'Product ID: ' + freightProductId.value,
        category: null
      }
    }
  }
};

// Watch for changes in freight product ID to update product info
watch(freightProductId, async (newProductId) => {
  if (newProductId && shippingMethod.value === 'lineitem') {
    await loadFreightProductInfo()
  } else {
    freightProductInfo.value = null
  }
})

// Address validation functions for manual mode
const validateAddress = async () => {
  if (!shippingAddressLine1.value || !shippingCity.value || !shippingState.value) {
    return
  }

  addressValidating.value = true
  addressValidationResult.value = null
  
  try {
    const response = await apiClient.post('/api/shipping/validate-address', {
      name: shippingName.value,
      street1: shippingAddressLine1.value,
      street2: shippingAddressLine2.value,
      city: shippingCity.value,
      state: shippingState.value,
      zip: postalCode.value,
      country: 'US'
    })
    
    addressValidationResult.value = response.data
  } catch (error) {
    console.error('Address validation failed:', error)
    addressValidationResult.value = {
      is_valid: false,
      messages: [{ text: 'Address validation failed. Please check your address and try again.', type: 'warning' }]
    }
  } finally {
    addressValidating.value = false
  }
}

// Scale connection functions
const connectToScale = async () => {
  if (!scaleSupported.value) return
  
  try {
    connectingToScale.value = true
    
    // Request port access
    scalePort = await navigator.serial.requestPort()
    await scalePort.open({ 
      baudRate: 9600,  // Common scale baud rate
      dataBits: 8,
      parity: 'none',
      stopBits: 1
    })
    
    scaleConnected.value = true
    console.log('✅ Scale connected successfully')
    
    // Start reading weight data
    startWeightReading()
    
  } catch (error) {
    console.error('Failed to connect to scale:', error)
    scaleConnected.value = false
    alert('Failed to connect to scale. Make sure your scale is connected and try again.')
  } finally {
    connectingToScale.value = false
  }
}

const startWeightReading = async () => {
  if (!scalePort || !scaleConnected.value) return
  
  try {
    scaleReader = scalePort.readable.getReader()
    const decoder = new TextDecoder()
    
    // Continuously read weight data
    while (scaleConnected.value && scalePort.readable) {
      const { value, done } = await scaleReader.read()
      if (done) break
      
      const text = decoder.decode(value)
      const weightValue = parseScaleData(text)
      
      if (weightValue !== null) {
        weight.value = weightValue
        console.log('📏 Weight updated from scale:', weightValue, 'lbs')
      }
    }
  } catch (error) {
    console.error('Error reading from scale:', error)
    disconnectScale()
  }
}

const parseScaleData = (data) => {
  // Parse common scale data formats
  // Example formats: "12.34 LB", "ST,GS,+00012.34,LB", "12.34"
  const text = data.trim()
  
  // Remove common prefixes and find weight value
  const weightMatch = text.match(/([+-]?\d+\.?\d*)\s*(?:lb|lbs?|pounds?)?/i)
  if (weightMatch) {
    const value = parseFloat(weightMatch[1])
    return value > 0 ? value : null
  }
  
  return null
}

const disconnectScale = async () => {
  try {
    if (scaleReader) {
      await scaleReader.cancel()
      scaleReader = null
    }
    if (scalePort) {
      await scalePort.close()
      scalePort = null
    }
    scaleConnected.value = false
    console.log('📡 Scale disconnected')
  } catch (error) {
    console.error('Error disconnecting scale:', error)
  }
}

const useSuggestedAddress = () => {
  if (addressValidationResult.value?.suggested_address) {
    const suggested = addressValidationResult.value.suggested_address
    shippingName.value = suggested.name || shippingName.value
    shippingAddressLine1.value = suggested.street1
    shippingAddressLine2.value = suggested.street2 || ''
    shippingCity.value = suggested.city
    shippingState.value = suggested.state
    postalCode.value = suggested.zip
  }
}

onMounted(async () => {
  try {
    // Check if Web Serial API is supported for scale connection
    scaleSupported.value = 'serial' in navigator && 'requestPort' in navigator.serial
    console.log('🔌 Scale support:', scaleSupported.value ? 'Available' : 'Not supported')
    
    // Load user's Ship54 settings first
    await loadShip54Settings()
    
    if (isManualMode.value) {
      // Manual mode: Initialize with defaults for manual entry
      console.log('🔧 Initializing manual shipping mode')
      shipDate.value = new Date().toISOString().split('T')[0]
      poNumber.value = ''
      balanceDue.value = 0
      salesTotal.value = 0
      writer.value = 'MANUAL'
      shippingInstructions.value = 'Manual shipment creation'
      shippingAddressLine1.value = ''
      shippingAddressLine2.value = ''
      shippingCity.value = ''
      shippingState.value = ''
      postalCode.value = ''
      shippingName.value = ''
      shipVia.value = 'MANUAL'
    } else {
      // Normal mode: Load order details
      const data = await getOrder(invoice)
      const gen = Array.isArray(data.generations) && data.generations.length ? data.generations[0] : {}
      shipDate.value = gen.shipDate
      poNumber.value = gen.poNumber
      balanceDue.value = gen.balanceDue?.value ?? 0
      salesTotal.value = gen.salesTotal?.value ?? 0
      writer.value = gen.writer
      shippingInstructions.value = gen.shippingInstructions
      shippingAddressLine1.value = gen.shippingAddressLine1
      shippingAddressLine2.value = gen.shippingAddressLine2
      shippingCity.value = gen.shippingCity
      shippingState.value = gen.shippingState
      postalCode.value = gen.postalCode
      shippingName.value = gen.shipToName
      shipVia.value = gen.shipVia
    }
  } catch (e) {
    console.error('Failed to load order details', e)
  }
})

async function getRates() {
  try {
    const payload = {
      address_to: {
        name: shippingName.value,
        street1: shippingAddressLine1.value,
        city: shippingCity.value,
        state: shippingState.value,
        zip: postalCode.value,
        country: 'US'
      },
      address_from: {
        name: shipFrom.name,
        street1: shipFrom.addressLine1,
        city: shipFrom.city,
        state: shipFrom.state,
        zip: shipFrom.postalCode,
        country: 'US',
        email: shipFrom.email,
        phone: shipFrom.phone
      },
      parcels: [
        {
          length: String(length.value),
          width: String(width.value),
          height: String(height.value),
          distance_unit: 'in',
          weight: String(weight.value),
          mass_unit: 'lb'
        }
      ],
      async: false,
      carrier_accounts: [
        'd7bb6c9a613c4824810c1899a38ebb1b',
        'ddf399237b364b81afaf79860e9c33ba',
        'ef78c6755d9e4561a44756d80cc23c1f',
      ]
    }

    const resp = await fetch('https://api.goshippo.com/shipments/', {
      method: 'POST',
      headers: {
        Authorization: `ShippoToken ${shippoToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!resp.ok) throw new Error(`Shippo error ${resp.status}`)
    const data = await resp.json()
    rates.value = (data.rates || []).map(r => ({
      object_id: r.object_id,
      serviceLevelName: r.servicelevel?.name || r.servicelevel?.display_name,
      estimatedDays: r.estimated_days,
      durationTerms: r.duration_terms,
      amount: parseFloat(r.amount),
      provider: r.provider,
      provider_image_75: r.provider_image_75,
      provider_image_200: r.provider_image_200
    }))
    console.log('✅ rates:', JSON.stringify(rates.value, null, 2))
  } catch (err) {
    console.error('Get Rates failed:', err)
  }
}

async function shipPackage() {
  const rate = selectedRateId.value
  if (!rate?.object_id) {
    console.warn('No rate selected')
    return
  }

  if (!isManualMode.value && shippingMethod.value === 'lineitem' && !freightProductId.value) {
    alert('Please enter a Freight Product ID for Invoice Line Item method')
    return
  }

  try {
    if (isManualMode.value) {
      // Manual mode: Use the manual shipment creation endpoint
      console.log('📦 Creating manual shipment...')
      
      const manualShipmentData = {
        from: {
          name: shipFrom.name,
          addressLine1: shipFrom.addressLine1,
          addressLine2: shipFrom.addressLine2 || '',
          city: shipFrom.city,
          state: shipFrom.state,
          postalCode: shipFrom.postalCode,
          phone: shipFrom.phone || '',
          email: shipFrom.email || ''
        },
        to: {
          name: shippingName.value,
          addressLine1: shippingAddressLine1.value,
          addressLine2: shippingAddressLine2.value || '',
          city: shippingCity.value,
          state: shippingState.value,
          postalCode: postalCode.value,
          phone: ''
        },
        details: {
          invoiceNumber: `MANUAL-${Date.now()}`,
          poNumber: poNumber.value || '',
          carrier: rate.serviceLevelName?.toLowerCase().includes('ups') ? 'ups' : 
                  rate.serviceLevelName?.toLowerCase().includes('fedex') ? 'fedex' : 'ups',
          weight: parseFloat(weight.value),
          value: null,
          description: `Manual shipment via ${rate.serviceLevelName}`
        },
        source: 'manual'
      }

      const response = await apiClient.post('/api/shipments/create-manual', manualShipmentData)
      const data = response.data
      
      console.log('✅ Manual shipment created:', data)
      console.log('🔗 Label URL:', data.label_url)
      console.log('📞 Tracking number:', data.tracking_number)
      
      if (data.label_url) {
        console.log('📄 Opening PDF in new tab...')
        window.open(data.label_url, '_blank')
      } else {
        console.error('❌ No label_url found in response')
      }
      
      lastLabelTracking.value = data.tracking_number
      
      // Show success modal
      console.log('🎉 About to show success modal for manual shipment');
      showSuccessModal.value = true
      console.log('🎉 Modal state set to:', showSuccessModal.value);
      
    } else {
      // Normal mode: Use existing Shippo workflow
      const response = await fetch('https://api.goshippo.com/transactions', {
        method: 'POST',
        headers: {
          Authorization: `ShippoToken ${shippoToken}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          rate: rate.object_id,
          label_file_type: 'PDF',
          async: 'false'
        })
      })
      if (!response.ok) throw new Error(`Transaction failed: ${response.status}`)
      const data = await response.json()
      console.log('📦 Shippo transaction response:', data);
      window.open(data.label_url, '_blank')
      
      lastLabelTracking.value = data.tracking_number

      // Create shipment record in our database
      try {
        console.log('💾 Creating shipment record in database...');
        
        // Build order data object from current form values
        const orderInfo = {
          orderNumber: invoice,
          invoice: invoice,
          fullInvoiceID: invoice,
          shipToName: shippingName.value,
          poNumber: poNumber.value,
          shipVia: shipVia.value
        }
        
        await createShipmentRecord(data, orderInfo)
      } catch (shipmentErr) {
        console.warn('⚠️ Failed to create shipment record (label still created):', shipmentErr)
        // Don't block the shipping process if shipment record creation fails
      }

      if (shippingMethod.value === 'filedrop') {
        await exportFreightFile(data)
      } else if (shippingMethod.value === 'lineitem') {
        await addInvoiceLineItem(data)
        await updatePrintStatus()
        
        // Show success modal
        console.log('🎉 About to show success modal');
        showSuccessModal.value = true
        console.log('🎉 Modal state set to:', showSuccessModal.value);
      }
    }
  } catch (err) {
    console.error('Failed to ship package:', err)
    alert(`Error: ${err.message}`)
  }
}

// Create shipment record in our database
async function createShipmentRecord(shippoData, orderInfo) {
  try {
    const shipmentData = {
      // Add cost information from Shippo response
      cost: {
        amount: shippoData.rate?.amount || selectedRateId.value?.amount,
        currency: shippoData.rate?.currency || 'USD'
      },
      retail_cost: {
        amount: shippoData.commercial_invoice_value || shippoData.rate?.amount || selectedRateId.value?.amount,
        currency: shippoData.rate?.currency || 'USD'
      },
      // Add order metadata for better tracking
      metadata: {
        orderId: orderInfo.orderNumber,
        invoiceNumber: orderInfo.invoice || orderInfo.fullInvoiceID,
        createdFromShipStation: true,
        orderData: {
          shipToName: orderInfo.shipToName,
          poNumber: orderInfo.poNumber,
          shipVia: orderInfo.shipVia
        }
      }
    }

    const response = await apiClient.post('/api/shipments/create-from-shipstation', {
      shippoData,
      shipmentData
    })

    console.log('✅ Shipment record created:', response.data)
    return response.data
  } catch (error) {
    console.error('❌ Failed to create shipment record:', error)
    throw error
  }
}

// Cleanup scale connection when component unmounts
onBeforeUnmount(() => {
  if (scaleConnected.value) {
    disconnectScale()
  }
})
</script>

<style scoped>
.v-card-text {
  padding-top: 0;
}
</style>
