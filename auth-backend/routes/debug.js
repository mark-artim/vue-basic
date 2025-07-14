import express from 'express'
const router = express.Router()

router.get('/env-debug', (req, res) => {
  res.json({
    NODE_ENV: process.env.NODE_ENV,
    ERP_BASE_URL: process.env.ERP_BASE_URL || '⚠️ Not Set',
    JWT_SECRET: process.env.JWT_SECRET ? '✅ Set' : '❌ Missing',
    VITE_API_URL: process.env.VITE_API_URL || '⚠️ Not Set',
    PORT: process.env.PORT || '⚠️ Not Set'
  })
})

export default router
