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
    <v-btn text to="/home">Home</v-btn>
    <v-btn text to="/contacts">Contacts</v-btn>
    <v-btn text to="/price-validation">Price Validation</v-btn>
    <v-btn text to="/invoice-lookup">Invoice Lookup</v-btn>
    <v-btn text to="/inv-bal">Inventory Balancing</v-btn>
    <v-btn text to="/testpage">Test Page</v-btn>
    <v-btn text @click="logout">Logout</v-btn>
  </v-app-bar>
</template>

<script>
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';
import { authStatus } from '@/utils/authStatus'; // ✅ Good import

export default {
  setup() {
    const authStore = useAuthStore();
    const router = useRouter();

    const logout = () => {
      authStore.logout();
      router.push('/');
    };

    return {
      isAuthenticated: authStore.isAuthenticated, // reactive from Pinia
      logout,
      authStatus, // ✅ ADD THIS to expose session status to the template!
      authStore, // ✅ this is the Pinia store instance
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

