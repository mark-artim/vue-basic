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
                <v-radio label="Add New Pay-To Only" value="new" />
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
                @focus="clearSelection"
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
                  <p class="font-weight-medium">Pay-To Settings</p>
                  <p>TYPE: {{ selectedVendor.type }}   Ship VIa: {{ selectedVendor.defaultShipVia }}   Terms: {{ selectedVendor.defaultTerms }}   Freight Terms: {{ selectedVendor.freight }}</p>
                </v-card-text>
              </v-card>
              <!-- Existing Ship-From Vendors -->
               <div v-if="updatedMessage" class="my-6 text-green-darken-2 font-weight-bold text-h6">
                  {{ updatedMessage }}
                </div>
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
      <!-- New Pay-To Vendor Form -->
       <v-container v-if="selectedOption === 'new'" fluid>
      <v-row justify="center">
    <v-col cols="12" md="10" lg="8">
      <v-card outlined class="pa-4 rounded-lg elevation-1">
        <v-card-title class="text-subtitle-1 font-weight-bold" style="color: dodgerblue; font-size: 1.2rem">
          New Pay-To Vendor
        </v-card-title>
            <v-divider class="mb-4"></v-divider>
              <v-card-text>
                <v-row dense>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.name" label="Name" outlined dense @blur="() => onNameInput(newPayTo.name)"/>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.nameIndex" label="Index" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.addressLine1" label="Address Line 1" outlined dense @blur="newPayTo.addressLine1 = newPayTo.addressLine1.toUpperCase()"/>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.addressLine2" label="Address Line 2" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field v-model="newPayTo.city" label="City" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field v-model="newPayTo.state" label="State" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field v-model="newPayTo.postalCode" label="Zip" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.countryCode" label="Country Code" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.sortBy" label="Sort By" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.defaultShipVia" label="Default Ship Via" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.freight" label="Freight Terms" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.defaultTerms" label="Default Terms" outlined dense />
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-text-field v-model="newPayTo.backOrderDays" label="Back Order Days" type="number" outlined dense />
                  </v-col>
                  <v-col cols="12">
                    <v-textarea
                      v-model="newPayTo.emails"
                      label="Emails"
                      outlined
                      dense
                      hint="One email address per line"
                      persistent-hint
                      rows="2"
                    />
                  </v-col>
                  <v-col cols="12">
                    <v-textarea
                      v-model="newPayTo.phones"
                      label="Phones"
                      outlined
                      dense
                      hint="Use format: 555-1234 (MAIN)"
                      persistent-hint
                      rows="2"
                    />
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
            <v-btn
              color="primary"
              class="mt-4"
              @click="submitNewPayToVendor"
            >
              Add Vendor
            </v-btn>
        </v-col>
      </v-row>
      <div v-if="updatedMessage" class="my-6 text-red-darken-2 font-weight-medium white-space-pre-line">
        {{ updatedMessage }}
      </div>
      </v-container>
    </v-container>
    <v-container v-if="selectedOption === 'existing'" fluid>
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
                                v-model="form[vendorCode].homeBranch"
                                label="Home Branch"
                                outlined
                                dense
                                />
                            </v-col>
                            <v-col cols="12" sm="6">
                                <v-text-field
                                v-model="form[vendorCode].homeTerritory"
                                label="Home Territory"
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
                        <v-row>
                          <v-col cols="12">
                            <v-btn text small @click="form[vendorCode].showAdvanced = !form[vendorCode].showAdvanced">
                              {{ form[vendorCode].showAdvanced ? 'Hide' : 'Show' }} Advanced Fields
                            </v-btn>
                          </v-col>
                        </v-row>

                        <v-expand-transition>
                          <div v-if="form[vendorCode].showAdvanced">
                            <v-row dense class="mt-2">
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].countryCode" label="Country Code" outlined dense />
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].sortBy" label="Sort By" outlined dense />
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].payToId" label="Pay-To ID" outlined dense disabled/>
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-select v-model="form[vendorCode].type" :items="vendorTypeOptions" label="Type" outlined dense clearable/>
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].defaultShipVia" label="Default Ship Via" outlined dense />
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].freight" label="Freight Terms" outlined dense disabled/>
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].defaultTerms" label="Default Terms" outlined dense />
                              </v-col>
                              <v-col cols="12" sm="6">
                                <v-text-field v-model="form[vendorCode].backOrderDays" label="Back Order Days" type="number" outlined dense />
                              </v-col>
                              <v-col cols="12">
                                <v-textarea
                                  v-model="form[vendorCode].emails"
                                  label="Emails"
                                  outlined
                                  dense
                                  hint="One email address per line"
                                  persistent-hint
                                  rows="2"
                                />
                              </v-col>
                              <v-col cols="12">
                                <v-textarea
                                  v-model="form[vendorCode].phones"
                                  label="Phones"
                                  outlined
                                  dense
                                  hint="Use format: 555-1234 (MAIN)"
                                  persistent-hint
                                  rows="2"
                                />
                              </v-col>
                            </v-row>
                          </div>
                        </v-expand-transition>

                        </v-card>
                    </v-col>
                    </v-row>
                </div>
                </v-expand-transition>
            </v-card-text>
            </v-card>
        </v-col>
        </v-row>
        <v-btn
          color="primary"
          class="mt-4"
          :disabled="!selectedVendors.length"
          @click="submitVendors"
        >
          Add Vendor(s)
        </v-btn>
        <v-btn
          color="primary"
          class="mt-4"
          :disabled="!selectedVendors.length"
          @click="logVendorForm"
        >
        Console Log Vendor
        </v-btn>
    </v-container>
    </template>

  
