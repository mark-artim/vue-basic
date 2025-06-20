import express from 'express'
import axios from 'axios'
import jwt from 'jsonwebtoken'
import User from '../models/User.js'
import redisClient from '../utils/redisClient.js' // ✅ Upstash Redis client

const router = express.Router()

router.post('/', async (req, res) => {
  // see if logging is enabled
  const logEnabled = req.headers['x-api-logging'] === 'true';
  if (logEnabled) {
    console.log('[ERP Proxy] ✅ Logging enabled for this request');
  }

  // Step 1: Validate JWT
  if (logEnabled) console.log('[ERP Proxy] POST /erp-proxy route validating JWT token...') 
  const authHeader = req.headers.authorization
  if (!authHeader) {
    return res.status(401).json({ error: 'Missing Authorization header' })
  }

  const token = authHeader.split(' ')[1]
  let decoded

  try {
    decoded = jwt.verify(token, process.env.JWT_SECRET)
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' })
  }

  // Step 2: Get user and company
  const user = await User.findById(decoded.userId).populate('companyId')
  if (!user || !user.companyId) {
    return res.status(401).json({ error: 'Invalid user or missing company data' })
  }

  // Step 3: Get ERP token from Redis (Upstash)
  const redisKey = `erpToken:${decoded.userId}`
  let erpToken
  try {
    erpToken = await redisClient.get(redisKey)
  } catch (err) {
    console.error(`[ERP Proxy] Redis error for key ${redisKey}:`, err)
    return res.status(500).json({ error: 'Redis error retrieving ERP token' })
  }

  if (!erpToken) {
    return res.status(401).json({ error: 'ERP token not found or expired. Please re-login.' })
  }

  // Step 4: Build outgoing ERP request
  const { method = 'GET', url, data = {}, params = {}, port } = req.body
  const baseUrl = user.companyId.apiBaseUrl
  const finalPort = port || user.lastPort || 5000
  const fullUrl = `${baseUrl}:${finalPort}${url}`

  try {
    if (logEnabled) {
      console.log('[ERP Proxy] Logging enabled - request details:', {
        method,
        url: fullUrl,
        data,
        params,
        userId: decoded.userId,
        companyId: user.companyId._id,
      })
    }
    // console.log('[ERP Proxy] ERP Token from Redis:', erpToken?.substring(0, 30), '...')
    // console.log(`[ERP Proxy] Forwarding request to ERP: ${method} ${fullUrl}`, {
    //   data,
    //   params,
    // })
    const erpResponse = await axios({
      method,
      url: fullUrl,
      headers: {
        Authorization: `SessionToken ${decodeURIComponent(erpToken)}`,
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      timeout: 30000,
      data,
      params,
    })

    res.json(erpResponse.data)
  } catch (err) {
  const errorData = err.response?.data || {};
  const status = err?.response?.status
  const message = errorData.message || JSON.stringify(errorData) || err.message
  const fullUrlSafe = `${baseUrl}:${finalPort}${url}`

  console.error('[ERP Proxy Error]', {
    status,
    url: fullUrlSafe,
    method,
    params,
    data,
    erpToken: erpToken?.substring(0, 10) + '...', // hide most of token
    errorMessage: message,
  })

  return res.status(status || 500).json({
    error: 'ERP Request Failed',
    status,
    details: message,
    attemptedUrl: fullUrlSafe,
  })
  }
})

export default router
