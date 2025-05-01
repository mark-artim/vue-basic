<template>
  <MainLayout />
</template>

<script setup>
import { onMounted } from 'vue';
import axios from '@/utils/axios';
import { authStatus } from '@/utils/authStatus';
import MainLayout from './layouts/MainLayout.vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();

onMounted(() => {
  authStore.initialize(); // ✅ this reloads session from localStorage
  setInterval(async () => {
    try {
      await axios.get('/UserDefined/PING');
      authStatus.sessionExpired = false;
    } catch (error) {
      if (error.response && error.response.status === 401) {
        console.warn('Session expired detected!');
        authStatus.sessionExpired = true;
      }
    }
  }, 5 * 60 * 1000);
});
</script>

