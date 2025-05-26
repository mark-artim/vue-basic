<template>
    <v-container class="vendor-add" fluid>
      <v-row justify="center">
        <v-col cols="12" md="10" lg="8">
          <v-card class="pa-6 elevation-2 rounded-xl">
            <v-card-title class="text-h5 font-weight-bold pb-4">Add Vendors</v-card-title>
            <v-divider></v-divider>
  
            <!-- Vendor Type Selection -->
            <v-card-text>
              <v-radio-group v-model="selectedOption" row>
                <v-radio label="Add Ship-From for Existing Pay-To" value="existing" />
                <v-radio label="Add New Pay-To and Ship-From" value="new" />
              </v-radio-group>
  
              <v-divider class="my-4"></v-divider>
  
              <!-- Autocomplete for Existing Pay-To -->
              <v-autocomplete
                v-if="selectedOption === 'existing'"
                v-model="selectedVendorId"
                :items="vendorResults"
                item-title="nameIndex"
                item-value="id"
                label="Search Pay-To Vendor"
                outlined
                dense
                :loading="isLoading"
                no-data-text="No matching vendors"
                hide-no-data
                hide-details
                @input="onVendorInput"
                @update:model-value="onVendorSelected"
              />
  
              <!-- Selected Pay-To Vendor Info -->
              <v-card
                v-if="selectedVendor"
                class="mt-6 pa-4 bg-grey-lighten-4"
                elevation="1"
              >
                <v-card-title class="text-subtitle-1 font-weight-medium">
                  Selected Pay-To Vendor
                </v-card-title>
                <v-card-text>
                  <p><strong>{{ selectedVendor.nameIndex }}</strong></p>
                  <p>{{ selectedVendor.addressLine1 }}</p>
                  <p v-if="selectedVendor.addressLine2">{{ selectedVendor.addressLine2 }}</p>
                  <p>{{ selectedVendor.city }}, {{ selectedVendor.state }} {{ selectedVendor.postalCode }}</p>
                </v-card-text>
              </v-card>
  
              <!-- Existing Ship-From Vendors -->
              <div v-if="shipFromVendors?.length" class="mt-8">
                <h3 class="text-h6 font-weight-medium mb-4">Existing Ship-From Accounts</h3>
  
                <v-row dense>
                  <v-col
                    v-for="vendor in shipFromVendors"
                    :key="vendor.id"
                    cols="12"
                    sm="6"
                    md="6"
                  >
                    <v-card class="pa-4" outlined>
                        <v-card-title class="font-weight-bold" style="font-size: 1.2rem; color: dodgerblue;">
                        {{ vendor.nameIndex }} ({{ vendor.id }})
                      </v-card-title>
                      <v-card-text>
                        <p>Home Branch: {{ vendor.homeBranch }} Home Territory: {{ vendor.homeTerritory }}</p>
                        <p>{{ vendor.addressLine1 }}</p>
                        <p v-if="vendor.addressLine2">{{ vendor.addressLine2 }}</p>
                        <p>{{ vendor.city }}, {{ vendor.state }} {{ vendor.postalCode }}</p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
    <v-container fluid>
        <v-row justify="center">
        <v-col cols="12" md="10" lg="8">
            <v-card class="pa-6 elevation-2 rounded-xl">
            <v-card-title class="text-h5 font-weight-bold">Add New Ship-From Vendors</v-card-title>
            <v-divider class="my-4"></v-divider>

            <v-card-text>
                <!-- Vendor Option Buttons -->
                <v-row class="mb-6" dense>
                <v-col
                    v-for="vendor in vendorOptions"
                    :key="vendor.code"
                    cols="6"
                    sm="4"
                    md="3"
                >
                    <v-btn
                    :color="selectedVendors.includes(vendor.code) ? 'primary' : 'grey lighten-3'"
                    class="text-uppercase font-weight-medium"
                    variant="elevated"
                    block
                    @click="toggleVendor(vendor.code)"
                    >
                    {{ vendor.name }}
                    </v-btn>
                </v-col>
                </v-row>

                <!-- Preview Section -->
                <v-expand-transition>
                <div v-if="selectedVendors.length">
                    <v-divider class="my-6"></v-divider>
                    <v-card-title class="text-h6 font-weight-bold mb-4">
                    New Vendor Preview
                    </v-card-title>

                    <v-row
                    v-for="vendorCode in selectedVendors"
                    :key="vendorCode"
                    class="mb-6"
                    >
                    <v-col cols="12">
                        <v-card outlined class="pa-4 rounded-lg elevation-1">
                        <v-card-title
                            class="text-subtitle-1 font-weight-bold"
                            style="color: dodgerblue; font-size: 1.2rem"
                        >
                            {{ getVendorName(vendorCode) }} Ship From
                        </v-card-title>
                        <v-divider class="mb-4"></v-divider>

                        <v-card-text>
                            <v-row dense>
                            <v-col cols="12" sm="6">
                                <v-text-field
                                v-model="form[vendorCode].name"
                                label="Name"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="6">
                                <v-text-field
                                v-model="form[vendorCode].index"
                                label="Index"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="6">
                                <v-text-field
                                v-model="form[vendorCode].addressLine1"
                                label="Address Line 1"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="6">
                                <v-text-field
                                v-model="form[vendorCode].addressLine2"
                                label="Address Line 2"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="4">
                                <v-text-field
                                v-model="form[vendorCode].city"
                                label="City"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="4">
                                <v-text-field
                                v-model="form[vendorCode].state"
                                label="State"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="4">
                                <v-text-field
                                v-model="form[vendorCode].postalCode"
                                label="Zip"
                                outlined
                                dense
                                />
                            </v-col>
                            </v-row>
                        </v-card-text>
                        </v-card>
                    </v-col>
                    </v-row>
                </div>
                </v-expand-transition>
            </v-card-text>
            </v-card>
        </v-col>
        </v-row>
    </v-container>
    </template>

  
