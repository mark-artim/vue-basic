import axios from '@/utils/axios'

export const searchPriceLines = async (keyword) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: '/PriceLines',
    params: {
      keyword,
      includeTotalItems: true,
    },
  })
  return res.data
}

export const getPriceLine = async (id) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'GET',
    url: `/PriceLines/${id}`,
  })
  return res.data
}

export const updatePriceLine = async (id, data) => {
  const res = await axios.post('/api/erp-proxy', {
    method: 'PUT',
    url: `/PriceLines/${id}`,
    data,
  })
  return res.data
}
