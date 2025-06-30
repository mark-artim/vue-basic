import apiClient from '@/utils/axios';

export const fetchShipViaGroup = async (keyword) => {
  const res = await apiClient.get('/ShipVias', { params: { keyword } });
  return res.data || [];
};
