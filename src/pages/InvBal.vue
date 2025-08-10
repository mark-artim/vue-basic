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
        v-model="displayCol"
        :items="availableDisplayColumns"
        label="Additional Column to Display"
        class="mt-2"
        clearable
        :key="`display-${compareOptions.length}`"
      />
      <v-alert
        v-if="matchedCount > 0"
        type="info"
        class="mt-4"
      >
        {{ matchedCount + unmatchedCount }} rows compared.
        {{ matchedCount }} matched,
        {{ unmatchedCount }} had variance.
        ({{ variancePercent }}% with variance)
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
            <th
              v-if="displayCol"
              class="numeric"
            >
              {{ displayCol }} (CONV)
            </th>
            <th
              v-if="displayCol"
              class="numeric"
            >
              {{ displayCol }} (EDS)
            </th>
            <th class="numeric">
              {{ compareCol }} (CONV)
            </th>
            <th class="numeric">
              {{ compareCol }} (EDS)
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
            <td
              v-if="displayCol"
              class="numeric"
            >
              {{ getDisplayValue(row, 'conv') }}
            </td>
            <td
              v-if="displayCol"
              class="numeric"
            >
              {{ getDisplayValue(row, 'eds') }}
            </td>
            <td class="numeric">
              {{ format(row.conv_val) }}
            </td>
            <td class="numeric">
              {{ format(row.eds_val) }}
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
    }
  },
  computed: {
    sharedHeaders() {
      return this.convHeaders.filter(h => this.edsHeaders.includes(h))
    },
    availableDisplayColumns() {
      return this.compareOptions.filter(h => h !== this.compareCol)
    },
    variancePercent() {
      const total = this.matchedCount + this.unmatchedCount
      return total === 0 ? 0 : ((this.unmatchedCount / total) * 100).toFixed(2)
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
        
        
        this.results = resp.data.differences
        this.matchedCount = resp.data.matched_row_count || 0
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
        const strVal = String(val).trim()

        // Reject clearly non-numeric values like "BUY_LINE"
        const num = parseFloat(strVal)
        const isNumeric = !isNaN(num) && /^-?\d+(\.\d+)?$/.test(strVal)

        if (!isNumeric) return strVal

        return strVal.includes('.') ? num.toFixed(2) : Math.round(num).toString()
      } catch (err) {
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