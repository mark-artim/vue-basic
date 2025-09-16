<template>
  <v-container class="pa-4">
    <v-row
      justify="space-between"
      align="center"
    >
      <v-col cols="6">
        <h2>Company Admin</h2>
      </v-col>
      <v-col
        cols="6"
        class="text-right"
      >
        <v-btn
          color="primary"
          @click="openDialog"
        >
          Add Company
        </v-btn>
      </v-col>
    </v-row>

    <v-data-table
      :items="companies"
      :headers="headers"
      class="elevation-1"
    >
      <template #item.webhookStatus="{ item }">
        <v-chip
          v-if="item.ship54Settings?.shippo?.webhook?.isActive"
          color="success"
          size="small"
        >
          <v-icon start>
            mdi-check-circle
          </v-icon>
          Active
        </v-chip>
        <v-chip
          v-else-if="item.ship54Settings?.shippo?.webhook?.lastError"
          color="error"
          size="small"
        >
          <v-icon start>
            mdi-alert-circle
          </v-icon>
          Error
        </v-chip>
        <v-chip
          v-else
          color="grey"
          size="small"
        >
          <v-icon start>
            mdi-minus-circle
          </v-icon>
          None
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn
          icon
          size="small"
          @click="editCompany(item)"
        >
          <v-icon>mdi-pencil</v-icon>
          <v-tooltip activator="parent">
            Edit Company
          </v-tooltip>
        </v-btn>
        <v-btn
          icon
          size="small"
          color="primary"
          @click="manageWebhook(item)"
        >
          <v-icon>mdi-webhook</v-icon>
          <v-tooltip activator="parent">
            Manage Webhook
          </v-tooltip>
        </v-btn>
        <v-btn
          icon
          size="small"
          @click="deleteCompany(item._id)"
        >
          <v-icon color="red">
            mdi-delete
          </v-icon>
          <v-tooltip activator="parent">
            Delete Company
          </v-tooltip>
        </v-btn>
      </template>
    </v-data-table>

    <v-dialog
      v-model="dialog"
      max-width="600"
    >
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingCompany ? 'Edit' : 'Add' }} Company</span>
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="saveCompany">
            <v-text-field
              v-model="form.name"
              label="Company Name"
              required
            />
            <v-text-field
              v-model="form.companyCode"
              label="Company Code"
              required
            />
            <v-text-field
              v-model="form.apiBaseUrl"
              label="API Base URL"
              required
            />
            <v-text-field
              v-model="form.addressLine1"
              label="Address Line 1"
              required
            />
            <v-text-field
              v-model="form.addressLine2"
              label="Address Line 2"
            />
            <v-text-field
              v-model="form.city"
              label="City"
              required
            />
            <v-text-field
              v-model="form.state"
              label="State"
              required
            />
            <v-text-field
              v-model="form.postalCode"
              label="Postal Code"
              required
            />
            <v-text-field
              v-model="form.phone"
              label="Phone Number"
              required
            />

            <v-combobox
              v-model="form.apiPorts"
              label="API Ports"
              multiple
              chips
              clearable
              :items="form.apiPorts"
              hint="Enter numeric port numbers"
            />

            <v-combobox
              v-model="form.products"
              label="Products"
              multiple
              chips
              clearable
            />
            <!-- Ship54 Tracking API Configuration -->
            <v-expansion-panels class="mb-4">
              <v-expansion-panel>
                <v-expansion-panel-title>Ship54 Tracking API Configuration</v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-alert
                    type="info"
                    class="mb-4"
                  >
                    <div class="font-weight-bold">Ship54 Tracking API Access</div>
                    <div class="text-caption">
                      Configure API credentials for Eclipse ERP to access invoice tracking without individual user login
                    </div>
                  </v-alert>
                  
                  <v-select
                    v-model="form.ship54Tracking.authMethod"
                    :items="[
                      { title: 'Disabled', value: 'disabled' },
                      { title: 'API User Credentials', value: 'apiUser' }
                    ]"
                    label="API Access Method"
                    outlined
                  />

                  <template v-if="form.ship54Tracking.authMethod === 'apiUser'">
                    <v-text-field
                      v-model="form.ship54Tracking.apiUser.username"
                      label="API Username"
                      hint="Username for Eclipse ERP tracking API access"
                      persistent-hint
                      outlined
                    />
                    <v-text-field
                      v-model="form.ship54Tracking.apiUser.password"
                      label="API Password"
                      type="password"
                      hint="Password for Eclipse ERP tracking API access"
                      persistent-hint
                      outlined
                    />
                    <v-alert
                      type="success"
                      class="mt-2"
                    >
                      <div class="text-caption">
                        <strong>Eclipse URL Format:</strong><br>
                        https://emp54.com/invoice-tracking/INV-12345?api_user={{form.ship54Tracking.apiUser.username}}&api_key={{form.ship54Tracking.apiUser.password}}
                      </div>
                    </v-alert>
                  </template>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <!-- Show only if surcharge is enabled -->
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title>Surcharge Configuration</v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-select
                    v-model="form.surcharge.authMethod"
                    :items="['loggedInUser', 'apiUser']"
                    label="Authorization Method"
                    outlined
                  />

                  <v-text-field
                    v-if="form.surcharge.authMethod === 'apiUser'"
                    v-model="form.surcharge.apiUser.username"
                    label="API Username"
                    outlined
                  />
                  <v-text-field
                    v-if="form.surcharge.authMethod === 'apiUser'"
                    v-model="form.surcharge.apiUser.password"
                    label="API Password"
                    type="password"
                    outlined
                  />

                  <v-divider class="my-4" />
                  <h4>Surcharge Product per Port</h4>
                  <div
                    v-for="port in form.apiPorts"
                    :key="port"
                  >
                    <v-text-field
                      v-model="form.surcharge.productsByPort[port]"
                      :label="`Port ${port} Product ID`"
                      outlined
                      type="number"
                    />
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <v-card-actions>
              <v-spacer />
              <v-btn
                text
                @click="closeDialog"
              >
                Cancel
              </v-btn>
              <v-btn
                color="primary"
                type="submit"
              >
                Save
              </v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Webhook Management Dialog -->
    <v-dialog
      v-model="webhookDialog"
      max-width="600"
    >
      <v-card v-if="selectedCompany">
        <v-card-title>
          <span class="text-h5">Manage Webhook - {{ selectedCompany.name }}</span>
        </v-card-title>

        <v-card-text>
          <div class="mb-4">
            <h4>Current Status</h4>
            <v-chip
              v-if="webhookStatus?.webhook?.isActive"
              color="success"
              class="mb-2"
            >
              <v-icon start>
                mdi-check-circle
              </v-icon>
              Active
            </v-chip>
            <v-chip
              v-else-if="webhookStatus?.webhook?.lastError"
              color="error"
              class="mb-2"
            >
              <v-icon start>
                mdi-alert-circle
              </v-icon>
              Error
            </v-chip>
            <v-chip
              v-else
              color="grey"
              class="mb-2"
            >
              <v-icon start>
                mdi-minus-circle
              </v-icon>
              No Webhook
            </v-chip>
          </div>

          <div
            v-if="webhookStatus?.webhook?.url"
            class="mb-4"
          >
            <h4>Webhook URL</h4>
            <v-text-field
              :value="webhookStatus.webhook.url"
              readonly
              density="compact"
              class="mb-2"
            />
          </div>

          <div
            v-if="webhookStatus?.webhook?.id"
            class="mb-4"
          >
            <h4>Webhook ID</h4>
            <v-text-field
              :value="webhookStatus.webhook.id"
              readonly
              density="compact"
              class="mb-2"
            />
          </div>

          <div
            v-if="webhookStatus?.webhook?.lastError"
            class="mb-4"
          >
            <h4>Last Error</h4>
            <v-alert
              type="error"
              density="compact"
            >
              {{ webhookStatus.webhook.lastError }}
            </v-alert>
          </div>

          <div
            v-if="webhookStatus?.webhook?.createdAt"
            class="mb-4"
          >
            <h4>Created</h4>
            <p class="text-caption">
              {{ formatDate(webhookStatus.webhook.createdAt) }}
            </p>
          </div>

          <div class="mb-4">
            <h4>Shippo Integration Status</h4>
            <v-chip
              v-if="webhookStatus?.hasValidToken"
              color="success"
              size="small"
            >
              <v-icon start>
                mdi-check
              </v-icon>
              Valid Token
            </v-chip>
            <v-chip
              v-else
              color="warning"
              size="small"
            >
              <v-icon start>
                mdi-alert
              </v-icon>
              No Valid Token
            </v-chip>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-btn
            v-if="!webhookStatus?.webhook?.isActive && webhookStatus?.hasValidToken"
            color="success"
            :loading="webhookLoading"
            @click="createWebhook"
          >
            <v-icon start>
              mdi-plus
            </v-icon>
            Create Webhook
          </v-btn>
          
          <v-btn
            v-if="webhookStatus?.webhook?.isActive"
            color="error"
            :loading="webhookLoading"
            @click="deleteWebhook"
          >
            <v-icon start>
              mdi-delete
            </v-icon>
            Delete Webhook
          </v-btn>

          <v-btn
            color="primary"
            :loading="webhookLoading"
            @click="refreshWebhookStatus"
          >
            <v-icon start>
              mdi-refresh
            </v-icon>
            Refresh Status
          </v-btn>

          <v-spacer />
          
          <v-btn
            text
            @click="closeWebhookDialog"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bulk Actions -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-btn
          color="primary"
          :loading="bulkLoading"
          @click="createAllWebhooks"
        >
          <v-icon start>
            mdi-webhook
          </v-icon>
          Create Webhooks for All Companies
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'

