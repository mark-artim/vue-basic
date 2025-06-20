// src/api/customers.js
import apiClient from '@/utils/axios';
import axios from '@/utils/axios'

export const searchCustomers = async (keyword) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Customers',
    params: {
      keyword,
      includeTotalItems: true,
    },
  });
  return res.data;
};

export const getCustomer = async (customerId) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Customers/${customerId}`,
  });
  return res.data;
};



// Create a new customer - OLD STYLE _ NEEDS TO BE CHANGED

// export const createCustomer = async (vendorData, sessionToken) => {
//   return await axios.post('/Customers', vendorData, {
//     headers: {
//       Authorization: `SessionToken ${sessionToken}`
//     }
//   });
// };