<script>
import { ref } from 'vue';
import { debounce } from 'lodash-es';
import { searchVendors } from '@/api/vendors';
import { getVendorById } from '@/api/vendors';
import { useAuthStore } from '@/store/auth';

export default {
    props: {
    payToVendor: Object
  },
  setup(props) {
    const keyword = ref('');
    const selectedOption = ref('existing');
    const vendorResults = ref([]);
    const selectedVendorId = ref(null);
    const selectedVendor = ref(null);
    const isLoading = ref(false);
    const searchTerm = ref('');
    const authStore = useAuthStore();
    const shipFromVendors = ref([]);
    const selectedVendors = ref([]);
    const form = ref({});

    const vendorOptions = [
      { name: 'Benoist', code: 'BBS' },
      { name: 'Coastal', code: 'CSC' },
      { name: "Ed's Central", code: 'ESC' },
      { name: "Ed's East", code: 'ESE' },
      { name: "Ed's West", code: 'ESW' },
      { name: 'NuComfort', code: 'NCS' },
      { name: 'Wittichen', code: 'WSC' }
    ];

    const toggleVendor = (code) => {
      const index = selectedVendors.value.indexOf(code);
      if (index >= 0) {
        selectedVendors.value.splice(index, 1);
        delete form.value[code];
      } else {
        selectedVendors.value.push(code);
        form.value[code] = generateDefaults(code);
      }
    };

    const getVendorName = (code) => {
      return vendorOptions.find(v => v.code === code)?.name || code;
    };

    const generateDefaults = (code) => {
  const firstWord = selectedVendor.value?.nameIndex?.split(' ')[0]?.toUpperCase() || 'VENDOR';

  return {
            name: selectedVendor.value?.nameIndex?.toUpperCase() || '',
            index: `${firstWord} - ${code} SHIP FROM`,
            addressLine1: selectedVendor.value?.addressLine1?.toUpperCase() || '',
            addressLine2: selectedVendor.value?.addressLine2?.toUpperCase() || '',
            city: selectedVendor.value?.city?.toUpperCase() || '',
            state: selectedVendor.value?.state?.toUpperCase() || '',
            postalCode: selectedVendor.value?.postalCode?.toUpperCase() || ''
        };
    };


    const debouncedFetchVendors = debounce(async (query) => {
      await fetchVendors(query);
    }, 1000);

    // Handle input changes
    const onVendorInput = (inputEvent) => {
        const input = (inputEvent?.target?.value || inputEvent || '').toUpperCase();
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
        // ✅ Sort alphabetically by nameIndex (case-insensitive)
        shipFromVendors.value = responses.sort((a, b) =>
            a.nameIndex.localeCompare(b.nameIndex, undefined, { sensitivity: 'base' })
        );
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
      onVendorSelected,
      vendorOptions,
      selectedVendors,
      toggleVendor,
      getVendorName,
      form
    };
}
};
</script>

<style scoped>
.ship-from-button {
  margin-bottom: 8px;
}
</style>

