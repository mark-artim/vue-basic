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
        @click:row="handleRowClick"
      >
        <template #item="{ item }">
          <tr 
            :style="(codSettings.termsCodes.includes(item.termsCode) && parseFloat(item.balanceDue) > 0) ? 'color: red; font-weight: bold;' : ''"
            @click="handleRowClick($event, { item })"
            style="cursor: pointer"
          >
            <td>{{ item.shipDate }}</td>
            <td>{{ item.fullInvoiceID }}</td>
            <td>{{ item.shipToName }}</td>
            <td>{{ item.poNumber }}</td>
            <td>{{ item.shipVia }}</td>
            <td>
              <span :style="codSettings.termsCodes.includes(item.termsCode) ? 'color: red; font-weight: bold;' : ''">
                {{ item.termsCode }}
              </span>
            </td>
            <td>
              <span :class="isCodWithBalance(item) ? 'cod-balance-highlight' : ''">
                ${{ item.balanceDue }}
              </span>
            </td>
            <td>{{ item.status }}</td>
          </tr>
        </template>
      </v-data-table>
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

    <!-- COD Warning Dialog -->
    <v-dialog v-model="showCodWarningDialog" max-width="500px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="warning" class="me-2">mdi-alert</v-icon>
          COD Order Warning
        </v-card-title>
        
        <v-card-text>
          <v-alert type="warning" class="mb-4">
            <div class="font-weight-bold mb-2">⚠️ Outstanding Balance Detected</div>
            <div>This COD order has an outstanding balance that should be collected before shipping:</div>
          </v-alert>
          
          <div v-if="pendingOrder" class="order-details">
            <div class="mb-2"><strong>Invoice:</strong> {{ pendingOrder.fullInvoiceID }}</div>
            <div class="mb-2"><strong>Customer:</strong> {{ pendingOrder.shipToName }}</div>
            <div class="mb-2"><strong>Terms Code:</strong> {{ pendingOrder.termsCode }}</div>
            <div class="mb-3"><strong>Outstanding Balance:</strong> 
              <span class="text-red font-weight-bold">${{ pendingOrder.balanceDue }}</span>
            </div>
          </div>
          
          <div class="text-body-2 text-medium-emphasis">
            COD (Cash On Delivery) orders should have payment collected upon delivery. 
            Shipping with an outstanding balance may result in collection issues.
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" variant="outlined" @click="showCodWarningDialog = false">
            Cancel
          </v-btn>
          <v-btn color="warning" variant="elevated" @click="proceedWithCodOrder">
            <v-icon class="me-1">mdi-truck</v-icon>
            Ship Anyway
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- COD Blocked Dialog -->
    <v-dialog v-model="showCodBlockedDialog" max-width="500px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon color="error" class="me-2">mdi-block-helper</v-icon>
          Shipment Blocked
        </v-card-title>
        
        <v-card-text>
          <v-alert type="error" class="mb-4">
            <div class="font-weight-bold mb-2">🚫 SHIPMENT BLOCKED</div>
            <div>This COD order cannot be shipped due to company policy:</div>
          </v-alert>
          
          <div v-if="pendingOrder" class="order-details">
            <div class="mb-2"><strong>Invoice:</strong> {{ pendingOrder.fullInvoiceID }}</div>
            <div class="mb-2"><strong>Customer:</strong> {{ pendingOrder.shipToName }}</div>
            <div class="mb-2"><strong>Terms Code:</strong> {{ pendingOrder.termsCode }}</div>
            <div class="mb-3"><strong>Outstanding Balance:</strong> 
              <span class="text-red font-weight-bold">${{ pendingOrder.balanceDue }}</span>
            </div>
          </div>
          
          <div class="text-body-2 text-medium-emphasis">
            COD orders with outstanding balances cannot be shipped per company policy. 
            Please collect payment before attempting to ship this order.
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" variant="elevated" @click="showCodBlockedDialog = false">
            <v-icon class="me-1">mdi-check</v-icon>
            Understood
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
const codSettings = ref({ termsCodes: [], balancePolicy: 'warn' });
const showCodWarningDialog = ref(false);
const showCodBlockedDialog = ref(false);
const pendingOrder = ref(null);

