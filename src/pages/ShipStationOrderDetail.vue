<template>
    <v-container fluid class="pa-4">
        <v-card max-width="800" class="mx-auto">
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
                        <v-text-field label="Sales Total" v-model="salesTotal" readonly />
                    </v-col>
                    <v-col cols="6">
                        <v-text-field label="Writer" v-model="writer" readonly />
                    </v-col>
                    <v-col cols="12">
                        <v-textarea label="Shipping Instructions" v-model="shippingInstructions" readonly rows="2" />
                    </v-col>
                    <v-col cols="12">
                        <v-text-field label="Name" v-model="shippingName" readonly />
                    </v-col>
                    <v-col cols="12">
                        <v-text-field label="Ship To Address Line 1" v-model="shippingAddressLine1" readonly />
                    </v-col>
                    <v-col cols="12">
                        <v-text-field label="Ship To Address Line 2" v-model="shippingAddressLine2" readonly />
                    </v-col>
                    <v-col cols="6">
                        <v-text-field label="City, State, ZIP" v-model="cityStateZip" readonly />
                    </v-col>
                </v-row>

                <v-divider class="my-4" />

                <v-row dense>
                    <v-col cols="12">
                        <strong>Ship From:</strong> {{ shipFrom.name }}<br />
                        {{ shipFrom.addressLine1 }}<br />
                        {{ shipFrom.addressLine2 }}<br />
                        {{ shipFrom.city }}, {{ shipFrom.state }} {{ shipFrom.postalCode }}<br />
                        {{ shipFrom.phone }} | {{ shipFrom.email }}
                    </v-col>
                </v-row>

                <v-divider class="my-4" />

                <v-row dense>
                    <v-col cols="3">
                        <v-text-field v-model="length" label="Length" suffix="in" type="number" />
                    </v-col>
                    <v-col cols="3">
                        <v-text-field v-model="width" label="Width" suffix="in" type="number" />
                    </v-col>
                    <v-col cols="3">
                        <v-text-field v-model="height" label="Height" suffix="in" type="number" />
                    </v-col>
                    <v-col cols="3">
                        <v-text-field v-model="weight" label="Weight" suffix="lb" type="number" />
                    </v-col>
                </v-row>

                <v-card-actions class="mt-4">
                    <v-btn color="primary" :disabled="!canGetRates" @click="getRates">
                        Get Rates
                    </v-btn>
                    <v-btn color="secondary" :disabled="!selectedRateId" @click="shipPackage">
                        Ship Package
                    </v-btn>
                </v-card-actions>
            </v-card-text>
        </v-card>

        <v-card v-if="rates.length" class="mt-6 pa-4 mx-auto" max-width="800" outlined>
            <v-card-title>Available Shipping Rates</v-card-title>
            <v-data-table
                :headers="rateHeaders"
                :items="rates"
                item-value="object_id"
                v-model="selectedRates"
                show-select
                single-select
                return-object
                dense
                class="elevation-1"
            >
                <template #item.amount="{ item }">
                    {{ new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(item.amount) }}
                </template>
                <template #no-data>No rates returned.</template>
            </v-data-table>
            <template #headers="{ columns }">
                <div>headers supposed to show here</div>
                <tr>
                    <th v-for="column in columns" :key="column.value">
                    {{ column.text }}
                    </th>
                </tr>
            </template>
            <pre class="mt-4">Selected Rate: {{ selectedRateId }}</pre>
        </v-card>
    </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/utils/axios'
import { useShipFromStore } from '@/stores/useShipFromStore'
import { getOrder } from '@/api/orders'
const shipFrom = useShipFromStore()

const route = useRoute()
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



onMounted(async () => {
  try {
    // const { data } = await apiClient.get(`/SalesOrders/${invoice}`)
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
        'ddf399237b364b81afaf79860e9c33ba'
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
    // Create a new transaction to send to Eclipse called ADEOUT.0
    lastLabelTracking.value = data.tracking_number // 🧠 you’ll need this ref
    await exportFreightFile(data)
  } catch (err) {
    console.error('Failed to ship package:', err)
  }
}
</script>

<style scoped>
.v-card-text {
  padding-top: 0;
}
</style>
