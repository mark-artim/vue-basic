<template>
  <v-container class="pa-4">
    <v-row
      justify="space-between"
      align="center"
    >
      <v-col cols="6">
        <h2>User Admin</h2>
      </v-col>
      <v-col
        cols="6"
        class="text-right"
      >
        <v-btn
          color="primary"
          @click="openDialog"
        >
          Add User
        </v-btn>
      </v-col>
    </v-row>

    <v-data-table
      :items="users"
      :headers="headers"
      class="elevation-1"
    >
      <template #item.company="{ item }">
        {{ item.companyId?.name || '—' }}
      </template>
      <template #item.actions="{ item }">
        <v-btn
          icon
          @click="editUser(item)"
        >
          <v-icon>mdi-pencil</v-icon>
        </v-btn>
        <v-btn
          icon
          @click="deleteUser(item._id)"
        >
          <v-icon color="red">
            mdi-delete
          </v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <v-dialog
      v-model="dialog"
      max-width="800"
      persistent
    >
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingUser ? 'Edit' : 'Add' }} User</span>
        </v-card-title>

        <v-card-text>
          <v-alert
            v-if="errorMessage"
            type="error"
            class="mb-4"
          >
            {{ errorMessage }}
          </v-alert>

          <v-alert
            v-if="inviteStatus.message"
            :type="inviteStatus.type"
            class="mb-4"
            dismissible
            @input="inviteStatus.message = ''"
          >
            {{ inviteStatus.message }}
          </v-alert>

          <v-form @submit.prevent="saveUser">
            <v-text-field
              v-model="form.email"
              label="Email"
              required
            />
            <v-text-field
              v-model="form.firstName"
              label="First Name"
              required
            />
            <v-text-field
              v-model="form.lastName"
              label="Last Name"
              required
            />
            <v-select
              v-model="form.userType"
              :items="['admin', 'customer']"
              label="User Type"
              required
            />

            <v-text-field
              v-if="form.userType === 'admin'"
              v-model="form.password"
              :type="'password'"
              :label="editingUser ? 'Reset Password (leave blank to keep current)' : 'Password'"
              :hint="editingUser ? 'Leave blank if you don’t want to reset' : ''"
              persistent-hint
            />

            <v-text-field
              v-if="form.userType === 'customer'"
              v-model="form.erpUserName"
              label="ERP Username"
              required
            />

            <v-select
              v-model="form.companyId"
              :items="companies"
              item-value="_id"
              item-title="name"
              label="Company"
              :disabled="form.userType === 'admin'"
            />

            <v-select
              v-model="form.products"
              :items="companyProducts"
              item-title="name"
              item-value="_id"
              label="Products"
              multiple
              chips
              clearable
            />

            <div
              v-for="product in form.products"
              :key="product"
            >
              <v-combobox
                v-model="rolesByProduct[product]"
                :label="`Roles for ${product}`"
                :items="getRolesForProduct(product) || []"
                multiple
                chips
                clearable
              />
            </div>

            <v-select
              v-model="selectedInviteType"
              :items="inviteOptions"
              item-title="label"
              item-value="value"
              label="Message Type"
            />

            <v-btn
              :loading="sendingInvite"
              :disabled="sendingInvite"
              color="success"
              class="mt-2"
              @click="sendInvite"
            >
              {{ sendingInvite ? 'Sending...' : 'Send Invite' }}
            </v-btn>

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
  </v-container>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import axios from '@/utils/axios'
import { useMenuStore } from '@/stores/menuStore'

const menuStore = useMenuStore()
const users = ref([])
const companies = ref([])
const dialog = ref(false)
const editingUser = ref(null)
const errorMessage = ref('')
const inviteStatus = ref({ type: '', message: '' })
const sendingInvite = ref(false)
const selectedInviteType = ref('standard')

const form = ref({
  email: '', firstName: '', lastName: '', userType: '',
  erpUserName: '', password: '', companyId: '', roles: {}, products: []
})

const allProducts = ref([])

const loadProducts = async () => {
  const res = await axios.get('/products')
  allProducts.value = res.data
}

const companyProducts = computed(() => {
  const company = companies.value.find(c => c._id === form.value.companyId)
  return company?.products || []
})

const rolesByProduct = reactive({})

const getRolesForProductFUCKEDUP = (productId) => {
  const product = allProducts.value.find(p => p._id === productId)
  const code = product?.code || product?.name
  console.log('[getRolesForProduct]', productId, '→', code)
  return code ? menuStore.getRolesByProduct(code) : []
}

