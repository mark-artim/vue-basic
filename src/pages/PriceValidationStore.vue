### First: Create a Pinia store file

```javascript
// src/store/priceValidation.js
import { defineStore } from 'pinia';

export const usePriceValidationStore = defineStore('priceValidation', {
  state: () => ({
    results: [],
    failedProducts: [],
  }),
  actions: {
    setResults(newResults) {
      this.results = newResults;
    },
    setFailedProducts(newFails) {
      this.failedProducts = newFails;
    },
    clear() {
      this.results = [];
      this.failedProducts = [];
    }
  }
});
```

---

### Now: Updated `PriceValidation.vue`

```vue
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

    <div v-if="store.results.length" class="summary">
      <p><strong>Pricing Summary:</strong><br /></p>
      <ul class="no-bullets">
        <li>Total Products: {{ priceDifferenceStats.total }}</li>
        <li>Zero Price Difference: {{ priceDifferenceStats.exactZero }}</li>
        <li>Some Price Difference: {{ priceDifferenceStats.greaterThanZero }}</li>
        <li>Difference less than $0.06: {{ priceDifferenceStats.tinyDifference }}</li>
        <li>% Exact Match: {{ priceDifferenceStats.zeroPct }}%</li>
        <li>% Match within 5 cents: {{ priceDifferenceStats.tinyPct }}%</li>
      </ul>
    </div>

    <table v-if="store.results.length">
      <thead>
        <tr>
          <th v-for="column in tableColumns" :key="column.key">{{ column.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in store.results" :key="index">
          <td v-for="column in tableColumns" :key="column.key" :class="column.class ? column.class(item) : ''">
            {{ column.format ? column.format(item[column.key]) : item[column.key] }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="store.failedProducts.length" class="failed-section">
      <h3>Failed Products</h3>
      <ul>
        <li v-for="(fail, index) in store.failedProducts" :key="index">
          Original ID: {{ fail.originalProductId }} | HER_PN: {{ fail.herProductId || 'N/A' }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import Papa from 'papaparse';
import axios from '@/utils/axios';
import { ref, watch } from 'vue';
import { usePriceValidationStore } from '@/store/priceValidation';

export default {
  setup() {
    const store = usePriceValidationStore();
    const resolvedCustomerCount = ref(0);
    const resolvedProductCount = ref(0);
    const fetchingHERPN = ref(false);
    const productIds = ref([]);
    const herProductIdMap = ref({});
    const originalProductData = ref({});
    const customerIdMap = ref({});
    const errorMessage = ref('');
    const loading = ref(false);

    const tableColumns = [
      { key: 'productId', label: 'Product ID' },
      { key: 'herProductId', label: 'HER Product ID' },
      { key: 'resolvedCustomerId', label: 'Customer ID (Resolved)' },
      { key: 'upcCode', label: 'UPC Code', format: (val) => val || 'N/A' },
      { key: 'branch', label: 'Branch' },
      { key: 'invoiceNumber', label: 'Invoice #', format: (val) => val || 'N/A' },
      { key: 'actualSellPrice', label: 'Actual Sell Price (USD)', format: (val) => val.toFixed(2) },
      { key: 'productUnitPrice', label: 'Unit Price (API) (USD)', format: (val) => val.value.toFixed(2) },
      { key: 'actualCost', label: 'Actual Cost (USD)', format: (val) => val.toFixed(2) },
      { key: 'productCost', label: 'Product Cost (USD)', format: (val) => val.value.toFixed(2) },
      { key: 'actualCogs', label: 'Actual COGS (USD)', format: (val) => val.toFixed(2) },
      { key: 'productCOGS', label: 'COGS (USD)', format: (val) => val.value.toFixed(2) },
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

    // ... Your handleFileUpload() and submitData() functions adapted to use store

    return {
      store,
      resolvedCustomerCount,
      resolvedProductCount,
      fetchingHERPN,
      productIds,
      herProductIdMap,
      originalProductData,
      customerIdMap,
      errorMessage,
      loading,
      tableColumns,
    };
  }
};
</script>
```

---

### ✅ Now your table stays alive even if you navigate around!
<style scoped>
.price-validation {
  max-width: 1000px;
  margin: auto;
  padding: 20px;
  text-align: center;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
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
