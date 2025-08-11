<template>
  <v-container>
    <h2>Applying Surcharge...</h2>
    <v-alert
      v-if="successMessage"
      type="success"
    >
      {{ successMessage }}
      <div
        v-if="shipToName || poNumber"
        class="mt-2"
      >
        <strong>Ship To:</strong> {{ shipToName }}<br>
        <strong>PO Number:</strong> {{ poNumber }}
      </div>
    </v-alert>
    <v-alert
      v-if="errorMessage"
      type="error"
    >
      {{ errorMessage }}
    </v-alert>
  </v-container>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/utils/axios'

const route = useRoute()
const successMessage = ref('')
const errorMessage = ref('')
const shipToName = ref('')
const poNumber = ref('')


onMounted(async () => {
  const order = route.query.order
  if (!order) {
    errorMessage.value = 'Missing order number in URL'
    return
  }

  try {
    console.log('[SurchargeCalc] about to POST /erp/surcharge')
    console.log('[SurchargeCalc] current JWT:', localStorage.getItem('jwt'))
    const res = await apiClient.post('/erp/surcharge', null, {
      params: {
        order: route.query.order,
        companyCode: route.query.companyCode,
        port: route.query.port,
      }
    })
    // NEW LOGIC
    // const res = await apiClient.post('api/erp-proxy', {
    //   method: 'GET',
    //   url: `/SurchargeCalc/${order}`,
    // } )


    successMessage.value = `Surcharge of $${res.data.amount.toFixed(2)} applied to ${order}.`
    // Set display values
    shipToName.value = res.data.shipToName
    poNumber.value = res.data.poNumber
  } catch (err) {
    errorMessage.value =
    err.response?.data?.message || err.message || 'Failed to apply surcharge'
  }
})
</script>