const companies = ref([])
const dialog = ref(false)
const editingCompany = ref(null)
const form = ref({
  name: '',
  companyCode: '',
  apiBaseUrl: '',
  addressLine1: '',
  addressLine2: '',
  city: '',
  state: '',
  postalCode: '',
  phone: '',
  apiPorts: [],
  products: [],
  surcharge: {
    authMethod: 'loggedInUser',
    apiUser: {
      username: '',
      password: ''
    },
    productsByPort: {}
  },
  ship54Tracking: {
    authMethod: 'disabled',
    apiUser: {
      username: '',
      password: ''
    }
  }
})

const headers = [
  { text: 'Name', value: 'name' },
  { text: 'Code', value: 'companyCode' },
  { text: 'Base URL', value: 'apiBaseUrl' },
  { text: 'Webhook Status', value: 'webhookStatus', sortable: false },
  { text: 'Actions', value: 'actions', sortable: false }
]

const loadCompanies = async () => {
  const res = await axios.get('/admin/companies')
  companies.value = res.data
}

const openDialog = () => {
  editingCompany.value = null
  form.value = {
    name: '',
    companyCode: '',
    apiBaseUrl: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postalCode: '',
    phone: '',
    apiPorts: [],
    products: [],
    surcharge: {
      authMethod: 'loggedInUser',
      apiUser: {
        username: '',
        password: ''
      },
      productsByPort: {}
    }
  }
  dialog.value = true
}

