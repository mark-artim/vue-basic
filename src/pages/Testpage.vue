<template>
    <v-data-table
      :headers="headers"
      :items="items"
      item-value="object_id"
      v-model="selected"
      return-object
      show-select
      single-select
      class="elevation-1"
    />
  </template>
  
  <script setup>
  import { ref, computed, watch } from 'vue'
  console.log('Testpage3.vue loaded!')
  
  const items = ref([
    {
      object_id: '1',
      serviceLevelName: 'Priority Mail',
      estimatedDays: 2,
      durationTerms: 'Delivery in 2–3 days',
      amount: 6.85
    }
  ])
  
  const headers = [
    { text: 'Service Level', value: 'serviceLevelName' },
    { text: 'Est. Days', value: 'estimatedDays' },
    { text: 'Duration Terms', value: 'durationTerms' },
    { text: 'Amount', value: 'amount' }
  ]
  
  // const selected = ref([null])
  const selected = defineModel('selected')

  const selectedRate = computed(() => selected.value[0] ?? null)

  watch(selected, (newVal) => {
  console.log('✅ Selected rate changed:', newVal)
})
  </script>
  