// clear previous results when branch changes
watch(selectedBranch, () => {
  hasSearched.value = false;
  orders.value      = [];
  error.value       = '';
});

// table headers…
const headers = [
  { title: 'Ship Date',      key: 'shipDate'      },
  { title: 'Invoice Number', key: 'fullInvoiceID' },
  { title: 'Ship To Name',   key: 'shipToName'    },
  { title: 'PO Number',      key: 'poNumber'      },
  { title: 'Ship Via',       key: 'shipVia'       },
  { title: 'Terms Code',     key: 'termsCode'     },
  { title: 'Balance Due',    key: 'balanceDue'    },
  { title: 'Status',         key: 'status'        }
];


// Load COD settings
const loadCodSettings = async () => {
  try {
    console.log('🔄 Attempting to load COD settings...');
    const response = await apiClient.get('/ship54/settings');
    console.log('📥 Full settings response:', response.data);
    
    if (response.data?.cod) {
      codSettings.value = response.data.cod;
      console.log('✅ Loaded COD settings:', codSettings.value);
    } else {
      console.log('⚠️ No COD settings found in response. Setting defaults...');
      // For now, let's default to COD so we can test
      codSettings.value = { termsCodes: ['COD'], balancePolicy: 'warn' };
      console.log('🔧 Using default COD settings:', codSettings.value);
    }
  } catch (err) {
    console.error('❌ Failed to load COD settings:', err);
    // Fallback to defaults
    codSettings.value = { termsCodes: ['COD'], balancePolicy: 'warn' };
    console.log('🔧 Using fallback COD settings due to error');
  }
};

