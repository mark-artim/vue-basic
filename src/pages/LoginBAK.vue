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
  import { createSession } from '../api/auth';
  
  export default {
    setup() {
      const username = ref('');
      const password = ref('');
      const error = ref('');
      const router = useRouter();
      const authStore = useAuthStore();

  authStore.hydrate(); // ✅ Re-sync from localStorage immediately
  
      const login = async () => {
        try {
          const session = await createSession(username.value, password.value);
          console.log('Session:', session);
          authStore.login(session.sessionToken, session.id, session.sessionUser.userName);
          router.push('/home');
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
  
  