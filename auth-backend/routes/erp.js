import express from 'express'
import jwt from 'jsonwebtoken'
import axios from 'axios'
import { getSalesOrderTotal, postSurchargeLine } from '../services/erpService.js'
import redis from '../utils/redisClient.js'

const router = express.Router()
const ERP_BASE_URL = process.env.ERP_BASE_URL || 'http://localhost:3001'
console.log('[ERP_BASE_URL]', ERP_BASE_URL)

// Middleware for protected routes
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization
  console.log('🔐 [authMiddleware] Authorization Header:', authHeader)

  if (!authHeader) {
    console.warn('⛔ No Authorization header found')
    return res.status(401).json({ error: 'No token provided' })
  }

  const token = authHeader.split(' ')[1]

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    console.log('✅ Decoded JWT:', decoded)
    req.user = decoded
    next()
  } catch (err) {
    console.error('❌ Invalid JWT:', err.message)
    return res.status(403).json({ error: 'Invalid token' })
  }
}

router.post('/surcharge', authMiddleware, async (req, res) => {
  const { order } = req.body
  console.log('🔍 [Surcharge Request] Order:', order)
  console.log('🔍 [Surcharge Request] Headers:', req.headers)
  const jwtToken = req.headers.authorization?.split(' ')[1]
  console.log('🔍 [Surcharge Request] userId:', req.user.userId)
  const erpToken = await redis.get(`erpToken:${req.user.userId}`)
  console.log('🔍 [Surcharge Request] ERP Token from Redis:', erpToken)
    if (!erpToken) {
      return res.status(401).json({ error: 'Missing ERP session token for user' })
    }

  console.log('🔍 [Surcharge Request] Token from redis:', erpToken)
  if (!order) {
    return res.status(400).json({ error: 'Missing order number' })
  }

  try {
    const decoded = jwt.verify(jwtToken, process.env.JWT_SECRET)
    const port = decoded.lastPort || '5000'

    console.log(`📦 Processing surcharge for order: ${order}, port: ${port}`)
    // console.log('🔑 ERP Token from JWT:', decoded.erpToken)
    // console.log('🔗 decoded:', decoded)


    // Step 1: GET the sales order to get the total
    const isLocalhost = ERP_BASE_URL.includes('localhost') || ERP_BASE_URL.includes('127.0.0.1')

    // If NOT localhost, add port to base URL
    const urlwport = isLocalhost ? ERP_BASE_URL : `${ERP_BASE_URL}:${port}`

    console.log('🔗 ERP URL WITH PORT:', urlwport)
    // const orderRes = await axios.post(`${urlwport}/api/erp-proxy`, {
    //   method: 'GET',
    //   url: `/SalesOrders/${order}`,
    //   port
    // }, {
    //   headers: {
    //     Authorization: `Bearer ${token}`
    //     // Authorization: `SessionToken ${decoded.erpToken}`
    //   }
    // })

    // const orderData = orderRes.data
    // const gen = orderData.generations?.[0] || {}
    // console.log('📊 Order data retrieved:', orderData)

    const total = await getSalesOrderTotal(order, erpToken, port)

    
    // OLD const total = gen.salesTotal?.value || gen.priceTotal?.value || 0
    const surcharge = Math.round(total * 0.025 * 100) / 100

    console.log(`💰 Order total: $${total} → Surcharge: $${surcharge}`)

    await postSurchargeLine(order, surcharge, erpToken, port)


    // Step 2: POST the line item
    // const payload = [
    //   {
    //     lineItemProduct: {
    //       productId: 101898,
    //       quantity: 1,
    //       um: 'ea',
    //       umQuantity: 1,
    //       unitPrice: surcharge
    //     }
    //   }
    // ]

    // const lineRes = await axios.post(`${urlwport}/api/erp-proxy`, {
    //   method: 'POST',
    //   url: `/SalesOrders/${order}/LineItems?invoiceNumber=1`,
    //   port,
    //   data: payload
    // }, {
    //   headers: {
    //     Authorization: `Bearer ${token}`
    //     // Authorization: `SessionToken ${decoded.erpToken}`
    //   }
    // })

    // console.log('✅ Line item added:', lineRes.status)
    // res.json({
    //   success: true,
    //   amount: surcharge,
    //   shipToName: gen.shipToName || '',
    //   poNumber: gen.poNumber || ''
    // })


  } catch (err) {
  console.error('❌ [Surcharge Error]', err.message)

  if (err.response) {
    const status = err.response.status
    const attemptedUrl = err.response.data?.attemptedUrl || 'unknown'
    let detailsMessage = 'Unknown error'

    // Try parsing the details field if it's a JSON string
    try {
      const details = JSON.parse(err.response.data?.details || '{}')
      detailsMessage = details.errors?.[0]?.message || 'ERP error occurred'
    } catch (jsonErr) {
      detailsMessage = err.response.data?.details || 'ERP error occurred'
    }

    console.error('🔍 ERP Response:', status, detailsMessage)

    return res.status(status).json({
      error: 'ERP Surcharge Failed',
      message: detailsMessage,
      attemptedUrl
    })
  }

  res.status(500).json({
    error: 'Unexpected server error',
    message: err.message,
    stack: err.stack
  })
}

})

export default router
