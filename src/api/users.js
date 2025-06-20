import apiClient from '@/utils/axios'
import axios from '@/utils/axios'

export const getUser = async (userId) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Users/${userId}`,
  });
  return res.data;
};

export const searchUsers = async (keyword) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Users',
    params: {
      keyword,
      includeTotalItems: true,
    },
  });
  return res.data;
};

export const updateUser = async (userId, userData) => {
  try {
    const res = await axios.put(`/Users/${userId}`, userData);
    return res.data;
  } catch (error) {
    throw new Error('Failed to update the user. ' + (error.response?.data?.message || ''));
  }
};

