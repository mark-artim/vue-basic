<template>
  <v-app-bar v-if="authStore.isAuthenticated" app>
    <v-toolbar-title>Eclipse:{{ portLabel }}</v-toolbar-title>
    <div>Hello {{ authStore.erpUserName }}</div>
    <v-spacer />

    <!-- Hamburger dropdown menu -->
    <v-menu>
      <template #activator="{ props }">
        <v-btn v-bind="props" icon>
          <v-icon>mdi-menu</v-icon>
        </v-btn>
      </template>

      <v-list>
        <v-list-item
          v-for="item in menuItems"
          :key="item.name"
          :to="item.path"
          link
          @click="item.action ? item.action() : null"
        >
          <v-list-item-title>{{ item.name }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-app-bar>
</template>



<script>
import { ref, computed, onMounted, watch } from 'vue';
import axios from '@/utils/axios'
import { useAuthStore } from '@/stores/auth';
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

    const menuItems = ref([])

    const loadMenus = async () => {
      try {
        // console.log('[loadMenus] JWT:', authStore.jwt)
        const res = await axios.get('/menus', {
          headers: {
            Authorization: `Bearer ${authStore.jwt}`
          }
        })
        
        const dynamicMenus = res.data
        const homeMenu = { name: 'Home', path: '/home' }
        const logoutMenu = { name: 'Logout', action: logout }

        menuItems.value = [homeMenu, ...dynamicMenus, logoutMenu]
        console.log('[NavigationBar] Loaded menu items:', menuItems.value);

      } catch (err) {
        console.error('[loadMenus] Error:', err)
      }
    }

    watch(
      () => authStore.isAuthenticated,
      (newVal) => {
        if (newVal) loadMenus()
      },
      { immediate: true }
    )

    // Dropdown state
    const navItems = [
      { text: 'Home', value: '/home' },
      { text: 'Contacts', value: '/contacts' },
      { text: 'Contact Change Password', value: '/contact-pw' },
      { text: 'Inventory Balancing', value: '/inv-bal' },
      { text: 'Customer Invoice Lookup', value: '/invoice-lookup' },
      { text: 'Conversion Price Validation', value: '/price-validation' },
      { text: 'Ship54 - 3rd Party Shipping', value: '/ship-station' },
      { text: 'Add New Vendor', value: '/vendor-add' },
      { text: 'Kohler Feed Report', value: '/kohler-feed' },
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
      menuItems,
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
