// backend/services/erpService.js
import axios from 'axios'

// 🔧 Build the full ERP base URL with port
function buildERPUrl(apiBaseUrl, port) {
  if (apiBaseUrl.includes('localhost') || apiBaseUrl.includes('127.0.0.1')) {
    return `${apiBaseUrl}`
  } else {
    return `${apiBaseUrl}:${port}`
  }
}

// ✅ GET: Retrieve the sales order total
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

// ✅ POST: Add a surcharge line item
export async function postSurchargeLine(order, amount, erpToken, apiBaseUrl, port, productId) {
  const fullUrl = `${buildERPUrl(apiBaseUrl, port)}/SalesOrders/${order}/LineItems?invoiceNumber=1`
  console.log('🔗 [postSurchargeLine] URL:', fullUrl)

  const payload = [
    {
      lineItemProduct: {
        productId: productId, // Dynamic based on config
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

// ✅ POST: Add a freight line item to invoice
export async function postFreightLineItem(order, amount, erpToken, apiBaseUrl, port, productId, description) {
  const fullUrl = `${buildERPUrl(apiBaseUrl, port)}/SalesOrders/${order}/LineItems?invoiceNumber=1`
  console.log('🔗 [postFreightLineItem] URL:', fullUrl)

  const payload = [
    {
      lineItemProduct: {
        productId: productId,
        quantity: 1,
        um: 'ea',
        umQuantity: 1,
        unitPrice: amount,
        description: description,
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
