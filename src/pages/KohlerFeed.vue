<template>
  <v-container>
    <h1>Kohler Monthly Sales Feed</h1>

    <!-- File Input -->
    <v-file-input
      label="Upload CSV File"
      v-model="uploadedFile"
      accept=".csv"
      @change="handleFileUpload"
      required
    />

    <!-- Options -->
    <v-switch v-model="combineItems" label="Combine items on same invoice with same part number" />
    <v-switch v-model="showOnlyTile" label="Show only tile (ProductSKU starts with 'AS')" />

    <!-- Filename Input -->
    <v-text-field
      v-model="exportFilename"
      label="Export Filename"
      :rules="[v => !!v || 'Filename is required']"
      placeholder="CompanyName_Sales_YYYY_MM_DD"
      hint="CompanyName_Sales_YYYY_MM_DD"
      persistent-hint
    />

    <!-- Table Output -->
    <v-data-table
      :headers="tableHeaders"
      :items="displayData"
      class="mt-4"
      dense
    />

    <!-- Export Button -->
    <v-btn
      class="mt-4"
      color="primary"
      :disabled="!exportFilename || displayData.length === 0"
      @click="downloadExport"
    >
      Save Kohler Export File
    </v-btn>
  </v-container>
</template>

<script setup>
import { ref, watch } from 'vue'
import Papa from 'papaparse'

const uploadedFile = ref(null)
const exportFilename = ref('')
const combineItems = ref(true)
const showOnlyTile = ref(false)

const originalData = ref([])
const displayData = ref([])
const tableHeaders = ref([])

function handleFileUpload() {
  const file = uploadedFile.value

  // If user selects multiple accidentally or wrapper object
  const actualFile = Array.isArray(file) ? file[0] : file

  if (!actualFile || !(actualFile instanceof Blob)) {
    console.error('Invalid file type')
    return
  }

  Papa.parse(actualFile, {
  header: true,
  skipEmptyLines: true,
  skipRows:1,
  transformHeader: header => header.trim(),
  complete: (results) => {
    console.log(results.meta.fields) // should now show clean headers
    originalData.value = results.data
    tableHeaders.value = results.meta.fields
        .filter(f => !!f) // ensure header is not null/undefined
        .map(f => ({
            text: f,
            value: f
        }))

    processData()
  }
})

}


function processData() {
  let data = [...originalData.value]

  // Filter for "tile" products if enabled
  if (showOnlyTile.value) {
    data = data.filter(row => row.ProductSKU?.startsWith('AS'))
  }

  // Combine logic if enabled
  if (combineItems.value) {
    const combinedMap = new Map()

    data.forEach(row => {
      const key = `${row['Invoice#']}_${row['ProductSKU']}`
      if (!combinedMap.has(key)) {
        combinedMap.set(key, { ...row })
      } else {
        combinedMap.get(key).Quantity = (
          parseInt(combinedMap.get(key).Quantity || 0, 10) +
          parseInt(row.Quantity || 0, 10)
        ).toString()
      }
    })

    data = Array.from(combinedMap.values())
  }

  displayData.value = data
}

watch([combineItems, showOnlyTile], processData)

function downloadExport() {
  if (!exportFilename.value || displayData.value.length === 0) return

  const headers = tableHeaders.value.map(h => h.value)
  const rows = displayData.value.map(row =>
    headers.map(header => row[header] || '')
  )

  const lines = [headers.join('\t'), ...rows.map(r => r.join('\t'))].join('\n')
  const blob = new Blob([lines], { type: 'text/plain' })

  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${exportFilename.value}.txt`
  link.click()
  URL.revokeObjectURL(link.href)
}
</script>