const closeDialog = () => dialog.value = false

const editCompany = (company) => {
  editingCompany.value = company._id
  form.value = {
    name: company.name || '',
    companyCode: company.companyCode || '',
    apiBaseUrl: company.apiBaseUrl || '',
    addressLine1: company.addressLine1 || '',
    addressLine2: company.addressLine2 || '',
    city: company.city || '',
    state: company.state || '',
    postalCode: company.postalCode || '',
    phone: company.phone || '',
    apiPorts: company.apiPorts || [],
    products: company.products || [],
    surcharge: {
      authMethod: company.surcharge?.authMethod || 'loggedInUser',
      apiUser: {
        username: company.surcharge?.apiUser?.username || '',
        password: company.surcharge?.apiUser?.password || ''
      },
      productsByPort: company.surcharge?.productsByPort || {}
    },
    ship54Tracking: {
      authMethod: company.ship54Tracking?.authMethod || 'disabled',
      apiUser: {
        username: company.ship54Tracking?.apiUser?.username || '',
        password: company.ship54Tracking?.apiUser?.password || ''
      }
    }
  }
  dialog.value = true
}

const saveCompany = async () => {
  if (editingCompany.value) {
    await axios.put(`/admin/companies/${editingCompany.value}`, form.value)
  } else {
    await axios.post('/admin/companies', form.value)
  }
  dialog.value = false
  loadCompanies()
}

