import axios from 'axios'

const ERP_BASE_URL = process.env.ERP_BASE_URL || 'http://localhost:3001'

// Optional: if port needs to be included for production
function buildERPUrl(port) {
  if (ERP_BASE_URL.includes('localhost') || ERP_BASE_URL.includes('127.0.0.1')) {
    return `${ERP_BASE_URL}/api/erp-proxy`
  } else {
    return `${ERP_BASE_URL}:${port}/api/erp-proxy`
  }
}

export async function getSalesOrderTotal(order, erpToken, port) {
  const urlx = buildERPUrl(port)
  console.log('🔗 getSalesOrderTotal ERP URL:', urlx)

  const response = await axios.post(urlx, {
    method: 'GET',
    url: `/SalesOrders/${order}`,
  }, {
    headers: {
      Authorization: `SessionToken ${erpToken}`,
    }
  })
  console.log('🔍 getSalesOrderTotal Response:', response.data)
  const gen = response.data.generations?.[0] || {}
  return gen.salesTotal?.value || gen.priceTotal?.value || 0
}

export async function postSurchargeLine(order, amount, erpToken, port) {
  const urlx = buildERPUrl(port)

  const payload = [
    {
      lineItemProduct: {
        productId: 101898,
        quantity: 1,
        um: 'ea',
        umQuantity: 1,
        unitPrice: amount,
      },
    },
  ]

  return axios.post(urlx, {
    method: 'POST',
    url: `/SalesOrders/${order}/LineItems?invoiceNumber=1`,
    data: payload,
  }, {
    headers: {
      Authorization: `SessionToken ${erpToken}`,
      'Content-Type': 'application/json',
    }
  })
}
