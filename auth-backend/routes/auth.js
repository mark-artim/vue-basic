import express from 'express'
import User from '../models/User.js'
import bcrypt from 'bcrypt'
import axios from 'axios'
import { generateToken } from '../utils/jwt.js'
import redis from '../utils/redisClient.js'

const router = express.Router()
console.log('[*****BACKEND Auth Route Hit******] POST /login')

router.post('/login', async (req, res) => {
  const { email, password } = req.body
  const user = await User.findOne({ email }).populate('companyId')
  // console.log('[Login Attempt]', {
  //   email,
  //   userType: user?.userType,
  //   companyId: user?.companyId?._id || user.companyId
  // }) REALLY FUCKED UP THE INSTALL ON RAILWAY

  if (!user) return res.status(404).json({ error: 'User not found' })

  const userType = user.userType

  if (user.userType === 'admin') {
    const match = await bcrypt.compare(password, user.hashedPassword)
    if (!match) return res.status(401).json({ error: 'Invalid credentials' })
    const token = generateToken(user, null, userType)
    // console.log('[JWT Payload (here is what is s in teh jwt)]', jwt.decode(token))
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


      return res.json({ token })
    } catch (err) {
      console.error('[ERP Login Error!]', err?.response?.data || err.message)
      console.error('[ERP Login Stack]', err.stack);
      return res.status(401).json({ error: 'ERP login failed' })
    }
  }
})

export default router
