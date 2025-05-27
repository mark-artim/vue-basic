<template>
    <v-container class="pa-4">
      <h2>Inventory Balance Comparison</h2>
      <h3>Utility to identify differences in OH-TOTAL column</h3>
  
      <v-form @submit.prevent="compareFiles">
        <v-file-input
          v-model="convFile"
          label="CONV File"
          accept=".csv"
          required
        />
        <div v-if="convHeaders.length" class="mt-2">
          <strong>CONV File Headers:</strong>
          <div>{{ convHeaders.join(', ') }}</div>
        </div>
        <v-file-input
          v-model="edsFile"
          label="EDS File"
          accept=".csv"
          required
        />
        <div v-if="edsHeaders.length" class="mt-2">
          <strong>EDS File Headers:</strong>
          <div>{{ edsHeaders.join(', ') }}</div>
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
        <h3>Records where OH-TOTAL column values do not match will be shown below.</h3>
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

  import apiClient from '@/utils/axios'
  
  export default {
    name: 'InvBal',
    data() {
      return {
        convFile: null,
        edsFile: null,
        edsPartCol: null,
        partColumns: ['ESC.PN', 'ESE.PN', 'ESW.PN'],
        results: [],
        loading: false,
        error: null,
        convHeaders: [],
        edsHeaders: [],
      }
    },
    methods: {
      readCsvHeaders(file) {
        return new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = (e) => {
            const lines = e.target.result.split(/\r?\n/)
            const headerLine = lines[8] // Row 9 = index 8
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
  
        try {
          const form = new FormData()
          form.append('conv_file', this.convFile)
          form.append('eds_file', this.edsFile)
          form.append('eds_part_col', this.edsPartCol)
  
          const resp = await apiClient.post(
            'http://localhost:5000/api/compare-inv-bal',
            form,
            { headers: { 'Content-Type': 'multipart/form-data' } }
          )
          this.results = resp.data.differences
        } catch (e) {
          this.error = e.response?.data?.message || e.message
        } finally {
          this.loading = false
        }
      }
    },
    watch: {
      convFile(newFile) {
        if (newFile) {
          this.readCsvHeaders(newFile).then(headers => {
            this.convHeaders = headers
          }).catch(() => {
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
          }).catch(() => {
            this.edsHeaders = []
          })
        } else {
          this.edsHeaders = []
        }
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