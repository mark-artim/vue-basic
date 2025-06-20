import express from 'express'
import mongoose from 'mongoose'
import dotenv from 'dotenv'
import erpProxyRoutes from './routes/erpProxy.js'
import authRoutes from './routes/auth.js'
import cors from 'cors'
import companyRoutes from './routes/companies.js'
import userRoutes from './routes/users.js'
import redisTestRoutes from './routes/redisTest.js'
import branches from './routes/branches.js';
import usersErp from './routes/usersErp.js';


dotenv.config()

const app = express()
app.use(cors({ origin: 'http://localhost:3000', credentials: true }))
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
app.use('/redis-test', redisTestRoutes)
app.use('/api/branches', branches);
app.use('/api/usersErp', usersErp);


export default app