// fetch the list of accessible branches on mount
onMounted(async () => {
  try {
    const userData = await getUser(erpUserName);
    // Map the array of { branchId } objects into an array of strings
    const branchesArray = userData.accessibleBranches || [];
    branches.value = branchesArray.map(b => b.branchId);
    
    // Load COD settings
    await loadCodSettings();
    
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

// Computed property to check if an order is COD with balance due
const isCodWithBalance = (order) => {
  const isCod = codSettings.value.termsCodes.includes(order.termsCode);
  const hasBalance = parseFloat(order.balanceDue) > 0;
  const result = isCod && hasBalance;
  
  // Debug logging
  if (result) {
    console.log('🚨 COD WITH BALANCE DETECTED:', {
      invoice: order.fullInvoiceID,
      termsCode: order.termsCode,
      balanceDue: order.balanceDue,
      codTermsCodes: codSettings.value.termsCodes,
      isCod,
      hasBalance,
      result
    });
  }
  
  return result;
};

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

    // Sort by ship date - newest to oldest
    filteredList.sort((a, b) => {
      const dateA = new Date(a.generations?.[0]?.shipDate || 0);
      const dateB = new Date(b.generations?.[0]?.shipDate || 0);
      return dateB - dateA; // Descending order (newest first)
    });

    orders.value = await Promise.all(filteredList.map(async (order) => {
      const gen = Array.isArray(order.generations) && order.generations.length
        ? order.generations[0]
        : {};
      
      // Fetch status from PRINT.REVIEW API
      const status = await fetchStatusFromPrintReview(gen.fullInvoiceID, gen.generationId);
      
      return {
        shipDate:      gen.shipDate,
        fullInvoiceID: gen.fullInvoiceID,
        shipToName:    gen.shipToName,
        poNumber:      gen.poNumber,
        shipVia:       gen.shipVia,
        termsCode:     gen.termsCode,
        balanceDue:    gen.balanceDue?.value ?? 0,
        status:        status
      };
    }));
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


// Handle row clicks with COD warning logic
function handleRowClick(event, order) {
  // v-data-table passes { event, item } as parameters
  const orderData = order.item || order;
  
  // Check against configured COD terms codes with balance > 0
  const isCodWithBalance = (codSettings.value.termsCodes.includes(orderData.termsCode) && parseFloat(orderData.balanceDue) > 0);
  
  if (isCodWithBalance) {
    if (codSettings.value.balancePolicy === 'prevent') {
      // Show blocked dialog
      pendingOrder.value = orderData;
      showCodBlockedDialog.value = true;
      return;
    } else {
      // Show warning dialog
      pendingOrder.value = orderData;
      showCodWarningDialog.value = true;
      return;
    }
  }
  
  // Normal navigation for non-COD or COD orders without balance
  goToOrder(event, order);
}

// Proceed with COD order after warning
function proceedWithCodOrder() {
  if (pendingOrder.value) {
    showCodWarningDialog.value = false;
    goToOrder(null, { item: pendingOrder.value });
    pendingOrder.value = null;
  }
}

function goToOrder(click, order) {
    console.log('⚙️  Order object keys:', Object.keys(order), order);
    
    // Handle different data structures - v-data-table passes { item } or direct item
    const orderData = order.item || order;
    console.log('🏷️  goToOrder received order data:', orderData)

    // 2) Extract the invoice and log it
    const invoice = orderData.fullInvoiceID
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

    async function fetchStatusFromPrintReview(fullInvoiceID, generationId) {
      // Extract order number (before the first dot) from fullInvoiceID
      const orderNumber = fullInvoiceID.split('.')[0];
      // Pad generationId to 4 digits with leading zeros
      const paddedGenerationId = String(generationId).padStart(4, '0');
      const apiId = `${orderNumber}.${paddedGenerationId}`;
      
      try {
        const response = await apiClient.post('/api/erp-proxy', {
          method: 'GET',
          url: `/UserDefined/PRINT.REVIEW?id=${apiId}`
        });
        return response.data?.STATUS || '';
      } catch (err) {
        // Handle "not found" as normal case (many invoices won't have print review records)
        if (err.response?.status === 400 && err.response?.data?.details?.includes('were not found')) {
          console.log(`📋 No PRINT.REVIEW record found for ${apiId} (normal)`);
          return '';
        }
        
        // Log other actual errors
        console.error(`❌ Failed to fetch status for ${fullInvoiceID}:`, err.message);
        return '';
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

/* COD Warning Row Styling - SCARY VERSION! */
.cod-warning-row {
    background: linear-gradient(90deg, #ff4444, #ff6666, #ff4444) !important;
    color: white !important;
    font-weight: bold !important;
    border: 3px solid #cc0000 !important;
    border-left: 8px solid #990000 !important;
    position: relative !important;
    box-shadow: 0 0 15px rgba(255, 0, 0, 0.5) !important;
}

.cod-warning-row:hover {
    background: linear-gradient(90deg, #cc0000, #ff3333, #cc0000) !important;
    box-shadow: 0 0 25px rgba(255, 0, 0, 0.8) !important;
    transform: scale(1.02) !important;
}

.cod-warning-row::before {
    content: "🚨 DANGER: COD WITH BALANCE! 🚨";
    position: absolute;
    left: 5px;
    top: 2px;
    font-size: 10px;
    color: yellow;
    font-weight: bold;
    text-shadow: 1px 1px 1px black;
    animation: flash 1s infinite;
}

.cod-terms-highlight {
    background-color: yellow !important;
    color: red !important;
    font-weight: bold !important;
    padding: 2px 4px !important;
    border-radius: 3px !important;
    border: 1px solid red !important;
}

.cod-balance-highlight {
    background-color: #ffff00 !important;
    color: #cc0000 !important;
    font-weight: bold !important;
    font-size: 1.1em !important;
    padding: 2px 4px !important;
    border-radius: 3px !important;
    border: 2px solid #cc0000 !important;
    text-shadow: 1px 1px 1px white !important;
}

/* Scary animation */
.cod-warning-row {
    animation: scary-pulse 1.5s infinite, shake 2s infinite;
}

@keyframes scary-pulse {
    0%, 100% { 
        background: linear-gradient(90deg, #ff4444, #ff6666, #ff4444) !important;
        box-shadow: 0 0 15px rgba(255, 0, 0, 0.5) !important;
    }
    50% { 
        background: linear-gradient(90deg, #ff0000, #ff4444, #ff0000) !important;
        box-shadow: 0 0 30px rgba(255, 0, 0, 0.9) !important;
    }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-1px); }
    20%, 40%, 60%, 80% { transform: translateX(1px); }
}

@keyframes flash {
    0%, 50% { opacity: 1; }
    25%, 75% { opacity: 0.5; }
}
</style>