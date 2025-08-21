import apiClient from '@/utils/axios';

export const fetchShipViaGroup = async (keyword) => {
  const res = await apiClient.post('/api/erp-proxy', {
    method: 'GET',
    url: '/ShipVias',
    params: { keyword }
  });
  return res.data || [];
};
