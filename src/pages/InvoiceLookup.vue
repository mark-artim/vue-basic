<template>
  <!-- Template remains the same as previous version -->
  <div class="invoice-lookup">
    <h1>Invoice Look Up</h1>

    <div class="search-form">
      <div class="form-group">
        <label for="shipToId">Ship To ID:</label>
        <input
          id="shipToId"
          v-model="shipToId"
          type="text"
          placeholder="Enter Ship To ID"
          @keyup.enter="fetchInvoices"
        >
      </div>
      <button
        :disabled="isLoading"
        @click="fetchInvoices"
      >
        {{ isLoading ? 'Loading...' : 'Search' }}
      </button>
    </div>

    <div
      v-if="error"
      class="error-message"
    >
      {{ error }}
    </div>
    <div class="form-group">
      <v-autocomplete
        v-model="selectedCustomerId"
        :items="customerResults"
        item-title="nameIndex"
        item-value="id"
        label="Search for Customer"
        outlined
        dense
        :loading="isLoading"
        no-data-text="No matching customers"
        hide-no-data
        hide-details
        @input="onCustomerInput"
        @focus="clearSelection"
        @update:model-value="onCustomerSelected"
      />
    </div>

    <div
      v-if="invoices.length > 0"
      class="invoice-table-container"
    >
      <table class="invoice-table">
        <thead>
          <tr>
            <th>Invoice Date</th>
            <th>Invoice Number</th>
            <th>PO Number</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(invoice, index) in invoices"
            :key="index"
          >
            <td>{{ formatDate(invoice.shipDate) }}</td>
            <td>{{ invoice.fullInvoiceID }}</td>
            <td>{{ invoice.poNumber }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div
      v-else-if="!isLoading && searchExecuted"
      class="no-results"
    >
      No invoices found for the provided Ship To ID.
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useDebouncedSearch } from '@/composables/useDebouncedSearch';
import { searchOrders } from '@/api/orders';
import { searchCustomers } from '@/api/customers';

// Reactive state
const shipToId = ref('');
const invoices = ref([]);
// const isLoading = ref(false);
const errorMessage = ref('');
const searchExecuted = ref(false);

// Pagination
const pageSize = 25;
const currentPage = ref(1);

const fetchCustomers = async (query) => {
      const result = await searchCustomers(query);
      const customerResults = result.results || result;
      console.log('[DEBUG INVOICE LOOKUP] Customers fetched:', customerResults);
      // return allCustomers.filter(v => v.isPayTo);
      return customerResults
    };

const {
      searchTerm: keyword,
      results: customerResults,
      isLoading,
      onSearch: onCustomerInput,
      clear,
    } = useDebouncedSearch(fetchCustomers, 1000);

const onCustomerSelected = (customerId) => {
  if (!customerId) {
    invoices.value = [];
    return;
  }
  shipToId.value = customerId;
  fetchInvoices();
};

const clearSelection = () => {
      console.log('Clearing selection Someday...');
      selectedCustomerId.value = null;
      selectedCustomer.value = [];
      // form.value = {};
      // updatedMessage.value = '';
    };

const fetchInvoices = async () => {
  if (!shipToId.value) {
    errorMessage.value = 'Please enter a Ship To ID.';
    return;
  }

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const startIndex = (currentPage.value - 1) * pageSize;

    const response = await searchOrders({
      params: {
        ShipTo: shipToId.value,
        OrderStatus: 'Invoice',
        includeTotalItems: true,
        sort: '-shipDate',
        startIndex,
        pageSize,
      }
    });
    // console.log('[DEBUG INVOICE LOOKUP] API response:', response);

    const resultsArray = Array.isArray(response.results)
      ? response.results
      : Object.values(response.results);

    const filtered = resultsArray.flatMap(order =>
      (order.generations || [])
        .filter(gen => String(gen.shipToId) === String(shipToId.value))
        .map(gen => formatInvoice(gen))
    );

    invoices.value = filtered;
    errorMessage.value = filtered.length
      ? ''
      : `No invoices found for Ship To ID ${shipToId.value}`;
  } catch (err) {
    console.error('[ERROR] Invoice fetch failed:', err);
    errorMessage.value = 'Failed to retrieve invoices.';
  } finally {
    isLoading.value = false;
    searchExecuted.value = true;
  }
};

// Utility functions
const formatInvoice = (generation) => ({
  shipDate: generation.shipDate,
  fullInvoiceID: generation.fullInvoiceID || generation.invoiceNumber,
  poNumber: generation.poNumber || 'N/A',
});

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleDateString();
  } catch (e) {
    console.warn('Date format error:', e);
    return dateString;
  }
};

// Optional extraction helpers (preserved for structure)
const extractInvoicesFromArray = (dataArray) =>
  dataArray.flatMap(item => item.generations?.map(formatInvoice) || []);

const extractInvoicesFromGenerations = (generations) =>
  generations.map(formatInvoice);

const extractInvoicesFromOrders = (orders) =>
  orders.flatMap(order => order.generations?.map(formatInvoice) || []);
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