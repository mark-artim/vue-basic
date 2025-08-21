import { createRouter, createWebHistory } from 'vue-router';
import Login from '../pages/Login.vue';
import Home from '../pages/Home.vue';
import About from '../pages/About.vue';
import Contacts from '../pages/Contacts.vue';
//import PriceValidation from '@/components/PriceValidation.vue';
import PriceValidation from '../pages/PriceValidation.vue';
import { useAuthStore } from '../stores/auth'; // Pinia store
import InvoiceLookup from '@/pages/InvoiceLookup.vue';
import InventoryBalance from '@/pages/InvBal.vue';
import Testpage from '@/pages/Testpage.vue';
import ShipStation from '@/pages/ShipStation.vue';
import ShipStationOrderDetail from '@/pages/ShipStationOrderDetail.vue';
import CreateProduct from '@/pages/CreateProduct.vue';
import PriceLine from '@/pages/PriceLine.vue';
import VendorAdd from '@/pages/VendorAdd.vue';
import ContactPW from '@/pages/ContactPW.vue';
import adminHome from '@/pages/admin/Home.vue';
import adminCompany from '@/pages/admin/Company.vue';
import adminUsers from '@/pages/admin/Users.vue';
import adminMenus from '@/pages/admin/MenuMaint.vue'; // Assuming you have a Menus page
import KohlerFeed from '@/pages/KohlerFeed.vue';
import DataTools from '@/pages/pythonTools.vue';
import WasabiManager from '@/pages/WasabiManager.vue';
import SurchargeCalc from '@/pages/SurchargeCalc.vue';
import LogViewer from '@/pages/admin/Logs.vue'
import Ship54Settings from '@/pages/Ship54Settings.vue'


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
  { path: '/ship54-settings',
    name: 'Ship54 Settings',
    component: Ship54Settings,
    meta: { requiresAuth: true },
  },
  { path: '/kohler-feed',
    name: 'Kohler Feed Report',
    component: KohlerFeed,
    meta: { requiresAuth: true },
  },
  { path: '/create-product',
    name: 'Create Product',
    component: CreateProduct,
    meta: { requiresAuth: true },
  },
  { path: '/price-line',
    name: 'Price Line',
    component: PriceLine,
    meta: { requiresAuth: true },
  },
  { path: '/vendor-add',
    name: 'Add Vendor',
    component: VendorAdd,
    meta: { requiresAuth: true },
  },
    { path: '/data-tools',
    name: 'Data Tools',
    component: DataTools,
    meta: { requiresAuth: true },
  },
    { path: '/manage-files',
    name: 'File Management',
    component: WasabiManager,
    meta: { requiresAuth: true },
  },
    { path: '/surcharge-calc',
    name: 'SurchargeCalc',
    component: SurchargeCalc,
    meta: { requiresAuth: false },
  },
  { 
    path: '/admin/home', 
    name: 'Admin Home', 
    component: adminHome, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/admin/companies', 
    name: 'Company Admin', 
    component: adminCompany, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/admin/users', 
    name: 'User Admin', 
    component: adminUsers, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/admin/menus', 
    name: 'Menu Maintenance', 
    component: adminMenus, 
    meta: { requiresAuth: true } 
  },
    { 
    path: '/admin/logs', 
    name: 'Log Viewer', 
    component: LogViewer, 
    meta: { requiresAuth: true } 
  },

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
