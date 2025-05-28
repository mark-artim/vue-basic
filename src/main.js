import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import router from './router';
import vuetify from './plugins/vuetify';

const app = createApp(App)
const pinia = createPinia()

app.use(pinia).use(router).use(vuetify)       // ✅ Only place you call app.use(pinia)
app.mount('#app')

// Hydrate store after pinia is active
import { useAuthStore } from '@/store/auth'
const authStore = useAuthStore()
authStore.hydrate()
