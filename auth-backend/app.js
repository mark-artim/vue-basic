import express from 'express'
import mongoose from 'mongoose'
import dotenv from 'dotenv'
import erpProxyRoutes from './routes/erpProxy.js'
import authRoutes from './routes/auth.js'
import cors from 'cors'
import companyRoutes from './routes/companies.js'
import userRoutes from './routes/users.js'
import usersErp from './routes/usersErp.js'
import emailRoutes from './routes/email.js'
import { c } from 'node_modules/unplugin-vue-router/dist/types-DBiN4-4c.js'


dotenv.config()

const app = express()

// CORS configuration
const allowedOrigins = [
  'http://localhost:3000',
  'https://vue-basic-flame.vercel.app',
  'https://vue-basic-mark-artims-projects.vercel.app'
];

console.log('[Mounting] CORS middleware with allowed origins:', allowedOrigins);
app.use(cors({
  origin: function (origin, callback) {
    console.log('[CORS] Incoming Origin:', origin)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true)
    } else {
      console.warn('[CORS] Blocked Origin:', origin)
      callback(new Error('Not allowed by CORS: ' + origin))
    }
  },
  credentials: true
}))

// app.options('*', cors())
console.log('FUCK')
app.use(express.json())
console.log('OFF')
console.log('[ENV] MONGODB_URI =', process.env.MONGODB_URI)
console.log('[DB] Attempting MongoDB connection...')

mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('[DB] Connected to MongoDB Atlas'))
.catch(err => console.error('[DB] MongoDB connection error:', err))

// Add this before your route mounts
app.use((req, res, next) => {
  console.log(`[Route Validation] ${req.method} ${req.path}`)
  if (req.path.includes(':')) {
    const parts = req.path.split('/')
    parts.forEach(part => {
      if (part.startsWith(':') && part.length === 1) {
        throw new Error(`Invalid route parameter in path: ${req.path}`)
      }
    })
  }
  next()
})


console.log('[app.js] Mounting ERP Proxy route at /api/erp-proxy')
app.use('/api/erp-proxy', erpProxyRoutes)
console.log('[app.js] ERP Proxy route registered')
console.log('[app.js] Mounting Auth routes at /auth')
app.use('/auth', authRoutes)
console.log('[app.js] Auth routes registered')
console.log('[app.js] Mounting Company routes at /admin/companies')
app.use('/admin/companies', companyRoutes)
console.log('[app.js] Company routes registered')
console.log('[app.js] Mounting User routes at /admin/users')
app.use('/admin/users', userRoutes)
console.log('[app.js] User routes registered')
console.log('[app.js] Mounting ERP User routes at /api/usersErp')
app.use('/api/usersErp', usersErp)
console.log('[app.js] ERP User routes registered')
console.log('[app.js] Mounting Email routes at /api')
app.use('/api', emailRoutes)
console.log('[app.js] Email routes registered')

app.use((err, req, res, next) => {
  console.error('[ERROR]', err.stack) // Log full error with stack trace
  res.status(500).json({ 
    error: 'Internal Server Error',
    message: err.message 
  })
})

export default app
