<template>
  <v-container class="pa-4">
    <v-card
      class="pa-6 elevation-8"
      color="#0a0f1c"
    >
      <div class="d-flex align-center mb-4">
        <h1 class="flex-grow-1 text-white">
          Product Management
        </h1>
        <v-btn
          color="success"
          variant="elevated"
          @click="showCreateDialog = true"
        >
          <v-icon start>
            mdi-plus
          </v-icon>
          Add Product
        </v-btn>
      </div>

      <!-- Products List -->
      <v-card
        variant="outlined"
        class="mb-4"
      >
        <v-card-title>All Products</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="products"
            :loading="loading"
            item-key="_id"
            class="elevation-1"
          >
            <template #item.longDescription="{ item }">
              <div class="pa-2">
                {{ item.longDescription || '—' }}
              </div>
            </template>

            <template #item.features="{ item }">
              <div class="pa-2">
                <div
                  v-if="item.features?.length > 0"
                  class="features-list"
                >
                  <div
                    v-for="feature in item.features"
                    :key="feature"
                    class="feature-item"
                  >
                    <v-icon
                      size="small"
                      color="success"
                      class="me-1"
                    >
                      mdi-check-circle
                    </v-icon>
                    {{ feature }}
                  </div>
                </div>
                <span
                  v-else
                  class="text-grey"
                >No features</span>
              </div>
            </template>

            <template #item.stripeProductId="{ item }">
              <v-chip
                v-if="item.stripeProductId"
                size="small"
                color="success"
                variant="outlined"
              >
                {{ item.stripeProductId }}
              </v-chip>
              <span
                v-else
                class="text-grey"
              >Not configured</span>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex gap-2">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click="editProduct(item)"
                >
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="error"
                  @click="deleteProduct(item)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-card>

    <!-- Create/Edit Product Dialog -->
    <v-dialog
      v-model="showCreateDialog"
      max-width="600px"
    >
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="primary"
          >
            mdi-package-variant
          </v-icon>
          {{ editingProduct ? 'Edit Product' : 'Create New Product' }}
        </v-card-title>
        
        <v-card-text>
          <v-form
            ref="formRef"
            v-model="formValid"
          >
            <v-text-field
              v-model="productForm._id"
              label="Product ID"
              hint="Unique identifier (e.g., 'ship54', 'eclipse')"
              persistent-hint
              :disabled="!!editingProduct"
              :rules="[v => !!v || 'Product ID is required']"
              variant="outlined"
              class="mb-3"
            />
            
            <v-text-field
              v-model="productForm.name"
              label="Product Name"
              hint="Display name for the product"
              persistent-hint
              :rules="[v => !!v || 'Product name is required']"
              variant="outlined"
              class="mb-3"
            />
            
            <v-textarea
              v-model="productForm.longDescription"
              label="Long Description"
              hint="Detailed description for marketing purposes"
              persistent-hint
              variant="outlined"
              rows="3"
              class="mb-3"
            />
            
            <v-text-field
              v-model="productForm.stripeProductId"
              label="Stripe Product ID"
              hint="Stripe product ID for subscription billing"
              persistent-hint
              variant="outlined"
              class="mb-3"
            />
            
            <v-combobox
              v-model="productForm.features"
              label="Features"
              hint="List of product features (press Enter to add each feature)"
              persistent-hint
              variant="outlined"
              multiple
              chips
              closable-chips
              class="mb-3"
            />
            
            <v-combobox
              v-model="productForm.roles"
              label="Allowed Roles"
              hint="Optional: restrict product to specific user roles"
              persistent-hint
              variant="outlined"
              multiple
              chips
              closable-chips
            />
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeDialog"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!formValid"
            :loading="saving"
            @click="saveProduct"
          >
            {{ editingProduct ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog
      v-model="showDeleteDialog"
      max-width="400px"
    >
      <v-card>
        <v-card-title class="text-h6">
          Confirm Delete
        </v-card-title>
        <v-card-text>
          Are you sure you want to delete the product "{{ productToDelete?.name }}"?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmDelete"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, toRaw } from 'vue'
import apiClient from '@/utils/axios'

// State
const products = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingProduct = ref(false)
const productToDelete = ref(null)
const formValid = ref(false)
const saving = ref(false)

// Form data
const productForm = ref({
  _id: '',
  name: '',
  longDescription: '',
  stripeProductId: '',
  features: [],
  roles: []
})

// Table headers
const headers = [
  { title: 'ID', value: '_id', sortable: true },
  { title: 'Name', value: 'name', sortable: true },
  { title: 'Description', value: 'longDescription', width: '300px' },
  { title: 'Features', value: 'features', sortable: false },
  { title: 'Stripe Product ID', value: 'stripeProductId', sortable: false },
  { title: 'Actions', value: 'actions', sortable: false, width: '100px' }
]

// Load all products
const loadProducts = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/products')
    products.value = response.data
    console.log('Loaded products:', products.value)
  } catch (err) {
    console.error('Failed to load products:', err)
  } finally {
    loading.value = false
  }
}

const editProduct = (product) => {
  editingProduct.value = product._id
  console.log('HEY FUCKO! Editing product:', toRaw(product))
  console.log('The prooduct id is:', product._id)
  console.log('The product name is:', product.name)
  
  // Direct assignment - same way the table accesses it
  productForm.value._id = product._id
  productForm.value.name = product.name
  productForm.value.longDescription = product.longDescription || ''
  productForm.value.stripeProductId = product.stripeProductId || ''
  productForm.value.features = product.features || []
  productForm.value.roles = product.roles || []
  
  showCreateDialog.value = true
}

// Save product (create or update)
const saveProduct = async () => {
  try {
    saving.value = true
    
    if (editingProduct.value) {
      // Update existing product
      await apiClient.put(`/products/${productForm.value._id}`, productForm.value)
    } else {
      // Create new product
      await apiClient.post('/products', productForm.value)
    }
    
    await loadProducts()
    closeDialog()
    
  } catch (err) {
    console.error('Failed to save product:', err)
    alert('Failed to save product. Please try again.')
  } finally {
    saving.value = false
  }
}

// Delete product
const deleteProduct = (product) => {
  productToDelete.value = product
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  try {
    await apiClient.delete(`/products/${productToDelete.value._id}`)
    await loadProducts()
    showDeleteDialog.value = false
    productToDelete.value = null
  } catch (err) {
    console.error('Failed to delete product:', err)
    alert('Failed to delete product. Please try again.')
  }
}

// Close dialog and reset form
const closeDialog = () => {
  showCreateDialog.value = false
  editingProduct.value = false
  productForm.value = {
    _id: '',
    name: '',
    longDescription: '',
    stripeProductId: '',
    features: [],
    roles: []
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.feature-item {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  line-height: 1.2;
}
</style>