const deleteCompany = async (id) => {
  await axios.delete(`/admin/companies/${id}`)
  loadCompanies()
}

// Webhook Management
const webhookDialog = ref(false)
const selectedCompany = ref(null)
const webhookStatus = ref(null)
const webhookLoading = ref(false)
const bulkLoading = ref(false)

const manageWebhook = async (company) => {
  selectedCompany.value = company
  webhookDialog.value = true
  await loadWebhookStatus()
}

const closeWebhookDialog = () => {
  webhookDialog.value = false
  selectedCompany.value = null
  webhookStatus.value = null
}

const loadWebhookStatus = async () => {
  if (!selectedCompany.value) return
  
  webhookLoading.value = true
  try {
    const response = await axios.get(`/admin/companies/${selectedCompany.value._id}/webhook/status`)
    webhookStatus.value = response.data
  } catch (error) {
    console.error('Failed to load webhook status:', error)
  } finally {
    webhookLoading.value = false
  }
}

const refreshWebhookStatus = async () => {
  await loadWebhookStatus()
  // Also refresh the main companies list to update the status chips
  await loadCompanies()
}

const createWebhook = async () => {
  if (!selectedCompany.value) return
  
  webhookLoading.value = true
  try {
    const response = await axios.post(`/admin/companies/${selectedCompany.value._id}/webhook/create`)
    console.log('Webhook created:', response.data)
    
    // Refresh status and companies list
    await refreshWebhookStatus()
    
    // Show success message
    alert('Webhook created successfully!')
    
  } catch (error) {
    console.error('Failed to create webhook:', error)
    alert(`Failed to create webhook: ${error.response?.data?.error || error.message}`)
  } finally {
    webhookLoading.value = false
  }
}

const deleteWebhook = async () => {
  if (!selectedCompany.value) return
  
  if (!confirm('Are you sure you want to delete this webhook?')) {
    return
  }
  
  webhookLoading.value = true
  try {
    const response = await axios.delete(`/admin/companies/${selectedCompany.value._id}/webhook`)
    console.log('Webhook deleted:', response.data)
    
    // Refresh status and companies list
    await refreshWebhookStatus()
    
    // Show success message
    alert('Webhook deleted successfully!')
    
  } catch (error) {
    console.error('Failed to delete webhook:', error)
    alert(`Failed to delete webhook: ${error.response?.data?.error || error.message}`)
  } finally {
    webhookLoading.value = false
  }
}

const createAllWebhooks = async () => {
  if (!confirm('This will create webhooks for all companies with valid Shippo tokens. Continue?')) {
    return
  }
  
  bulkLoading.value = true
  try {
    const response = await axios.post('/admin/companies/webhooks/create-all')
    console.log('Bulk webhook creation result:', response.data)
    
    // Refresh companies list
    await loadCompanies()
    
    // Show results
    const results = response.data.results || []
    const successful = results.filter(r => r.success).length
    const failed = results.filter(r => !r.success).length
    
    alert(`Webhook creation complete!\nSuccessful: ${successful}\nFailed: ${failed}\n\nCheck console for details.`)
    
  } catch (error) {
    console.error('Failed to create webhooks:', error)
    alert(`Failed to create webhooks: ${error.response?.data?.error || error.message}`)
  } finally {
    bulkLoading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

onMounted(loadCompanies)
</script>
