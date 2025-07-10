import axios from '@/utils/axios'

export const getTerritory = async (id) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/Territories/${id}`,
  })
  return res.data
}
