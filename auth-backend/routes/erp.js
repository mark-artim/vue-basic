// backend/routes/erp.js
import express from 'express'
import jwt from 'jsonwebtoken'
import redis from '../utils/redisClient.js'
import axios from 'axios'
import { getSalesOrderTotal, postSurchargeLine, postFreightLineItem } from '../services/erpService.js'
import Company from '../models/Company.js' // ✅ Ensure this is available

const router = express.Router()

// Test route to verify server is loading this file
router.get('/test', (req, res) => {
  res.json({ message: 'ERP routes loaded successfully', timestamp: new Date().toISOString() });
});

// Simple test route for invoice line item
router.get('/invoice-line-item-test', (req, res) => {
  res.json({ message: 'Invoice line item route exists!', timestamp: new Date().toISOString() });
});

router.post('/surcharge', async (req, res) => {
  const order = req.body.order || req.query.order
  const companyCode = req.body.companyCode || req.query.companyCode
  const portParam = req.body.port || req.query.port
  // console.log('[DEBUG] Incoming request body:', req.body)
  console.log('[DEBUG] Incoming request query:', req.query)
  console.log('[DEBUG] 🆕 NEW CODE LOADED! File has been updated!', new Date().toISOString())
  console.log('[DEBUG] Incoming order:', order)
  console.log('[DEBUG] Incoming companyCode:', companyCode)
  console.log('[DEBUG] Incoming port:', portParam)

  if (!order || !companyCode) {
    return res.status(400).json({ error: 'MODIFIED! Missing order or companyCode' })
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

router.post('/invoice-line-item', async (req, res) => {
  console.log('🚀 [DEBUG] Invoice line item route hit!', req.body);
  const { invoiceNumber, productId, amount, description } = req.body
  
  if (!invoiceNumber || !productId || !amount) {
    return res.status(400).json({ error: 'Missing required fields: invoiceNumber, productId, amount' })
  }

  try {
    const authHeader = req.headers.authorization
    if (!authHeader) return res.status(401).json({ error: 'Missing JWT' })

    const token = authHeader.split(' ')[1]
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.user = decoded

    const userId = decoded.userId
    const erpToken = await redis.get(`erpToken:${userId}`)
    if (!erpToken) return res.status(401).json({ error: 'Missing ERP token in Redis' })

    // For now, using default values - this should be configurable in the future
    const apiBaseUrl = 'http://192.168.12.88'
    const port = '5000'

    await postFreightLineItem(invoiceNumber, amount, erpToken, apiBaseUrl, port, productId, description)

    return res.json({
      success: true,
      message: 'Freight line item added successfully',
      invoiceNumber,
      productId,
      amount,
      description
    })
  } catch (err) {
    const status = err.response?.status || 500
    const data = err.response?.data || {}
    const attemptedUrl = err.config?.url || 'unknown'

    console.error('❌ [Invoice Line Item Error]', err.message)
    console.error('🔗 Attempted URL:', attemptedUrl)
    if (err.response) {
      console.error('🧾 ERP Response Data:', JSON.stringify(data, null, 2))
    }

    res.status(status).json({
      error: 'Failed to add invoice line item',
      message: data?.message || err.message,
      details: data,
      attemptedUrl
    })
  }
})

// SIMPLE TEST ROUTE - MUST WORK!
router.get('/simple-test', (req, res) => {
  res.json({ success: true, message: 'Simple test route works!' });
});

export default router
