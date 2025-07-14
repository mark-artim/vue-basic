import axios from 'axios'

const BASE_URL = 'http://192.168.12.85:5000'

export async function getSalesOrderTotal(order, token) {
  const res = await axios.get(`${BASE_URL}/SalesOrders/${order}`, {
    headers: {
      Authorization: `SessionToken ${token}`,
    },
  })

  // Adjust based on ERP structure
  return res.data.totalNetAmount || res.data.orderTotal || 0
}

export async function postSurchargeLine(order, amount, token) {
  const payload = [
    {
      lineItemProduct: {
        productId: 101898, // Surcharge product
        quantity: 1,
        um: 'ea',
        umQuantity: 1,
        unitPrice: amount,
      },
    },
  ]

  await axios.post(`${BASE_URL}/SalesOrders/${order}/LineItems?invoiceNumber=1`, payload, {
    headers: {
      Authorization: `SessionToken ${token}`,
      'Content-Type': 'application/json',
      Accept: 'text/plain',
    },
  })
}
