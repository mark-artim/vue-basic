<template>
    <v-container fluid>
      <!-- … header & card wrapper … -->
      <v-select
        v-model="selectedBranch"
        :items="branches"
        label="Shipping Branch"
        outlined
        dense
        :disabled="branches.length === 0"
      />
  
      <!-- <v-btn
        :disabled="!selectedBranch || isLoading"
        color="primary"
        @click="fetchOrders"
        block
      > -->
      <v-btn
        :disabled="!selectedBranch || isLoading"
        color="primary"
        @click="handleBranchSelection"
        block
      >
        <!-- Get Orders -->
      <!-- </v-btn> -->


        <span v-if="!isLoading">Get Orders</span>
        <v-progress-circular v-else indeterminate size="20" width="2"/>
      </v-btn>
      <v-alert v-if="error" type="error" dense text class="mt-4">
                {{ error }}
            </v-alert>

        <v-card v-if="orders.length">
            <v-card-title>Orders for {{ selectedBranch }}</v-card-title>
            <v-data-table :headers="headers" :items="orders" class="elevation-1" dense
                @click:row="goToOrder"></v-data-table>
        </v-card>

        <v-row v-else-if="hasSearched && !isLoading && orders.length === 0">
            <v-col cols="12">
                <v-alert type="info" dense>
                    No orders found for branch {{ selectedBranch }}.
                </v-alert>
            </v-col>
        </v-row>
    </v-container>
  </template>
  
<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRouter }             from 'vue-router';
import apiClient                  from '@/utils/axios';
import { useAuthStore }           from '../store/auth';
import { useShipFromStore } from '@/store/useShipFromStore'
const shipFromStore = useShipFromStore()
const authStore      = useAuthStore();
console.log('authStore.userNmae: ', authStore.userName);
const router         = useRouter();

// branches will now come from the API
const branches       = ref([]);
const selectedBranch = ref('');

// orders state…
const orders    = ref([]);
const isLoading = ref(false);
const error     = ref('');
const hasSearched = ref(false);

// clear previous results when branch changes
watch(selectedBranch, () => {
  hasSearched.value = false;
  orders.value      = [];
  error.value       = '';
});

// table headers…
const headers = [
  { title: 'Invoice Number', key: 'fullInvoiceID' },
  { title: 'Ship Date',      key: 'shipDate'      },
  { title: 'PO Number',      key: 'poNumber'      },
  { title: 'Ship Via',       key: 'shipVia'    },
  { title: 'Balance Due',    key: 'balanceDue'    }
];


// fetch the list of accessible branches on mount
onMounted(async () => {
  try {
    const userName = authStore.userName;
    const { data } = await apiClient.get(`/Users/${userName}`);

    // Map the array of { branchId } objects into an array of strings
    branches.value = Array.isArray(data.accessibleBranches)
      ? data.accessibleBranches.map(item => item.branchId)
      : [];
  } catch (e) {
    console.error('Failed to load accessible branches', e);
  }
});

async function loadShipFromInfo(branchId) {
  try {
    const branchResp = await apiClient.get(`/Branches/${branchId}`)
    console.log('branchResp.data:', branchResp.data)
    const branchEntityId = branchResp.data.branchEntityId

    const customerResp = await apiClient.get(`/Customers/${branchEntityId}`)
    const customer = customerResp.data

    shipFromStore.set({
      name: customer.name,
      addressLine1: customer.addressLine1,
      addressLine2: customer.addressLine2,
      city: customer.city,
      state: customer.state,
      postalCode: customer.postalCode,
      phone: customer.phones?.[0]?.number,
      email: customer.emails?.[0]
    })
  } catch (err) {
    console.error('Failed to load ship-from info:', err)
  }
}

async function fetchOrders() {
  if (!selectedBranch.value) return;

  hasSearched.value = true;
  isLoading.value   = true;
  error.value       = '';
  orders.value      = [];

  try {
    const response = await apiClient.get('/SalesOrders', {
      params: {
        ShipBranch:  selectedBranch.value,
        // ShipVia:     'UPS GROUND',
        OrderStatus: 'Invoice',
        PrintStatus: 'Q'
      }
    });

    const list = Array.isArray(response.data.results)
      ? response.data.results
      : Array.isArray(response.data)
        ? response.data
        : [];

    // filter for only UPS-based shipping methods
    const filteredList = list.filter(order => {
    const gen = Array.isArray(order.generations) && order.generations.length
      ? order.generations[0]
      : {};
      return gen.shipVia?.startsWith('UPS');
    });

    orders.value = filteredList.map(order => {
      const gen = Array.isArray(order.generations) && order.generations.length
        ? order.generations[0]
        : {};
      return {
        fullInvoiceID: gen.fullInvoiceID,
        shipDate:      gen.shipDate,
        poNumber:      gen.poNumber,
        balanceDue:    gen.balanceDue?.value ?? 0,
        shipVia:       gen.shipVia,
      };
    });
  }
  catch (err) {
    console.error(err);
    error.value = 'Failed to load orders.';
  }
  finally {
    isLoading.value = false;
  }
}

const handleBranchSelection = async () => {
  await loadShipFromInfo(selectedBranch.value)
  await fetchOrders()
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