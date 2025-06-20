<template>
  <div class="price-validation">
    <h1>Price Comparison</h1>

    <!-- <input type="file" @change="handleFileUpload" accept=".csv" :disabled="fetchingHERPN || loading" /> -->
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
    <table v-if="results.length">
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

<script>
import Papa from 'papaparse';
import apiClient from '@/utils/axios';
import { ref, watch } from 'vue';
import { getUserDefined } from '@/api/userdefined';
import { productPricingMassInquiry } from '@/api/pricing';

export default {

  data() {
    return {
      showExactMatches: true,
      resolvedCustomerCount: 0,
      resolvedProductCount: 0,
      fetchingHERPN: false,
      failedProducts: [],
      productIds: [],
      herProductIdMap: {}, // originalProductId -> HER_PN
      originalProductData: {}, // originalProductId -> row data
      customerIdMap: {}, // originalCustomerId -> resolvedCustomerId
      results: [],
      errorMessage: '',
      loading: false,
      tableColumns: [
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

      ],
    };
  },
  methods: {
    async handleFileUpload(event) {
      // Reset
      this.results = [];
      this.failedProducts = [];
      this.errorMessage = '';
      this.productIds = [];
      this.herProductIdMap = {};
      this.originalProductData = {};
      this.customerIdMap = {};
      this.fetchingHERPN = true;

      const file = event.target.files[0];
      if (!file) {
        this.errorMessage = 'Please select a file.';
        this.fetchingHERPN = false;
        return;
      }

      Papa.parse(file, {
        complete: async (result) => {
          const dataRows = result.data.slice(9);
          const rawData = dataRows.filter((row) => row.length >= 7 && row[0] && row[7]);

          if (rawData.length === 0) {
            this.errorMessage = 'No valid data found in CSV.';
            this.fetchingHERPN = false;
            return;
          }

          const productMap = {};
          const herMap = {};
          const customerXrefMap = {};
          const uniqueCustomerIds = [...new Set(rawData.map(row => row[7]?.trim()).filter(Boolean))];

          // Resolve customer cross-references
          const customerXrefPromises = uniqueCustomerIds.map(async (originalId) => {
            try {
              const res = await getUserDefined(`/EDS.CUS.XREF?id=${encodeURIComponent(originalId)}`);
              console.log(`res for ${originalId}:`, res);
              console.log(`Resolved customer XREF for ${originalId}:`, res.F1);
              // const { data } = await apiClient.get(`/UserDefined/EDS.CUS.XREF?id=${encodeURIComponent(originalId)}`);
              customerXrefMap[originalId] = res.F1;
            } catch (err) {
              console.error(`Failed customer XREF for ${originalId}`, err);
              customerXrefMap[originalId] = null;
            }
          });

          await Promise.all(customerXrefPromises);
          this.customerIdMap = customerXrefMap;
          this.resolvedCustomerCount = Object.values(customerXrefMap).filter(Boolean).length;

          for (const row of rawData) {
            const originalProductId = row[0].trim();
            const originalCustomerId = row[7].trim();
            const resolvedCustomerId = customerXrefMap[originalCustomerId];
            const invoiceNumber = row[2] ? row[2].trim() : 'N/A';
            const actualSellPrice = parseFloat(row[3]) || 0;
            const actualCost = parseFloat(row[4]) || 0;
            const actualCogs = parseFloat(row[5]) || 0;
            const branch = row[6].trim();

            productMap[originalProductId] = {
              originalProductId,
              resolvedCustomerId,
              invoiceNumber,
              actualSellPrice,
              actualCost,
              actualCogs,
              branch,
            };
          }

          this.originalProductData = productMap;

          const fetchPromises = Object.keys(productMap).map(async (productId) => {
            try {
              const res = await getUserDefined(`/EDS.PN.XREF?id=${encodeURIComponent(productId)}`);
              // const { data } = await apiClient.get(`/UserDefined/EDS.PN.XREF?id=${encodeURIComponent(productId)}`);
              herMap[productId] = res.HER_PN;
            } catch (err) {
              console.error(`❌ Failed pricing fetch for HER_PN ${herProductId}`, {
                error,
                status: error?.response?.status,
                data: error?.response?.data,
                headers: error?.response?.headers,
              });

              herMap[productId] = null;
            }
          });

          await Promise.all(fetchPromises);
          this.herProductIdMap = herMap;
          this.productIds = Object.values(herMap).filter(Boolean);
          this.resolvedProductCount = this.productIds.length;
          this.fetchingHERPN = false;
        },
        header: false,
        skipEmptyLines: true,
      });
    },

    downloadCSV() {
      const headers = this.tableColumns.map(col => col.label);
      const rows = this.filteredResults.map(item =>
        this.tableColumns.map(col => {
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
    },


    async submitData() {
      if (!this.productIds.length) {
        this.errorMessage = 'No valid products to process.';
        return;
      }

      this.loading = true;
      this.errorMessage = '';
      this.results = [];
      this.failedProducts = [];

      const successfulResults = [];

      const requests = this.productIds.map(async (herProductId) => {
        try {
          const originalProductId = Object.keys(this.herProductIdMap).find(
            (key) => this.herProductIdMap[key] === herProductId
          );
          const local = this.originalProductData[originalProductId] || {};
          const resolvedCustomerId = local.resolvedCustomerId;

          const queryParams = `CustomerId=${encodeURIComponent(resolvedCustomerId)}&ShowCost=true&ProductId=${encodeURIComponent(herProductId)}`;
          // const response = await apiClient.get(`/ProductPricingMassInquiry?${queryParams}`, {
          //   timeout: 30000,
          // });
          const response = await productPricingMassInquiry(`${queryParams}`)
          const apiResults = response.results || [];

          apiResults.forEach((item) => {
            const herId = item.productId.toString();
            const originalProductId = Object.keys(this.herProductIdMap).find(
              (key) => this.herProductIdMap[key] === herId
            );
            const local = this.originalProductData[originalProductId] || {};

            // ✅ Adjust actualSellPrice using pricingPerQuantity
            // const adjustedActualSellPrice = local.actualSellPrice / (item.pricingPerQuantity || 1);
            const adjustedProductUnitPrice = item.productUnitPrice?.value / (item.pricingPerQuantity || 1);

            successfulResults.push({
              ...item,
              productId: originalProductId,
              herProductId: herId,
              resolvedCustomerId: local.resolvedCustomerId,
              upcCode: item.upcCode || 'N/A',
              invoiceNumber: local.invoiceNumber,
              actualSellPrice: local.actualSellPrice, 
              productUnitPrice: { value: adjustedProductUnitPrice} , // ✅ USE adjusted value
              actualCost: local.actualCost,
              actualCogs: local.actualCogs,
              branch: local.branch,
              priceDifference: local.actualSellPrice - (adjustedProductUnitPrice || 0), // ✅ USE adjusted value
            });
          });

        } catch (error) {
          console.error(`Failed pricing fetch for HER_PN ${herProductId}`, error);
          const originalId = Object.keys(this.herProductIdMap).find(
            (key) => this.herProductIdMap[key] === herProductId
          );
          this.failedProducts.push({ herProductId, originalProductId: originalId });
        }
      });

      await Promise.all(requests);
      this.results = successfulResults;
      this.loading = false;

      if (this.failedProducts.length) {
        this.errorMessage = `Pricing data could not be retrieved for ${this.failedProducts.length} product(s).`;
      }
    }
  },
  computed: {
    filteredResults() {
      if (this.showExactMatches) return this.results;
      return this.results.filter(r => r.priceDifference !== 0);
    },
    priceDifferenceStats() {
      const total = this.results.length;
      const exactZero = this.results.filter(r => r.priceDifference === 0).length;
      const greaterThanZero = this.results.filter(r => r.priceDifference != 0).length;
      const tinyDifference = this.results.filter(r => {
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
    }
  }

};
</script>

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
