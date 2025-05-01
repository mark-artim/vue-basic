<template>
    <div class="invoice-lookup">
        <h1>Invoice Look Up</h1>

        <div class="form">
            <label for="shipToId">Customer Ship To ID:</label>
            <input id="shipToId" v-model="shipToId" placeholder="Enter Ship To ID" type="text" />
            <button @click="submitSearch()">Search Invoices</button>
            <button @click="() => console.log('Hello from Vue')">Test Vue</button>
            <button @click="submitSearch">Search Invoices</button>
        </div>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <table v-if="invoices.length">
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

        <div class="pagination" v-if="invoices.length">
            <button @click="prevPage" :disabled="currentPage === 1">Previous</button>
            <span>Page {{ currentPage }}</span>
            <button @click="nextPage" :disabled="!hasMoreData">Next</button>
        </div>
    </div>
</template>

<script>
import axios from '@/utils/axios';

export default {
    name: 'InvoiceLookup',
    data() {
        return {
            shipToId: '',
            invoices: [],
            errorMessage: '',
            currentPage: 1,
            pageSize: 5,
            hasMoreData: false,
        };
    },
    methods: {
        submitSearch() {
            console.log('🚀 Submit button clicked');
            this.currentPage = 1;
            this.invoices = [];
            this.fetchInvoices();
        },
        async fetchInvoices() {
            if (!this.shipToId) {
                this.error = 'Please enter a Ship To ID';
                return;
            }

            this.isLoading = true;
            this.error = '';

            try {
                const response = await axios.get(`/SalesOrders`, {
                    params: {
                        ShipTo: this.shipToId,
                        OrderStatus: 'Invoice',
                        includeTotalItems: true
                    }
                });

                // Handle the response data structure from your example
                if (Array.isArray(response.data)) {
                    this.invoices = response.data.reduce((acc, order) => {
                        if (order.generations && Array.isArray(order.generations)) {
                            return acc.concat(order.generations.map(gen => ({
                                shipDate: gen.shipDate,
                                fullInvoiceID: gen.fullInvoiceID,
                                poNumber: gen.poNumber
                            })));
                        }
                        return acc;
                    }, []);

                    this.totalItems = this.invoices.length;
                } else {
                    this.invoices = [];
                    this.error = 'Unexpected response format from server';
                }

            } catch (err) {
                console.error('Error fetching invoices:', err);
                this.error = 'Failed to fetch invoices. Please try again.';
                this.invoices = [];
            } finally {
                this.isLoading = false;
            }
        },
    nextPage() {
            this.currentPage++;
            this.fetchInvoices();
        },
        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.fetchInvoices();
            }
        },
        formatDate(dateStr) {
            if (!dateStr) return 'N/A';
            return new Date(dateStr).toLocaleDateString();
        },
    }
</script>


<style scoped>
.invoice-lookup {
    max-width: 900px;
    margin: auto;
    padding: 20px;
    text-align: center;
}

.form {
    margin-bottom: 20px;
}

input {
    margin: 0 10px;
    padding: 8px;
    font-size: 1em;
    width: 200px;
}

button {
    padding: 8px 12px;
    font-size: 1em;
    margin-top: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th,
td {
    border: 1px solid #ccc;
    padding: 10px;
}

th {
    background-color: #007bff;
    color: white;
}

.error {
    color: red;
    margin-top: 10px;
}

.pagination {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    gap: 15px;
}
</style>