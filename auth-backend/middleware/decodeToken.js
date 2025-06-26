import jwt from 'jsonwebtoken'

const decodeToken = (req, res, next) => {
  const authHeader = req.headers.authorization

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid token' })
  }

  const token = authHeader.replace('Bearer ', '')

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    req.user = decoded
    next()
  } catch (err) {
    console.error('[decodeToken] JWT error:', err)
    res.status(401).json({ error: 'Invalid token' })
  }
}

export default decodeToken
