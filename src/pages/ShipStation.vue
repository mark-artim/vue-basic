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
  
      <v-btn
        :disabled="!selectedBranch || isLoading"
        color="primary"
        @click="fetchOrders"
        block
      >
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
  { text: 'Invoice Number', value: 'fullInvoiceID' },
  { text: 'Ship Date',      value: 'shipDate'      },
  { text: 'PO Number',      value: 'poNumber'     },
  { text: 'Balance Due',    value: 'balanceDue'   }
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
        ShipVia:     'UPS GROUND',
        OrderStatus: 'Invoice',
        PrintStatus: 'Q'
      }
    });

    const list = Array.isArray(response.data.results)
      ? response.data.results
      : Array.isArray(response.data)
        ? response.data
        : [];

    orders.value = list.map(order => {
      const gen = Array.isArray(order.generations) && order.generations.length
        ? order.generations[0]
        : {};
      return {
        fullInvoiceID: gen.fullInvoiceID,
        shipDate:      gen.shipDate,
        poNumber:      gen.poNumber,
        balanceDue:    gen.balanceDue?.value ?? 0
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

function goToOrder(_evt, order) {
  router.push({
    name:   'ShipStationOrderDetail',
    params: { invoice: order.fullInvoiceID }
  });
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