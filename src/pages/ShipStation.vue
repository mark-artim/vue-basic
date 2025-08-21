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
    <v-text-field
      v-model="shipViaKeywordsInput"
      label="Ship Via Keywords (comma-separated)"
      placeholder="e.g. UPS, FEDEX"
      dense
      class="my-4"
      @change="resolveShipViaFilters"
    />
    <v-btn
      color="primary"
      class="mb-4"
      :disabled="!shipViaKeywordsInput"
      @click="saveDefaultShipViaKeywords"
    >
      Save as Default
      <v-tooltip activator="parent" location="bottom">
        Saves Ship Via Keywords and Shipping Branch (if selected) as defaults
      </v-tooltip>
    </v-btn>
    <v-btn
      :disabled="!selectedBranch || isLoading"
      color="primary"
      block
      @click="handleBranchSelection"
    >
      <!-- Get Orders -->
      <!-- </v-btn> -->


      <span v-if="!isLoading">Get Orders</span>
      <v-progress-circular
        v-else
        indeterminate
        size="20"
        width="2"
      />
    </v-btn>
    <v-alert
      v-if="error"
      type="error"
      dense
      text
      class="mt-4"
    >
      {{ error }}
    </v-alert>

    <v-card v-if="orders.length">
      <v-card-title>Orders for {{ selectedBranch }}</v-card-title>
      <v-data-table
        :headers="headers"
        :items="orders"
        class="elevation-1"
        dense
        @click:row="goToOrder"
      />
    </v-card>

    <v-row v-else-if="hasSearched && !isLoading && orders.length === 0">
      <v-col cols="12">
        <v-alert
          type="info"
          dense
        >
          No orders found for branch {{ selectedBranch }}.
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>
  
<script setup>
import { ref, watch, onMounted } from 'vue';
import { useRouter }            from 'vue-router';
import apiClient                from '@/utils/axios';
import { useAuthStore }         from '../stores/auth';
import { getUser }              from '@/api/users';
import { getBranch }           from '@/api/branches';
import { getCustomer }         from '@/api/customers';
import { searchOrders}        from '@/api/orders';
import { useShipFromStore } from '@/stores/useShipFromStore';
import { fetchShipViaGroup } from '@/api/shipVias'; 

const authStore      = useAuthStore();
const router         = useRouter();
const shipFromStore = useShipFromStore();
const shipViaKeywordsInput = ref(localStorage.getItem('defaultShipViaKeywords') || 'UPS, FEDEX');
const shipViaFilterList    = ref([]);

const jwt = authStore.jwt;
const payload = JSON.parse(atob(jwt.split('.')[1]));
const erpUserName = (payload.erpUserName || payload.erpLogin).toUpperCase();
console.log('[ShipStation] ERP User Name:', erpUserName);

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
  { title: 'Ship Via',       key: 'shipVia'       },
  { title: 'Terms Code',     key: 'termsCode'     },
  { title: 'Balance Due',    key: 'balanceDue'    }
];


// fetch the list of accessible branches on mount
onMounted(async () => {
  try {
    const userData = await getUser(erpUserName);
    // Map the array of { branchId } objects into an array of strings
    const branchesArray = userData.accessibleBranches || [];
    branches.value = branchesArray.map(b => b.branchId);
    
    // Load default shipping branch if it exists and user has access to it
    const defaultBranch = localStorage.getItem('defaultShippingBranch');
    if (defaultBranch && branches.value.includes(defaultBranch)) {
      selectedBranch.value = defaultBranch;
      
      // Auto-execute search if we have a saved branch (with small delay to ensure everything is ready)
      console.log('🚀 Auto-executing search for default branch:', defaultBranch);
      setTimeout(async () => {
        try {
          await loadShipFromInfo(defaultBranch);
          await fetchOrders();
        } catch (err) {
          console.error('❌ Auto-search failed:', err);
          // Don't show error to user, they can manually click Get Orders
        }
      }, 500); // 500ms delay to ensure all initialization is complete
    }
  } catch (e) {
    console.error('Failed to load accessible branches', e);
  }
  await resolveShipViaFilters(); // 🚀 load default filters
});

// Get the shipping branch address when selected
async function loadShipFromInfo(branchId) {
  try {
    const branchResp = await getBranch(branchId)
    // const branchResp = await apiClient.get(`/Branches/${branchId}`)
    console.log('branchResp.data:', branchResp)
    const branchEntityId = branchResp.branchEntityId

    const customer = await getCustomer(branchEntityId)
    // const customer = customerResp
    console.log('[shipstation] customer:', customer.name, customer.addressLine1)


    shipFromStore.setAddress({
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
    const response = await searchOrders({
      params: {
        ShipBranch:  selectedBranch.value,
        // ShipVia:     'UPS GROUND',
        OrderStatus: 'Invoice',
        PrintStatus: 'Q'
      }
    });

    const list = Array.isArray(response.results)
      ? response.results
      : Array.isArray(response)
        ? response
        : [];

    // filter for only UPS-based shipping methods
    list.forEach(order => {
      const gen = Array.isArray(order.generations) && order.generations.length
        ? order.generations[0]
        : {};
    });


    const filteredList = list.filter(order => {
    const gen = Array.isArray(order.generations) && order.generations.length
      ? order.generations[0]
      : {};
      // return gen.shipVia?.startsWith('WILL');
      return shipViaFilterList.value.includes(gen.shipVia);
    });

    orders.value = filteredList.map(order => {
      const gen = Array.isArray(order.generations) && order.generations.length
        ? order.generations[0]
        : {};
      return {
        fullInvoiceID: gen.fullInvoiceID,
        shipDate:      gen.shipDate,
        poNumber:      gen.poNumber,
        shipVia:       gen.shipVia,
        termsCode:     gen.termsCode,
        balanceDue:    gen.balanceDue?.value ?? 0,
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
    async function resolveShipViaFilters() {
      const keywords = shipViaKeywordsInput.value
        .split(',')
        .map(k => k.trim().toUpperCase())
        .filter(Boolean);

      const allMatches = new Set();

      for (const keyword of keywords) {
        try {
          const result = await fetchShipViaGroup(keyword);

          // ✅ Use result.results if present
          const matches = Array.isArray(result?.results)
            ? result.results
            : [];

          matches.forEach(r => {
            if (r.id) allMatches.add(r.id.toUpperCase());  // ✅ Use `id` not `code`
          });
        } catch (err) {
          console.error(`❌ Failed to load ship vias for "${keyword}"`, err);
        }
      }

      shipViaFilterList.value = Array.from(allMatches);
      console.log('✅ Final Filter List:', shipViaFilterList.value);
    }


    function saveDefaultShipViaKeywords() {
      localStorage.setItem('defaultShipViaKeywords', shipViaKeywordsInput.value);
      if (selectedBranch.value) {
        localStorage.setItem('defaultShippingBranch', selectedBranch.value);
      }
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