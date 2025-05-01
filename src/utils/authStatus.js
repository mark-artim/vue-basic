// src/store/authStatus.js
import { reactive } from 'vue';

export const authStatus = reactive({
  sessionExpired: false,
});
