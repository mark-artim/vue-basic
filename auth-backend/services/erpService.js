import axios from 'axios'

const ERP_BASE_URL = process.env.ERP_BASE_URL || 'http://localhost:3001'

// Optional: if port needs to be included for production
function buildERPUrl(path, port) {
  if (ERP_BASE_URL.includes('localhost') || ERP_BASE_URL.includes('127.0.0.1')) {
    return `${ERP_BASE_URL}/api/erp-proxy`
  } else {
    return `${ERP_BASE_URL}:${port}/api/erp-proxy`
  }
}

export async function getSalesOrderTotal(order, erpToken, port = '5000') {
  const url = buildERPUrl(`/SalesOrders/${order}`, port)

  const response = await axios.post(url, {
    method: 'GET',
    url: `/SalesOrders/${order}`,
    port,
  }, {
    headers: {
      Authorization: `Bearer ${erpToken}`,
    }
  })

  const gen = response.data.generations?.[0] || {}
  return gen.salesTotal?.value || gen.priceTotal?.value || 0
}

export async function postSurchargeLine(order, amount, erpToken, port = '5000') {
  const url = buildERPUrl(`/SalesOrders/${order}/LineItems?invoiceNumber=1`, port)

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

  return axios.post(url, {
    method: 'POST',
    url: `/SalesOrders/${order}/LineItems?invoiceNumber=1`,
    port,
    data: payload,
  }, {
    headers: {
      Authorization: `Bearer ${erpToken}`,
      'Content-Type': 'application/json',
    }
  })
}
