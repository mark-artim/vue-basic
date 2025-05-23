<template>
    <div class="vendor-add">
        <h1>Add Vendors</h1>
        <div class="option-select">
            <!-- Radio buttons for the two options -->
            <label>
                <input type="radio" value="existing" v-model="selectedOption" />
                Add Ship-From for **Existing** Pay-To
            </label>
            <label style="margin-left:1em;">
                <input type="radio" value="new" v-model="selectedOption" />
                Add **New** Pay-To and Ship-From
            </label>
            <v-autocomplete v-if="selectedOption === 'existing'"
                v-model="selectedVendorId"
                :items="vendorResults"
                item-title="nameIndex"
                item-value="id"
                label="Search Pay-To Vendor"
                outlined dense
                :loading="isLoading"
                no-data-text="No matching vendors"
                hide-no-data
                hide-details
                @input="onVendorInput"
                @update:model-value="onVendorSelected"
                >
            </v-autocomplete>
            <div class="vendor-details" v-if="selectedVendor">
                <h3>Selected Pay-To Vendor</h3>
                <p><strong>{{ selectedVendor.nameIndex }}</strong></p>
                <p>{{ selectedVendor.addressLine1 }}</p>
                <p v-if="selectedVendor.addressLine2">{{ selectedVendor.addressLine2 }}</p>
                <p>{{ selectedVendor.city }}, {{ selectedVendor.state }} {{ selectedVendor.postalCode }}</p>
            </div>

        </div>


    </div>
</template>
<script>
import { ref } from 'vue';
import { debounce } from 'lodash-es';
import { searchVendors } from '@/api/vendors';
import { useAuthStore } from '@/store/auth';

export default {
  setup() {
    const keyword = ref('');
    const selectedOption = ref('existing');
    const vendorResults = ref([]);
    const selectedVendorId = ref(null);
    const selectedVendor = ref(null);
    const isLoading = ref(false);
    const searchTerm = ref('');
    const authStore = useAuthStore();

    const debouncedFetchVendors = debounce(async (query) => {
      await fetchVendors(query);
    }, 1000);

    const onVendorInputOLD = (input) => {
      searchTerm.value = input;
      if (!input || input.length < 2) {
        vendorResults.value = [];
        return;
      }
      debouncedFetchVendors(input);
    };

    // Handle input changes
    const onVendorInput = (inputEvent) => {
      const input = inputEvent.target.value; // Extract the string value from InputEvent
      console.log('Input event triggered with value:', input); // Debug log
      keyword.value = input; // Update the reactive keyword
      debouncedFetchVendors(input); // Pass the string value directly
    };


    const fetchVendors = async (query) => {
      isLoading.value = true;
      try {
        const result = await searchVendors(query, authStore.sessionToken);
        const allVendors = result.results || result;
        vendorResults.value = allVendors.filter(v => v.isPayTo);
      } catch (err) {
        console.error('Error fetching vendors:', err);
        vendorResults.value = [];
      } finally {
        isLoading.value = false;
      }
    };

    const onVendorSelected = (vendorId) => {
      if (!vendorId) {
        selectedVendor.value = null;
        return;
      }
      selectedVendor.value = vendorResults.value.find(v => v.id === vendorId) || null;
    };

    return {
      selectedOption,
      vendorResults,
      selectedVendorId,
      selectedVendor,
      isLoading,
      onVendorInput,
      onVendorSelected
    };
  }
};
</script>

