import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
// import store from './store';
import vuetify from './plugins/vuetify';
import { createPinia } from 'pinia';

const pinia = createPinia();

createApp(App).use(router).use(pinia).use(vuetify).mount('#app');
