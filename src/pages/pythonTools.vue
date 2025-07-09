<template>
  <v-container class="pa-4">
    <h2>Python Tools</h2>
    <v-select
      v-model="selectedTool"
      :items="toolOptions"
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

    <!-- Value Count Tool -->
    <div v-else-if="selectedTool === 'value-count'">
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
        label="Select Column to Summarize"
        outlined
        class="mb-4"
      />
      <v-btn
        :disabled="!uploadedFile || !selectedColumn"
        color="primary"
        @click="countValues"
        :loading="loading"
      >
        Count Values
      </v-btn>

      <v-alert v-if="error" type="error" class="mt-4">{{ error }}</v-alert>

      <v-simple-table v-if="valueCounts.length" class="mt-4">
        <thead>
          <tr>
            <th>{{ selectedColumn }}</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in valueCounts" :key="item.value">
            <td>{{ item.value }}</td>
            <td>{{ item.count }}</td>
          </tr>
        </tbody>
      </v-simple-table>

      <v-btn
        v-if="valueCounts.length"
        color="primary"
        class="mt-2"
        @click="exportValueCounts"
      >
        Export Results
      </v-btn>
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
  { value: 'value-count', text: 'Value Count by Column' },
  { value: 'comma-remover', text: 'Comma Remover (Coming Soon)' }
]

// File input & processing state
const uploadedFile = ref(null)
const headers = ref([])
const selectedColumn = ref(null)
const allRows = ref([])
const filteredRows = ref([])
const valueCounts = ref([])
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
    valueCounts.value = []
  }
})

watch(headerRow, () => {
  if (uploadedFile.value) parseHeaders(uploadedFile.value)
  valueCounts.value = []
})

watch(selectedTool, () => {
  selectedColumn.value = null
  filteredRows.value = []
  valueCounts.value = []
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

function countValues() {
  error.value = null
  loading.value = true
  const counts = {}
  allRows.value.forEach(row => {
    const rawValue = row[selectedColumn.value]
    if (rawValue === undefined || rawValue === null) return
    const key = String(rawValue).trim()
    if (key === '') return
    counts[key] = (counts[key] || 0) + 1
  })

  valueCounts.value = Object.entries(counts)
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count)

  loading.value = false
}

function exportValueCounts() {
  if (!valueCounts.value.length) return
  const headers = [`${selectedColumn.value}`, 'Count']
  const rows = valueCounts.value.map(item => [item.value, item.count])
  const csvContent = [headers, ...rows]
    .map(r => r.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'value_counts.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

</script>

<style scoped>
h2 {
  margin: 1rem 0;
}
</style>
