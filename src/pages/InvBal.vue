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
        <div v-if="Array.isArray(convHeaders) && convHeaders.length" class="mt-4 mb-4">
          <strong>CONV File Headers:</strong>
          <div class="pl-2 pt-1 pb-1">{{ convHeaders.join(', ') }}</div>
        </div>
        <v-file-input
          v-model="edsFile"
          label="EDS File"
          accept=".csv"
          required
        />
        <div v-if="Array.isArray(edsHeaders) && edsHeaders.length" class="mt-4 mb-4">
          <strong>EDS File Headers:</strong>
          <div class="pl-2 pt-1 pb-1">{{ edsHeaders.join(', ') }}</div>
        </div>
        <v-select
          v-model="edsPartCol"
          :items="partColumns"
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
        <v-alert v-if="matchedCount > 0" type="info" class="mt-4">
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
      <v-alert
        v-if="error"
        type="warning"
        class="mb-4"
        dense
        border="start"
        variant="tonal"
      >
        {{ error }}
      </v-alert>
  
     <v-simple-table
        v-if="Array.isArray(results) && results.length"
        class="styled-results-table mt-4"
      >
        <thead>
          <tr>
            <th>EDS ECL_PN</th>
            <th>CONV ECL_PN</th>
            <th>Matched ({{ edsPartCol }})</th>
            <th class="numeric">{{ selectedColumn }} (CONV)</th>
            <th class="numeric">{{ selectedColumn }} (EDS)</th>
            <th class="numeric">Difference</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in results" :key="row.eds_ecl + row.conv_ecl">
            <td>{{ row.eds_ecl }}</td>
            <td>{{ row.conv_ecl }}</td>
            <td>{{ row.matched_val }}</td>
            <td class="numeric">{{ format(row.conv_val) }}</td>
            <td class="numeric">{{ format(row.eds_val) }}</td>
            <td class="numeric">{{ format(row.diff) }}</td>
          </tr>
        </tbody>
      </v-simple-table>

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
      partColumns: ['ESC.PN', 'ESE.PN', 'ESW.PN'],
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

        const resp = await pythonClient.post('/api/compare-inv-bal', form, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        this.results = resp.data.differences
        this.compareOptions = resp.data.shared_columns || []
        this.matchedCount = resp.data.matched_row_count || 0
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
      const shared = this.convHeaders.filter(h => this.edsHeaders.includes(h))
      this.compareOptions = shared
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
    }
  },
  computed: {
    sharedHeaders() {
      return this.convHeaders.filter(h => this.edsHeaders.includes(h))
    },
    variancePercent() {
    const total = this.matchedCount + this.unmatchedCount
    return total === 0 ? 0 : ((this.unmatchedCount / total) * 100).toFixed(2)
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
.styled-results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background-color: #121212;
  color: #fff;
}

.styled-results-table th,
.styled-results-table td {
  padding: 10px 14px;
  border-bottom: 1px solid #444;
  white-space: nowrap;
}

.styled-results-table th {
  background-color: #1e1e1e;
  font-weight: 600;
  border-bottom: 2px solid #666;
  text-align: left;
}

.styled-results-table td.numeric,
.styled-results-table th.numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}


</style>