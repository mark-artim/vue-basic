import apiClient from '@/utils/axios';

export const createSession = async (username, password) => {
  try {
    console.log('[auth.js] Creating session...');
    const response = await apiClient.post('/Sessions', {
      username,
      password,
    });
    console.log('[auth.js] Session created:', response.data);
    return response.data;
  } catch (error) {
    console.error('[auth.js] Login error:', error);
    throw new Error('Invalid username or password');
  }
};

export const destroySession = async (sessionId, sessionToken) => {
  try {
    await apiClient.delete(`/Sessions/${sessionId}`, {
      headers: { sessionToken },
    });
  } catch (error) {
    console.error('[auth.js] Logout error:', error);
  }
};