const getRolesForProduct = (productCode) => {
  console.log('[getRolesForProduct]', productCode, '→ roles:', menuStore.getRolesByProduct(productCode))
  return menuStore.getRolesByProduct(productCode)
}



const inviteOptions = [
  { label: 'Standard Invite', value: 'standard' },
  { label: 'Heritage Invite', value: 'heritage' }
]

const headers = [
  { text: 'Email', value: 'email' },
  { text: 'Name', value: 'firstName' },
  { text: 'Type', value: 'userType' },
  { text: 'Company', value: 'company' },
  { text: 'Actions', value: 'actions', sortable: false }
]

const loadUsers = async () => {
  const res = await axios.get('/admin/users')
  users.value = res.data
}

const loadCompanies = async () => {
  const res = await axios.get('/admin/companies')
  companies.value = res.data
}

const openDialog = () => {
  editingUser.value = null
  errorMessage.value = ''
  inviteStatus.value = { type: '', message: '' }
  selectedInviteType.value = 'standard'
  form.value = {
    email: '', firstName: '', lastName: '', userType: '',
    erpUserName: '', password: '', companyId: '', roles: {}, products: []
  }
  Object.keys(rolesByProduct).forEach(k => delete rolesByProduct[k])
  dialog.value = true
}

const closeDialog = () => dialog.value = false

const editUser = (user) => {
  console.log('[editUser] roles:', user.roles)
  editingUser.value = user._id
  errorMessage.value = ''
  inviteStatus.value = { type: '', message: '' }
  form.value = {
    ...user,
    password: '',
    companyId: user.companyId?._id || user.companyId,
    roles: user.roles || {},
    products: Object.keys(user.roles || {})
  }
  form.value.products = form.value.products.filter(p => typeof p === 'string' && p !== '0')
  Object.keys(rolesByProduct).forEach(k => delete rolesByProduct[k])
  for (const p of form.value.products) {
    rolesByProduct[p] = [...(form.value.roles?.[p] || [])]
  }
  dialog.value = true
}

const onProductsChange = (products) => {
  form.value.products = products
  const existing = new Set(Object.keys(rolesByProduct))
  for (const p of products) {
    if (!rolesByProduct[p]) rolesByProduct[p] = []
  }
  for (const old of existing) {
    if (!products.includes(old)) delete rolesByProduct[old]
  }
}

const saveUser = async () => {
  try {
    const validProductIds = allProducts.value.map(p => p._id)
    const invalid = form.value.products.filter(p => !validProductIds.includes(p))

    if (invalid.length) {
      errorMessage.value = `Invalid product(s): ${invalid.join(', ')}`
      return
    }

    const cleanedRoles = {}
    for (const p of form.value.products) {
      if (rolesByProduct[p]) {
        cleanedRoles[p] = rolesByProduct[p]
      }
    }

    const payload = {
      ...form.value,
      roles: cleanedRoles,
      products: Object.keys(cleanedRoles)
    }


    if (!payload.password) delete payload.password

    if (editingUser.value) {
      await axios.put(`/admin/users/${editingUser.value}`, payload)
    } else {
      await axios.post('/admin/users', payload)
    }

    dialog.value = false
    loadUsers()
  } catch (err) {
    const msg = err?.response?.data?.error || err.message || 'Unknown error occurred'
    errorMessage.value = `Save failed: ${msg}`
  }
}


const deleteUser = async (id) => {
  await axios.delete(`/admin/users/${id}`)
  loadUsers()
}

const sendInvite = async () => {
  try {
    const { email, _id } = form.value
    if (!email || !_id) {
      inviteStatus.value = { type: 'error', message: 'Missing email or user ID.' }
      return
    }
    sendingInvite.value = true

    await axios.post('/api/send', {
      toEmail: email,
      userId: _id,
      templateType: selectedInviteType.value
    })

    inviteStatus.value = {
      type: 'success',
      message: `Invite (${selectedInviteType.value}) sent to ${email}`
    }
    setTimeout(() => (inviteStatus.value.message = ''), 5000)
  } catch (err) {
    const msg = err.response?.data?.message || err.message
    inviteStatus.value = {
      type: 'error',
      message: `Failed to send invite: ${msg}`
    }
  } finally {
    sendingInvite.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadCompanies()
  loadProducts()
  menuStore.fetchMenus().then(() => {
    console.log('[menuStore loaded menus]', menuStore.menus)
  })
})
</script>

<style scoped>
.v-card-actions {
  padding-bottom: 16px;
}
</style>
