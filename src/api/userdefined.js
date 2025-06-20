import axios from '@/utils/axios'

export const getUserDefined = async (id) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/UserDefined/${id}`,
  });
  return res.data;
}