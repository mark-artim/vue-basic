<template>
  <v-container class="pa-4">
    <v-card class="pa-6 elevation-4">
      <h1>{{ title }}</h1>

      <div class="form-group">
        <label for="port">Select the port you'd like to use for API calls.</label>
        <select id="port" v-model="selectedPort" @change="savePort">
          <option disabled value="">-- Select a port --</option>
          <option v-for="port in allowedPorts" :key="port.value" :value="port.value">
            {{ port.value }} - {{ port.label }}
          </option>
        </select>
      </div>

      <v-checkbox
        v-model="authStore.apiLogging"
        label="API call logging enabled"
        hide-details
        @change="authStore.setApiLogging(authStore.apiLogging)"
      />
      <div>Logging: {{ authStore.apiLogging ? 'ON' : 'OFF' }}</div>


      <h3 v-if="logoutMessage" class="logout-warning">
        {{ logoutMessage }} Logging out in {{ countdown }} seconds...
      </h3>
    </v-card>
  </v-container>
</template>

<script>
import { useAuthStore } from '@/stores/auth';
import { computed } from 'vue';
import apiClient from '@/utils/axios';



export default {
  name: 'Home',

  setup() {
    const authStore = useAuthStore();
    return { authStore };
  },

  data() {
    return {
      allowedPorts: [
        { value: '5000', label: 'Heritage Production' },
        { value: '5001', label: 'Heritage Train' },
        { value: '5002', label: 'Heritage ECOM' },
        { value: '5003', label: 'Heritage CONV1' },
      ],
      selectedPort: this.authStore.port || '',
      logoutMessage: '',
      countdown: 5,
      countdownTimer: null
    };
  },

  computed: {
    selectedPortLabel() {
      const port = this.allowedPorts.find(p => p.value === this.selectedPort);
      return port ? port.label : '';
    },
  title() {
    return this.authStore.companyCode === 'heritage'
      ? 'Welcome to Heritage ERP Portal'
      : 'Welcome to emp54';
  }
  },

  methods: {
    async savePort() {
      try {
        // const userId = this.authStore.user._id; // or userId if flat
        const userId = this.authStore.userId; // or userId if flat
        const port = this.selectedPort;
        console.log('Saving port:', port, 'for user:', userId);

        // ✅ Send to backend to persist in Mongo
        await apiClient.put(`/admin/users/${userId}/port`, { port });

        this.logoutMessage = 'Port changed. Please log in again.';
        this.countdown = 5;

        if (this.countdownTimer) clearInterval(this.countdownTimer);

        this.countdownTimer = setInterval(() => {
          if (this.countdown <= 1) {
            clearInterval(this.countdownTimer);
            this.logoutNow();
          } else {
            this.countdown--;
          }
        }, 1000);
      } catch (err) {
        console.error('Failed to save port:', err);
        alert('Could not save your selected port. Please try again.');
      }
    },


    logoutNow() {
      console.log('Logging out...');
      const authStore = useAuthStore();
      authStore.logout();
      this.$router.push('/');
    }
  }
};
</script>

<style scoped>
.home-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  min-height: 100vh;
  background-color: black;
  font-family: 'Segoe UI', sans-serif;
}

.card {
  color: orange;
  background-color: white;
  padding: 2rem 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.card h1 {
  margin-bottom: 0.5rem;
  font-size: 1.75rem;
  color: #333;
}

.card p {
  margin-bottom: 1.5rem;
  color: #666;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
  color: #007bff;
}

label {
  font-weight: 500;
  color: #555;
  color: white;

}

select {
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 1rem;
  color: #007bff
}

.current-port {
  margin-top: 1.5rem;
  font-size: 1rem;
  color: #007bff;
}

.logout-warning {
  color: #dc3545;
  font-weight: bold;
  margin-top: 1rem;
}
</style>
