<template>
  <v-container class="pa-4">
    <h1>Price Line Access</h1>

    <v-autocomplete
      v-model="selectedPriceLineId"
      v-model:search="priceLineSearch"
      :items="priceLineOptions"
      item-title="description"
      item-value="id"
      label="Price Line"
      :loading="loadingPriceLines"
      no-data-text="No Price Lines found"
      @input="onSearchPriceLine"
      @update:model-value="selectedPriceLineId"
    />
    <!-- @update:search="onSearchPriceLine" -->
    <div
      v-if="selectedPriceLine"
      class="mt-4"
    >
      <p><strong>ID:</strong> {{ selectedPriceLine.id }}</p>
      <p><strong>Description:</strong> {{ selectedPriceLine.description }}</p>

      <h3 class="mt-6">
        Limit Access by Company
      </h3>
      <v-checkbox
        v-for="company in companies"
        :key="company.name"
        v-model="companyChecks[company.name]"
        :label="company.name"
        hide-details
        @update:model-value="val => toggleCompany(company, val)"
      >
        <template #append>
          <v-icon v-if="companyChecks[company.name]">
            mdi-check
          </v-icon>
        </template>
      </v-checkbox>

      <v-btn
        class="mt-4"
        color="primary"
        @click="save"
      >
        Save
      </v-btn>
    </div>
  </v-container>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useDebouncedSearch } from '@/composables/useDebouncedSearch'
import apiClient from '@/utils/axios'
import { searchPriceLines } from '@/api/priceLines'
import { getPriceLine } from '@/api/priceLines'
import { getTerritory } from '@/api/territories'

const selectedPriceLineId = ref(null)
const selectedPriceLine = ref(null)
const branchAccessList = ref([])

const fetchPriceLines = async (query) => {
      const result = await searchPriceLines(query);
      const searchResults = result.results || result;
      console.log('[DEBUG PRICE LINE SEARCH] Price Lines fetched:', searchResults);
      // return allCustomers.filter(v => v.isPayTo);
      return searchResults
    };

const {
  searchTerm: priceLineSearch,
  results: priceLineOptions,
  isLoading: loadingPriceLines,
  onSearch: onSearchPriceLine,
  clear: clearPriceLines
} = useDebouncedSearch(fetchPriceLines,1000)
  // const { data } = await apiClient.get(`/PriceLines?keyword=${keyword}`)
  // return data.results || []
// }, 300)

const companies = [
  { name: 'Benoist', territoryId: 'TCBBS' },
  { name: 'Coastal', territoryId: 'TCCSC' },
  { name: "Ed's Central", territoryId: 'TCESC' },
  { name: "Ed's East", territoryId: 'TCESE' },
  { name: "Ed's West", territoryId: 'TCESW' },
  { name: 'NuComfort', territoryId: 'TCNCS' },
  { name: 'Wittichen', territoryId: 'TCWSC' }
]

const companyChecks = ref({})
companies.forEach(c => { companyChecks.value[c.name] = false })

const territoryCache = {}

async function getTerritoryBranches (id) {
  if (territoryCache[id]) return territoryCache[id]
  const data = await getTerritory(id)
  const branches = data.branches || []
  territoryCache[id] = branches
  return branches
}

async function updateCompanyChecks () {
  const promises = companies.map(async company => {
    try {
      const branches = await getTerritoryBranches(company.territoryId)
      companyChecks.value[company.name] = branches.every(b => branchAccessList.value.includes(b))
    } catch (err) {
      console.error('Failed to load territory', company.territoryId, err)
      companyChecks.value[company.name] = false
    }
  })
}

watch(selectedPriceLineId, async id => {
  if (!id) {
    selectedPriceLine.value = null
    branchAccessList.value = []
    companies.forEach(c => { companyChecks.value[c.name] = false })
    return
  }
  // const { data } = await apiClient.get(`/PriceLines/${id}`)
  console.log('[DEBUG PRICE LINE SELECTED] Fetching Price Line:', id)
  const data = await getPriceLine(id)
  console.log('[DEBUG PRICE LINE SELECTED] Price Line data:', data)
  selectedPriceLine.value = data
  branchAccessList.value = data.branchAccessList || []
  console.log('[DEBUG PRICE LINE SELECTED] Branch access list:', branchAccessList)
  await updateCompanyChecks()
})

async function toggleCompany (company, checked) {
  const branches = await getTerritoryBranches(company.territoryId)
  if (checked) {
    for (const b of branches) {
      if (!branchAccessList.value.includes(b)) branchAccessList.value.push(b)
    }
  } else {
    branchAccessList.value = branchAccessList.value.filter(b => !branches.includes(b))
  }
  companyChecks.value[company.name] = checked
}

async function save () {
  if (!selectedPriceLine.value) return
  try {
    await apiClient.put(`/PriceLines/${selectedPriceLine.value.id}`, {
      ...selectedPriceLine.value,
      branchAccessList: branchAccessList.value
    })
    alert('Price line saved successfully.')
  } catch (error) {
    console.error('Failed to save price line:', error)
    alert('Failed to save price line. Please try again.')
  }
}
</script>
