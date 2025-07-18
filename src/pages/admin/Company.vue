<template>
  <v-container class="pa-4">
    <v-row justify="space-between" align="center">
      <v-col cols="6">
        <h2>Company Admin</h2>
      </v-col>
      <v-col cols="6" class="text-right">
        <v-btn color="primary" @click="openDialog">Add Company</v-btn>
      </v-col>
    </v-row>

    <v-data-table :items="companies" :headers="headers" class="elevation-1">
      <template #item.actions="{ item }">
        <v-btn icon @click="editCompany(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn icon @click="deleteCompany(item._id)"><v-icon color="red">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingCompany ? 'Edit' : 'Add' }} Company</span>
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="saveCompany">
            <v-text-field v-model="form.name" label="Company Name" required />
            <v-text-field v-model="form.companyCode" label="Company Code" required />
            <v-text-field v-model="form.apiBaseUrl" label="API Base URL" required />
            <v-text-field v-model="form.addressLine1" label="Address Line 1" required />
            <v-text-field v-model="form.addressLine2" label="Address Line 2" />
            <v-text-field v-model="form.city" label="City" required />
            <v-text-field v-model="form.state" label="State" required />
            <v-text-field v-model="form.postalCode" label="Postal Code" required />
            <v-text-field v-model="form.phone" label="Phone Number" required />

            <v-combobox
              v-model="form.apiPorts"
              label="API Ports"
              multiple
              chips
              clearable
              :items="form.apiPorts"
              hint="Enter numeric port numbers"
            />

            <v-combobox v-model="form.products" label="Products" multiple chips clearable />
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
                  <div v-for="port in form.apiPorts" :key="port">
                    <v-text-field
                      :label="`Port ${port} Product ID`"
                      v-model="form.surcharge.productsByPort[port]"
                      outlined
                      type="number"
                    />
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <v-card-actions>
              <v-spacer />
              <v-btn text @click="closeDialog">Cancel</v-btn>
              <v-btn color="primary" type="submit">Save</v-btn>
            </v-card-actions>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>
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
  }
})

const headers = [
  { text: 'Name', value: 'name' },
  { text: 'Code', value: 'companyCode' },
  { text: 'Base URL', value: 'apiBaseUrl' },
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

onMounted(loadCompanies)
</script>
