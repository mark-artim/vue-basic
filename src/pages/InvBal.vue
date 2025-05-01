<template>
    <v-container class="pa-4">
        <h2>Inventory Balance Comparison</h2>

        <v-form @submit.prevent="compareFiles">
            <v-text-field v-model="convFilename" label="CONV Filename" required />
            <v-text-field v-model="edsFilename" label="Eds Filename" required />
            <v-select v-model="edsPartCol" :items="partColumns" label="Eds Part Number Column" required />
            <v-btn color="primary" type="submit" :loading="loading" class="mt-4">
                Compare
            </v-btn>
        </v-form>

        <v-alert v-if="error" type="error" class="mt-4">
            {{ error }}
        </v-alert>

        <v-simple-table v-if="results.length" class="mt-4">
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
import axios from 'axios'

export default {
    name: 'InvBal',
    data() {
        return {
            convFilename: '',
            edsFilename: '',
            edsPartCol: null,
            partColumns: ['ESC.PN', 'ESE.PN', 'ESW.PN'],
            results: [],
            loading: false,
            error: null,
        }
    },
    methods: {
        async compareFiles() {
            this.loading = true
            this.error = null
            this.results = []

            try {
                const resp = await axios.post(
                    'http://localhost:5000/api/compare-inv-bal',
                    {
                        conv_filename: this.convFilename,
                        eds_filename: this.edsFilename,
                        eds_part_col: this.edsPartCol
                    }
                )
                this.results = resp.data.differences
            } catch (e) {
                this.error = e.response?.data?.message || e.message
            } finally {
                this.loading = false
            }
        }
    }
}
</script>

<style scoped>
h2 {
    margin-bottom: 1rem;
}
</style>