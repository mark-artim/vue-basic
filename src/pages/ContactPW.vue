
<template>
  <v-container class="py-10">
    <v-row justify="center">
      <v-col cols="12" md="6">
        <v-card elevation="3" class="pa-6 rounded-xl">
          <v-card-title class="text-h5 font-weight-bold text-primary">
            🔐 Update Web Password
          </v-card-title>
          <v-card-subtitle class="mb-4">
            Provide your user ID, contact ID, and new password.
          </v-card-subtitle>

          <v-form @submit.prevent="submitForm" ref="formRef" v-model="valid">
            <v-text-field
              v-model="form.userId"
              label="User ID"
              placeholder="e.g. mark.artim@gmail.com"
              :rules="[rules.required]"
              clearable
              prepend-inner-icon="mdi-account"
            />

            <v-text-field
              v-model="form.contactId"
              label="ERP Contact ID"
              type="number"
              :rules="[rules.required]"
              clearable
              prepend-inner-icon="mdi-account-box"
            />

            <v-text-field
              v-model="form.newPassword"
              label="New Password"
              type="password"
              :rules="[rules.required, rules.min]"
              clearable
              prepend-inner-icon="mdi-lock"
            />

            <v-btn
              color="primary"
              class="mt-4"
              type="submit"
              :disabled="!valid || loading"
              block
            >
              <span v-if="!loading">Update Password</span>
              <v-progress-circular v-else indeterminate color="white" size="20" />
            </v-btn>

            <v-alert v-if="successMessage" type="success" class="mt-4" border="start" colored-border>
              {{ successMessage }}
            </v-alert>

            <v-alert v-if="errorMessage" type="error" class="mt-4" border="start" colored-border>
              {{ errorMessage }}
            </v-alert>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import axios from '@/utils/axios'; // Adjust if needed

const formRef = ref(null);
const valid = ref(false);
const loading = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

const form = ref({
  userId: '',
  contactId: '',
  newPassword: '',
});

const rules = {
  required: v => !!v || 'This field is required',
  min: v => (v && v.length >= 8) || 'Password must be at least 8 characters',
};

const submitForm = async () => {
  if (!formRef.value?.validate()) return;

  loading.value = true;
  successMessage.value = '';
  errorMessage.value = '';

  try {
    const { userId, contactId, newPassword } = form.value;

    // 1. GET /Contacts/{contactId}
    // 1. GET /Contacts/{contactId}
    const { data: contactData } = await axios.get(`/Contacts/${contactId}/WebSettings`);
    const updateKey = contactData.updateKey;

    if (!updateKey) throw new Error('Update key not found in contact record');


    // 2. Prepare WebSettings payload
    const webSettings = contactData ?? {}; // safely fallback to empty object

    const payload = {
    updateKey,
    id: userId,
    contactId: Number(contactId),
    password: newPassword,

    trackerViewOnly: webSettings.trackerViewOnly ?? false,
    enableShipToEdit: webSettings.enableShipToEdit ?? false,
    bidViewOnly: webSettings.bidViewOnly ?? false,
    hideAccountInquiry: webSettings.hideAccountInquiry ?? false,
    superuser: webSettings.superuser ?? false,
    enableShipToCreate: webSettings.enableShipToCreate ?? false,
    hideAccountLedger: webSettings.hideAccountLedger ?? false,
    enableShipBranchOverride: webSettings.enableShipBranchOverride ?? false,
    sendEmailOnTrackerUpdate: webSettings.sendEmailOnTrackerUpdate ?? false,
    };


    // 3. POST to /Contacts/{contactId}/WebSettings
    await axios.put(`/Contacts/${contactId}/WebSettings`, payload);

    successMessage.value = 'Password updated successfully!';
    form.value.newPassword = '';
  } catch (err) {
    if (err.response) {
        const { status, data } = err.response;
        const serverMsg = data?.message || JSON.stringify(data);
        errorMessage.value = `Error ${status}: ${serverMsg}`;
        console.error('[Password Update Error]', status, data);
        } else if (err.request) {
        errorMessage.value = 'No response from server. Check network or endpoint.';
        console.error('[Password Update Error] No response', err.request);
        } else {
        errorMessage.value = `Request setup error: ${err.message}`;
        console.error('[Password Update Error]', err.message);
        }
    console.error('[Password Update Error]', err);
  } finally {
    loading.value = false;
  }
};
</script>
