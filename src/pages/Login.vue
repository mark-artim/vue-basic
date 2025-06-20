<template>
    <v-container>
      <v-form @submit.prevent="login">
        <v-text-field
          v-model="username"
          label="Username"
          outlined
          required
        />
        <v-text-field
          v-model="password"
          label="Password"
          type="password"
          outlined
          required
        />
        <v-btn type="submit" color="primary" class="mt-4">Login</v-btn>
      </v-form>
      <v-alert v-if="error" type="error" class="mt-2">{{ error }}</v-alert>
    </v-container>
  </template>
  
  <script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

export default {
  setup() {
    const username = ref('');
    const password = ref('');
    const error = ref('');
    const router = useRouter();
    const authStore = useAuthStore();

    const login = async () => {
      error.value = ''
      try {
        const { isAdmin } = await authStore.login(username.value, password.value);
        console.log('[router] routing to', isAdmin ? '/admin/home' : '/home')
        router.push(isAdmin ? '/admin/home' : '/home');
      } catch (err) {
        error.value = 'Login failed. Please check your credentials.';
      }
    };

    return { username, password, error, login };
  },
};
</script>

  
  <style scoped>
  .v-container {
    max-width: 400px;
    margin: 100px auto;
  }
  </style>
  
  