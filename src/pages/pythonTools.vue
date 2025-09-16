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
        :loading="loading"
        @click="findDuplicates"
      >
        Find Duplicates
      </v-btn>

      <v-alert
        v-if="error"
        type="error"
        class="mt-4"
      >
        {{ error }}
      </v-alert>

      <div
        v-if="filteredRows.length"
        class="text-red text--darken-4 font-weight-bold text-h6 py-4"
      >
        <strong>{{ duplicateCount }} duplicate row<span v-if="duplicateCount !== 1">s</span> found</strong>
      </div>

      <v-simple-table
        v-if="filteredRows.length"
        class="mt-4"
      >
        <thead>
          <tr>
            <th
              v-for="(col, i) in headers"
              :key="i"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in filteredRows"
            :key="i"
          >
            <td
              v-for="col in headers"
              :key="col"
            >
              {{ row[col] }}
            </td>
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
          :loading="loading"
          @click="countValues"
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
      <v-simple-table
        v-if="valueCounts.length"
        class="mt-4"
      >
        <thead>
          <tr>
            <th>{{ selectedColumn }}</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in valueCounts"
            :key="item.value"
          >
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

    <!-- PDW Import File Prep Tool -->
    <div v-else-if="selectedTool === 'pdw-file-prep'">
      <!-- File Upload Section -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="primary"
          >
            mdi-file-upload
          </v-icon>
          File Upload & Preview
        </v-card-title>
        <v-card-text>
          <v-file-input
            v-model="uploadedFile"
            label="Upload CSV File"
            accept=".csv"
            outlined
            class="mb-4"
            @change="onFileUpload"
          />
          
          <v-text-field
            v-model.number="skipRows"
            type="number"
            min="0"
            label="Skip Rows (headers usually on row after skipped rows)"
            hint="Number of rows to skip at the top of the file"
            persistent-hint
            class="mb-4"
            @input="refreshPreview"
          />
          
          <v-btn
            v-if="uploadedFile"
            color="secondary"
            variant="outlined"
            :loading="loadingPreview"
            class="mb-4"
            @click="refreshPreview"
          >
            <v-icon class="me-1">
              mdi-refresh
            </v-icon>
            Refresh Preview
          </v-btn>
        </v-card-text>
      </v-card>

      <!-- File Preview Section -->
      <v-card
        v-if="filePreview"
        class="mb-6"
      >
        <v-card-title class="d-flex align-center">
          <v-icon
            class="me-2"
            color="info"
          >
            mdi-table-eye
          </v-icon>
          File Preview
          <v-spacer />
          <v-chip
            color="info"
            variant="outlined"
          >
            {{ filePreview.total_lines }} total lines, {{ filePreview.data_rows_count }} data rows
          </v-chip>
        </v-card-title>
        <v-card-text>
          <v-alert
            type="info"
            class="mb-4"
          >
            Showing {{ filePreview.showing_rows }} rows from page {{ filePreview.current_page }} of {{ filePreview.total_pages }} 
            ({{ filePreview.data_rows_count }} total data rows after skipping {{ filePreview.skiprows_used }} rows)
          </v-alert>
          
          <!-- Pagination Controls -->
          <div class="d-flex justify-center align-center mb-4">
            <v-btn 
              :disabled="filePreview.current_page <= 1" 
              variant="outlined" 
              class="me-2"
              @click="changePage(filePreview.current_page - 1)"
            >
              <v-icon>mdi-chevron-left</v-icon>
              Previous
            </v-btn>
            
            <v-chip
              color="primary"
              class="mx-3"
            >
              Page {{ filePreview.current_page }} of {{ filePreview.total_pages }}
            </v-chip>
            
            <v-btn 
              :disabled="filePreview.current_page >= filePreview.total_pages" 
              variant="outlined" 
              class="ms-2"
              @click="changePage(filePreview.current_page + 1)"
            >
              Next
              <v-icon>mdi-chevron-right</v-icon>
            </v-btn>
          </div>
          
          <!-- Headers -->
          <div class="mb-3">
            <h4>Detected Headers:</h4>
            <div class="d-flex flex-wrap gap-2">
              <v-chip 
                v-for="header in filePreview.headers" 
                :key="header"
                color="primary"
                variant="outlined"
                size="small"
              >
                {{ header }}
              </v-chip>
            </div>
          </div>
          
          <!-- Sample Data Table -->
          <v-data-table
            :headers="previewTableHeaders"
            :items="filePreview.sample_rows"
            density="compact"
            class="elevation-1"
            :items-per-page="-1"
            hide-default-footer
          />
        </v-card-text>
      </v-card>

      <div v-if="filePreview">
        <h3 class="mb-4">
          File Processing Options
        </h3>
        
        <!-- Remove Commas -->
        <v-card class="mb-4">
          <v-card-title>1. Remove Commas</v-card-title>
          <v-card-text>
            <v-checkbox
              v-model="pdwOptions.removeCommas"
              label="Remove all commas from all fields in the file"
            />
          </v-card-text>
        </v-card>

        <!-- Remove Dollar Signs -->
        <v-card class="mb-4">
          <v-card-title>2. Remove Dollar Signs</v-card-title>
          <v-card-text>
            <v-checkbox
              v-model="pdwOptions.removeDollarSigns"
              label="Remove all dollar signs ($) from all columns"
            />
          </v-card-text>
        </v-card>

        <!-- Uppercase Column -->
        <v-card class="mb-4">
          <v-card-title>3. Uppercase Text</v-card-title>
          <v-card-text>
            <v-checkbox
              v-model="pdwOptions.uppercaseText"
              label="Convert text to uppercase in selected column"
            />
            <v-select
              v-if="pdwOptions.uppercaseText"
              v-model="pdwOptions.uppercaseColumn"
              :items="filePreview?.headers || []"
              label="Select Column to Uppercase"
              outlined
              class="mt-2"
            />
          </v-card-text>
        </v-card>

        <!-- Format UPC Code -->
        <v-card class="mb-4">
          <v-card-title>4. Format UPC Code</v-card-title>
          <v-card-text>
            <v-checkbox
              v-model="pdwOptions.formatUPC"
              label="Format column as 11-digit UPC code"
            />
            <v-select
              v-if="pdwOptions.formatUPC"
              v-model="pdwOptions.upcColumn"
              :items="filePreview?.headers || []"
              label="Select UPC Column"
              outlined
              class="mt-2"
            />
          </v-card-text>
        </v-card>

        <!-- Search and Replace -->
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            5. Search and Replace Operations
            <v-spacer />
            <v-btn 
              color="primary"
              variant="outlined"
              size="small"
              :disabled="pdwOptions.searchReplaceOperations.length >= 10"
              @click="addSearchReplaceOperation"
            >
              <v-icon class="me-1">
                mdi-plus
              </v-icon>
              Add Section
            </v-btn>
          </v-card-title>
          <v-card-text>
            <div
              v-if="pdwOptions.searchReplaceOperations.length === 0"
              class="text-center py-4"
            >
              <p class="text-medium-emphasis">
                No search and replace operations defined
              </p>
              <v-btn
                color="primary"
                @click="addSearchReplaceOperation"
              >
                <v-icon class="me-1">
                  mdi-plus
                </v-icon>
                Add First Operation
              </v-btn>
            </div>
            
            <div 
              v-for="(operation, index) in pdwOptions.searchReplaceOperations" 
              :key="operation.id"
              class="mb-4 pa-3"
              style="border: 1px solid #e0e0e0; border-radius: 4px;"
            >
              <div class="d-flex align-center mb-3">
                <h4 class="flex-grow-1">
                  Operation {{ index + 1 }}
                </h4>
                <v-btn 
                  color="error"
                  variant="text"
                  size="small"
                  :disabled="pdwOptions.searchReplaceOperations.length <= 1"
                  @click="removeSearchReplaceOperation(index)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </div>
              
              <v-select
                v-model="operation.column"
                :items="filePreview?.headers || []"
                label="Select Column"
                outlined
                class="mb-2"
              />
              
              <v-text-field
                v-model="operation.searchText"
                label="Search For"
                outlined
                class="mb-2"
                hint="Text to find in the selected column"
                persistent-hint
              />
              
              <v-text-field
                v-model="operation.replaceText"
                label="Replace With"
                outlined
                hint="Text to replace matches with (leave empty to remove)"
                persistent-hint
              />
            </div>
          </v-card-text>
        </v-card>

        <!-- Preview Processed Data -->
        <v-card
          v-if="hasSelectedOptions"
          class="mb-6"
        >
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="success"
            >
              mdi-eye-check
            </v-icon>
            Preview Processed Data
          </v-card-title>
          <v-card-text>
            <v-btn
              color="success"
              variant="outlined"
              :loading="loadingProcessPreview"
              :disabled="!hasSelectedOptions"
              class="mb-4"
              @click="previewProcessedData"
            >
              <v-icon class="me-1">
                mdi-magnify
              </v-icon>
              Preview Changes
            </v-btn>
            
            <div v-if="processPreview">
              <v-alert
                type="success"
                class="mb-4"
              >
                <div class="font-weight-bold mb-2">
                  ✅ Processing Preview Ready
                </div>
                <div>Changes applied:</div>
                <ul class="mt-2">
                  <li
                    v-for="change in processPreview.processing_summary"
                    :key="change"
                  >
                    {{ change }}
                  </li>
                </ul>
              </v-alert>
              
              <v-data-table
                :headers="processPreviewHeaders"
                :items="processPreview.sample_rows"
                density="compact"
                class="elevation-1"
                :items-per-page="10"
              >
                <template #top>
                  <div class="pa-2 bg-success-lighten-4">
                    <strong>Processed Data Preview</strong> - Showing how your data will look after processing
                  </div>
                </template>
              </v-data-table>
            </div>
          </v-card-text>
        </v-card>

        <!-- Output Options -->
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <v-icon
              class="me-2"
              color="warning"
            >
              mdi-content-save
            </v-icon>
            Save Options
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="pdwOptions.outputFilename"
              label="Output Filename (without extension)"
              placeholder="e.g., processed_products_2025"
              outlined
              class="mb-2"
            />
          </v-card-text>
        </v-card>

        <!-- Final Process Button -->
        <div class="d-flex gap-3 mb-4">
          <v-btn
            v-if="processPreview"
            color="success"
            variant="elevated"
            size="large"
            :disabled="!pdwOptions.outputFilename"
            :loading="loadingFinalProcess"
            @click="downloadProcessedFile"
          >
            <v-icon class="me-2">
              mdi-download
            </v-icon>
            Download Processed CSV
          </v-btn>
          
          <v-btn
            v-else
            :disabled="!hasSelectedOptions"
            color="primary"
            variant="outlined"
            size="large"
            :loading="loadingProcessPreview"
            @click="previewProcessedData"
          >
            <v-icon class="me-2">
              mdi-magnify
            </v-icon>
            Preview Changes First
          </v-btn>
        </div>

        <v-alert
          v-if="error"
          type="error"
          class="mt-4"
        >
          {{ error }}
        </v-alert>
      </div>
    </div>
  </v-container>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import Papa from 'papaparse'
