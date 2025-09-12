<template>
  <v-container class="pa-4">
    <h2>File Comparison Tool</h2>
    <h3>Utility to identify differences in specified column</h3>
  
    <v-form @submit.prevent="compareFiles">
      <v-file-input
        v-model="convFile"
        label="CONV File"
        accept=".csv"
        required
      />
      <div
        v-if="Array.isArray(convHeaders) && convHeaders.length"
        class="mt-4 mb-4"
      >
        <strong>CONV File Headers:</strong>
        <div class="pl-2 pt-1 pb-1">
          {{ convHeaders.join(', ') }}
        </div>
      </div>
      <v-file-input
        v-model="edsFile"
        label="EDS File"
        accept=".csv"
        required
      />
      <div
        v-if="Array.isArray(edsHeaders) && edsHeaders.length"
        class="mt-4 mb-4"
      >
        <strong>EDS File Headers:</strong>
        <div class="pl-2 pt-1 pb-1">
          {{ edsHeaders.join(', ') }}
        </div>
      </div>
      <v-select
        v-model="edsPartCol"
        :items="partColumns"
        item-title="text"
        item-value="value"
        label="Eds Part Number Column"
        required
      />
      <v-btn
        color="primary"
        type="submit"
        :loading="loading"
        class="mt-4"
        :disabled="!convFile || !edsFile || !edsPartCol"
      >
        Compare
      </v-btn>
      <v-select
        v-model="compareCol"
        :items="compareOptions"
        label="Column to Compare (e.g. OH-TOTAL)"
        required
        class="mt-2"
      />
      <v-select
        :key="`display-${compareOptions.length}`"
        v-model="displayCol"
        :items="availableDisplayColumns"
        label="Additional Column to Display"
        class="mt-2"
        clearable
      />
      <v-alert
        v-if="matchedCount > 0 || unmatchedCount > 0"
        type="info"
        class="mt-4"
      >
        {{ matchedCount + unmatchedCount }} rows compared.
        {{ matchedCount }} matched,
        {{ unmatchedCount }} had variance.
        ({{ variancePercent }}% with variance)
        
        
        <div v-if="allItems.length > 0" class="mt-2">
          <v-btn
            color="white"
            variant="elevated"
            size="small"
            style="color: #000 !important; background-color: #fff !important; border: 1px solid #ccc !important;"
            @click="showAllItems = !showAllItems"
          >
            {{ showAllItems ? 'Hide Items' : 'Show Items' }} ({{ allItems.length }} items)
          </v-btn>
        </div>
      </v-alert>
    </v-form>
  
    <v-alert
      v-if="error"
      type="error"
      class="mt-4"
    >
      {{ error }}
    </v-alert>
  
    <div
      v-if="Array.isArray(results) && results.length"
      class="results-section"
    >
      <v-btn
        color="primary"
        class="mb-4"
        :disabled="!results.length"
        @click="downloadCSV"
      >
        Download CSV
      </v-btn>
        
      <table class="styled-results-table">
        <thead>
          <tr>
            <th>EDS ECL_PN</th>
            <th>CONV ECL_PN</th>
            <th class="numeric">
              {{ compareCol }} (CONV)
            </th>
            <th class="numeric">
              {{ compareCol }} (EDS)
            </th>
            <th
              v-if="displayCol && displayCol !== compareCol && results.length"
              class="numeric"
            >
              {{ displayCol }} (CONV)
            </th>
            <th
              v-if="displayCol && displayCol !== compareCol && results.length"
              class="numeric"
            >
              {{ displayCol }} (EDS)
            </th>
            <th class="numeric diff-header">
              Difference
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in results"
            :key="row.eds_ecl + row.conv_ecl"
          >
            <td>{{ row.eds_ecl }}</td>
            <td>{{ row.conv_ecl }}</td>
            <td class="numeric">
              {{ format(row.conv_val) }}
            </td>
            <td class="numeric">
              {{ format(row.eds_val) }}
            </td>
            <td
              v-if="displayCol && displayCol !== compareCol && results.length"
              class="numeric"
            >
              {{ safeGetDisplayValue(row, 'conv') }}
            </td>
            <td
              v-if="displayCol && displayCol !== compareCol && results.length"
              class="numeric"
            >
              {{ safeGetDisplayValue(row, 'eds') }}
            </td>
            <td
              class="numeric"
              :class="getDiffClass(row.diff)"
            >
              {{ format(row.diff) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- All Items Table (Paginated) -->
    <div
      v-if="showAllItems && allItems.length"
      class="all-items-section mt-6"
    >
      <h3 class="mb-4">All Compared Items ({{ allItems.length }} total)</h3>
      <v-data-table
        :headers="allItemsHeaders"
        :items="allItems"
        :items-per-page="25"
        class="elevation-1"
        item-key="id"
      >
        <template #item.conv_val="{ item }">
          <span class="numeric">{{ format(item.conv_val) }}</span>
        </template>
        <template #item.eds_val="{ item }">
          <span class="numeric">{{ format(item.eds_val) }}</span>
        </template>
        <template #item.diff="{ item }">
          <span 
            class="numeric" 
            :class="getDiffClass(item.diff)"
          >
            {{ format(item.diff) }}
          </span>
        </template>
        <template #item.conv_display="{ item }">
          <span class="numeric">{{ safeGetDisplayValue(item, 'conv') }}</span>
        </template>
        <template #item.eds_display="{ item }">
          <span class="numeric">{{ safeGetDisplayValue(item, 'eds') }}</span>
        </template>
      </v-data-table>
    </div>
  </v-container>
</template>
  
  <script>
import pythonClient from '@/utils/pythonClient'

export default {
  name: 'InvBal',
  data() {
    return {
      convFile: null,
      edsFile: null,
      edsPartCol: null,
      compareCol: null,
      displayCol: null,
      partColumns: [
        { text: 'ESC.PN - Eds Central (NASH) & Coastal', value: 'ESC.PN' },
        { text: 'ESE.PN - Eds East (CHAT)', value: 'ESE.PN' },
        { text: 'ESW.PN - Eds West (LITT)', value: 'ESW.PN' }
      ],
      compareOptions: [],
      convHeaders: [],
      edsHeaders: [],
      results: [],
      matchedCount: 0,
      loading: false,
      error: null,
      unmatchedCount: 0,
      showAllItems: false,
      allItems: [],
    }
  },
  computed: {
    sharedHeaders() {
      return this.convHeaders.filter(h => this.edsHeaders.includes(h))
    },
    availableDisplayColumns() {
      try {
        if (!Array.isArray(this.compareOptions)) {
          console.warn('[InvBal] compareOptions is not an array:', this.compareOptions)
          return []
        }
        return this.compareOptions.filter(h => h !== this.compareCol)
      } catch (error) {
        console.error('[InvBal] Error in availableDisplayColumns:', error)
        return []
      }
    },
    variancePercent() {
      const total = this.matchedCount + this.unmatchedCount
      return total === 0 ? 0 : ((this.unmatchedCount / total) * 100).toFixed(2)
    },
    allItemsHeaders() {
      const headers = [
        { title: 'EDS ECL_PN', value: 'eds_ecl', sortable: true },
        { title: 'CONV ECL_PN', value: 'conv_ecl', sortable: true },
        { title: `${this.compareCol} (CONV)`, value: 'conv_val', sortable: true },
        { title: `${this.compareCol} (EDS)`, value: 'eds_val', sortable: true }
      ]
      
      // Add display columns if different from compare column
      if (this.displayCol && this.displayCol !== this.compareCol) {
        headers.push(
          { title: `${this.displayCol} (CONV)`, value: 'conv_display', sortable: true },
          { title: `${this.displayCol} (EDS)`, value: 'eds_display', sortable: true }
        )
      }
      
      headers.push({ title: 'Difference', value: 'diff', sortable: true })
      return headers
    }
  },
  watch: {
    convFile(newFile) {
      if (newFile) {
        this.readCsvHeaders(newFile)
          .then(headers => {
            this.convHeaders = Array.isArray(headers) ? headers : []
                this.updateCompareOptions()
          })
          .catch(() => {
            this.convHeaders = []
          })
      } else {
        this.convHeaders = []
      }
    },
    edsFile(newFile) {
      if (newFile) {
        this.readCsvHeaders(newFile).then(headers => {
          this.edsHeaders = headers
          this.updateCompareOptions()
        }).catch(() => { this.edsHeaders = [] })
      } else {
        this.edsHeaders = []
      }
    },
    compareCol() {
      this.results = []
      this.matchedCount = 0
      this.unmatchedCount = 0
      this.error = null
    },
    displayCol() {
      // No need to clear results when display column changes since it's just visual
    }
  },
  methods: {
    readCsvHeaders(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          const lines = e.target.result.split(/\r?\n/)
          const headerLine = lines[8] || ''
          const headers = headerLine
            .split(',')
            .map(h => h.trim().replace(/^"(.*)"$/, '$1'))
          resolve(headers)
        }
        reader.onerror = reject
        reader.readAsText(file)
      })
    },
    async compareFiles() {
      this.loading = true
      this.error = null
      this.results = []
      this.matchedCount = 0

      try {
        const form = new FormData()
        form.append('conv_file', this.convFile)
        form.append('eds_file', this.edsFile)
        form.append('eds_part_col', this.edsPartCol)
        form.append('value_col', this.compareCol)
        if (this.displayCol) {
          form.append('display_col', this.displayCol)
        }

        const resp = await pythonClient.post('/api/compare-inv-bal', form, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // Handle string responses (convert NaN to null and parse)
        if (typeof resp.data === 'string') {
          try {
            const cleanedData = resp.data.replace(/:\s*NaN/g, ':null')
            resp.data = JSON.parse(cleanedData)
          } catch (parseError) {
            this.error = 'Backend error: Invalid JSON response'
            return
          }
        }
        
        this.results = resp.data.differences
        this.allItems = resp.data.all_items || []
        this.matchedCount = resp.data.matched_row_count || 0
        
        // Debug logging
        console.log('Backend response:', resp.data)
        console.log('Results length:', this.results.length)
        console.log('All items length:', this.allItems.length)
        console.log('Matched count:', this.matchedCount)
        // Update shared columns if provided by backend, but don't overwrite existing options
        if (resp.data.shared_columns && resp.data.shared_columns.length > 0) {
          this.compareOptions = resp.data.shared_columns
        }
        this.unmatchedCount = resp.data.unmatched_count || this.results.length
        if (this.results.length > 1000) {
          this.error = `Warning: ${this.results.length} unmatched items. Only showing first 1000.`
          this.results = this.results.slice(0, 1000)
        }
        this.updateCompareOptions()
      } catch (e) {
        this.error = e.response?.data?.message || e.message
      } finally {
        this.loading = false
      }
    },
    updateCompareOptions() {
      // Only calculate shared columns if both files have headers
      if (this.convHeaders.length === 0 || this.edsHeaders.length === 0) {
        return
      }
      
      const shared = this.convHeaders.filter(h => this.edsHeaders.includes(h))
      this.compareOptions = [...shared] // Force array recreation for reactivity
      if (!shared.includes(this.compareCol)) {
        this.compareCol = shared.includes('OH-TOTAL') ? 'OH-TOTAL' : shared[0] || null
      }
    },
    format(val) {
      if (val === null || val === undefined || val === '') return '-'

      try {
        // Add safety check for val before processing
        if (typeof val === 'object' && val !== null) {
          console.warn('[InvBal] Unexpected object value in format():', val)
          return String(val) || '-'
        }

        // Extra safety for array values or other complex types
        if (Array.isArray(val)) {
          console.warn('[InvBal] Array value in format():', val)
          return val.join(',') || '-'
        }

        // Check if val has a length property but is undefined
        if (val && typeof val.length !== 'undefined' && val.length === undefined) {
          console.error('[InvBal] Value has undefined length property:', val, typeof val)
          return String(val) || '-'
        }

        const strVal = String(val).trim()
        
        // Early return for empty strings after trimming
        if (strVal === '') return '-'

        // Reject clearly non-numeric values like "BUY_LINE"
        const num = parseFloat(strVal)
        let isNumeric = false
        try {
          isNumeric = !isNaN(num) && /^-?\d+(\.\d+)?$/.test(strVal)
        } catch (regexError) {
          console.error('[InvBal] Regex test error:', regexError, 'for string:', strVal)
          isNumeric = !isNaN(num)
        }

        if (!isNumeric) return strVal

        return strVal.includes('.') ? num.toFixed(2) : Math.round(num).toString()
      } catch (err) {
        console.error('[InvBal] Format error:', err, 'for value:', val, 'type:', typeof val)
        return String(val) || '-'
      }
    },
    getDiffClass(diff) {
      if (diff === null || diff === undefined || diff === '') return ''
      const num = parseFloat(diff)
      if (isNaN(num)) return ''
      if (num === 0) return 'diff-zero'
      if (Math.abs(num) < 1) return 'diff-small'
      return 'diff-large'
    },
    safeGetDisplayValue(row, fileType) {
      try {
        if (!row) return '-'
        if (!this.displayCol) return '-'
        
        // Simple direct access without calling format function for now
        const value = fileType === 'conv' ? row.conv_display : row.eds_display
        if (value === null || value === undefined || value === '') return '-'
        return String(value)
      } catch (error) {
        console.error('[InvBal] Error in safeGetDisplayValue:', error)
        return '-'
      }
    },
    getDisplayValue(row, fileType) {
      if (!this.displayCol) return '-'
      const value = fileType === 'conv' ? row.conv_display : row.eds_display
      return this.format(value)
    },
    downloadCSV() {
      if (!this.results.length) return
      
      const headers = [
        'EDS ECL_PN',
        'CONV ECL_PN'
      ]
      
      if (this.displayCol) {
        headers.push(`${this.displayCol} (CONV)`)
        headers.push(`${this.displayCol} (EDS)`)
      }
      
      headers.push(
        `${this.compareCol} (CONV)`,
        `${this.compareCol} (EDS)`,
        'Difference'
      )
      
      const rows = this.results.map(row => {
        const rowData = [
          row.eds_ecl || '',
          row.conv_ecl || ''
        ]
        
        if (this.displayCol) {
          rowData.push(
            this.getDisplayValue(row, 'conv'),
            this.getDisplayValue(row, 'eds')
          )
        }
        
        rowData.push(
          this.format(row.conv_val),
          this.format(row.eds_val),
          this.format(row.diff)
        )
        
        return rowData
      })
      
      const csvContent = [headers, ...rows]
        .map(row => row.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))
        .join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `inventory_balance_comparison_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  },
}
</script>


<style scoped>
h2 {
    margin: 2rem 0;
}
h3 {
    margin: 2rem 0;
    color: aqua;
}
.results-section {
  margin-top: 20px;
}

.styled-results-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
  font-size: 14px;
}

.styled-results-table th,
.styled-results-table td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: center;
}

.styled-results-table th {
  background-color: #007bff;
  color: white;
  font-weight: bold;
  padding: 12px;
}

.styled-results-table td {
  background-color: white;
  color: black;
}

.styled-results-table td.numeric,
.styled-results-table th.numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.diff-zero {
  color: green;
  font-weight: bold;
}

.diff-small {
  color: orange;
  font-weight: bold;
}

.diff-large {
  color: red;
  font-weight: bold;
}

.diff-header {
  background-color: #0056b3;
}


</style>