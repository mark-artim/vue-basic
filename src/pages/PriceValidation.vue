<template>
  <div class="price-validation">
    <h1>Price Comparison</h1>

    <label class="custom-file-upload">
      <input type="file" @change="handleFileUpload" accept=".csv" :disabled="fetchingHERPN || loading" />
      📂 Choose CSV File
    </label>

    <button @click="submitData" :disabled="!productIds.length || loading || fetchingHERPN">
      {{ loading ? 'Loading...' : 'Submit Data' }}
    </button>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <div v-if="fetchingHERPN" class="loading-indicator">
      <span class="spinner"></span> Fetching product and customer cross-references...
    </div>
    <p v-if="!fetchingHERPN && (resolvedCustomerCount || resolvedProductCount)" class="xref-summary">
      ✅ Resolved {{ resolvedCustomerCount }} customer IDs and {{ resolvedProductCount }} HER_PNs from file.
    </p>

    <div v-if="results.length" class="summary">
      <p>
        <strong>Pricing Summary:</strong><br />
      <ul class="no-bullets">
        <li>Total Products: {{ priceDifferenceStats.total }}</li>
        <li>Zero Price Difference: {{ priceDifferenceStats.exactZero }}</li>
        <li>Some Price Difference: {{ priceDifferenceStats.greaterThanZero }}</li>
        <li>Difference less than $0.06: {{ priceDifferenceStats.tinyDifference }}</li>
        <li>% Exact Match: {{ priceDifferenceStats.zeroPct }}%</li>
        <li>% Match within 5 cents: {{ priceDifferenceStats.tinyPct }}%</li>
      </ul>
      </p>
    </div>
    <div v-if="results.length" style="margin: 10px 0;">
      <label>
        <input type="checkbox" v-model="showExactMatches" />
        Show Exact Matches
      </label>
    </div>
    <button @click="downloadCSV" :disabled="!filteredResults.length">
      Download CSV
    </button>
    <table class="table-wrapper" v-if="results.length">
      <thead>
        <tr>
          <th v-for="column in tableColumns" :key="column.key">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in filteredResults" :key="index">
          <td v-for="column in tableColumns" :key="column.key" :class="column.class ? column.class(item) : ''">
            {{ column.format ? column.format(item[column.key]) : item[column.key] }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="failedProducts.length" class="failed-section">
      <h3>Failed Products</h3>
      <ul>
        <li v-for="(fail, index) in failedProducts" :key="index">
          Original ID: {{ fail.originalProductId }} | HER_PN: {{ fail.herProductId || 'N/A' }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import Papa from 'papaparse';
import { productPricingMassInquiry } from '@/api/pricing';
import { useAuthStore } from '@/stores/auth';
import { loadCrossReferences, getHerPN, getConvCUS, getAllPNXrefs, getAllCUSXrefs } from '@/composables/useXrefLoader'
import { filter } from 'lodash-es';

const authStore = useAuthStore();

const showExactMatches = ref(true);
const resolvedCustomerCount = ref(0);
const resolvedProductCount = ref(0);
const fetchingHERPN = ref(false);
const failedProducts = ref([]);
const productIds = ref([]);
const herProductIdMap = ref({});
const originalProductData = ref({});
const customerIdMap = ref({});
const results = ref([]);
const errorMessage = ref('');
const loading = ref(false);
const logging = sessionStorage.getItem('apiLogging') === 'true';

const uploadedProductIds = new Set();

const tableColumns = [
  { key: 'productId', label: 'Eds Product ID' },
  { key: 'herProductId', label: 'HER Product ID' },
  { key: 'customerId', label: 'Eds Customer ID' },
  { key: 'resolvedCustomerId', label: 'HER Customer ID' },
  { key: 'upcCode', label: 'UPC Code', format: (val) => val || 'N/A' },
  { key: 'branch', label: 'Branch' },
  { key: 'invoiceNumber', label: 'Invoice #', format: (val) => val || 'N/A' },
  { key: 'actualSellPrice', label: 'Actual Sell Price (Eds)', format: (val) => val.toFixed(2) },
  { key: 'productUnitPrice', label: 'New Sell Price (HER)', format: (val) => val.value.toFixed(2) },
  { key: 'actualCost', label: 'Actual Cost (Eds)', format: (val) => val.toFixed(2) },
  { key: 'productCost', label: 'Product Cost (HER)', format: (val) => val.value.toFixed(2) },
  { key: 'actualCogs', label: 'Actual COGS (Eds)', format: (val) => val.toFixed(2) },
  { key: 'productCOGS', label: 'COGS (HER)', format: (val) => val.value.toFixed(2) },
  {
    key: 'priceDifference',
    label: 'Price Difference',
    format: (val) => val.toFixed(2),
    class: (item) => {
      const diff = item.priceDifference;
      if (diff === 0) return 'diff-zero';
      if (Math.abs(diff) < 1) return 'diff-small';
      return 'diff-large';
    }
  }
];

const filteredResults = computed(() => {
  return showExactMatches.value ? results.value : results.value.filter(r => r.priceDifference !== 0);
});

const priceDifferenceStats = computed(() => {
  const total = results.value.length;
  const exactZero = results.value.filter(r => r.priceDifference === 0).length;
  const greaterThanZero = results.value.filter(r => r.priceDifference != 0).length;
  const tinyDifference = results.value.filter(r => {
    const absDiff = Math.abs(r.priceDifference);
    return absDiff > 0.00 && absDiff < 0.06;
  }).length;
  const zeroPct = total ? ((exactZero / total) * 100).toFixed(1) : 0;
  const tinyPct = total ? (((exactZero + tinyDifference) / total) * 100).toFixed(1) : 0;
  return {
    total,
    exactZero,
    greaterThanZero,
    tinyDifference,
    zeroPct,
    tinyPct,
  };
});

const handleFileUpload = async (event) => {
  results.value = [];
  failedProducts.value = [];
  errorMessage.value = '';
  productIds.value = [];
  herProductIdMap.value = {};
  originalProductData.value = {};
  customerIdMap.value = {};
  uploadedProductIds.clear();
  fetchingHERPN.value = true;

  const file = event.target.files[0];
  if (!file) {
    errorMessage.value = 'Please select a file.';
    fetchingHERPN.value = false;
    return;
  }

  Papa.parse(file, {
    complete: async (result) => {
      const dataRows = result.data.slice(9);
      const rawData = dataRows.filter((row) => row.length >= 7 && row[0] && row[7]);
      if (logging) console.log(`[PriceValidation] Parsed ${rawData.length} rows from CSV.`);

      if (rawData.length === 0) {
        errorMessage.value = 'No valid data found in CSV.';
        fetchingHERPN.value = false;
        return;
      }

      const productMap = {};
      const herMap = {};
      const customerXrefMap = {};

      for (const row of rawData) {
        const originalProductId = row[0].trim();
        uploadedProductIds.add(originalProductId);
        const originalCustomerId = row[7].trim();
        const resolvedCustomerId = getConvCUS(originalCustomerId) || originalCustomerId;
        const invoiceNumber = row[2]?.trim() || 'N/A';
        const actualSellPrice = parseFloat(row[3]) || 0;
        const actualCost = parseFloat(row[4]) || 0;
        const actualCogs = parseFloat(row[5]) || 0;
        const branch = row[6]?.trim();

        customerXrefMap[originalCustomerId] = resolvedCustomerId;

        productMap[originalProductId] = {
          originalProductId,
          resolvedCustomerId,
          invoiceNumber,
          actualSellPrice,
          actualCost,
          actualCogs,
          branch,
        };

        herMap[originalProductId] = getHerPN(originalProductId) || null;
      }

      customerIdMap.value = customerXrefMap;
      originalProductData.value = productMap;
      herProductIdMap.value = herMap;
      productIds.value = Array.from(new Set(Object.entries(herMap)
        .filter(([key]) => uploadedProductIds.has(key))
        .map(([_, val]) => val)
        .filter(Boolean)));
      resolvedCustomerCount.value = Object.values(customerXrefMap).filter(Boolean).length;
      resolvedProductCount.value = productIds.value.length;
      fetchingHERPN.value = false;
    },
    header: false,
    skipEmptyLines: true,
  });
};

const submitData = async () => {
  if (!productIds.value.length) {
    errorMessage.value = 'No valid products to process.';
    return;
  }

  loading.value = true;
  errorMessage.value = '';
  results.value = [];
  failedProducts.value = [];

  const successfulResults = [];

  const requests = productIds.value.map(async (herProductId) => {
    try {
      const originalProductIds = Object.entries(herProductIdMap.value)
        .filter(([key, val]) => val === herProductId && uploadedProductIds.has(key))
        .map(([key]) => key);

      if (!originalProductIds.length) return;

      const queryParams = `CustomerId=${encodeURIComponent(
        originalProductData.value[originalProductIds[0]]?.resolvedCustomerId || ''
      )}&ShowCost=true&ProductId=${encodeURIComponent(herProductId)}`;

      const response = await productPricingMassInquiry(`${queryParams}`);
      const apiResults = response.results || [];

      apiResults.forEach((item) => {
        const herId = item.productId.toString();
        originalProductIds.forEach((originalId) => {
          const local = originalProductData.value[originalId] || {};
          const adjustedProductUnitPrice = item.productUnitPrice?.value / (item.pricingPerQuantity || 1);

          successfulResults.push({
            ...item,
            productId: originalId,
            herProductId: herId,
            resolvedCustomerId: local.resolvedCustomerId,
            upcCode: item.upcCode || 'N/A',
            invoiceNumber: local.invoiceNumber,
            actualSellPrice: local.actualSellPrice,
            productUnitPrice: { value: adjustedProductUnitPrice },
            actualCost: local.actualCost,
            actualCogs: local.actualCogs,
            branch: local.branch,
            priceDifference: local.actualSellPrice - (adjustedProductUnitPrice || 0),
          });
        });
      });
    } catch (error) {
      console.error(`Failed pricing fetch for HER_PN ${herProductId}`, error);

      const originalProductIds = Object.entries(herProductIdMap.value)
        .filter(([key, val]) => val === herProductId && uploadedProductIds.has(key))
        .map(([key]) => key);

      originalProductIds.forEach((originalId) => {
        failedProducts.value.push({ herProductId, originalProductId: originalId });
      });
    }
  });

  await Promise.all(requests);
  results.value = successfulResults;
  loading.value = false;

  if (failedProducts.value.length) {
    errorMessage.value = `Pricing data could not be retrieved for ${failedProducts.value.length} product(s).`;
  }
};

const downloadCSV = () => {
  const headers = tableColumns.map(col => col.label);
  const rows = filteredResults.value.map(item =>
    tableColumns.map(col => {
      const value = item[col.key];
      if (col.format) return col.format(value);
      if (typeof value === 'object' && value !== null && 'value' in value) return value.value;
      return value;
    })
  );

  const csvContent = [headers, ...rows]
    .map(row => row.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'price_validation_results.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

onMounted(async () => {
  await loadCrossReferences();
  const pnxrefs = getAllPNXrefs();
  console.log('[PriceValidation] First few product xrefs:', Object.entries(pnxrefs).slice(0, 5));
  const cnxrefs = getAllCUSXrefs();
  console.log('[PriceValidation] First few customer xrefs:', Object.entries(cnxrefs).slice(0, 5));
});
</script>



<style scoped>
.price-validation {
  max-width: 1400px;
  margin: auto;
  padding: 20px;
  text-align: center;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.table-wrapper {
  overflow-x: auto;
}

th,
td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: center;
}

th {
  background-color: #007bff;
  color: white;
  font-weight: bold;
  padding: 12px;
}

td {
  background-color: white;
  color: black;
}

.negative {
  color: red;
  font-weight: bold;
}

.positive {
  color: green;
  font-weight: bold;
}

.failed-section {
  margin-top: 20px;
  color: #cc0000;
  font-weight: bold;
  text-align: left;
}

.loading-indicator {
  margin: 15px 0;
  font-weight: bold;
  color: #007bff;
}

.diff-zero {
  color: green;
  font-weight: bold;
}

.diff-small {
  color: orange;
  font-weight: bold;
}

.diff-large {
  color: red;
  font-weight: bold;
}

.summary {
  margin: 20px 0;
  font-weight: bold;
  color: #f3a01c;
}

.spinner {
  display: inline-block;
  width: 1em;
  height: 1em;
  border: 2px solid #007bff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  font-size: 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-top: 15px;
  margin-left: 40px;
}

button:hover {
  background-color: #0056b3;
}

button:disabled {
  background-color: #cccccc;
  color: #666666;
  cursor: not-allowed;
}

.custom-file-upload {
  display: inline-block;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  font-weight: bold;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-bottom: 15px;
}

.custom-file-upload:hover {
  background-color: #218838;
}

.custom-file-upload input[type="file"] {
  display: none;
}

.no-bullets {
  list-style-type: none;
  padding-left: 0;
}

.xref-summary {
  font-weight: bold;
  color: #28a745;
  margin: 10px 0;
}
</style>
