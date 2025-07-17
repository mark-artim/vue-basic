// backend/services/erpService.js
import axios from 'axios'

// 🔧 Builds the correct ERP base URL with optional port
function buildERPUrl(apiBaseUrl, port) {
  if (apiBaseUrl.includes('localhost') || apiBaseUrl.includes('127.0.0.1')) {
    return `${apiBaseUrl}`
  } else {
    return `${apiBaseUrl}:${port}`
  }
}

// ✅ GET the sales order total directly from ERP
export async function getSalesOrderTotal(order, erpToken, apiBaseUrl, port) {
  const fullUrl = `${buildERPUrl(apiBaseUrl, port)}/SalesOrders/${order}`
  console.log('🔗 [getSalesOrderTotal] URL:', fullUrl)

  const response = await axios.get(fullUrl, {
    headers: {
      Authorization: `SessionToken ${erpToken}`,
    },
  })

  const gen = response.data.generations?.[0] || {}
  return gen.salesTotal?.value || gen.priceTotal?.value || 0
}

// ✅ POST a surcharge line directly to ERP
export async function postSurchargeLine(order, amount, erpToken, apiBaseUrl, port) {
  const fullUrl = `${buildERPUrl(apiBaseUrl, port)}/SalesOrders/${order}/LineItems?invoiceNumber=1`
  console.log('🔗 [postSurchargeLine] URL:', fullUrl)

  const payload = [
    {
      lineItemProduct: {
        productId: 101898, // Surcharge item ID
        quantity: 1,
        um: 'ea',
        umQuantity: 1,
        unitPrice: amount,
      },
    },
  ]

  return axios.post(fullUrl, payload, {
    headers: {
      Authorization: `SessionToken ${erpToken}`,
      'Content-Type': 'application/json',
    },
  })
}
