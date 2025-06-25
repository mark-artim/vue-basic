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


dotenv.config()

const app = express()

// CORS configuration
const allowedOrigins = [
  'http://localhost:3000', // for local dev
  'https://vue-basic-flame.vercel.app',  // ✅ for production
  'https://vue-basic-mark-artims-projects.vercel.app',
];

app.use(cors({
  origin: function (origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));

app.use(express.json())

console.log('[ENV] MONGODB_URI =', process.env.MONGODB_URI)
console.log('[DB] Attempting MongoDB connection...')

mongoose.connect(process.env.MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('[DB] Connected to MongoDB Atlas'))
.catch(err => console.error('[DB] MongoDB connection error:', err))

app.use('/api/erp-proxy', erpProxyRoutes)
console.log('[app.js] ERP Proxy route registered')
app.use('/auth', authRoutes)
app.use('/admin/companies', companyRoutes)
app.use('/admin/users', userRoutes)
app.use('/api/usersErp', usersErp)
app.use('/api', emailRoutes)


export default app
