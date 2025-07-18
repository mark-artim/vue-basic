// backend/routes/erp.js
import express from 'express'
import jwt from 'jsonwebtoken'
import redis from '../utils/redisClient.js'
import axios from 'axios'
import { getSalesOrderTotal, postSurchargeLine } from '../services/erpService.js'
import Company from '../models/Company.js' // ✅ Ensure this is available

const router = express.Router()

router.post('/surcharge', async (req, res) => {
  const order = req.body.order || req.query.order
  const companyCode = req.body.companyCode || req.query.companyCode
  const portParam = req.body.port || req.query.port
  // console.log('[DEBUG] Incoming request body:', req.body)
  console.log('[DEBUG] Incoming request query:', req.query)
  console.log('[DEBUG] Incoming order:', order)
  console.log('[DEBUG] Incoming companyCode:', companyCode)
  console.log('[DEBUG] Incoming port:', portParam)

  if (!order || !companyCode) {
    return res.status(400).json({ error: 'Missing order or companyCode' })
  }

  try {
    const company = await Company.findOne({ companyCode })
    console.log('[DEBUG] Found company:', company)
    if (!company) return res.status(404).json({ error: 'Company not found' })

    const apiBaseUrl = company.apiBaseUrl
    const port = portParam || company.apiPorts?.[0] || '5000'
    const authMethod = company.surcharge?.authMethod || 'loggedInUser'
    if (!company.surcharge.productsByPort.get(port)) {
      console.error(`❌ No surcharge product configured for port ${port}`)
      return res.status(400).json({ error: `No surcharge product for port ${port}` })
    }
    const productId = company.surcharge.productsByPort.get(port)


    let erpToken

    if (authMethod === 'apiUser') {
      console.log('🔐 Attempting ERP login with stored API user:', {
        username: company.surcharge.apiUser?.username,
        passwordSet: company.surcharge.apiUser?.password
      })
      const creds = company.surcharge?.apiUser
      if (!creds?.username || !creds?.password) {
        return res.status(400).json({ error: 'Missing stored ERP credentials' })
      }
      const sessionRes = await axios.post(`${apiBaseUrl}:${port}/Sessions`, {
        username: creds.username,
        password: creds.password,
      })
      erpToken = sessionRes.data.sessionToken
    } else {
      const authHeader = req.headers.authorization
      if (!authHeader) return res.status(401).json({ error: 'Missing JWT' })

      const token = authHeader.split(' ')[1]
      const decoded = jwt.verify(token, process.env.JWT_SECRET)
      req.user = decoded

      const userId = decoded.userId
      erpToken = await redis.get(`erpToken:${userId}`)
      if (!erpToken) return res.status(401).json({ error: 'Missing ERP token in Redis' })
    }

    // ✅ Compute surcharge
    const total = await getSalesOrderTotal(order, erpToken, apiBaseUrl, port)
    const surcharge = Math.round(total * 0.025 * 100) / 100
    await postSurchargeLine(order, surcharge, erpToken, apiBaseUrl, port, productId)

    return res.json({
      success: true,
      order,
      port,
      companyCode,
      amount: surcharge,
    })
  } catch (err) {
      const status = err.response?.status || 500
      const data = err.response?.data || {}
      const attemptedUrl = err.config?.url || 'unknown'

      console.error('❌ [Surcharge Error]', err.message)
      console.error('🔗 Attempted URL:', attemptedUrl)
      if (err.response) {
        console.error('🧾 ERP Response Data:', JSON.stringify(data, null, 2))
      }
      console.error('📛 Stack Trace:', err.stack)

      res.status(status).json({
        error: 'ERP Surcharge Failed',
        message: data?.message || err.message,
        details: data,
        attemptedUrl
      })
    }

  
})

export default router
