import apiClient from '@/utils/axios';

export const createSession = async (username, password) => {
  try {
    console.log('[api/auth.js] About to POST to /Sessions via apiClient.');
    const response = await apiClient.post('/Sessions', {
      username,
      password,
    });
    console.log('[api/auth.js] Session created:', response.data);
    return response.data;
  } catch (error) {
    console.error('[api/auth.js] Login error:', error);
    throw new Error('Invalid username or password');
  }
};

export const destroySession = async (sessionId, sessionToken) => {
  try {
    await apiClient.delete(`/Sessions/${sessionId}`, {
      headers: { sessionToken },
    });
  } catch (error) {
    console.error('[api/auth.js] Logout error:', error);
  }
};
