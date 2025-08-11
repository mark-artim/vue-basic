<template>
  <v-container class="pa-4">
    <v-card outlined>
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="text-h6 d-flex align-center">
          <v-icon class="mr-2">
            mdi-file-document
          </v-icon> System Logs
        </div>
      </v-card-title>

      <v-card-text>
        <v-row
          class="mb-4"
          align="center"
          dense
        >
          <v-col
            cols="12"
            sm="4"
          >
            <v-select
              v-model="selectedType"
              :items="logTypes"
              label="Filter by Type"
              clearable
              dense
              outlined
            />
          </v-col>
          <v-col
            cols="12"
            sm="4"
          >
            <v-text-field
              v-model="emailFilter"
              label="Filter by Email"
              dense
              clearable
              outlined
            />
          </v-col>
          <v-col
            cols="6"
            sm="2"
            class="d-flex justify-end"
          >
            <v-btn
              color="primary"
              class="w-100"
              :loading="loadingLogs"
              @click="fetchLogs"
            >
              Apply Filters
            </v-btn>
          </v-col>
          <v-col
            cols="6"
            sm="2"
            class="d-flex justify-end"
          >
            <v-btn
              color="primary"
              class="w-100"
              :loading="loadingLogs"
              variant="flat"
              @click="fetchLogs"
            >
              Refresh
            </v-btn>
          </v-col>
        </v-row>

        <v-data-table
          :items="logs"
          :headers="headers"
          item-value="_id"
          class="elevation-1"
          dense
          fixed-header
          height="500px"
          :header-props="{ color: 'grey darken-4', class: 'text-white' }"
        >
          <template #item.timestamp="{ item }">
            {{ new Date(item.timestamp).toLocaleString() }}
          </template>

          <template #item.meta="{ item }">
            <div>
              <v-chip
                class="ma-1"
                color="indigo"
                label
                small
              >
                IP: {{ item.meta.ip }}
              </v-chip>
              <v-chip
                class="ma-1"
                color="purple"
                label
                small
              >
                Method: {{ item.meta.method }}
              </v-chip>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>


<script setup>
import { ref, onMounted } from 'vue'
import axios from '@/utils/axios'

const logs = ref([])
const loadingLogs = ref(false)
const selectedType = ref('')
const emailFilter = ref('')
const logTypes = ['login', 'login-failure', 'file-upload', 'surcharge'] // add more as needed

const headers = [
  { text: 'Timestamp', value: 'timestamp' },
  { text: 'User', value: 'userEmail' },
  { text: 'Company', value: 'companyCode' },
  { text: 'Type', value: 'type' },
  { text: 'Message', value: 'message' },
  { text: 'Meta Info', value: 'meta' }
]

async function fetchLogs() {
  loadingLogs.value = true
  try {
    const res = await axios.get('/logs', { params: {
        type: selectedType.value || undefined,
        email: emailFilter.value || undefined
      }})
      logs.value = res.data
  } catch (err) {
    console.error('Failed to fetch logs:', err)
  } finally {
    loadingLogs.value = false
  }
}

onMounted(fetchLogs)
</script>
