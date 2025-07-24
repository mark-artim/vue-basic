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
        <div v-if="convHeaders.length" class="mt-4 mb-4">
          <strong>CONV File Headers:</strong>
          <div class="pl-2 pt-1 pb-1">{{ convHeaders.join(', ') }}</div>
        </div>
        <v-file-input
          v-model="edsFile"
          label="EDS File"
          accept=".csv"
          required
        />
        <div v-if="edsHeaders.length" class="mt-4 mb-4">
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
  
      <v-simple-table
        v-if="results.length"
        class="mt-4"
      >
        <thead>
          <tr>
            <th>EDS ECL_PN</th>
            <th>CONV ECL_PN</th>
            <th>Matched ({{ edsPartCol }})</th>
            <th>CONV OH-TOTAL</th>
            <th>EDS OH-TOTAL</th>
            <th>Difference</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in results" :key="row.eds_ecl + row.conv_ecl">
            <td>{{ row.eds_ecl }}</td>
            <td>{{ row.conv_ecl }}</td>
            <td>{{ row.matched_val }}</td>
            <td>{{ row.conv_total }}</td>
            <td>{{ row.eds_total }}</td>
            <td>{{ row.diff }}</td>
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
          const headerLine = lines[8]
          const headers = headerLine?.split(',')?.map(h => h.trim()) || []
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
    }
  },
  watch: {
    convFile(newFile) {
      if (newFile) {
        this.readCsvHeaders(newFile).then(headers => {
          this.convHeaders = headers
          this.updateCompareOptions()
        }).catch(() => { this.convHeaders = [] })
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

</style>