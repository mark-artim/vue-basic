<template>
  <!-- <v-app-bar app> -->
  <v-app-bar v-if="authStore.isAuthenticated" app>
    <v-toolbar-title>Beyond Eclipse</v-toolbar-title>

    <div class="session-status">
      <span v-if="authStatus.sessionExpired" class="session-badge warning">
        ⚠️ Session Expired
      </span>
      <span v-else class="session-badge good">
        ✅ Session Active
      </span>
    </div>

    <v-spacer></v-spacer>

      <!-- Navigation dropdown -->
      <v-select v-model="selectedPage"
      :items="navItems"
      item-title="text"
      item-value="value"
      label="Menu"
      placeholder="Menu"
      single-line
      hide-details
      item-height="10"
      style="max-width: 200px"
      @update:modelValue="navigate"
      />
  </v-app-bar>
</template>

<script>
import { ref } from 'vue';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';
import { authStatus } from '@/utils/authStatus'; // ✅ Good import

export default {
  name: 'NavigationBar',
  setup() {
    const authStore = useAuthStore();
    const router = useRouter();

    // Dropdown state
    const navItems = [
      { text: 'Home', value: '/home' },
      { text: 'Contacts', value: '/contacts' },
      { text: 'Inventory Balancing', value: '/inv-bal' },
      { text: 'Customer Invoice Lookup', value: '/invoice-lookup' },
      { text: 'Conversion Price Validation', value: '/price-validation' },
      { text: 'Ship Station', value: '/ship-station' },
      { text: 'Test', value: '/testpage' },
      { text: 'Logout', value: 'logout' },
    ];
    const selectedPage = ref(null);

    // Navigate on select change
    function navigate(path) {
      if (path) {
        router.push(path);
        selectedPage.value = null;
      }
    }

    // Logout logic
    function logout() {
      authStore.logout();
      router.push('/');
    }

    return {
      isAuthenticated: authStore.isAuthenticated, // reactive from Pinia
      logout,
      authStatus, // ✅ ADD THIS to expose session status to the template!
      authStore, // ✅ this is the Pinia store instance
      navItems,
      selectedPage,
      navigate,
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
