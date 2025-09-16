<template>
  <v-container fluid class="pa-4">
    <v-card max-width="1200" class="mx-auto">
      <v-card-title class="text-h5 pa-4">
        Invoice Tracking: {{ $route.params.invoiceNumber || 'Search' }}
      </v-card-title>
      
      <v-card-text>
        <!-- Search Section -->
        <v-row class="mb-4">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="searchInvoice"
              label="Enter Invoice Number"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              clearable
              @keyup.enter="searchByInvoice"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-btn
              color="primary"
              size="large"
              @click="searchByInvoice"
              :loading="loading"
              block
            >
              Search Tracking
            </v-btn>
          </v-col>
          <v-col cols="12" md="3" class="d-flex align-center">
            <v-chip
              v-if="testMode"
              color="orange"
              text-color="white"
              size="small"
              class="mt-2"
            >
              <v-icon start size="small">mdi-flask</v-icon>
              Test Mode Active
            </v-chip>
            <div v-if="testMode" class="text-caption text-grey ml-2">
              Using Shippo test tracking data
            </div>
          </v-col>
        </v-row>

        <!-- Results Section -->
        <div v-if="trackingData">
          <v-alert
            v-if="trackingData.shipmentCount === 0"
            type="info"
            class="mb-4"
          >
            No shipments found for invoice: {{ trackingData.invoiceNumber }}
          </v-alert>

          <div v-else>
            <v-alert
              type="success"
              class="mb-4"
            >
              Found {{ trackingData.shipmentCount }} shipment{{ trackingData.shipmentCount > 1 ? 's' : '' }} 
              for invoice: {{ trackingData.invoiceNumber }}
            </v-alert>

            <!-- Shipments Table -->
            <v-data-table
              :headers="headers"
              :items="trackingData.shipments"
              class="elevation-1"
              :loading="loading"
            >
              <template v-slot:item.trackingNumber="{ item }">
                <div v-if="item.trackingNumber">
                  <v-chip
                    :color="getCarrierColor(item.carrier)"
                    text-color="white"
                    small
                    class="mb-1"
                  >
                    {{ item.carrier?.toUpperCase() || 'UNKNOWN' }}
                  </v-chip>
                  <br>
                  <a
                    :href="getTrackingUrl(item.carrier, item.trackingNumber)"
                    target="_blank"
                    class="text-decoration-none"
                  >
                    {{ item.trackingNumber }}
                    <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                  </a>
                </div>
                <span v-else class="text-grey">No tracking</span>
              </template>

              <template v-slot:item.internalStatus="{ item }">
                <v-chip
                  :color="getStatusColor(item.internalStatus)"
                  text-color="white"
                  small
                >
                  {{ item.internalStatus || 'UNKNOWN' }}
                </v-chip>
              </template>

              <template v-slot:item.tracking_status="{ item }">
                <div v-if="item.tracking_status">
                  <v-chip
                    :color="getTrackingStatusColor(item.tracking_status)"
                    text-color="white"
                    small
                  >
                    {{ item.tracking_status }}
                  </v-chip>
                  <div v-if="item.tracking_status_details" class="text-caption text-grey mt-1">
                    {{ item.tracking_status_details }}
                  </div>
                </div>
                <span v-else class="text-grey">No status</span>
              </template>

              <template v-slot:item.address_to="{ item }">
                <div v-if="item.address_to">
                  <div class="font-weight-medium">{{ item.address_to.name }}</div>
                  <div class="text-caption">
                    {{ item.address_to.city }}, {{ item.address_to.state }}
                  </div>
                </div>
              </template>

              <template v-slot:item.cost="{ item }">
                <div v-if="item.cost && item.cost.amount">
                  ${{ parseFloat(item.cost.amount).toFixed(2) }}
                  <div class="text-caption">{{ item.cost.currency || 'USD' }}</div>
                </div>
                <span v-else class="text-grey">-</span>
              </template>

              <template v-slot:item.createdAt="{ item }">
                {{ formatDate(item.createdAt) }}
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="d-flex ga-2">
                  <v-btn
                    color="info"
                    variant="text"
                    size="small"
                    @click="viewTimeline(item)"
                    :disabled="!item.tracking_history || item.tracking_history.length === 0"
                  >
                    Timeline
                    <v-icon size="small" class="ml-1">mdi-timeline-clock</v-icon>
                  </v-btn>
                  <v-btn
                    v-if="item.shippoLabelUrl"
                    color="primary"
                    variant="text"
                    size="small"
                    :href="item.shippoLabelUrl"
                    target="_blank"
                  >
                    Label
                    <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                  </v-btn>
                </div>
              </template>
            </v-data-table>

            <!-- Detailed Timeline View -->
            <v-row class="mt-6" v-if="selectedShipment">
              <v-col cols="12">
                <v-card elevation="2">
                  <v-card-title class="d-flex justify-space-between align-center">
                    <span>Tracking Timeline: {{ selectedShipment.trackingNumber }}</span>
                    <v-btn 
                      icon="mdi-close" 
                      variant="text" 
                      @click="selectedShipment = null"
                    />
                  </v-card-title>
                  <v-card-text>
                    <v-timeline
                      side="end"
                      line-inset="8"
                      truncate-line="start"
                    >
                      <v-timeline-item
                        v-for="(event, index) in selectedShipment.tracking_history"
                        :key="index"
                        :dot-color="getTimelineColor(event.status)"
                        size="small"
                      >
                        <template v-slot:opposite>
                          <div class="text-caption">
                            {{ formatTrackingDate(event.status_date || event.object_created) }}
                          </div>
                        </template>
                        
                        <div class="pb-4">
                          <v-chip
                            :color="getTimelineColor(event.status)"
                            text-color="white"
                            size="small"
                            class="mb-2"
                          >
                            {{ event.status || 'Unknown' }}
                          </v-chip>
                          <div class="font-weight-medium mb-1">
                            {{ formatStatusDetails(event.status_details || event.status) }}
                          </div>
                          <div v-if="event.location" class="text-body-2 text-grey">
                            📍 {{ formatLocation(event.location) }}
                          </div>
                        </div>
                      </v-timeline-item>
                    </v-timeline>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </div>

        <!-- Error State -->
        <v-alert
          v-if="error"
          type="error"
          class="mb-4"
        >
          {{ error }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/utils/axiosPublic'

const route = useRoute()
const router = useRouter()

// Reactive data
const searchInvoice = ref(route.params.invoiceNumber || '')
const trackingData = ref(null)
const loading = ref(false)
const error = ref('')
const testMode = ref(false)
const selectedShipment = ref(null)

// Table headers
const headers = [
  { title: 'Tracking Number', key: 'trackingNumber', sortable: false },
  { title: 'Internal Status', key: 'internalStatus', sortable: false },
  { title: 'Tracking Status', key: 'tracking_status', sortable: false },
  { title: 'Ship To', key: 'address_to', sortable: false },
  { title: 'Cost', key: 'cost', sortable: false },
  { title: 'Created', key: 'createdAt', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false }
]

// Methods
const searchByInvoice = async () => {
  if (!searchInvoice.value?.trim()) {
    error.value = 'Please enter an invoice number'
    return
  }

  loading.value = true
  error.value = ''
  trackingData.value = null
  selectedShipment.value = null

  try {
    let response
    if (testMode.value) {
      // Use real Shippo test API calls with test tracking numbers
      response = await apiClient.get(`/api/shipments/by-invoice/${encodeURIComponent(searchInvoice.value.trim())}?testMode=true`)
    } else {
      response = await apiClient.get(`/api/shipments/by-invoice/${encodeURIComponent(searchInvoice.value.trim())}`)
    }
    
    trackingData.value = response.data
    
    // Update URL without page reload
    if (route.params.invoiceNumber !== searchInvoice.value) {
      router.replace({ params: { invoiceNumber: searchInvoice.value.trim() } })
    }
  } catch (err) {
    console.error('Error searching invoice tracking:', err)
    error.value = err.response?.data?.message || 'Failed to retrieve tracking information'
  } finally {
    loading.value = false
  }
}

const getCarrierColor = (carrier) => {
  const colors = {
    'ups': 'brown',
    'fedex': 'purple',
    'usps': 'blue',
    'dhl': 'red'
  }
  return colors[carrier?.toLowerCase()] || 'grey'
}

const getStatusColor = (status) => {
  const colors = {
    'CREATED': 'grey',
    'LABEL_PURCHASED': 'orange', 
    'SHIPPED': 'blue',
    'IN_TRANSIT': 'purple',
    'DELIVERED': 'green',
    'EXCEPTION': 'red',
    'RETURNED': 'red'
  }
  return colors[status] || 'grey'
}

const getTrackingStatusColor = (status) => {
  const colors = {
    'DELIVERED': 'green',
    'IN_TRANSIT': 'blue',
    'PRE_TRANSIT': 'orange',
    'EXCEPTION': 'red',
    'RETURNED': 'red'
  }
  return colors[status] || 'grey'
}

const getTrackingUrl = (carrier, trackingNumber) => {
  const urls = {
    'ups': `https://www.ups.com/track?loc=en_US&tracknum=${trackingNumber}`,
    'fedex': `https://www.fedex.com/fedextrack/?trknbr=${trackingNumber}`,
    'usps': `https://tools.usps.com/go/TrackConfirmAction?tLabels=${trackingNumber}`,
    'dhl': `https://www.dhl.com/us-en/home/tracking.html?tracking-id=${trackingNumber}`
  }
  return urls[carrier?.toLowerCase()] || `https://www.google.com/search?q=${trackingNumber}+tracking`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const viewTimeline = async (shipment) => {
  // If we don't have tracking history, fetch it
  if (!shipment.tracking_history || shipment.tracking_history.length === 0) {
    try {
      const response = await apiClient.get(`/api/shipments/${shipment.shipmentId}`)
      shipment.tracking_history = response.data.tracking_history || []
    } catch (err) {
      console.error('Failed to load tracking history:', err)
    }
  }
  selectedShipment.value = shipment
}

const getTimelineColor = (status) => {
  const colors = {
    'DELIVERED': 'green',
    'IN_TRANSIT': 'blue', 
    'TRANSIT': 'blue',
    'OUT_FOR_DELIVERY': 'purple',
    'PACKAGE_ACCEPTED': 'orange',
    'PRE_TRANSIT': 'orange',
    'EXCEPTION': 'red',
    'FAILURE': 'red',
    'RETURNED': 'red'
  }
  return colors[status] || 'grey'
}

const formatTrackingDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatStatusDetails = (statusDetails) => {
  if (!statusDetails) return 'Status update'
  return statusDetails.replace(/_/g, ' ').toLowerCase()
    .replace(/\b\w/g, l => l.toUpperCase())
}

const formatLocation = (location) => {
  if (!location) return ''
  const parts = []
  if (location.city) parts.push(location.city)
  if (location.state) parts.push(location.state)
  if (location.country) parts.push(location.country)
  return parts.join(', ')
}

// Mock data generation removed - now using real Shippo test API calls

// Load test mode setting and auto-search if invoice number in URL
onMounted(async () => {
  // Load test mode setting
  try {
    const response = await apiClient.get('/api/shipments/tracking-test-mode')
    testMode.value = response.data.testMode
  } catch (err) {
    console.error('Failed to load test mode setting:', err)
    testMode.value = false
  }

  // Auto-search if invoice number in URL
  if (route.params.invoiceNumber) {
    searchByInvoice()
  }
})
</script>