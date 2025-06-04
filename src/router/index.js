import { createRouter, createWebHistory } from 'vue-router';
import Login from '../pages/Login.vue';
import Home from '../pages/Home.vue';
import About from '../pages/About.vue';
import Contacts from '../pages/Contacts.vue';
//import PriceValidation from '@/components/PriceValidation.vue';
import PriceValidation from '../pages/PriceValidation.vue';
import { useAuthStore } from '../store/auth'; // Pinia store
import InvoiceLookup from '@/pages/InvoiceLookup.vue';
import InventoryBalance from '@/pages/InvBal.vue';
import Testpage from '@/pages/Testpage.vue';
import ShipStation from '@/pages/ShipStation.vue';
import ShipStationOrderDetail from '@/pages/ShipStationOrderDetail.vue';
import CreateProduct from '@/pages/CreateProduct.vue';
import VendorAdd from '@/pages/VendorAdd.vue';
import ContactPW from '@/pages/ContactPW.vue';

const routes = [
  { path: '/', name: 'Login', component: Login },
  // { path: '/login', name: 'Login', component: Login },
  { 
    path: '/home', 
    name: 'Home', 
    component: Home, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/about', 
    name: 'About', 
    component: About, 
    meta: { requiresAuth: true } 
  },
  {
    path: '/contacts',
    name: 'Contacts',
    component: Contacts,
    meta: { requiresAuth: true },
  },
  {
    path: '/contact-pw',
    name: 'Contact Passwords',
    component: ContactPW,
    meta: { requiresAuth: true },
  },
  { path: '/price-validation',
    name: 'Price Validation',
    component: PriceValidation ,
    meta: { requiresAuth: true },
  },
  { path: '/invoice-lookup',
    name: 'Invoice Lookup',
    component: InvoiceLookup ,
    meta: { requiresAuth: true },
  },
  { path: '/inv-bal',
    name: 'Inventory Balance',
    component: InventoryBalance,
    meta: { requiresAuth: true },
  },
  { path: '/testpage',
    name: 'Test Page',
    component: Testpage ,
    meta: { requiresAuth: true },
  },
  { path: '/ship-station',
    name: 'Ship Station',
    component: ShipStation,
    meta: { requiresAuth: true },
  },
  { path: '/ship-station/:invoice',
    name: 'ShipStationOrderDetail',
    component: ShipStationOrderDetail,
    meta: { requiresAuth: true },
  },
  { path: '/create-product',
    name: 'Create Product',
    component: CreateProduct,
    meta: { requiresAuth: true },
  },
  { path: '/vendor-add',
    name: 'Add Vendor',
    component: VendorAdd,
    meta: { requiresAuth: true },
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;
