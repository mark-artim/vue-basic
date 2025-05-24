<template>
    <div class="vendor-add">
        <h1>Add Vendors</h1>
        <div class="option-select">
            <!-- Radio buttons for the two options -->
            <v-radio-group v-model="selectedOption" row>
                <v-radio label="Add Ship-From for Existing Pay-To" value="existing" />
                <v-radio label="Add New Pay-To and Ship-From" value="new" />
            </v-radio-group>

            <p>Selected Option: {{ selectedOption }}</p>
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
            <!-- <div class="vendor-details" v-if="selectedVendor">
                <h3>Selected Pay-To Vendor</h3>
                <p><strong>{{ selectedVendor.nameIndex }}</strong></p>
                <p>{{ selectedVendor.addressLine1 }}</p>
                <p v-if="selectedVendor.addressLine2">{{ selectedVendor.addressLine2 }}</p>
                <p>{{ selectedVendor.city }}, {{ selectedVendor.state }} {{ selectedVendor.postalCode }}</p>
            </div> -->
            <div class="vendor-details" v-if="selectedVendor">
                <h3>Selected Pay-To Vendor</h3>
                <p><strong>{{ selectedVendor.nameIndex }}</strong></p>
                <p>{{ selectedVendor.addressLine1 }}</p>
                <p v-if="selectedVendor.addressLine2">{{ selectedVendor.addressLine2 }}</p>
                <p>{{ selectedVendor.city }}, {{ selectedVendor.state }} {{ selectedVendor.postalCode }}</p>
            </div>

            <div class="ship-from-list" v-if="shipFromVendors?.length">
                <h3>Existing Ship-From Accounts</h3>
                <div v-for="vendor in shipFromVendors" :key="vendor.id" class="vendor-details">
                    <p><strong>{{ vendor.nameIndex }}</strong></p>
                    <p>{{ vendor.addressLine1 }}</p>
                    <p v-if="vendor.addressLine2">{{ vendor.addressLine2 }}</p>
                    <p>{{ vendor.city }}, {{ vendor.state }} {{ vendor.postalCode }}</p>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import { ref } from 'vue';
import { debounce } from 'lodash-es';
import { searchVendors } from '@/api/vendors';
import { getVendorById } from '@/api/vendors';
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
    const shipFromVendors = ref([]);

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

    // const onVendorSelected = (vendorId) => {
    //   if (!vendorId) {
    //     selectedVendor.value = null;
    //     return;
    //   }
    //   selectedVendor.value = vendorResults.value.find(v => v.id === vendorId) || null;
    // };

    const onVendorSelected = async (vendorId) => {
      // Fetch selected Pay-To vendor details
      selectedVendor.value = await getVendorById(vendorId, authStore.sessionToken);

      // Extract shipFromIds from the selected vendor
      const shipFromIds = selectedVendor.value.shipFromLists?.map(item => item.shipFromId) || [];

      // Fetch details for each Ship-From vendor
      try {
        const responses = await Promise.all(
          shipFromIds.map(id => getVendorById(id, authStore.sessionToken))
        );
        shipFromVendors.value = responses;
      } catch (error) {
        console.error('Error fetching Ship-From vendors:', error);
        shipFromVendors.value = [];
      }
  }
  return {
      selectedOption,
      vendorResults,
      selectedVendorId,
      selectedVendor,
      shipFromVendors,
      isLoading,
      onVendorInput,
      onVendorSelected
    };
}
};
</script>

