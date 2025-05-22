<template>
    <v-container>
        <h1>Create New Product</h1>
        <!-- VERSION BEFORE REFACTORING -->
        <v-form>
            <v-row>
                <v-col cols="12" sm="6">
                    <v-autocomplete
                    v-model="priceLineInput"
                    :items="priceLineOptions"
                    item-title="description"
                    item-value="id" label="Price Line"
                    required
                    :loading="loadingPriceLines"
                    no-data-text="No Price Lines found"
                    @input="handleInput"
                    @update:model-value="onSearchPriceLine">
                        <template #item="{ item }">
                            <v-list-item-content>
                                <v-list-item-title>{{ item.description }}</v-list-item-title>
                            </v-list-item-content>
                        </template>
                    </v-autocomplete>
                </v-col>
                <v-col cols="12" sm="6">
                    <v-text-field v-model="description" label="Description" required />
                </v-col>
                <v-col cols="12" sm="6">
                    <v-text-field v-model="catalogNumber" label="Catalog Number" required />
                </v-col>
                <v-col cols="12" sm="6">
                    <v-text-field v-model="upcCode" label="UPC Code" />
                </v-col>
                <v-col cols="12" sm="6">
                    <v-text-field v-model="repCost" label="REP-COST" type="number" />
                </v-col>
            </v-row>
        </v-form>

        <v-card class="mt-4">
            <v-card-title>Preview</v-card-title>
            <v-card-text>{{ previewDescription }}</v-card-text>
        </v-card>

        <v-btn class="mt-4" color="primary" @click="createProduct">
            Create Product
        </v-btn>
    </v-container>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { debounce } from 'lodash-es' // Import lodash debounce
import apiClient from '@/utils/axios'

export default {
    name: 'CreateProduct',
    setup() {
        const priceLineInput = ref('')
        const priceLineOptions = ref([])
        const loadingPriceLines = ref(false)
        const selectedPriceLineId = ref(null)
        const shortCode = ref('XXX')
        const description = ref('')
        const catalogNumber = ref('')
        const upcCode = ref('')
        const repCost = ref('')

        const previewDescription = computed(
            () => (shortCode.value && description.value ? `${shortCode.value}.${catalogNumber.value} ${description.value}` : '')
        )

        const debouncedFetchPriceLines = debounce((input) => {
            console.log('Debounced Function Called with input:', input); // Debug log
            fetchPriceLines(input);
        }, 1000)

        const fetchPriceLines = async (keyword) => {
            loadingPriceLines.value = true
            console.log('Fetching price lines with keyword:', keyword)
            try {
                const { data } = await apiClient.get(`/PriceLines?keyword=${keyword}`)
                priceLineOptions.value = data.results || []
            } catch (err) {
                console.error('Failed to fetch price lines', err)
            } finally {
                loadingPriceLines.value = false
            }
        }

        // Handle input changes
        const handleInput = (inputEvent) => {
            const input = inputEvent.target.value; // Extract the string value from InputEvent
            console.log('Input event triggered with value:', input); // Debug log
            keyword.value = input; // Update the reactive keyword
            debouncedFetchPriceLines(input); // Pass the string value directly
        }


        const onSearchPriceLine = (val) => {
            priceLineInput.value = val
            if (val && val.length >= 2) {
                fetchPriceLines(val)
            } else {
                priceLineOptions.value = []
            }
        }

        watch(priceLineInput, (val) => {
            selectedPriceLineId.value = null
            shortCode.value = ''
        })

        watch(selectedPriceLineId, async (id) => {
            if (id) {
                try {
                    const { data } = await apiClient.get(
                        `/UserDefined/UD.PRICELINE?id=${id}`
                    )
                    shortCode.value = data.SHORT?.CODE || ''
                } catch (err) {
                    console.error('Failed to fetch UD priceline', err)
                }
            }
        })

        const createProduct = () => {
            console.log('Creating product with', {
                priceLineId: selectedPriceLineId.value,
                shortCode: shortCode.value,
                description: description.value,
                catalogNumber: catalogNumber.value,
                upcCode: upcCode.value,
                repCost: repCost.value,
            })
        }

        return {
            priceLineInput,
            priceLineOptions,
            loadingPriceLines,
            selectedPriceLineId,
            shortCode,
            description,
            catalogNumber,
            upcCode,
            repCost,
            previewDescription,
            onSearchPriceLine,
            createProduct,
        }
    }
}
</script>

<style scoped>
h1 {
    margin-bottom: 1rem;
}
</style>