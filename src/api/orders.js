// orders.js
import axios from '@/utils/axios';

export const searchOrders = async ({ params = {} } = {}) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/SalesOrders',
    params, // Pass params directly into the proxy
  });

  return res.data;
};

// const { data } = await apiClient.get(`/SalesOrders/${invoice}`)

export const getOrder = async (invoice) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/SalesOrders/${invoice}`,
  });

  return res.data;
};