import pythonClient from '@/utils/pythonClient'

// Tool selection
const selectedTool = ref('duplicate-finder')
const toolOptions = [
  { value: 'duplicate-finder', label: 'Find Duplicates by Column' },
  { value: 'value-count', label: 'Value Count by Column' },
  { value: 'comma-remover', label: 'Comma Remover (Coming Soon)' },
  { value: 'pdw-file-prep', label: 'PDW Import File Prep' }
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

// Enhanced PDW processing state
const skipRows = ref(0)
const filePreview = ref(null)
const processPreview = ref(null)
const loadingPreview = ref(false)
const loadingProcessPreview = ref(false)
const loadingFinalProcess = ref(false)

// Pagination state
const currentPage = ref(1)
const rowsPerPage = ref(20)
const totalPages = ref(1)

// PDW File Prep options
const pdwOptions = ref({
  removeCommas: false,
  removeDollarSigns: false,
  uppercaseText: false,
  uppercaseColumn: null,
  formatUPC: false,
  upcColumn: null,
  searchReplaceOperations: [
    { id: 1, column: null, searchText: '', replaceText: '' }
  ],
  outputFilename: ''
})

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
  
  // Reset PDW options when switching tools
  pdwOptions.value = {
    removeCommas: false,
    removeDollarSigns: false,
    uppercaseText: false,
    uppercaseColumn: null,
    formatUPC: false,
    upcColumn: null,
    searchReplaceOperations: [
      { id: 1, column: null, searchText: '', replaceText: '' }
    ],
    outputFilename: ''
  }
  
  // Reset pagination
  currentPage.value = 1
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

// Check if any PDW processing options are selected
const hasSelectedOptions = computed(() => {
  const opts = pdwOptions.value
  const hasSearchReplace = opts.searchReplaceOperations.some(op => 
    op.column && op.searchText
  )
  return opts.removeCommas || opts.removeDollarSigns || opts.uppercaseText || 
         opts.formatUPC || hasSearchReplace
})

// Computed table headers for preview tables
const previewTableHeaders = computed(() => {
  if (!filePreview.value?.headers) return []
  return filePreview.value.headers.map(header => ({
    title: header,
    key: header,
    sortable: false
  }))
})

const processPreviewHeaders = computed(() => {
  if (!processPreview.value?.headers) return []
  return processPreview.value.headers.map(header => ({
    title: header,
    key: header,
    sortable: false
  }))
})

// Update headers for dropdowns when file preview changes
watch(filePreview, (newPreview) => {
  if (newPreview?.headers) {
    headers.value = newPreview.headers
  }
})

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

// Enhanced PDW File Processing Functions
async function onFileUpload() {
  if (uploadedFile.value) {
    currentPage.value = 1 // Reset to first page on new file
    await refreshPreview()
  } else {
    filePreview.value = null
    processPreview.value = null
    headers.value = []
    currentPage.value = 1
  }
}

async function refreshPreview() {
  if (!uploadedFile.value) return
  
  loadingPreview.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('skiprows', skipRows.value.toString())
    formData.append('page', currentPage.value.toString())
    formData.append('rowsPerPage', rowsPerPage.value.toString())
    
    const response = await pythonClient.post('/api/csv/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    filePreview.value = response.data
    processPreview.value = null // Clear processed preview when file changes
    
    console.log('📊 File preview loaded:', filePreview.value)
  } catch (err) {
    console.error('Failed to preview file:', err)
    error.value = `Failed to preview file: ${err.response?.data?.error || err.message}`
  } finally {
    loadingPreview.value = false
  }
}

async function previewProcessedData() {
  if (!uploadedFile.value) return
  
  console.log('🔄 [DEBUG] Starting preview processed data')
  console.log('🔄 [DEBUG] Current pdwOptions:', pdwOptions.value)
  console.log('🔄 [DEBUG] hasSelectedOptions:', hasSelectedOptions.value)
  
  loadingProcessPreview.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('skiprows', skipRows.value.toString())
    
    // Add processing options
    formData.append('removeCommas', pdwOptions.value.removeCommas.toString())
    formData.append('removeDollarSigns', pdwOptions.value.removeDollarSigns.toString())
    formData.append('uppercaseText', pdwOptions.value.uppercaseText.toString())
    formData.append('uppercaseColumn', pdwOptions.value.uppercaseColumn || '')
    formData.append('formatUPC', pdwOptions.value.formatUPC.toString())
    formData.append('upcColumn', pdwOptions.value.upcColumn || '')
    
    // Send multiple search/replace operations as JSON
    const validOperations = pdwOptions.value.searchReplaceOperations.filter(op => 
      op.column && op.searchText
    )
    console.log('🔍 [DEBUG] Valid search/replace operations:', validOperations)
    console.log('🔍 [DEBUG] JSON stringified:', JSON.stringify(validOperations))
    formData.append('searchReplaceOperations', JSON.stringify(validOperations))
    
    console.log('🔄 [DEBUG] Calling /api/csv/process-preview with formData')
    console.log('🔄 [DEBUG] pythonClient base URL:', pythonClient.defaults.baseURL)
    
    const response = await pythonClient.post('/api/csv/process-preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    console.log('🔄 [DEBUG] Response received:', response)
    processPreview.value = response.data
    console.log('🔄 Process preview loaded:', processPreview.value)
  } catch (err) {
    console.error('Failed to preview processing:', err)
    error.value = `Failed to preview processing: ${err.response?.data?.error || err.message}`
  } finally {
    loadingProcessPreview.value = false
  }
}

async function downloadProcessedFile() {
  if (!uploadedFile.value || !pdwOptions.value.outputFilename) return
  
  loadingFinalProcess.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('skiprows', skipRows.value.toString())
    formData.append('outputFilename', pdwOptions.value.outputFilename)
    
    // Add processing options
    formData.append('removeCommas', pdwOptions.value.removeCommas.toString())
    formData.append('removeDollarSigns', pdwOptions.value.removeDollarSigns.toString())
    formData.append('uppercaseText', pdwOptions.value.uppercaseText.toString())
    formData.append('uppercaseColumn', pdwOptions.value.uppercaseColumn || '')
    formData.append('formatUPC', pdwOptions.value.formatUPC.toString())
    formData.append('upcColumn', pdwOptions.value.upcColumn || '')
    
    // Send multiple search/replace operations as JSON
    const validOperations = pdwOptions.value.searchReplaceOperations.filter(op => 
      op.column && op.searchText
    )
    console.log('🔍 [DEBUG] Valid search/replace operations:', validOperations)
    console.log('🔍 [DEBUG] JSON stringified:', JSON.stringify(validOperations))
    formData.append('searchReplaceOperations', JSON.stringify(validOperations))
    
    const response = await pythonClient.post('/api/csv/download-processed', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    // Download the processed CSV
    const csvContent = response.data.csv_content
    const filename = response.data.filename
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    console.log(`✅ Downloaded: ${filename} (${response.data.processed_rows} rows)`)
    
    // Show success message
    error.value = null
    // Could add a success snackbar here if desired
    
  } catch (err) {
    console.error('Failed to download processed file:', err)
    error.value = `Failed to process file: ${err.response?.data?.error || err.message}`
  } finally {
    loadingFinalProcess.value = false
  }
}

// Legacy PDW File Processing Functions (kept for backup)
function processPDWFile() {
  error.value = null
  loading.value = true
  
  try {
    // Create a deep copy of the data to avoid modifying original
    let processedData = allRows.value.map(row => ({ ...row }))
    
    // 1. Remove commas from all fields
    if (pdwOptions.value.removeCommas) {
      processedData = processedData.map(row => {
        const newRow = {}
        Object.keys(row).forEach(key => {
          newRow[key] = String(row[key] || '').replace(/,/g, '')
        })
        return newRow
      })
    }
    
    // 2. Remove dollar signs from all fields
    if (pdwOptions.value.removeDollarSigns) {
      processedData = processedData.map(row => {
        const newRow = {}
        Object.keys(row).forEach(key => {
          newRow[key] = String(row[key] || '').replace(/\$/g, '')
        })
        return newRow
      })
    }
    
    // 3. Uppercase text in selected column
    if (pdwOptions.value.uppercaseText && pdwOptions.value.uppercaseColumn) {
      processedData = processedData.map(row => ({
        ...row,
        [pdwOptions.value.uppercaseColumn]: String(row[pdwOptions.value.uppercaseColumn] || '').toUpperCase()
      }))
    }
    
    // 4. Format UPC code (11 digits)
    if (pdwOptions.value.formatUPC && pdwOptions.value.upcColumn) {
      processedData = processedData.map(row => ({
        ...row,
        [pdwOptions.value.upcColumn]: formatUPCCode(row[pdwOptions.value.upcColumn])
      }))
    }
    
    // 5. Search and replace in selected column
    if (pdwOptions.value.searchReplace && pdwOptions.value.searchColumn && 
        pdwOptions.value.searchText !== undefined) {
      const searchRegex = new RegExp(escapeRegExp(pdwOptions.value.searchText), 'g')
      processedData = processedData.map(row => ({
        ...row,
        [pdwOptions.value.searchColumn]: String(row[pdwOptions.value.searchColumn] || '')
          .replace(searchRegex, pdwOptions.value.replaceText || '')
      }))
    }
    
    // Generate CSV and download
    downloadProcessedFileLegacy(processedData)
    
  } catch (err) {
    error.value = `Processing error: ${err.message}`
  } finally {
    loading.value = false
  }
}

function formatUPCCode(value) {
  if (!value) return ''
  
  // Remove all non-numeric characters
  const numericOnly = String(value).replace(/\D/g, '')
  
  if (numericOnly.length === 0) return ''
  
  // If 12 digits, remove the last character to make it 11
  if (numericOnly.length === 12) {
    return numericOnly.slice(0, 11)
  }
  
  // If less than 11 digits, pad with leading zeros
  if (numericOnly.length < 11) {
    return numericOnly.padStart(11, '0')
  }
  
  // If exactly 11 digits, return as is
  if (numericOnly.length === 11) {
    return numericOnly
  }
  
  // If more than 12 digits, take first 11
  return numericOnly.slice(0, 11)
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function downloadProcessedFileLegacy(processedData) {
  if (!processedData.length) {
    error.value = 'No data to export'
    return
  }
  
  // Use the original headers order
  const csvRows = [headers.value]
  
  // Add data rows
  processedData.forEach(row => {
    const csvRow = headers.value.map(header => {
      const value = row[header] || ''
      // Escape quotes and wrap in quotes if necessary
      return `"${String(value).replace(/"/g, '""')}"`
    })
    csvRows.push(csvRow)
  })
  
  const csvContent = csvRows.map(row => 
    Array.isArray(row) ? row.join(',') : row
  ).join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${pdwOptions.value.outputFilename}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Pagination functions
function changePage(newPage) {
  currentPage.value = newPage
  refreshPreview()
}

// Search/Replace operation management
let nextOperationId = 2 // Start from 2 since we initialize with ID 1

function addSearchReplaceOperation() {
  pdwOptions.value.searchReplaceOperations.push({
    id: nextOperationId++,
    column: null,
    searchText: '',
    replaceText: ''
  })
}

function removeSearchReplaceOperation(index) {
  if (pdwOptions.value.searchReplaceOperations.length > 1) {
    pdwOptions.value.searchReplaceOperations.splice(index, 1)
  }
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
