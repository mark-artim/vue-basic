<template>
  <v-container class="pa-4">
    <v-card
      max-width="600"
      class="mx-auto mb-6"
    >
      <v-card-title>Add Menu</v-card-title>
      <v-card-text>
        <v-form
          ref="formRef"
          @submit.prevent="submitForm"
        >
          <v-text-field
            v-model="menu.name"
            label="Menu Name"
            :rules="[rules.required]"
            outlined
            dense
            class="mb-3"
          />
          <v-text-field
            v-model="menu.path"
            label="Path"
            :rules="[rules.required]"
            outlined
            dense
            class="mb-3"
          />
          <v-select
            v-model="menu.product"
            :items="productOptions"
            label="Product"
            :rules="[rules.required]"
            outlined
            dense
            class="mb-3"
          />
          <v-combobox
            v-model="menu.roles"
            :items="roleOptions"
            label="Roles"
            multiple
            chips
            clearable
            outlined
            class="mb-3"
          />

          <v-btn
            :loading="loading"
            type="submit"
            color="primary"
            block
          >
            Add Menu
          </v-btn>
        </v-form>

        <v-alert
          v-if="successMessage"
          type="success"
          class="mt-4"
        >
          {{ successMessage }}
        </v-alert>
        <v-alert
          v-if="errorMessage"
          type="error"
          class="mt-4"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title>Existing Menus</v-card-title>
      <v-data-table
        :headers="tableHeaders"
        :items="menus"
        :loading="loadingMenus"
        class="elevation-1"
        item-value="_id"
        dense
      >
        <template #item.roles="{ item }">
          <v-chip-group column>
            <v-chip
              v-for="role in item.roles"
              :key="role"
              small
            >
              {{ role }}
            </v-chip>
          </v-chip-group>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/utils/axios'

const formRef = ref(null)
const loading = ref(false)
const loadingMenus = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const menu = ref({
  name: '',
  path: '',
  product: '',
  roles: []
})

const productOptions = ['e54', 'eclipse']
const roleOptions = ['admin', 'contact', 'product']

const menus = ref([])

const rules = {
  required: v => !!v || 'Required'
}

const tableHeaders = [
  { title: 'Name', key: 'name' },
  { title: 'Path', key: 'path' },
  { title: 'Product', key: 'product' },
  { title: 'Roles', key: 'roles' }
]

const fetchMenus = async () => {
  loadingMenus.value = true
  try {
    const res = await apiClient.get('/admin/menus')
    menus.value = res.data
  } catch (err) {
    console.error('Failed to fetch menus:', err)
  } finally {
    loadingMenus.value = false
  }
}

const submitForm = async () => {
  if (!(await formRef.value.validate())) return

  loading.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await apiClient.post('/admin/menus', menu.value)
    successMessage.value = 'Menu created successfully!'
    menu.value = { name: '', path: '', product: '', roles: [] }
    fetchMenus()
  } catch (err) {
    console.error(err)
    errorMessage.value = err.response?.data?.message || 'Failed to create menu.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMenus()
})
</script>
