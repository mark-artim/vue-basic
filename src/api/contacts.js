import apiClient from '@/utils/axios';
import axios from '@/utils/axios'

export const searchContacts = async (keyword) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Contacts',
    params: {
      keyword,
      includeTotalItems: true,
    },
  });
  return res.data;
};




export const updateContact = async (contactId, contactData, sessionToken) => {
    try {
      const response = await apiClient.put(
        `/Contacts/${contactId}`,
        contactData,
      );
      return response.data;
    } catch (error) {
      throw new Error('Failed to update the contact. ' + error.response?.data?.message || '');
    }
  };

  export const getContact = async (contactId) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Contacts/${contactId}`,
    // port: 5000  <-- optionally pass if dynamic per user
  });
  return res.data;
};


