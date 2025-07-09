<template>
  <v-container class="pa-4">
    <h2>Python Tools</h2>
    <v-select
      v-model="selectedTool"
      :items="tools"
      item-title="label"
      item-value="value"
      label="Select a Tool"
    />
    <!-- Duplicate Finder Tool -->
    <div v-if="selectedTool === 'duplicate-finder'">
    <v-file-input
      v-model="uploadedFile"
      label="Upload CSV File"
      accept=".csv"
      outlined
      class="mb-4"
    />
    <v-text-field
      v-model.number="headerRow"
      type="number"
      min="1"
      label="Header Row Number"
      class="mb-4"
    />
      <v-select
        v-if="headers.length"
        v-model="selectedColumn"
        :items="headers"
        label="Select Column to Check for Duplicates"
        outlined
        class="mb-4"
      />
      <v-btn
        :disabled="!uploadedFile || !selectedColumn"
        color="primary"
        @click="findDuplicates"
        :loading="loading"
      >
        Find Duplicates
      </v-btn>

      <v-alert v-if="error" type="error" class="mt-4">{{ error }}</v-alert>

      <div v-if="filteredRows.length" class="text-red text--darken-4 font-weight-bold text-h6 py-4">
        <strong>{{ duplicateCount }} duplicate row<span v-if="duplicateCount !== 1">s</span> found</strong>
      </div>

      <v-simple-table v-if="filteredRows.length" class="mt-4">
        <thead>
          <tr>
            <th v-for="(col, i) in headers" :key="i">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in filteredRows" :key="i">
            <td v-for="col in headers" :key="col">{{ row[col] }}</td>
          </tr>
        </tbody>
      </v-simple-table>
    </div>

    <!-- Placeholder for Comma Remover Tool -->
    <div v-else-if="selectedTool === 'comma-remover'">
      <p>This tool will remove commas and save as .txt. (Coming soon!)</p>
    </div>
  </v-container>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import Papa from 'papaparse'

// Tool selection
const selectedTool = ref('duplicate-finder')
const toolOptions = [
  { value: 'duplicate-finder', text: 'Find Duplicates by Column' },
  { value: 'comma-remover', text: 'Comma Remover (Coming Soon)' }
]

// File input & processing state
const uploadedFile = ref(null)
const headers = ref([])
const selectedColumn = ref(null)
const allRows = ref([])
const filteredRows = ref([])
const error = ref(null)
const loading = ref(false)
const headerRow = ref(1)

// Watch file change and trigger CSV parse
watch(uploadedFile, (newFile) => {
  if (newFile) {
    parseHeaders(newFile)
  } else {
    headers.value = []
    allRows.value = []
    filteredRows.value = []
  }
})

watch(headerRow, () => {
  if (uploadedFile.value) parseHeaders(uploadedFile.value)
})

// Parse CSV and extract headers
function parseHeaders(file) {
  loading.value = true
  error.value = null
  const skipRows = Math.max(0, headerRow.value - 1)
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    skipRows,
    complete: (results) => {
      allRows.value = results.data
      headers.value = results.meta.fields || []
      loading.value = false
    },
    error: (err) => {
      error.value = err.message
      loading.value = false
    }
  })
}

// Find rows with duplicate values in selected column
function findDuplicates() {
  error.value = null
  loading.value = true
  const counts = {}
  allRows.value.forEach(row => {
    const rawValue = row[selectedColumn.value]
    if (rawValue === undefined || rawValue === null) return
    const key = String(rawValue).trim()
    if (key === '') return
    if (!counts[key]) counts[key] = []
    counts[key].push(row)
  })

  filteredRows.value = Object.values(counts)
    .filter(group => group.length > 1)
    .flat()

  loading.value = false
}

const duplicateCount = computed(() => filteredRows.value.length)

</script>

<style scoped>
h2 {
  margin: 1rem 0;
}
</style>
