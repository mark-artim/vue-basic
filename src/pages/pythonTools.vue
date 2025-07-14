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
      <div class="value-count-controls">
        <v-btn
          :disabled="!uploadedFile || !selectedColumn"
          color="primary"
          @click="countValues"
          :loading="loading"
        >
          Count Values
        </v-btn>
        <v-btn
          v-if="valueCounts.length"
          color="primary"
          @click="exportValueCounts"
        >
          Export Results
        </v-btn>
      </div>
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
  { value: 'duplicate-finder', label: 'Find Duplicates by Column' },
  { value: 'value-count', label: 'Value Count by Column' },
  { value: 'comma-remover', label: 'Comma Remover (Coming Soon)' }
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
  console.log('[headerRow changed] New value:', headerRow.value)
  selectedColumn.value = null
  valueCounts.value = []
  if (uploadedFile.value) {
    console.log('[parseHeaders triggered]')
    parseHeaders(uploadedFile.value)
  }
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

  Papa.parse(file, {
    header: false,
    skipEmptyLines: true,
    complete: (results) => {
      const rows = results.data
      const headerIndex = Math.max(0, headerRow.value - 1)

      if (!rows.length || rows.length <= headerIndex) {
        error.value = 'Invalid header row. Not enough data.'
        headers.value = []
        allRows.value = []
        loading.value = false
        return
      }

      const rawHeaders = rows[headerIndex].map(h => String(h).trim())
      headers.value = rawHeaders.filter(h => h !== '')
      selectedColumn.value = null

      // Convert rows below the header into objects
      const dataRows = rows.slice(headerIndex + 1)
      allRows.value = dataRows.map(row => {
        const obj = {}
        rawHeaders.forEach((key, i) => {
          obj[key] = row[i]
        })
        return obj
      })

      loading.value = false
      console.log('[Manual Header Parse]', headers.value)
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

.v-simple-table th {
  font-weight: bold;
  text-align: left;
  padding: 8px;
  background-color: #1e1e1e; /* dark mode friendly */
  border-bottom: 1px solid #444;
}

.v-simple-table td {
  padding: 8px;
  border-bottom: 1px solid #333;
}

.v-simple-table {
  width: 100%;
  margin-top: 1rem;
}

.value-count-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

</style>
