import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    sessionToken: '',
    sessionId: '',
  }),
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
      console.log('Hey im in store/auth.js in teh initialize method.');
      if (token) {
        this.isAuthenticated = true;
        this.sessionToken = token;
        this.sessionId = id;
        console.log('Hey im in store/auth.js in initialize and there must be a token: ', token);
      }
    }
  }
});
