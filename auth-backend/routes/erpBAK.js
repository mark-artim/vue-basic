import express from 'express'
import jwt from 'jsonwebtoken'
import axios from 'axios'
import { getSalesOrderTotal, postSurchargeLine } from '../services/erpService.js'

const router = express.Router()
const ERP_BASE_URL = process.env.ERP_BASE_URL || 'http://localhost:3001'
console.log('[ERP_BASE_URL]', ERP_BASE_URL)
// const decoded = jwt.verify(jwtToken, process.env.JWT_SECRET)
// const port = decoded.lastPort || '5000'
// const URL = `${ERP_BASE_URL}:${port}`
// console.log('[ERP URL WITH PORT]', URL)

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
  const jwtToken = req.headers.authorization?.split(' ')[1]

  if (!order) {
    return res.status(400).json({ error: 'Missing order number' })
  }

  try {
    const decoded = jwt.verify(jwtToken, process.env.JWT_SECRET)
    const port = decoded.lastPort || '5000'
    const erpToken = decoded.erpToken

    if (!erpToken) {
      return res.status(401).json({ error: 'Missing ERP session token' })
    }

    const total = await getSalesOrderTotal(order, erpToken, port)
    const surcharge = Math.round(total * 0.025 * 100) / 100

    await postSurchargeLine(order, surcharge, erpToken, port)

    res.json({ success: true, amount: surcharge })
  } catch (err) {
    console.error('❌ [Surcharge Error]', err.message)
    if (err.response) {
      const status = err.response.status || 500
      const message = err.response.data?.message || 'ERP error'
      return res.status(status).json({ error: 'ERP Surcharge Failed', message })
    }
    res.status(500).json({ error: 'Unexpected server error', message: err.message })
  }
})

export default router
