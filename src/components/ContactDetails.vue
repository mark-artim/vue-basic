<template>
  <v-card class="mt-4">
    <v-card-title class="orange-title">
      <span v-if="!isEditMode">{{ contact.firstName }} {{ contact.lastName }}</span>
      <v-text-field
        v-if="isEditMode"
        v-model="editableContact.firstName"
        label="First Name"
        outlined
        dense
      />
      <v-text-field
        v-if="isEditMode"
        v-model="editableContact.lastName"
        label="Last Name"
        outlined
        dense
      />
    </v-card-title>

    <v-card-text>
      <!-- Display ID -->
      <p><strong>ID:</strong> {{ contact.id }}</p>
      <p><strong>Name:</strong> {{ contact.fullName }}</p>

      <!-- Display Company Name (Non-Editable) -->
      <p>
        <strong>Company Name:</strong>
        <span>{{ contact.companyName }}</span>
      </p>

      <!-- Display Emails -->
      <div class="emails-section">
        <h3>Emails:</h3>
        <div v-if="!isEditMode">
          <ul>
            <li
              v-for="email in contact.emails"
              :key="email.address"
            >
              {{ email.address }}
            </li>
          </ul>
        </div>
        <div v-else>
          <ul>
            <li
              v-for="(email, index) in editableContact.emails"
              :key="`email-${index}`"
            >
              <v-text-field
                v-model="email.address"
                label="Email Address"
                outlined
                dense
              />
            </li>
          </ul>
        </div>
      </div>

      <!-- Display Classifications -->
      <div>
        <h3>Classifications:</h3>
        <div v-if="!isEditMode">
          <ul>
            <li
              v-for="(classification, index) in contact.classifications"
              :key="index"
            >
              {{ classification.classification || 'N/A' }}
            </li>
          </ul>
        </div>
        <div v-else>
          <ul>
            <li
              v-for="(classification, index) in editableContact.classifications"
              :key="`classification-${index}`"
            >
              <v-text-field
                v-model="classification.classification"
                label="Classification"
                outlined
                dense
              />
            </li>
          </ul>
        </div>
      </div>

      <!-- Display Phones (Editable) -->
      <div>
        <h3>Phones:</h3>
        <div v-if="!isEditMode">
          <ul>
            <li
              v-for="phone in contact.phones"
              :key="phone.number"
            >
              {{ phone.number }} ({{ phone.description || 'No Description' }})
            </li>
          </ul>
        </div>
        <div v-else>
          <ul>
            <li
              v-for="(phone, index) in editableContact.phones"
              :key="`phone-${index}`"
            >
              <v-text-field
                v-model="phone.number"
                label="Phone Number"
                outlined
                dense
              />
              <v-text-field
                v-model="phone.description"
                label="Description"
                outlined
                dense
              />
            </li>
          </ul>
        </div>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn
        color="primary"
        @click="toggleEditMode"
      >
        {{ isEditMode ? 'Cancel' : 'Edit' }}
      </v-btn>
      <v-btn
        v-if="isEditMode"
        color="success"
        @click="saveChanges"
      >
        Save
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { ref } from 'vue';
import { updateContact } from '../api/contacts';
import { useAuthStore } from '../stores/auth';

export default {
  props: {
    contact: {
      type: Object,
      required: true,
    },
  },
  setup(props, { emit }) {
    const isEditMode = ref(false);
    const editableContact = ref({ ...props.contact }); // Clone contact data for editing
    const authStore = useAuthStore();

    // Ensure classifications is always an array
    if (!Array.isArray(editableContact.value.classifications)) {
      editableContact.value.classifications = [];
    }

    const toggleEditMode = () => {
      if (isEditMode.value) {
        // Cancel editing by resetting to original data
        editableContact.value = { ...props.contact };
      }
      isEditMode.value = !isEditMode.value;
    };

    const saveChanges = async () => {
      try {
        // Create a payload with the entire editableContact object
        const payload = {
          ...editableContact.value, // Include all fields from editableContact
          updateKey: props.contact.updateKey, // Always include the updateKey
        };

        // Log the payload for debugging
        console.log('Payload being sent to API:', payload);

        // Send the update request
        await updateContact(editableContact.value.id, payload, authStore.sessionToken);

        // Notify user of success
        isEditMode.value = false;
        alert('Contact updated successfully!');

        // Emit an event to notify the parent component
        emit('contact-updated');
      } catch (error) {
        console.error('Error updating the contact:', error);
        alert('Failed to update the contact. Please try again.');
      }
    };

    return {
      isEditMode,
      editableContact,
      toggleEditMode,
      saveChanges,
    };
  },
};
</script>

<style scoped>
.orange-title {
  color: orange; /* Set the font color to orange */
}

.emails-section {
  margin-top: 16px; /* Add space before the Emails section */
  margin-bottom: 16px; /* Add space after the Emails section */
}
</style>