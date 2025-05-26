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

                <!-- Additional generation fields -->
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

                <!-- Hard-coded ship-from info -->
                <v-row dense>
                    <v-col cols="12">
                        <strong>Ship From:</strong> {{ shipBranchName }}<br />
                        {{ shipFromAddressLine1 }}<br />
                        {{ shipFromAddressLine2 }}<br />
                        {{ shipFromCity }}, {{ shipFromState }} {{ shipFromPostalCode }}
                    </v-col>
                </v-row>

                <v-divider class="my-4" />

                <!-- User-input dims & weight -->
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

                <!-- future buttons for Get Rates / Ship Package -->
                <v-card-actions class="mt-4">
                    <v-btn color="primary" :disabled="!canGetRates" @click="getRates">
                        Get Rates
                    </v-btn>
                    <v-btn
                        color="secondary"
                        :disabled="!selectedRateId.length"
                        @click="shipPackage"
                        >
                        Ship Package
                    </v-btn>

                </v-card-actions>
            </v-card-text>
        </v-card>
        <!-- show the rates table once we have them -->
        <v-card v-if="rates.length" class="mt-6 pa-4 mx-auto" max-width="800" outlined>
        <v-card-title>Available Shipping Rates</v-card-title>
        <v-data-table
            :headers="rateHeaders"
            :items="rates"
            item-value="object_id"
            v-model:selected="selectedRates"
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
        <pre class="mt-4">Selected Rate:
            {{ selectedRateId }}
        </pre>
        </v-card>
    </v-container>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/utils/axios'

const route = useRoute()
const invoice = route.params.invoice

const cityStateZip = computed(() => {
    return `${shippingCity.value}, ${shippingState.value} ${postalCode.value}`.trim()
})

const canGetRates = computed(() =>
    length.value > 0 &&
    width.value > 0 &&
    height.value > 0 &&
    weight.value > 0
)

// detail fields
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
// const selectedRateId = ref([])
const selectedRates = ref([])

const selectedRateId = computed({
  get() {
    return selectedRates.value[0] ?? null
  },
  set(val) {
    selectedRates.value = val ? [val] : []
  }
})



// hard-coded “ship from”
const shipBranchName = 'NuComfort Supply'
const shipFromAddressLine1 = '450 Tower Blvd'
const shipFromAddressLine2 = 'Suite 100'
const shipFromCity = 'Carol Stream'
const shipFromState = 'IL'
const shipFromPostalCode = '60188'

// dims & weight
const length = ref(null)
const width = ref(null)
const height = ref(null)
const weight = ref(null)

// headers for the rates table
const rateHeaders = [
    { text: 'Service Level', value: 'serviceLevelName' },
    { text: 'Est. Days', value: 'estimatedDays' },
    { text: 'Duration Terms', value: 'durationTerms' },
    { text: 'Amount (USD)', value: 'amount' }
]

watch(selectedRateId, (newVal) => {
  console.log('✅ Selected rate changed:', newVal)
})

onMounted(async () => {
    try {
        const { data } = await apiClient.get(`/SalesOrders/${invoice}`)
        // console.log('On opening ShipStationOrderDetails i called ths API: /salesOrders/', invoice)
        // console.log('📦 ShipStationOrderDetails Raw results:', data)

        // pull the first generation record
        const gen = Array.isArray(data.generations) && data.generations.length
            ? data.generations[0]
            : {}

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
        // you could surface an error alert here
    }
})

// replace this with your real Shippo token (e.g. from env)
// const shippoToken = 'shippo_test_3a47d23c032ca626fce863c48d0f93d63a394396'
const shippoToken = import.meta.env.VITE_SHIPPO_API_KEY
console.log('🚚 Rate request shippotoken:', shippoToken)


async function getRates() {
    try {
        const payload = {
            address_to: {
                name: shippingName.value,
                street1: shippingAddressLine1.value,
                city: shippingCity.value,
                state: shippingState.value,
                zip: postalCode.value,
                country: 'US',
                // optional – add phone/email if you have them
                // phone:   '4151234567',
                // email:   'customer@example.com'
            },
            address_from: {
                name: shipBranchName,
                street1: shipFromAddressLine1,
                city: shipFromCity,
                state: shipFromState,
                zip: shipFromPostalCode,
                country: 'US',
                // optional
                // phone:   '555-123-4567',
                // email:   'nucomfort@example.com'
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
                'Authorization': `ShippoToken ${shippoToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })

        if (!resp.ok) throw new Error(`Shippo error ${resp.status}`)
        const data = await resp.json()
        console.log('🚚 Rate response:', data)

        // Flatten the rates into the shape our table needs:
        rates.value = (data.rates || []).map(r => ({
            object_id: r.object_id,
            serviceLevelName: r.servicelevel.name || r.servicelevel.display_name,
            estimatedDays: r.estimated_days,
            durationTerms: r.duration_terms,
            amount: parseFloat(r.amount)   // convert to number if needed
        }))
        console.log('✅ rates:', JSON.stringify(rates.value, null, 2))
    }
    catch (err) {
        console.error('Get Rates failed:', err)
        // you could show a v-alert here
    }
}


        const rateObject = selectedRateId.value[0] // because it's an array
        if (!rateObject?.object_id) {
        console.warn('No rate selected')
        return
        }

        const response = await fetch('https://api.goshippo.com/transactions', {
        method: 'POST',
        headers: {
            'Authorization': `ShippoToken ${shippoToken}`,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            rate: rateObject.object_id,
            label_file_type: 'PDF',
            async: 'false'
        })
        })

</script>

<style scoped>
/* optional spacing tweaks */
.v-card-text {
    padding-top: 0;
}
</style>