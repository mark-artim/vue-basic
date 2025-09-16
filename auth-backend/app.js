import express from 'express'
import mongoose from 'mongoose'
import dotenv from 'dotenv'
import erpProxyRoutes from './routes/erpProxy.js'
import authRoutes from './routes/auth.js'
import cors from 'cors'
// admin routes
import adminRouter from './routes/admin/index.js'
import companyRoutes from './routes/companies.js'
import userRoutes from './routes/users.js'
import productRoutes from './routes/products.js'
import menuRoutes from './routes/menus.js'
// erp routes
import usersErp from './routes/usersErp.js'
import shipViasRoutes from './routes/shipVias.js'
import postFreightRoutes from './routes/postFreight.js'
import erpRoutes from './routes/erp.js'
// specialty routes
import emailRoutes from './routes/email.js'
import wasabiRoutes from './routes/wasabi.js';
import debugRoutes from './routes/debug.js'
import logRoutes from './routes/logs.js';
import ship54Routes from './routes/ship54.js';
import stripeRoutes from './routes/stripe.js';
import shippoRoutes from './routes/shippo.js';
import shipmentsRoutes from './routes/shipments.js';
import shippingRoutes from './routes/shipping.js';

dotenv.config()

const app = express()

// CORS configuration
const allowedOrigins = [
  'http://localhost:3000',
  'https://vue-basic-flame.vercel.app',
  'https://vue-basic-mark-artims-projects.vercel.app',
  'https://emp54.app',
  'https://www.emp54.app',
  'https://goshippo.com', // For Shippo OAuth callbacks
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
app.use(express.urlencoded({ extended: true }))

// Debug: Log all incoming requests
app.use((req, res, next) => {
  console.log(`[REQUEST] ${req.method} ${req.originalUrl} - ${new Date().toISOString()}`)
  next()
})

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
app.use('/auth', authRoutes)
app.use('/admin', adminRouter)
app.use('/admin/companies', companyRoutes)
app.use('/admin/users', userRoutes)
app.use('/menus', menuRoutes)
app.use('/api/usersErp', usersErp)
app.use('/api', emailRoutes)
app.use('/products', productRoutes)
app.use('/shipVias', shipViasRoutes)
app.use('/postFreight', postFreightRoutes)
app.use('/wasabi', wasabiRoutes);
app.use('/erp', erpRoutes)
app.use('/debug', debugRoutes)
app.use('/logs', logRoutes);
console.log('[ROUTE MOUNTING] Mounting ship54 routes at /ship54')
app.use('/ship54', ship54Routes);
console.log('[ROUTE MOUNTING] Ship54 routes mounted successfully')
app.use('/stripe', stripeRoutes);
console.log('[ROUTE MOUNTING] Mounting Shippo webhook routes at /shippo')
app.use('/shippo', shippoRoutes);
console.log('[ROUTE MOUNTING] Shippo webhook routes mounted successfully')
console.log('[ROUTE MOUNTING] Mounting shipments API at /api/shipments')
app.use('/api/shipments', (req, res, next) => {
  console.log('[DEBUG] Request to /api/shipments:', req.method, req.url)
  next()
}, shipmentsRoutes);
console.log('[ROUTE MOUNTING] Shipments API routes mounted successfully')
console.log('[ROUTE MOUNTING] Mounting shipping API at /api/shipping')
app.use('/api/shipping', shippingRoutes);
console.log('[ROUTE MOUNTING] Shipping API routes mounted successfully')

// Test route to verify routing works
app.get('/api/test-route', (req, res) => {
  console.log('[TEST ROUTE] Hit test route!')
  res.json({ message: 'Test route works!', timestamp: new Date().toISOString() })
})

// Debug: catch unmatched routes
app.use((req, res, _next) => {
  console.log(`[UNMATCHED ROUTE] ${req.method} ${req.originalUrl} - No route handler found`)
  res.status(404).json({ error: 'Route not found' })
})

app.use((err, req, res, _next) => {
  console.error('[ERROR]', err.stack) // Log full error with stack trace
  res.status(500).json({ 
    error: 'Internal Server Error',
    message: err.message 
  })
})

export default app