<script>
import { ref, watch } from 'vue';
import { useDebouncedSearch } from '@/composables/useDebouncedSearch';
import { searchVendors } from '@/api/vendors';
import { getVendor } from '@/api/vendors';
import { useAuthStore } from '@/stores/auth';
import { createVendor } from '@/api/vendors';
import { validVendorTypes } from '@/utils/validators';
const vendorTypeOptions = validVendorTypes;

export default {
    props: {
    payToVendor: Object
  },
  setup(props) {
    const selectedOption = ref('existing');
    const selectedVendorId = ref(null);
    const selectedVendor = ref(null);
    const authStore = useAuthStore();
    const shipFromVendors = ref([]);
    const selectedVendors = ref([]);
    const form = ref({});
    const updatedMessage = ref('');
    const code = ref('');

    const fetchVendors = async (query) => {
      const result = await searchVendors(query, authStore.sessionToken);
      const allVendors = result.results || result;
      return allVendors.filter(v => v.isPayTo);
    };

    const {
      searchTerm: keyword,
      results: vendorResults,
      isLoading,
      onSearch: onVendorInput,
      clear,
    } = useDebouncedSearch(fetchVendors, 1000);

    const vendorOptions = [
      { name: 'Benoist', code: 'BBS', homeBranch: 'ILMV', homeTerritory: 'TCBBS' },
      { name: 'Coastal', code: 'CSC', homeBranch: 'TNKN', homeTerritory: 'TCCSC' },
      { name: "Ed's Central", code: 'ESC', homeBranch: 'TNNA', homeTerritory: 'TCESC' },
      { name: "Ed's East", code: 'ESE', homeBranch: 'TNCH', homeTerritory: 'TCESE' },
      { name: "Ed's West", code: 'ESW', homeBranch: 'ARLR', homeTerritory: 'TCESW' },
      { name: 'NuComfort', code: 'NCS', homeBranch: 'ILCS', homeTerritory: 'TCNCS' },
      { name: 'Wittichen', code: 'WSC', homeBranch: '1', homeTerritory: 'TCWSC' }
    ];

    const getVendorName = (code) => {
      return vendorOptions.find(v => v.code === code)?.name || code;
    };

    const generateDefaults = (code) => {
      const payTo = selectedVendor.value;
      const firstWord = payTo?.nameIndex?.split(' ')[0]?.toUpperCase() || 'VENDOR';
      const vendorMeta = vendorOptions.find(v => v.code === code) || {};

      return {
        name: payTo?.nameIndex?.toUpperCase() || '',
        index: `${firstWord} - ${code} SHIP FROM`,
        addressLine1: payTo?.addressLine1?.toUpperCase() || '',
        addressLine2: payTo?.addressLine2?.toUpperCase() || '',
        city: payTo?.city?.toUpperCase() || '',
        state: payTo?.state?.toUpperCase() || '',
        postalCode: payTo?.postalCode?.toUpperCase() || '',
        countryCode: 'USA',
        isPayTo: false,
        isShipFrom: true,
        isFreightVendor: false,
        isManufacturer: false,
        sortBy: payTo?.sortBy || '',
        payToId: payTo?.id || '',
        type: payTo?.type || '',
        defaultShipVia: 'BEST WAY',
        freight: 'Freight Allowed',
        defaultTerms: payTo?.defaultTerms || '',
        backOrderDays: 7,
        emails: payTo?.emails?.map(e => e.address) || [],
        phones: payTo?.phones?.map(p => `${p.number} (${p.description})`) || [],
        homeBranch: vendorMeta.homeBranch || '',
        homeTerritory: vendorMeta.homeTerritory || ''
      };
    };

    const logVendorForm = (code) => {
      const vendorMeta = vendorOptions.find(v => v.code === code) || {};
      console.log('Know the Code:', code);
      console.log('Selected Vendors:', selectedVendors.value)
      console.log('vendorMeta.homebranch:', vendorMeta.homeBranch)
      console.log('vendorMeta.hometerritory:', vendorMeta.homeTerritory)
    };

    const toggleVendor = (code) => {
      logVendorForm(code);
      const index = selectedVendors.value.indexOf(code);
      if (index >= 0) {
        selectedVendors.value.splice(index, 1);
        delete form.value[code];
      } else {
        selectedVendors.value.push(code);
        form.value[code] = generateDefaults(code);
      }
    };




    const clearSelection = () => {
      selectedVendorId.value = null;
      selectedVendor.value = null;
      shipFromVendors.value = [];
      selectedVendors.value = [];
      form.value = {};
      updatedMessage.value = '';
    };


    const submitVendors = async () => {
      try {
        const payloads = selectedVendors.value.map(code => {
          const raw = form.value[code];

          return {
            name: raw.name,
            addressLine1: raw.addressLine1,
            addressLine2: raw.addressLine2,
            city: raw.city,
            state: raw.state,
            postalCode: raw.postalCode,
            countryCode: raw.countryCode || 'USA',
            isPayTo: false,
            isShipFrom: true,
            isFreightVendor: false,
            isManufacturer: false,
            sortBy: raw.sortBy,
            nameIndex: raw.index,
            payToId: raw.payToId,
            type: raw.type,
            defaultShipVia: raw.defaultShipVia,
            freight: raw.freight,
            homeBranch: raw.homeBranch,
            homeTerritory: raw.homeTerritory,
            defaultTerms: raw.defaultTerms,
            backOrderDays: String(raw.backOrderDays),
            emails: (raw.emails || []).filter(Boolean).map(addr => ({
              address: addr.trim()
            })),
            phones: (raw.phones || []).filter(Boolean).map(p => {
              const match = p.match(/^(.+?)\s*\((.*?)\)$/);
              return {
                number: match?.[1]?.trim() || p.trim(),
                description: match?.[2]?.trim() || ''
              };
            })
          };
        });

        // Submit each vendor individually
        for (const vendorData of payloads) {
          // const response = await createVendor(vendorData, authStore.sessionToken);
          const response = await createVendor(vendorData, authStore.erpToken);
          console.log('Vendor created:', response.data);
        }

        selectedVendors.value = [];
        form.value = {};
        await onVendorSelected(selectedVendor.value.id); // 👈 re-fetch pay-to and ship-froms
        updatedMessage.value = 'Updated with new ship-from\'s'; // 👈 show confirmation
      } catch (error) {
        if (error.response?.data?.errors) {
          console.error('Validation errors:', error.response.data.errors);
          updatedMessage.value = 'Error: ' + error.response.data.errors.map(e => `${e.field}: ${e.message}`).join(', ');
        }
        console.error('Error creating vendors:', error);
        alert('One or more vendors failed to be created. See console for details.');
      }
    };


    const onVendorSelected = async (vendorId) => {
      // Fetch selected Pay-To vendor details
      selectedVendor.value = await getVendor(vendorId, authStore.sessionToken);

      // Extract shipFromIds from the selected vendor
      const shipFromIds = selectedVendor.value.shipFromLists?.map(item => item.shipFromId) || [];

      // Fetch details for each Ship-From vendor
      try {
        const responses = await Promise.all(
          shipFromIds.map(id => getVendor(id, authStore.sessionToken))
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

  const newPayTo = ref({
    name: '',
    nameIndex: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postalCode: '',
    countryCode: 'USA',
    payToId: null,
    isPayTo: true,
    isShipFrom: false,
    isFreightVendor: false,
    isManufacturer: false,
    sortBy: '',
    defaultShipVia: 'BEST WAY',
    freight: 'Freight Allowed',
    defaultTerms: 'NET30',
    backOrderDays: 7,
    emails: [],
    phones: []
  });

  const submitNewPayToVendor = async () => {
    try {
      const payload = {
        ...newPayTo.value,
        backOrderDays: String(newPayTo.value.backOrderDays),
        emails: (newPayTo.value.emails || '')
      .split('\n')
      .map(addr => addr.trim())
      .filter(Boolean)
      .map(addr => ({
        address: addr,
        type: '',
        preference: ''
    })),
        // Convert phones to the expected format
        phones: (newPayTo.value.phones || '')
    .split('\n')
    .map(p => {
      const match = p.match(/^(.+?)\s*\((.*?)\)$/);
      return {
        number: match?.[1]?.trim() || p.trim(),
        description: match?.[2]?.trim() || ''
      };
    })
      };  

      const response = await createVendor(payload, authStore.sessionToken);
      console.log('Pay-To Vendor created:', response.data);
      updatedMessage.value = 'New Pay-To vendor successfully created!';
      Object.assign(newPayTo.value, {
        name: '',
        nameIndex: '',
        addressLine1: '',
        addressLine2: '',
        city: '',
        state: '',
        postalCode: '',
        sortBy: '',
        defaultTerms: '',
        emails: [],
        phones: []
      }); // Reset form
    } catch (error) {
      console.error('Error creating Pay-To vendor:', error);

      if (error.response?.data?.errors?.length) {
        // Extract and format field-level errors
        const messages = error.response.data.errors.map(e =>
          `${e.field || 'Unknown'}: ${e.message}`
        );
        updatedMessage.value = '❌ Validation error(s):\n' + messages.join('\n');
      } else {
        updatedMessage.value = '❌ Failed to create new Pay-To vendor. Please try again.';
      }
    }
  };

    watch(selectedOption, (newVal) => {
    if (newVal === 'new') {
      selectedVendor.value = null;
      selectedVendorId.value = null;
      shipFromVendors.value = [];
      selectedVendors.value = [];
      form.value = {};
    } else if (newVal === 'existing') {
      Object.assign(newPayTo.value, {
        name: '',
        nameIndex: '',
        addressLine1: '',
        addressLine2: '',
        city: '',
        state: '',
        postalCode: '',
        sortBy: '',
        defaultTerms: '',
        emails: [],
        phones: []
      });
    }
  });

const onNameInput = (val) => {
      if (typeof val !== 'string') return;
      const upper = val.toUpperCase();
      newPayTo.value.name = upper;

      // If nameIndex is still blank, copy it from name
      if (!newPayTo.value.nameIndex) {
        newPayTo.value.nameIndex = upper;
      }

      // Always update sortBy to the first 12 characters
      newPayTo.value.sortBy = upper.slice(0, 12);

      // return onNameInput(val);
    };


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
      form,
      submitVendors,
      updatedMessage,
      logVendorForm,
      clearSelection,
      newPayTo,
      submitNewPayToVendor,
      onNameInput,
      vendorTypeOptions
    };
}
};
</script>

<style scoped>
.ship-from-button {
  margin-bottom: 8px;
}
</style>

