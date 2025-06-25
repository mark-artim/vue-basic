import express from 'express';
import jwt from 'jsonwebtoken';
import erpClient from '../utils/erpClient.js';
import redis from '../utils/redisClient.js';

const router = express.Router();

router.get('/me', async (req, res) => {
  const log = req.headers['x-api-logging'] === 'true';
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Missing auth token' });

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    if (log) console.log('[usersErp/me] Decoded JWT:', decoded);

    const userId = decoded.userId; // matches generateToken()
    const erpUserName = decoded.erpUserName;

    if (!userId || !erpUserName) {
      return res.status(401).json({ error: 'Invalid token payload' });
    }

    // Attach ERP token to request (used by erpProxy internally)
    req.erpToken = await redis.get(`erpToken:${userId}`);
    if (log) console.log(`[usersErp/me] ERP token retrieved for user ${userId}`);
    if (!req.erpToken) {
      return res.status(401).json({ error: 'ERP session expired or not found' });
    }
    const client = erpClient({
      baseUrl: process.env.ERP_API_BASE,
      port: decoded.lastPort || 5000,
      token: req.erpToken,
      log
    });

    const { data } = await client.get(`/Users/${erpUserName}`);

    if (log) console.log(`[usersErp/me] ERP response received`);

    res.json(data);
  } catch (err) {
    console.error('❌ /me route failed:', err.message || err);
    res.status(500).json({ error: 'Failed to fetch ERP user' });
  }
});

// router.get('/:userName', async (req, res) => {
//   try {
//     const { data } = await erpProxy(req).get(`/Users/${req.params.userName}`);
//     res.json(data);
//   } catch (err) {
//     console.error('❌ ERP user fetch failedA:', err.message || err);
//     res.status(500).json({ error: 'Failed to fetch user info' });
//   }
// });

router.get('/:userName', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '')
    if (!token) return res.status(401).json({ error: 'Missing auth token' })

    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    const userId = decoded.userId
    const port = decoded.lastPort || 5000

    const erpToken = await redis.get(`erpToken:${userId}`)
    if (!erpToken) return res.status(401).json({ error: 'ERP session expired or missing' })

    const client = erpClient({
      baseUrl: process.env.ERP_API_BASE,
      port,
      token: erpToken
    })

    const { data } = await client.get(`/Users/${req.params.userName}`)
    res.json(data)
  } catch (err) {
    console.error('❌ ERP user fetch failed:', err.message || err)
    res.status(500).json({ error: 'Failed to fetch user info' })
  }
})


export default router;
