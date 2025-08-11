<template>
  <v-container>
    <h1>Contact Search</h1>

    <!-- Auto-complete with debounced search -->
    <v-autocomplete
      v-model="selectedContact"
      :items="contacts"
      item-title="fullName"
      item-value="id"
      label="Search Contacts"
      outlined
      dense
      :loading="isLoading"
      no-data-text="No contacts found"
      hide-no-data
      hide-details
      @input="handleInput"
      @update:model-value="onContactSelected"
    >
      <!-- Custom dropdown item -->
      <template #item="{ item, props }">
        <v-list-item v-bind="props">
          <v-list-item-content class="blue">
            Co: {{ item.raw.companyName }}
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-autocomplete>

    <!-- Selected Contact Details -->
    <ContactDetails
      v-if="selectedContact"
      :contact="selectedContact"
      @contact-updated="fetchContact(selectedContact.id)"
    />
  </v-container>
</template>

<script>
import { ref } from 'vue';
import { useDebouncedSearch } from '@/composables/useDebouncedSearch';
import { searchContacts, getContact } from '../api/contacts';
import ContactDetails from '../components/ContactDetails.vue';
import { useAuthStore } from '../stores/auth';

export default {
  components: { ContactDetails },
  setup() {
    const selectedContact = ref(null);
    const authStore = useAuthStore();

    const fetchContacts = async (input) => {
      if (!input || input.length < 2) {
        return [];
      }
      const result = await searchContacts(input);
      return result.results.map((contact) => ({
        id: contact.id,
        fullName: `${contact.firstName} ${contact.middleName ? contact.middleName + ' ' : ''}${contact.lastName}`,
        companyName: contact.companyName || 'No Company',
        ...contact,
      }));
    };

    const {
      searchTerm: keyword,
      results: contacts,
      isLoading,
      onSearch: handleInput,
      clear,
    } = useDebouncedSearch(fetchContacts, 1000);

    const fetchContact = async (contactId) => {
      console.log('Fetching contact for ID:', contactId); // Debug log
      if (!contactId) {
        console.log('No contact ID provided, skipping fetch');
        selectedContact.value = null; // Clear the selected contact
        return;
      }

      isLoading.value = true;
      try {
        // Ensure the sessionToken is available
        if (!authStore.sessionToken) {
          throw new Error('No session token available. Please log in.');
        }

        // Fetch the contact data with the sessionToken
        // const result = await getContact(contactId, authStore.sessionToken);
        const result = await getContact(contactId);
        console.log('API Response:', result); // Log API response

        // Ensure the result is an object and has the required fields
        if (!result || typeof result !== 'object') {
          throw new Error('Invalid API response: Expected an object.');
        }

        // Update the selectedContact with the fetched data
        selectedContact.value = {
          id: result.id,
          fullName: `${result.firstName} ${result.middleName ? result.middleName + ' ' : ''}${result.lastName}`,
          companyName: result.companyName || 'No Company',
          ...result, // Include all other fields from the API response
        };

        console.log('Updated Selected Contact:', selectedContact.value); // Debug log
      } catch (err) {
        console.error('Error fetching contact:', err);
        alert('Failed to fetch contact. Please check your authentication and try again.');
      } finally {
        isLoading.value = false;
      }
    };




    const onContactSelected = (contactId) => {
      console.log("Selected Contact ID:", contactId);
      selectedContact.value = contacts.value.find(contact => contact.id === contactId) || null;
      console.log("Selected Contact Object:", selectedContact.value);
    };

    return {
      keyword,
      contacts,
      selectedContact,
      isLoading,
      handleInput,
      onContactSelected,
      fetchContact,
    };
  },
};
</script>
<style scoped>
.blue {
  color: dodgerblue;
  /* Set the font color to orange */
}
</style>