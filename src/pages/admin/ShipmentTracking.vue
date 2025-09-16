<template>
  <v-container class="pa-4">
    <v-card
      class="pa-6 elevation-8"
      color="#0a0f1c"
    >
      <div class="d-flex align-center mb-4">
        <h1 class="flex-grow-1 text-white">
          Shipment Tracking
        </h1>
        <v-btn
          color="primary"
          variant="elevated"
          :loading="loading"
          @click="refreshData"
        >
          <v-icon start>
            mdi-refresh
          </v-icon>
          Refresh
        </v-btn>
      </div>

      <!-- Summary Stats Cards -->
      <v-row class="mb-6">
        <v-col
          v-for="stat in stats"
          :key="stat.title"
          cols="12"
          md="3"
        >
          <v-card
            variant="outlined"
            :color="stat.color"
          >
            <v-card-text class="text-center">
              <div class="text-h4 mb-2">
                {{ stat.value }}
              </div>
              <div class="text-subtitle-1">
                {{ stat.title }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Filters -->
      <v-card
        variant="outlined"
        class="mb-4"
      >
        <v-card-title>Filters</v-card-title>
        <v-card-text>
          <v-row>
            <v-col
              cols="12"
              md="3"
            >
              <v-select
                v-model="filters.status"
                :items="statusOptions"
                label="Status"
                clearable
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col
              cols="12"
              md="3"
            >
              <v-select
                v-model="filters.carrier"
                :items="carrierOptions"
                label="Carrier"
                clearable
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col
              cols="12"
              md="3"
            >
              <v-text-field
                v-model="filters.trackingNumber"
                label="Tracking Number"
                clearable
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col
              cols="12"
              md="3"
            >
              <v-text-field
                v-model="filters.invoiceNumber"
                label="Invoice Number"
                clearable
                variant="outlined"
                density="compact"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col
              cols="12"
              md="4"
            >
              <v-text-field
                v-model="filters.dateFrom"
                label="Date From"
                type="date"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
            <v-col
              cols="12"
              md="4"
            >
              <v-text-field
                v-model="filters.dateTo"
                label="Date To"
                type="date"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
            <v-col
              cols="12"
              md="4"
            >
              <v-checkbox
                v-model="filters.needsAttention"
                label="Needs Attention Only"
                density="compact"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="auto">
              <v-btn
                color="primary"
                :loading="loading"
                @click="applyFilters"
              >
                Apply Filters
              </v-btn>
            </v-col>
            <v-col cols="auto">
              <v-btn
                variant="outlined"
                @click="clearFilters"
              >
                Clear Filters
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Shipments Table -->
      <v-card variant="outlined">
        <v-card-title>Shipments</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="shipments"
            :loading="loading"
            item-key="_id"
            class="elevation-1"
            :items-per-page="50"
          >
            <template #item.tracking_number="{ item }">
              <v-btn
                variant="text"
                color="primary"
                @click="showShipmentDetail(item)"
              >
                {{ item.tracking_number }}
              </v-btn>
            </template>

            <template #item.statusDisplay="{ item }">
              <v-chip
                :color="getStatusColor(item.internalStatus)"
                variant="flat"
                size="small"
              >
                {{ item.statusDisplay }}
              </v-chip>
            </template>

            <template #item.needsAttention="{ item }">
              <v-icon
                v-if="item.needsAttention || item.isOverdue"
                color="warning"
                size="small"
              >
                mdi-alert-circle
              </v-icon>
            </template>

            <template #item.cost="{ item }">
              <div v-if="item.cost">
                ${{ parseFloat(item.cost.amount).toFixed(2) }}
                <small class="text-grey">{{ item.cost.currency }}</small>
              </div>
              <span
                v-else
                class="text-grey"
              >—</span>
            </template>

            <template #item.createdAt="{ item }">
              {{ formatDate(item.createdAt) }}
            </template>

            <template #item.shipDate="{ item }">
              {{ item.shipDate ? formatDate(item.shipDate) : '—' }}
            </template>

            <template #item.actions="{ item }">
              <v-btn
                icon="mdi-eye"
                variant="text"
                size="small"
                @click="showShipmentDetail(item)"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent">
                  View Details
                </v-tooltip>
              </v-btn>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-card>

    <!-- Shipment Detail Dialog -->
    <v-dialog
      v-model="detailDialog"
      max-width="800px"
    >
      <v-card v-if="selectedShipment">
        <v-card-title class="d-flex align-center">
          <span>Shipment Details</span>
          <v-spacer />
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="detailDialog = false"
          />
        </v-card-title>
        
        <v-card-text>
          <v-row>
            <v-col
              cols="12"
              md="6"
            >
              <v-card
                variant="outlined"
                class="mb-4"
              >
                <v-card-title>Shipping Information</v-card-title>
                <v-card-text>
                  <div class="mb-2">
                    <strong>Tracking Number:</strong> {{ selectedShipment.tracking_number }}
                  </div>
                  <div class="mb-2">
                    <strong>Carrier:</strong> {{ selectedShipment.carrier }}
                  </div>
                  <div class="mb-2">
                    <strong>Service Level:</strong> {{ selectedShipment.servicelevel }}
                  </div>
                  <div class="mb-2">
                    <strong>Status:</strong>
                    <v-chip
                      :color="getStatusColor(selectedShipment.internalStatus)"
                      variant="flat"
                      size="small"
                      class="ml-2"
                    >
                      {{ selectedShipment.statusDisplay }}
                    </v-chip>
                  </div>
                  <div class="mb-2">
                    <strong>Invoice Number:</strong> {{ selectedShipment.invoiceNumber || '—' }}
                  </div>
                  <div class="mb-2">
                    <strong>Ship Date:</strong> {{ selectedShipment.shipDate ? formatDate(selectedShipment.shipDate) : '—' }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col
              cols="12"
              md="6"
            >
              <v-card
                variant="outlined"
                class="mb-4"
              >
                <v-card-title>Cost Information</v-card-title>
                <v-card-text>
                  <div class="mb-2">
                    <strong>Shipping Cost:</strong>
                    {{ selectedShipment.cost ? `$${parseFloat(selectedShipment.cost.amount).toFixed(2)} ${selectedShipment.cost.currency}` : '—' }}
                  </div>
                  <div class="mb-2">
                    <strong>Retail Cost:</strong>
                    {{ selectedShipment.retail_cost ? `$${parseFloat(selectedShipment.retail_cost.amount).toFixed(2)} ${selectedShipment.retail_cost.currency}` : '—' }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Tracking Timeline -->
          <v-card
            v-if="selectedShipment.tracking_history?.length"
            variant="outlined"
          >
            <v-card-title>Tracking Timeline</v-card-title>
            <v-card-text>
              <v-timeline density="compact">
                <v-timeline-item
                  v-for="(event, index) in selectedShipment.tracking_history"
                  :key="index"
                  size="small"
                  :color="getTrackingEventColor(event.status)"
                >
                  <div class="d-flex justify-space-between">
                    <div>
                      <div class="font-weight-medium">
                        {{ event.status_details || event.status }}
                      </div>
                      <div class="text-caption text-grey">
                        {{ event.location || 'Location unknown' }}
                      </div>
                    </div>
                    <div class="text-caption">
                      {{ formatDateTime(event.datetime) }}
                    </div>
                  </div>
                </v-timeline-item>
              </v-timeline>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from '@/utils/axios'

export default {
  name: 'ShipmentTracking',
  setup() {
    const loading = ref(false)
    const shipments = ref([])
    const detailDialog = ref(false)
    const selectedShipment = ref(null)
    
    const filters = reactive({
      status: null,
      carrier: null,
      trackingNumber: '',
      invoiceNumber: '',
      dateFrom: '',
      dateTo: '',
      needsAttention: false
    })

    const statsData = ref({
      total_shipments: 0,
      status_breakdown: {},
      needing_attention: 0,
      total_shipping_cost: 0
    })

    const stats = computed(() => [
      {
        title: 'Total Shipments',
        value: statsData.value.total_shipments,
        color: 'primary'
      },
      {
        title: 'Delivered',
        value: statsData.value.status_breakdown?.DELIVERED || 0,
        color: 'success'
      },
      {
        title: 'In Transit',
        value: (statsData.value.status_breakdown?.IN_TRANSIT || 0) + (statsData.value.status_breakdown?.SHIPPED || 0),
        color: 'info'
      },
      {
        title: 'Needs Attention',
        value: statsData.value.needing_attention,
        color: 'warning'
      }
    ])

    const headers = [
      { title: 'Tracking #', key: 'tracking_number', sortable: true },
      { title: 'Status', key: 'statusDisplay', sortable: true },
      { title: 'Carrier', key: 'carrier', sortable: true },
      { title: 'Invoice #', key: 'invoiceNumber', sortable: true },
      { title: 'Cost', key: 'cost', sortable: false },
      { title: 'Ship Date', key: 'shipDate', sortable: true },
      { title: 'Created', key: 'createdAt', sortable: true },
      { title: 'Alert', key: 'needsAttention', sortable: false },
      { title: 'Actions', key: 'actions', sortable: false }
    ]

    const statusOptions = [
      { title: 'Created', value: 'CREATED' },
      { title: 'Label Purchased', value: 'LABEL_PURCHASED' },
      { title: 'Shipped', value: 'SHIPPED' },
      { title: 'In Transit', value: 'IN_TRANSIT' },
      { title: 'Out for Delivery', value: 'OUT_FOR_DELIVERY' },
      { title: 'Delivered', value: 'DELIVERED' },
      { title: 'Exception', value: 'EXCEPTION' },
      { title: 'Returned', value: 'RETURNED' }
    ]

    const carrierOptions = [
      { title: 'UPS', value: 'ups' },
      { title: 'FedEx', value: 'fedex' },
      { title: 'USPS', value: 'usps' },
      { title: 'DHL', value: 'dhl' }
    ]

    const getStatusColor = (status) => {
      const colors = {
        'CREATED': 'grey',
        'LABEL_PURCHASED': 'info',
        'SHIPPED': 'primary',
        'IN_TRANSIT': 'primary',
        'OUT_FOR_DELIVERY': 'warning',
        'DELIVERED': 'success',
        'EXCEPTION': 'error',
        'RETURNED': 'error'
      }
      return colors[status] || 'grey'
    }

    const getTrackingEventColor = (status) => {
      return getStatusColor(status)
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    const formatDateTime = (dateString) => {
      return new Date(dateString).toLocaleString()
    }

    const fetchShipments = async () => {
      loading.value = true
      try {
        const params = new URLSearchParams()
        
        if (filters.status) params.append('status', filters.status)
        if (filters.carrier) params.append('carrier', filters.carrier)
        if (filters.trackingNumber) params.append('trackingNumber', filters.trackingNumber)
        if (filters.invoiceNumber) params.append('invoiceNumber', filters.invoiceNumber)
        if (filters.dateFrom) params.append('dateFrom', filters.dateFrom)
        if (filters.dateTo) params.append('dateTo', filters.dateTo)
        if (filters.needsAttention) params.append('needsAttention', 'true')

        const queryString = params.toString()
        const url = queryString ? `/api/shipments?${queryString}` : '/api/shipments'
        const response = await axios.get(url)
        shipments.value = response.data.shipments
      } catch (error) {
        console.error('Error fetching shipments:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/shipments/summary/stats')
        statsData.value = response.data
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }

    const refreshData = async () => {
      await Promise.all([
        fetchShipments(),
        fetchStats()
      ])
    }

    const applyFilters = () => {
      fetchShipments()
    }

    const clearFilters = () => {
      Object.keys(filters).forEach(key => {
        if (typeof filters[key] === 'boolean') {
          filters[key] = false
        } else {
          filters[key] = null
        }
      })
      fetchShipments()
    }

    const showShipmentDetail = (shipment) => {
      selectedShipment.value = shipment
      detailDialog.value = true
    }

    onMounted(() => {
      // Check for query parameters (like invoice number from ShipStation)
      const route = useRoute()
      if (route.query.invoiceNumber) {
        filters.invoiceNumber = route.query.invoiceNumber
      }
      refreshData()
    })

    return {
      loading,
      shipments,
      filters,
      stats,
      headers,
      statusOptions,
      carrierOptions,
      detailDialog,
      selectedShipment,
      getStatusColor,
      getTrackingEventColor,
      formatDate,
      formatDateTime,
      refreshData,
      applyFilters,
      clearFilters,
      showShipmentDetail
    }
  }
}
</script>

<style scoped>
.features-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-item {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}
</style>