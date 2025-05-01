<template>
  <!-- Template remains the same as previous version -->
  <div class="invoice-lookup">
    <h1>Invoice Look Up</h1>

    <div class="search-form">
      <div class="form-group">
        <label for="shipToId">Ship To ID:</label>
        <input type="text" id="shipToId" v-model="shipToId" placeholder="Enter Ship To ID"
          @keyup.enter="fetchInvoices" />
      </div>
      <button @click="fetchInvoices" :disabled="isLoading">
        {{ isLoading ? 'Loading...' : 'Search' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="invoices.length > 0" class="invoice-table-container">
      <table class="invoice-table">
        <thead>
          <tr>
            <th>Invoice Date</th>
            <th>Invoice Number</th>
            <th>PO Number</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(invoice, index) in invoices" :key="index">
            <td>{{ formatDate(invoice.shipDate) }}</td>
            <td>{{ invoice.fullInvoiceID }}</td>
            <td>{{ invoice.poNumber }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!isLoading && searchExecuted" class="no-results">
      No invoices found for the provided Ship To ID.
    </div>
  </div>
</template>

<script>
import axios from '@/utils/axios'; // Adjust the import based on your project structure

export default {
  name: 'InvoiceLookup',
  data() {
    return {
      shipToId: '',
      invoices: [],
      isLoading: false,
      error: '',
      searchExecuted: false
    };
  },
  methods: {
    async fetchInvoices() {
      if (!this.shipToId) {
        this.errorMessage = 'Please enter a Ship To ID.';
        return;
      }

      try {
        const startIndex = (this.currentPage - 1) * this.pageSize;
        const url = `/SalesOrders?startIndex=${startIndex}&pageSize=${this.pageSize}`;

        console.log('🔍 Fetching:', url);

        const response = await axios.get(`/SalesOrders`, {
          params: {
            ShipTo: this.shipToId,
            OrderStatus: 'Invoice',
            includeTotalItems: true,
            sort: '-shipDate'
          }
        });

        const data = response.data;

        if (!Array.isArray(data.results)) {
          console.error('❌ Unexpected response structure:', Object.keys(data));
          throw new Error('API returned unexpected data structure');
        }

        console.log('📦 Raw results:', data.results.slice(0, 3));

        // Flatten generations and filter by Ship To ID
        const filtered = data.results.flatMap((order) =>
          (order.generations || [])
            .filter((gen) => String(gen.shipToId) === String(this.shipToId))
            .map((gen) => ({
              shipDate: gen.shipDate,
              fullInvoiceID: gen.fullInvoiceID,
              poNumber: gen.poNumber,
            }))
        );

        console.log('✅ Filtered:', filtered);

        this.invoices = filtered;
        this.hasMoreData = filtered.length === this.pageSize;
        this.errorMessage = filtered.length
          ? ''
          : `No invoices found for Ship To ID ${this.shipToId}`;
      } catch (error) {
        this.errorMessage = 'Failed to retrieve invoices.';
        console.error('[ERROR] Invoice fetch failed:', error);
      }
    },

    // NEW: Specific extraction methods for different response structures
    extractInvoicesFromArray(dataArray) {
      return dataArray.flatMap(item => {
        if (item.generations && Array.isArray(item.generations)) {
          return item.generations.map(gen => this.formatInvoice(gen));
        }
        return [];
      });
    },

    extractInvoicesFromGenerations(generations) {
      return generations.map(gen => this.formatInvoice(gen));
    },

    extractInvoicesFromOrders(orders) {
      return orders.flatMap(order => {
        if (order.generations && Array.isArray(order.generations)) {
          return order.generations.map(gen => this.formatInvoice(gen));
        }
        return [];
      });
    },

    formatInvoice(generation) {
      return {
        shipDate: generation.shipDate,
        fullInvoiceID: generation.fullInvoiceID || generation.invoiceNumber,
        poNumber: generation.poNumber || 'N/A'
      };
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      try {
        return new Date(dateString).toLocaleDateString();
      } catch (e) {
        console.warn('Date format error:', e);
        return dateString;
      }
    }
  }
};
</script>

<style scoped>
/* Styles remain the same as previous version */
.invoice-lookup {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.search-form {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
}

input {
  padding: 8px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 200px;
}

button {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  height: 40px;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.invoice-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
}

.invoice-table th,
.invoice-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}

.invoice-table th {
  background-color: #ef4b22;
  position: sticky;
  top: 0;
  font-weight: bold;
}

.invoice-table tr:nth-child(even) {
  background-color: #272622; /* light gray */
  color: inherit;
  font-weight: normal;
}

.invoice-table tr:hover {
  background-color: #f1f1f1;
}

.error-message {
  color: #d32f2f;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 4px;
}

.no-results {
  margin-top: 20px;
  font-style: italic;
  color: #666;
  padding: 20px;
  text-align: center;
  border: 1px dashed #ddd;
  border-radius: 4px;
}

@media (max-width: 600px) {
  .search-form {
    flex-direction: column;
    align-items: stretch;
  }

  input {
    width: auto;
  }
}
</style>