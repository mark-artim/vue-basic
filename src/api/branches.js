import axios from '@/utils/axios'
import apiClient from '@/utils/axios'

export const searchBranches = async (keyword) => {
  const res = await apiClient.post('/api/erp-proxy', {
    method: 'GET',
    url: '/Branches',
    params: {
      keyword,
      includeTotalItems: true,
    },
  });
  return res.data;
};

  export const getBranch = async (branchId) => {
  const res = await apiClient.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Branches/${branchId}`,
    // port: 5000  <-- optionally pass if dynamic per user
  });
  return res.data;
};


