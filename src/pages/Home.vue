<template>
  <div class="home-container">
    <div class="card">
      <h1>Welcome to Beyond Eclipse</h1>
      <p>Select the port you'd like to use for API calls.</p>

      <div class="form-group">
        <label for="port">Choose API Port:</label>
        <select id="port" v-model="selectedPort" @change="savePort">
          <option disabled value="">-- Select a port --</option>
          <option v-for="port in allowedPorts" :key="port.value" :value="port.value">
            {{ port.value }} - {{ port.label }}
          </option>

        </select>
      </div>
      <div v-if="selectedPort" class="current-port">
        <strong>Current Port:</strong> {{ selectedPort }} - {{ selectedPortLabel }}
      </div>
      <v-checkbox
        v-model="apiLogging"
        label="API call logging enabled"
        hide-details
      />
      <h3 v-if="logoutMessage" class="logout-warning">
        {{ logoutMessage }} Logging out in {{ countdown }} seconds...
      </h3>

    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/store/auth'; // Adjust the path as necessary
import { authStatus } from '@/utils/authStatus';
import { watch } from 'vue';

export default {  
  name: 'Home',

  setup() {
    const authStore = useAuthStore(); // ✅ Activate Pinia store
    return {
      authStore, // ✅ RETURN it manually so template can see it
    }
},

  data() {
    return {
      allowedPorts: [
        { value: '5000', label: 'Heritage Production' },
        { value: '5001', label: 'Heritage Train' },
        { value: '5002', label: 'Heritage ECOM' },
        { value: '5003', label: 'Heritage CONV1' },
      ],
      selectedPort: localStorage.getItem('apiPort') || '',
      logoutMessage: '',
      countdown: 5,
      countdownTimer: null,
      apiLogging: sessionStorage.getItem('apiLogging') === 'true'
    };
  },

    computed: {
      selectedPortLabel() {
        const port = this.allowedPorts.find(p => p.value === this.selectedPort);
        return port ? port.label : '';
      }
    },

  watch: {
    apiLogging(val) {
      sessionStorage.setItem('apiLogging', val);
    }
  },

  methods: {
   savePort() {
    localStorage.setItem('apiPort', this.selectedPort);
    this.authStore.port = this.selectedPort; // ✅ Also update Pinia store
    console.log('In auth.js in savePort Port saved to Pinia store:', this.authStore.port);
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
  },

    logoutNow() {
      console.log('Logging out...');
      localStorage.getItem('apiPort'); // Get the latest port from localStorage
      console.log('Logging out but the current API Port is ', this.selectedPort);
      const authStore = useAuthStore(); // ✅ Initialize the store
      authStore.logout();               // ✅ Clear Pinia + localStorage
      this.$router.push('/');
    },
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
}

label {
  font-weight: 500;
  color: #555;
}

select {
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid #ccc;
  font-size: 1rem;
  color: #333
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
