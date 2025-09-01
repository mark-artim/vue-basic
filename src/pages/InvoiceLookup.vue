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

    <!-- Beautiful Customer Info Section -->
    <div v-if="customerInfo" class="customer-info-card">
      <div class="customer-header">
        <div class="customer-icon">
          <v-icon color="primary" size="32">mdi-office-building</v-icon>
        </div>
        <div class="customer-title">
          <h2>{{ customerInfo.name }}</h2>
          <p class="customer-id">Customer ID: {{ customerInfo.id }}</p>
        </div>
      </div>
      
      <div class="customer-details">
        <div class="address-section">
          <h3><v-icon>mdi-map-marker</v-icon> Address</h3>
          <div class="address-text">
            <p>{{ customerInfo.addressLine1 }}</p>
            <p v-if="customerInfo.addressLine2">{{ customerInfo.addressLine2 }}</p>
            <p>{{ customerInfo.city }}, {{ customerInfo.state }} {{ customerInfo.postalCode }}</p>
            <p v-if="customerInfo.country && customerInfo.country !== 'US'">{{ customerInfo.country }}</p>
          </div>
        </div>
        
        <div class="contact-section" v-if="customerInfo.phones?.length || customerInfo.emails?.length">
          <h3><v-icon>mdi-phone</v-icon> Contact</h3>
          <div class="contact-info">
            <p v-if="customerInfo.phones?.length" class="phone">
              <v-icon size="16">mdi-phone</v-icon> {{ customerInfo.phones[0].number }}
            </p>
            <p v-if="customerInfo.emails?.length" class="email">
              <v-icon size="16">mdi-email</v-icon> {{ customerInfo.emails[0].address }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="invoices.length > 0"
      class="invoice-table-container"
    >
      <div class="results-info">
        Page {{ currentPage }} ({{ invoices.length }} results{{ hasMorePages ? ', more available' : '' }})
      </div>
      
      <table class="invoice-table">
        <thead>
          <tr>
            <th>Invoice Date</th>
            <th>Invoice Number</th>
            <th>PO Number</th>
            <th>PDF</th>
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
            <td>
              <button 
                class="pdf-button"
                @click="viewPDF(invoice.fullInvoiceID)"
                :disabled="pdfLoading === invoice.fullInvoiceID"
              >
                {{ pdfLoading === invoice.fullInvoiceID ? 'Loading...' : 'View PDF' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-controls" v-if="invoices.length === pageSize || currentPage > 1">
        <button 
          @click="goToPreviousPage" 
          :disabled="currentPage === 1"
          class="pagination-button"
        >
          ← Previous
        </button>
        
        <span class="pagination-info">
          Page {{ currentPage }}
        </span>
        
        <button 
          @click="goToNextPage" 
          :disabled="!hasMorePages"
          class="pagination-button"
        >
          Next →
        </button>
      </div>
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
import { searchCustomers, getCustomer } from '@/api/customers';
import apiClient from '@/utils/axios';

// Reactive state
const shipToId = ref('');
const invoices = ref([]);
// const isLoading = ref(false);
const errorMessage = ref('');
const searchExecuted = ref(false);
const pdfLoading = ref(null);
const customerInfo = ref(null);

// Pagination
const pageSize = 25;
const currentPage = ref(1);
const totalItems = ref(0);
const hasMorePages = computed(() => invoices.value.length === pageSize);

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

const onCustomerSelected = async (customerId) => {
  if (!customerId) {
    invoices.value = [];
    customerInfo.value = null;
    return;
  }
  shipToId.value = customerId;
  currentPage.value = 1; // Reset to first page
  
  // Fetch customer details for display
  try {
    customerInfo.value = await getCustomer(customerId);
  } catch (err) {
    console.error('Failed to fetch customer details:', err);
    customerInfo.value = null;
  }
  
  fetchInvoices();
};

// Pagination functions
const goToNextPage = () => {
  if (hasMorePages.value) {
    currentPage.value++;
    fetchInvoices();
  }
};

const goToPreviousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchInvoices();
  }
};

const goToPage = (page) => {
  currentPage.value = page;
  fetchInvoices();
};

const selectedCustomerId = ref(null);

const clearSelection = () => {
      console.log('Clearing selection Someday...');
      selectedCustomerId.value = null;
      // selectedCustomer.value = [];
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
  
  // Reset to first page if this is a new search (not pagination)
  if (arguments.length === 0) {
    currentPage.value = 1;
  }

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
    totalItems.value = response.totalItems || filtered.length;
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

// PDF viewing function
const viewPDF = async (fullInvoiceID) => {
  try {
    pdfLoading.value = fullInvoiceID;
    
    const response = await apiClient.post('/api/erp-proxy', {
      method: 'GET',
      url: `/SalesOrders/${fullInvoiceID}/PrintInvoice`
    }, {
      responseType: 'blob'
    });
    
    // Create blob URL and open in new tab
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank');
    
    // Clean up the object URL after a delay
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 10000);
    
  } catch (err) {
    console.error('Failed to fetch PDF for', fullInvoiceID, err);
    alert('Failed to load PDF. Please try again.');
  } finally {
    pdfLoading.value = null;
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

.pdf-button {
  padding: 4px 8px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  height: auto;
}

.pdf-button:hover:not(:disabled) {
  background-color: #1565c0;
}

.pdf-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.results-info {
  font-size: 14px;
  color: #666;
  margin: 16px 20px;
  font-style: italic;
  font-weight: 500;
  background: linear-gradient(90deg, #667eea, #764ba2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-align: center;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding: 10px;
}

.pagination-button {
  padding: 8px 16px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  height: auto;
}

.pagination-button:hover:not(:disabled) {
  background-color: #369870;
}

.pagination-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.pagination-info {
  font-size: 14px;
  color: #333;
  font-weight: bold;
}

/* Beautiful Customer Info Card */
.customer-info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  margin: 20px 0;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.customer-info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.25);
}

.customer-header {
  display: flex;
  align-items: center;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.customer-icon {
  margin-right: 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.customer-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.customer-id {
  margin: 4px 0 0 0;
  font-size: 14px;
  opacity: 0.8;
  font-weight: 400;
}

.customer-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 24px;
}

.address-section, .contact-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(5px);
}

.customer-details h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.95);
}

.address-text p, .contact-info p {
  margin: 4px 0;
  font-size: 14px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.9);
}

.contact-info .phone, .contact-info .email {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
}

@media (max-width: 768px) {
  .customer-details {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .customer-header {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .customer-icon {
    margin-right: 0;
  }
}

.invoice-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin: 20px 0;
  transition: box-shadow 0.3s ease;
}

.invoice-table-container:hover {
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
}

.invoice-table {
  width: 100%;
  border-collapse: collapse;
}

.invoice-table th,
.invoice-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}

.invoice-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  position: sticky;
  top: 0;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  border: none;
}

.invoice-table td {
  border: none;
  color:black;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s ease;
}

.invoice-table tr:nth-child(even) {
  background-color: #f8f9fb;
}

.invoice-table tr:hover {
  background-color: #e8f0fe;
  transform: scale(1.01);
  transition: all 0.2s ease;
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