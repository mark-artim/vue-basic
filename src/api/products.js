import axios from '@/utils/axios';

export const searchProducts = async (query) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Products',
    params: {
      keyword: query,
      includeInactive: true,
      pageSize: 50
    }
  });

  return res.data;
};

export const getProduct = async (productId) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Products/${productId}`
  });

  return res.data;
};