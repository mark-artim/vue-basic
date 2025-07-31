import express from 'express'
import User from '../models/User.js'
import bcrypt from 'bcrypt'
import axios from 'axios'
import { generateToken } from '../utils/jwt.js'
import redis from '../utils/redisClient.js'
import { logEvent } from '../services/logService.js';

const router = express.Router()
console.log('[*****BACKEND Auth Route Hit******] POST /login')

router.post('/login', async (req, res) => {
  const { email, password } = req.body
  const user = await User.findOne({ email }).populate('companyId')

  if (!user) return res.status(404).json({ error: 'User not found' })

  const userType = user.userType

  if (user.userType === 'admin') {
    const match = await bcrypt.compare(password, user.hashedPassword)
    if (!match) return res.status(401).json({ error: 'Invalid credentials' })
    const token = generateToken(user, null, userType)

    await logEvent({
      userId: user._id,
      userEmail: user.email,
      companyId: user.companyId._id,
      companyCode: user.companyId.companyCode,
      type: 'login',
      source: 'auth-backend',
      message: 'Admin user logged in',
      meta: {
        ip: req.ip,
        method: 'internal-password'
      }
    });

    return res.json({ token })

  }

  if (user.userType === 'customer') {
    try {
      const { erpUserName, lastPort, companyId } = user
      const { apiBaseUrl } = companyId

      console.log(`[ERP Login] Using API base URL: ${apiBaseUrl}`)
      console.log('erpUserName : ', erpUserName)
      console.log('lastPort : ', lastPort)

      const erpRes = await axios.post(`${apiBaseUrl}:${lastPort}/Sessions`, {
        username: erpUserName,
        password: password
      })

      console.log('[ERP Login] ERP Response:', erpRes.data)

      const erpToken = erpRes?.data?.sessionToken
      if (!erpToken) {
        console.error('[ERP Login Error] Missing ERP session token in ERP response')
        return res.status(401).json({ error: 'Missing ERP session token in ERP response' })
      }

      // ✅ Store ERP token in Redis (keyed by user ID)
      await redis.set(`erpToken:${user._id}`, erpToken, { ex: 7200 })

      const token = generateToken(user, null, userType)
      console.log('[ERP Login Success] Token generated:', token)

      await logEvent({
        userId: user._id,
        userEmail: user.email,
        companyId: user.companyId._id,
        companyCode: user.companyId.companyCode,
        type: 'login',
        source: 'auth-backend',
        message: 'Customer user logged in via ERP',
        meta: {
          ip: req.ip,
          method: 'erp-session',
          erpPort: lastPort
        }
      });

      return res.json({ token })
    } catch (err) {
      await logEvent({
        userId: user._id,
        userEmail: user.email,
        companyId: user.companyId._id,
        companyCode: user.companyId.companyCode,
        type: 'login-failure',
        source: 'auth-backend',
        message: 'ERP login failed',
        meta: {
          ip: req.ip,
          method: 'erp-session',
          error: err?.message,
          erpResponse: err?.response?.data
        }
      });

      console.error('[ERP Login Error!]', err?.response?.data || err.message)
      console.error('[ERP Login Stack]', err.stack);
      return res.status(401).json({ error: 'ERP login failed' })
    }
  }
})

export default router
