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
import productRoutes from './routes/products.js'
import menuRoutes from './routes/menus.js'
import shipViasRoutes from './routes/shipVias.js'
import postFreightRoutes from './routes/postFreight.js'
import adminRouter from './routes/admin/index.js'

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


app.use(express.json())

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

app.use('/api/erp-proxy', erpProxyRoutes)
console.log('[app.js] ERP Proxy route registered')
app.use('/auth', authRoutes)
console.log('[app.js] Auth routes registered')
app.use('/admin/companies', companyRoutes)
console.log('[app.js] Company routes registered')
app.use('/admin/users', userRoutes)
console.log('[app.js] User routes registered')
app.use('/api/usersErp', usersErp)
console.log('[app.js] ERP User routes registered')
app.use('/api', emailRoutes)
console.log('[app.js] Email routes registered')
app.use('/products', productRoutes)
console.log('[app.js] Product routes registered')
app.use('/menus', menuRoutes)
console.log('[app.js] Menu routes registered')  
app.use('/shipVias', shipViasRoutes)
console.log('[app.js] ShipVias routes registered')
app.use('/postFreight', postFreightRoutes)
console.log('[app.js] PostFreight routes registered')
app.use('/admin', adminRouter) // ✅ this activates /admin/menus

app.use((err, req, res, next) => {
  console.error('[ERROR]', err.stack) // Log full error with stack trace
  res.status(500).json({ 
    error: 'Internal Server Error',
    message: err.message 
  })
})

export default app
