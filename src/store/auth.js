import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    sessionToken: '',
    sessionId: '',
    port: localStorage.getItem('apiPort') || '5000',
  }),
  getters: {
    portLabel: (state) => {
      const labels = {
        '5000': 'Production',
        '5001': 'Train',
        '5002': 'ECOM',
        '5003': 'CONV1',
      }
      return labels[state.port] || 'Unknown'
    }
  },
  actions: {
    login(token, id, userName) {
      this.isAuthenticated = true;
      this.sessionToken = token;
      this.sessionId = id;
      this.userName = userName;
      localStorage.setItem('SessionToken', token);
      localStorage.setItem('SessionId', id);
      console.log('Hey im in store/auth.js and SessionToken is ', token);
      console.log('Hey im in store/auth.js and userName is ', userName);
    },
    logout() {
      this.isAuthenticated = false;
      this.sessionToken = '';
      this.sessionId = '';
      this.username = '';
      localStorage.removeItem('SessionToken');
      localStorage.removeItem('SessionId');
    },
    initialize() { // 🆕 ADD THIS METHOD
      const token = localStorage.getItem('SessionToken');
      const id = localStorage.getItem('SessionId');
      const port = localStorage.getItem('apiPort') || '5000';
      console.log('Hey im in store/auth.js in the initialize method.');
      if (token) {
        this.isAuthenticated = true;
        this.sessionToken = token;
        this.sessionId = id;
        this.port = port;
        console.log('Hey im in store/auth.js in initialize and there must be a token: ', token);
      }
    }
  }
});
