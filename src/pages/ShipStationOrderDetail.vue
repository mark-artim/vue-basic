<template>
  <v-container
    fluid
    class="pa-4"
  >
    <v-card
      max-width="800"
      class="mx-auto"
    >
      <v-card-title style="color: dodgerblue;">
        <strong>Shipment Preparation for:</strong> {{ invoice }} - {{ shipVia }}
      </v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col cols="6">
            <strong>Invoice #:</strong> {{ invoice }}
          </v-col>
          <v-col cols="6">
            <strong>Ship To:</strong> {{ shippingName }}
          </v-col>
          <v-col cols="6">
            <strong>Ship Branch:</strong> {{ shipBranchName }}
          </v-col>
          <v-col cols="6">
            <strong>Ship Date:</strong> {{ shipDate }}
          </v-col>
          <v-col cols="6">
            <strong>PO Number:</strong> {{ poNumber }}
          </v-col>
          <v-col cols="12">
            <strong>Balance Due:</strong>
            {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
              .format(balanceDue) }}
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <v-row dense>
          <v-col cols="6">
            <v-text-field
              v-model="salesTotal"
              label="Sales Total"
              readonly
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="writer"
              label="Writer"
              readonly
            />
          </v-col>
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
              readonly
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="shippingAddressLine1"
              label="Ship To Address Line 1"
              readonly
            />
          </v-col>
          <v-col cols="12">
            <v-text-field
              v-model="shippingAddressLine2"
              label="Ship To Address Line 2"
              readonly
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="cityStateZip"
              label="City, State, ZIP"
              readonly
            />
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <v-row dense>
          <v-col cols="12">
            <strong>Ship From:</strong> {{ shipFrom.name }}<br>
            {{ shipFrom.addressLine1 }}<br>
            {{ shipFrom.addressLine2 }}<br>
            {{ shipFrom.city }}, {{ shipFrom.state }} {{ shipFrom.postalCode }}<br>
            {{ shipFrom.phone }} | {{ shipFrom.email }}
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <v-row dense>
          <v-col cols="12">
            <v-radio-group
              v-model="shippingMethod"
              label="Freight Posting Method"
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
            <div v-if="freightProductInfo" class="mt-2 pa-3" style="background-color: #f5f5f5; border-radius: 4px; color: #333;">
              <div class="text-body-2" style="color: #333;">
                <strong>Product:</strong> {{ freightProductInfo.id }} - {{ freightProductInfo.description }}
              </div>
              <div v-if="freightProductInfo.category" class="text-caption" style="color: #666;">
                Category: {{ freightProductInfo.category }}
              </div>
            </div>
          </v-col>
        </v-row>

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
            />
          </v-col>
        </v-row>

        <v-card-actions class="mt-4">
          <v-btn
            color="primary"
            :disabled="!canGetRates"
            @click="getRates"
          >
            Get Rates
          </v-btn>
          <v-btn
            color="secondary"
            :disabled="!selectedRateId"
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
      <v-card-title>Available Shipping Rates</v-card-title>
      <v-data-table
        v-model="selectedRates"
        :headers="rateHeaders"
        :items="rates"
        item-value="object_id"
        show-select
        single-select
        return-object
        dense
        class="elevation-1"
      >
        <template #item.amount="{ item }">
          {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.amount) }}
        </template>
        <template #no-data>
          No rates returned.
        </template>
      </v-data-table>
      <template #headers="{ columns }">
        <div>headers supposed to show here</div>
        <tr>
          <th
            v-for="column in columns"
            :key="column.value"
          >
            {{ column.text }}
          </th>
        </tr>
      </template>
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
          <p class="text-body-1 mb-2">
            Freight line item has been added to the invoice and print status updated to "P".
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/utils/axios'
import { useShipFromStore } from '@/stores/useShipFromStore'
import { getOrder } from '@/api/orders'
import { getProduct } from '@/api/products'
const shipFrom = useShipFromStore()

const route = useRoute()
const router = useRouter()
const invoice = route.params.invoice

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
  { text: 'Service Level', value: 'serviceLevelName' },
  { text: 'Est. Days', value: 'estimatedDays' },
  { text: 'Duration Terms', value: 'durationTerms' },
  { text: 'Amount (USD)', value: 'amount' }
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
            comments: `Carrier: ${labelResponse.rate?.provider || 'N/A'} Ship Method: ${labelResponse.rate?.servicelevel?.name || selectedRateId.value.serviceLevelName || 'N/A'} Tracking: ${labelResponse.tracking_number || 'N/A'}`,
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

onMounted(async () => {
  try {
    // Load user's Ship54 settings first
    await loadShip54Settings()
    
    // Load order details
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
      amount: parseFloat(r.amount)
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

  if (shippingMethod.value === 'lineitem' && !freightProductId.value) {
    alert('Please enter a Freight Product ID for Invoice Line Item method')
    return
  }

  try {
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
  } catch (err) {
    console.error('Failed to ship package:', err)
    alert(`Error: ${err.message}`)
  }
}
</script>

<style scoped>
.v-card-text {
  padding-top: 0;
}
</style>
