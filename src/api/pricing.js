import axios from '@/utils/axios'

// apiClient.get(`/ProductPricingMassInquiry?${queryParams}`

export const productPricingMassInquiry = async (queryParams) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/ProductPricingMassInquiry?${queryParams}`,
    // params: {
    //   queryParams
    // },
  });
  return res.data;
}