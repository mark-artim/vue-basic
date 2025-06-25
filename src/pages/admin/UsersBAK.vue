<template>
  <v-container class="pa-4">
    <v-row justify="space-between" align="center">
      <v-col cols="6">
        <h2>User Admin</h2>
      </v-col>
      <v-col cols="6" class="text-right">
        <v-btn color="primary" @click="openDialog">Add User</v-btn>
      </v-col>
    </v-row>

    <v-data-table :items="users" :headers="headers" class="elevation-1">
      <template #item.company="{ item }">
        {{ item.companyId?.name || '—' }}
      </template>
      <template #item.actions="{ item }">
        <v-btn icon @click="editUser(item)"><v-icon>mdi-pencil</v-icon></v-btn>
        <v-btn icon @click="deleteUser(item._id)"><v-icon color="red">mdi-delete</v-icon></v-btn>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingUser ? 'Edit' : 'Add' }} User</span>
        </v-card-title>

        <v-card-text>
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
            <v-text-field v-model="form.email" label="Email" required />
            <v-text-field v-model="form.firstName" label="First Name" required />
            <v-text-field v-model="form.lastName" label="Last Name" required />
            <!-- <v-select v-model="form.authType" :items="['internal', 'erp']" label="Auth Type" required /> -->
            <v-select v-model="form.userType" :items="['admin', 'customer']" label="User Type" required />
            <v-text-field
              v-if="form.userType === 'admin'"
              v-model="form.password"
              :type="'password'"
              :label="editingUser ? 'Reset Password (leave blank to keep current)' : 'Password'"
              :hint="editingUser ? 'Leave blank if you don’t want to reset' : ''"
              persistent-hint
            />

            <v-text-field v-if="form.userType === 'customer'" v-model="form.erpUserName" label="ERP Username" required />
            <v-select
              v-model="form.companyId"
              :items="companies"
              item-value="_id"
              item-title="name"
              label="Company"
              :disabled="form.userType === 'admin'"
            />
            <v-combobox v-model="form.roles" label="Roles" multiple chips clearable />
            <v-combobox v-model="form.products" label="Products" multiple chips clearable />
            <v-divider class="my-4" />
            <v-select
              v-model="selectedInviteType"
              :items="inviteOptions"
              item-title="label"
              item-value="value"
              label="Message Type"
            />
            <v-btn color="primary" @click="sendInvite">Send Messge</v-btn>

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

const users = ref([])
const companies = ref([])
const dialog = ref(false)
const editingUser = ref(null)
const errorMessage = ref('')
const inviteStatus = ref({ type: '', message: '' })
const form = ref({
  email: '', firstName: '', lastName: '', userType: '',
  erpUserName: '', password: '', companyId: '', roles: [], products: []
})
const selectedInviteType = ref('standard')
const inviteOptions = [
  { label: 'Standard Invite', value: 'standard' },
  { label: 'Heritage Invite', value: 'heritage' },
  // Add more later like 'reset-password'
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
  form.value = {
    email: '', firstName: '', lastName: '', userType: '',
    erpUserName: '', hashedPassword: '', companyId: '', roles: [], products: []
  }
  dialog.value = true
}

const closeDialog = () => dialog.value = false

const editUser = (user) => {
  editingUser.value = user._id
  errorMessage.value = ''
  form.value = {
    ...user,
    companyId: user.companyId?._id || '',
    password: '' // Clear password field
  }
  dialog.value = true
}

const sendInvite = async () => {
  try {
    const { email, _id } = form.value
    if (!email || !_id) {
      inviteStatus.value = { type: 'error', message: 'Missing email or user ID.' }
      return
    }

    await axios.post('/api/send', {
      toEmail: email,
      userId: _id,
      templateType: selectedInviteType.value
    })

    inviteStatus.value = {
      type: 'success',
      message: `Invite (${selectedInviteType.value}) sent to ${email}`
    }
  } catch (err) {
    const msg = err.response?.data?.message || err.message
    inviteStatus.value = {
      type: 'error',
      message: `Failed to send invite: ${msg}`
    }
  }
}

const saveUser = async () => {
  try {
    errorMessage.value = ''
    const payload = { ...form.value }
    console.log('[Frontend] Payload being sent to backend:', payload)

    // Only send password if it's set
    if (!payload.password) {
      delete payload.password
    }

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

onMounted(() => {
  loadUsers()
  loadCompanies()
})
</script>
