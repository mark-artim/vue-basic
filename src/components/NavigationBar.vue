<template>
  <!-- <v-app-bar app> -->
  <v-app-bar v-if="authStore.isAuthenticated" app>
    <v-toolbar-title>Eclipse:{{ portLabel }}</v-toolbar-title>
    <div> Hi {{ userName }}</div>

    <v-spacer></v-spacer>

      <!-- Navigation dropdown -->
      <v-select v-model="selectedPage"
      :items="navItems"
      item-title="text"
      item-value="value"
      persistent-placeholder
      placeholder="Menu"
      single-line
      hide-details
      item-height="10"
      style="max-width: 200px; color: white"
      @update:modelValue="navigate"
      />
  </v-app-bar>
</template>

<script>
import { ref, computed } from 'vue';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';
import { authStatus } from '@/utils/authStatus'; // ✅ Good import
import { value } from 'lodash-es';

export default {
  name: 'NavigationBar',
  setup() {
    
    const router = useRouter();
    const authStore = useAuthStore();
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const userName = computed(() => authStore.userName)
    const portLabel = computed(() => authStore.portLabel)
    
    console.log('username: ', userName);
    // Dropdown state
    const navItems = [
      { text: 'Home', value: '/home' },
      { text: 'Contacts', value: '/contacts' },
      { text: 'Contact Change Password', value: '/contact-pw' },
      { text: 'Inventory Balancing', value: '/inv-bal' },
      { text: 'Customer Invoice Lookup', value: '/invoice-lookup' },
      { text: 'Conversion Price Validation', value: '/price-validation' },
      { text: 'Shipli 3rd Party Shipping', value: '/ship-station' },
      { text: 'Add New Vendor', value: '/vendor-add' },
      { text: 'Create Product', value: '/create-product' },
      { text: 'API Test - Eds PN Lookup', value: '/testpage' },
      { text: 'Logout', value: 'logout' },
    ];
    const selectedPage = ref(null);

    // Navigate on selection; handle logout specially
    function navigate(path) {
      if (!path) return;
      // If the Logout item is chosen, call logout
      if (path === 'logout' || path === '/logout') {
        logout();
      } else {
        router.push(path);
      }
      // Reset select back to placeholder
      selectedPage.value = null;
    }

    // Logout logic
    function logout() {
      console.log('Logging out from NavBar logout()');
      authStore.logout();
      router.push('/');
    }

    return {
      // isAuthenticated: authStore.isAuthenticated, // reactive from Pinia
      isAuthenticated,
      logout,
      authStatus, // ✅ ADD THIS to expose session status to the template!
      authStore, // ✅ this is the Pinia store instance
      navItems,
      selectedPage,
      navigate,
      userName,
      portLabel,
    };
  },
};
</script>

<style scoped>
.session-status {
  margin-left: 20px;
  display: flex;
  align-items: center;
  font-weight: bold;
}

.session-badge {
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.9rem;
}

.session-badge.good {
  background-color: #d4edda;
  color: #155724;
}

.session-badge.warning {
  background-color: #fff3cd;
  color: #856404;
}
</style>
