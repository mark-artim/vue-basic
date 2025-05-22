<template>
    <v-container>
      <h1>Create New Product</h1>
  
      <v-form>
        <v-row>
          <!-- Price Line Autocomplete -->
          <v-col cols="12" sm="6">
            <v-autocomplete
              v-model="selectedPriceLineId"
              v-model:search="priceLineSearch"
              :items="priceLineOptions"
              item-title="description"
              item-value="id"
              label="Price Line"
              required
              :loading="loadingPriceLines"
              no-data-text="No Price Lines found"
              @update:search="onSearchPriceLine"
            />
          </v-col>
  
          <!-- Description -->
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="descriptionUpper"
              label="Description"
              required
            />
          </v-col>
  
          <!-- Catalog Number -->
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="catalogNumber"
              label="Catalog Number"
              required
            />
          </v-col>
  
          <!-- UPC Code -->
          <v-text-field
            v-model="upcCode"
            label="UPC Code"
            :rules="upcCodeRules"
            maxlength="11"
            counter="11"
            />
  
          <!-- REP-COST -->
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="repCost"
              label="REP-COST"
              type="number"
            />
          </v-col>
        </v-row>
      </v-form>
  
      <!-- Preview -->
      <v-card class="mt-4">
        <v-card-title>Preview</v-card-title>
        <v-card-text class="big-bold">
          {{ previewDescription }}
        </v-card-text>
      </v-card>
  
      <!-- Placeholder Create Button -->
      <v-btn class="mt-4" color="primary" @click="createProduct">
        Create Product
      </v-btn>
    </v-container>
  </template>
  
  <script setup>
  import { ref, computed, watch } from 'vue'
  import { debounce } from 'lodash-es'
  import apiClient from '@/utils/axios'
  
  // Reactive state
  const priceLineSearch      = ref('')
  const selectedPriceLineId  = ref(null)
  const priceLineOptions     = ref([])
  const loadingPriceLines    = ref(false)
  const shortCode            = ref('XXX')
  const description          = ref('')
  const catalogNumber        = ref('')
  const upcCode              = ref('')
  const repCost              = ref('')
  
  // Computed preview: SHORT.CODE + "." + description
  const previewDescription = computed(
            () => (shortCode.value && description.value ? `${shortCode.value}.${catalogNumber.value} ${description.value}` : '')
        )

    // define a rules array that you bind via :rules
    const upcCodeRules = [
        // allow blank or exactly 11 chars
        v => v === '' || v.length === 11 || 'UPC must be exactly 11 characters',
        // allow blank or numeric only
        v => v === '' || /^\d{11}$/.test(v) || 'UPC must be numeric'
    ]

    const descriptionUpper = computed({
        get() {
            return description.value
        },
        set(val) {
            description.value = val.toUpperCase()
        }
    })
  
  // Fetch matching price lines
  async function fetchPriceLines(keyword) {
    loadingPriceLines.value = true
    try {
      const { data } = await apiClient.get(`/PriceLines?keyword=${keyword}`)
      priceLineOptions.value = data.results || []
    } catch (err) {
      console.error('Failed to fetch price lines', err)
      priceLineOptions.value = []
    } finally {
      loadingPriceLines.value = false
    }
  }
  
  // Debounce to avoid too-many API calls
  const debouncedFetch = debounce(fetchPriceLines, 300)
  
  // Called on every keystroke in the autocomplete
  function onSearchPriceLine(val) {
    priceLineSearch.value = val
    if (val.length >= 2) {
      debouncedFetch(val)
    } else {
      priceLineOptions.value = []
    }
  }
  
  
  // When user picks a price line, fetch its SHORT.CODE
    watch(selectedPriceLineId, async (id) => {
        if (!id) {
        console.log('No Price Line selected, clearing shortCode')
        shortCode.value = ''
        return
    }

    console.log(`→ Fetching UD.PRICELINE with id=${id}`)
    try {
        const { data } = await apiClient.get(`/UserDefined/UD.PRICELINE?id=${id}`)
        console.log('← Received UD.PRICELINE response:', data)

        shortCode.value = data['SHORT.CODE'] || ''
        console.log('✱ shortCode set to:', shortCode.value)
    } catch (err) {
        console.error(`✖ Error fetching UD.PRICELINE for id=${id}:`, err)
        shortCode.value = ''
    }
    })

  
  // Placeholder create handler
  function createProduct() {
    console.log('Creating product with:', {
      priceLineId:   selectedPriceLineId.value,
      shortCode:     shortCode.value,
      catalogNumber: catalogNumber.value,
      description:   description.value,
      upcCode:       upcCode.value,
      repCost:       repCost.value,
    })
  }
  </script>
  
  <style scoped>
  h1 {
    margin-bottom: 1rem;
  }
  .big-bold {
    font-size: 1.5rem;
    font-weight: bold;
    }
  </style>
  