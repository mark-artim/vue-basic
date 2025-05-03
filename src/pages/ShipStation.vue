<template>
    <v-container fluid>
        <v-row>
            <v-col cols="12">
                <h1 class="display-1 text-center my-6">Ship Station</h1>
            </v-col>
        </v-row>

        <v-card class="pa-4 mb-6">
            <v-row align="center" justify="space-between">
                <v-col cols="12" md="4">
                    <v-select v-model="selectedBranch" :items="branches" label="Shipping Branch" outlined
                        dense></v-select>
                </v-col>
                <v-col cols="12" md="4">
                    <v-btn :disabled="!selectedBranch || isLoading" color="primary" @click="fetchOrders" block>
                        <span v-if="!isLoading">Get Orders</span>
                        <v-progress-circular v-else indeterminate size="20" width="2"></v-progress-circular>
                    </v-btn>
                </v-col>
            </v-row>

            <v-alert v-if="error" type="error" dense text class="mt-4">
                {{ error }}
            </v-alert>
        </v-card>

        <v-card v-if="orders.length">
            <v-card-title>Orders for {{ selectedBranch }}</v-card-title>
            <v-data-table :headers="headers" :items="orders" class="elevation-1" dense @click:row="goToOrder"></v-data-table>
        </v-card>

        <v-row v-else-if="!isLoading && selectedBranch">
            <v-col cols="12">
                <v-alert type="info" dense>
                    No orders found for branch {{ selectedBranch }}.
                </v-alert>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router'
import apiClient from '@/utils/axios';

// Shipping branches options
const branches = ['ILCH', 'ILCR', 'ILCS'];
const selectedBranch = ref('');

// State
const orders = ref([]);
const isLoading = ref(false);
const error = ref('');

// Table headers
const headers = [
    { text: 'Invoice Number', value: 'fullInvoiceID' },
    { text: 'Ship Date', value: 'shipDate' },
    { text: 'PO Number', value: 'poNumber' },
    { text: 'Balance Due', value: 'balanceDue' }
];

const router = useRouter()

// Base URL
const url = '/SalesOrders';

async function fetchOrders() {
    if (!selectedBranch.value) return

    isLoading.value = true
    error.value = ''
    orders.value = []

    try {
        const response = await apiClient.get(url, {
            params: {
                ShipBranch: selectedBranch.value,
                ShipVia: 'UPS GROUND',
                OrderStatus: 'Invoice',
                PrintStatus: 'Q'
            }
        })

        // pick the array
        const list = Array.isArray(response.data.results)
            ? response.data.results
            : Array.isArray(response.data)
                ? response.data
                : []

        orders.value = list.map(order => {
            const gen = Array.isArray(order.generations) && order.generations.length
                ? order.generations[0]
                : {}
            return {
                fullInvoiceID: gen.fullInvoiceID,
                shipDate: gen.shipDate,
                poNumber: gen.poNumber,
                balanceDue: gen.balanceDue?.value ?? 0
            }
        })
    }
    catch (err) {
        console.error(err)
        error.value = 'Failed to load orders.'
    }
    finally {
        isLoading.value = false
    }
}

function goToOrderBAK(order) {
  // order.fullInvoiceID is your invoice number
  router.push({
    name: 'ShipStationOrderDetail',
    params: { invoice: order.fullInvoiceID }
  })
}

function goToOrder(click, order) {
    console.log('⚙️  Order object keys:', Object.keys(order), order);
  // 1) Log the entire order object
  console.log('🏷️  goToOrder received order:', order.item)

  // 2) Extract the invoice and log it
  const invoice = order.item.fullInvoiceID
  console.log('📦 invoice to navigate with:', invoice)

  // 3) Prepare the route target
  const target = {
    name: 'ShipStationOrderDetail',  // must match your route name exactly
    params: { invoice }
  }

  // 4) Resolve it to see the final URL
  const resolved = router.resolve(target)
  console.log('🚗 resolved route:', resolved.fullPath)

  // 5) Finally push
  router.push(target).catch(err => {
    console.error('❌ navigation error:', err)
  })
}

</script>

<style scoped>
.my-6 {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}

.pa-4 {
    padding: 1rem;
}

.mb-6 {
    margin-bottom: 1.5rem;
}
</style>