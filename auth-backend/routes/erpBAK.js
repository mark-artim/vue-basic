import express from 'express'
import jwt from 'jsonwebtoken'
import redis from '../utils/redisClient.js'
import { getSalesOrderTotal, postSurchargeLine } from '../services/erpService.js'

const router = express.Router()

// Middleware for protected routes
function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization
  if (!authHeader) {
    return res.status(401).json({ error: 'No token provided' })
  }

  const token = authHeader.split(' ')[1]
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.user = decoded
    next()
  } catch (err) {
    console.error('❌ Invalid JWT:', err.message)
    return res.status(403).json({ error: 'Invalid token' })
  }
}

router.post('/surcharge', authMiddleware, async (req, res) => {
  const { order } = req.body
  if (!order) {
    return res.status(400).json({ error: 'Missing order number' })
  }

  try {
    const { userId, lastPort, apiBaseUrl } = req.user
    const port = lastPort || '5000'
    console.log(`📦 Processing surcharge for order ${order} on port ${port}`)

    // ✅ Get ERP token from Redis
    const erpToken = await redis.get(`erpToken:${userId}`)
    if (!erpToken) {
      console.error('❌ No ERP token found in Redis for user:', userId)
      return res.status(401).json({ error: 'Missing ERP token' })
    }

    // ✅ Step 1: Get sales order total
    const total = await getSalesOrderTotal(order, erpToken, apiBaseUrl, port)
    const surcharge = Math.round(total * 0.025 * 100) / 100
    console.log(`💰 Order total: $${total} → Surcharge: $${surcharge}`)

    // ✅ Step 2: Post line item
    await postSurchargeLine(order, surcharge, erpToken, apiBaseUrl, port)

    res.json({
      success: true,
      amount: surcharge,
      message: `Surcharge of $${surcharge} added to order ${order}`
    })

  } catch (err) {
    console.error('❌ [Surcharge Error]', err.message)
    const status = err.response?.status || 500
    const details = err.response?.data || {}
    res.status(status).json({
      error: 'ERP Surcharge Failed',
      message: details.message || err.message,
      details
    })
  }
})

export default router
