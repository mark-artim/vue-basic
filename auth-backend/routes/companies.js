// routes/companies.js
import express from 'express'
import Company from '../models/Company.js'
import decodeToken from '../middleware/decodeToken.js'
import { 
  createWebhookForCompany, 
  deleteWebhookForCompany, 
  getWebhookStatusForCompany,
  createWebhooksForAllCompanies 
} from '../services/shippoWebhookService.js'

const router = express.Router()

// GET all companies
router.get('/', async (req, res) => {
  const companies = await Company.find()
  res.json(companies)
})

// GET one company
router.get('/:id', async (req, res) => {
  try {
    const company = await Company.findById(req.params.id)
    if (!company) return res.status(404).json({ error: 'Not found' })
    res.json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// CREATE company
router.post('/', async (req, res) => {
  try {
    const company = new Company(req.body)
    await company.save()
    res.status(201).json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// UPDATE company
router.put('/:id', async (req, res) => {
  try {
    const company = await Company.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true })
    res.json(company)
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// DELETE company
router.delete('/:id', async (req, res) => {
  try {
    await Company.findByIdAndDelete(req.params.id)
    res.json({ message: 'Deleted' })
  } catch (err) {
    res.status(400).json({ error: err.message })
  }
})

// ============ WEBHOOK MANAGEMENT ENDPOINTS ============

// GET /admin/companies/:id/webhook/status - Get webhook status for company
router.get('/:id/webhook/status', decodeToken, async (req, res) => {
  try {
    console.log(`[WEBHOOK API] Getting webhook status for company: ${req.params.id}`)
    
    // Check if user has admin access or belongs to the company
    const userCompanyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const hasAdminAccess = req.user.userType === 'admin'
    const hasCompanyAccess = userCompanyId === req.params.id
    
    console.log('[WEBHOOK API] Authorization check:', {
      userType: req.user.userType,
      userCompanyId,
      requestedCompanyId: req.params.id,
      hasAdminAccess,
      hasCompanyAccess
    })
    
    if (!hasAdminAccess && !hasCompanyAccess) {
      return res.status(403).json({ error: 'Access denied' })
    }
    
    const result = await getWebhookStatusForCompany(req.params.id)
    
    if (!result.success) {
      return res.status(400).json({ error: result.error })
    }
    
    res.json(result)
    
  } catch (error) {
    console.error('[WEBHOOK API] Error getting webhook status:', error)
    res.status(500).json({ error: 'Failed to get webhook status' })
  }
})

// POST /admin/companies/:id/webhook/create - Create webhook for company
router.post('/:id/webhook/create', decodeToken, async (req, res) => {
  try {
    console.log(`[WEBHOOK API] Creating webhook for company: ${req.params.id}`)
    
    // Check if user has admin access or Ship54 admin role for this company
    const userCompanyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const hasSystemAdminAccess = req.user.userType === 'admin'
    const hasCompanyAccess = userCompanyId === req.params.id
    
    // Check if user has Ship54 admin role
    const hasShip54Admin = req.user.roles?.ship54?.includes('admin') || 
                          (Array.isArray(req.user.roles?.ship54) && req.user.roles.ship54.includes('admin'))
    
    console.log('[WEBHOOK CREATE] Authorization check:', {
      userType: req.user.userType,
      userCompanyId,
      requestedCompanyId: req.params.id,
      hasSystemAdminAccess,
      hasCompanyAccess,
      hasShip54Admin,
      userRoles: req.user.roles
    })
    
    if (!hasSystemAdminAccess && (!hasCompanyAccess || !hasShip54Admin)) {
      return res.status(403).json({ error: 'Admin access required' })
    }
    
    const result = await createWebhookForCompany(req.params.id)
    
    if (!result.success) {
      return res.status(400).json({ error: result.error, details: result.details })
    }
    
    res.json({
      message: result.message,
      webhookId: result.webhookId,
      webhookUrl: result.webhookUrl
    })
    
  } catch (error) {
    console.error('[WEBHOOK API] Error creating webhook:', error)
    res.status(500).json({ error: 'Failed to create webhook' })
  }
})

// DELETE /admin/companies/:id/webhook - Delete webhook for company
router.delete('/:id/webhook', decodeToken, async (req, res) => {
  try {
    console.log(`[WEBHOOK API] Deleting webhook for company: ${req.params.id}`)
    
    // Check if user has admin access or Ship54 admin role for this company
    const userCompanyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const hasSystemAdminAccess = req.user.userType === 'admin'
    const hasCompanyAccess = userCompanyId === req.params.id
    
    // Check if user has Ship54 admin role
    const hasShip54Admin = req.user.roles?.ship54?.includes('admin') || 
                          (Array.isArray(req.user.roles?.ship54) && req.user.roles.ship54.includes('admin'))
    
    console.log('[WEBHOOK DELETE] Authorization check:', {
      userType: req.user.userType,
      userCompanyId,
      requestedCompanyId: req.params.id,
      hasSystemAdminAccess,
      hasCompanyAccess,
      hasShip54Admin,
      userRoles: req.user.roles
    })
    
    if (!hasSystemAdminAccess && (!hasCompanyAccess || !hasShip54Admin)) {
      return res.status(403).json({ error: 'Admin access required' })
    }
    
    const result = await deleteWebhookForCompany(req.params.id)
    
    if (!result.success) {
      return res.status(400).json({ error: result.error, details: result.details })
    }
    
    res.json({ message: result.message })
    
  } catch (error) {
    console.error('[WEBHOOK API] Error deleting webhook:', error)
    res.status(500).json({ error: 'Failed to delete webhook' })
  }
})

// POST /admin/companies/webhooks/create-all - Create webhooks for all companies (super admin)
router.post('/webhooks/create-all', decodeToken, async (req, res) => {
  try {
    console.log('[WEBHOOK API] Creating webhooks for all companies')
    
    // Check if user has admin access
    if (req.user.userType !== 'admin') {
      return res.status(403).json({ error: 'Admin access required' })
    }
    
    const result = await createWebhooksForAllCompanies()
    
    if (!result.success) {
      return res.status(400).json({ error: result.error })
    }
    
    res.json({
      message: `Processed ${result.processed} companies`,
      results: result.results
    })
    
  } catch (error) {
    console.error('[WEBHOOK API] Error in batch webhook creation:', error)
    res.status(500).json({ error: 'Failed to create webhooks' })
  }
})

export default router
