import jwt from 'jsonwebtoken'

export function authMiddleware(req, res, next) {
  // console.log('🔐 [authMiddleware] Incoming Request:', req.method, req.path)
  // console.log('🔐 [authMiddleware] Request Headers:', req.headers)
  // console.log('🔐 [authMiddleware] Request Body:', req.body)
  // console.log('🔐 [authMiddleware] Request Query:', req)
  const authHeader = req.headers.authorization
  console.log('🔐 [authMiddleware] Authorization Header:', authHeader)

  if (!authHeader) {
    console.warn('⛔ No Authorization header found')
    return res.status(401).send({ error: 'No token provided' })
  }

  const token = authHeader.split(' ')[1]
  if (!token) {
    console.warn('⛔ Malformed Authorization header:', authHeader)
    return res.status(401).send({ error: 'Malformed token' })
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    console.log('✅ JWT decoded:', decoded)

    req.user = decoded
    next()
  } catch (err) {
    console.error('❌ Invalid or expired JWT:', err.message)
    return res.status(403).send({ error: 'Invalid token' })
  }
}

