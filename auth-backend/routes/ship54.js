import express from 'express'
import User from '../models/User.js'
import Company from '../models/Company.js'
import decodeToken from '../middleware/decodeToken.js'
import { makeShippoAPICall, testShippoConnection } from '../utils/shippo.js'
import { encryptToken, decryptToken } from '../utils/encryption.js'

const router = express.Router()

// Debug middleware to log all requests to this router
router.use((req, res, next) => {
  console.log(`[Ship54 Router] ${req.method} ${req.path} - Middleware reached`)
  console.log(`[Ship54 Router] Full URL: ${req.originalUrl}`)
  console.log(`[Ship54 Router] Headers:`, Object.keys(req.headers))
  console.log(`[Ship54 Router] Body:`, req.body ? 'body_present' : 'no_body')
  next()
})

// Using encryption functions from utils/encryption.js

// Test route to verify router is working
router.get('/test', (req, res) => {
  console.log('[Ship54 Router] TEST ROUTE HIT')
  res.json({ message: 'Ship54 router is working' })
})

// Get user's Ship54 settings (combines user + company settings)
router.get('/settings', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const user = await User.findById(userId).populate('companyId')
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }
    
    if (!user.companyId) {
      return res.status(404).json({ error: 'User has no associated company' })
    }

    // Get user-specific settings (shipping preferences)
    const userSettings = user.ship54Settings?.shipping || {
      enableAutoSearch: true,
      defaultShipViaKeywords: 'UPS, FEDEX',
      defaultBranch: ''
    }
    
    // Get company-wide settings (shippo, freight, cod)
    const companySettings = user.companyId.ship54Settings || {
      shippo: {
        connected: false,
        accountInfo: null
      },
      freight: {
        defaultMethod: 'filedrop',
        productId: ''
      },
      cod: {
        termsCodes: [],
        balancePolicy: 'warn'
      }
    }

    // Combine settings for the frontend
    const combinedSettings = {
      // Company-wide settings
      shippo: companySettings.shippo,
      freight: companySettings.freight,
      cod: companySettings.cod,
      // User-specific settings
      shipping: userSettings
    }

    console.log('📤 Returning combined settings:', JSON.stringify(combinedSettings, null, 2))
    res.json(combinedSettings)
  } catch (err) {
    console.error('Failed to get Ship54 settings:', err)
    res.status(500).json({ error: 'Failed to load settings' })
  }
})

// Update Ship54 settings (routes to user vs company based on setting type)
router.put('/settings', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const newSettings = req.body

    // Validate settings structure
    if (!newSettings || typeof newSettings !== 'object') {
      return res.status(400).json({ error: 'Invalid settings format' })
    }

    const user = await User.findById(userId).populate('companyId')
    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }
    
    if (!user.companyId) {
      return res.status(404).json({ error: 'User has no associated company' })
    }

    console.log('📥 Received settings to save:', JSON.stringify(newSettings, null, 2))

    // Update user-specific settings (shipping preferences)
    if (newSettings.shipping) {
      console.log('💾 Saving user shipping settings:', newSettings.shipping)
      user.ship54Settings = user.ship54Settings || {}
      user.ship54Settings.shipping = {
        ...user.ship54Settings.shipping,
        ...newSettings.shipping
      }
      await user.save()
    }

    // Update company-wide settings (shippo, freight, cod)
    const companyUpdates = {}
    let hasCompanyUpdates = false
    
    if (newSettings.shippo) {
      console.log('💾 Saving company shippo settings:', newSettings.shippo)
      companyUpdates['ship54Settings.shippo'] = {
        ...user.companyId.ship54Settings?.shippo,
        ...newSettings.shippo
      }
      hasCompanyUpdates = true
    }
    
    if (newSettings.freight) {
      console.log('💾 Saving company freight settings:', newSettings.freight)
      companyUpdates['ship54Settings.freight'] = {
        ...user.companyId.ship54Settings?.freight,
        ...newSettings.freight
      }
      hasCompanyUpdates = true
    }
    
    if (newSettings.cod) {
      console.log('💾 Saving company COD settings:', newSettings.cod)
      companyUpdates['ship54Settings.cod'] = {
        ...user.companyId.ship54Settings?.cod,
        ...newSettings.cod
      }
      hasCompanyUpdates = true
    }
    
    if (hasCompanyUpdates) {
      await Company.findByIdAndUpdate(user.companyId._id, { $set: companyUpdates })
    }

    res.json({ 
      success: true, 
      message: 'Settings updated successfully'
    })
  } catch (err) {
    console.error('Failed to update Ship54 settings:', err)
    res.status(500).json({ error: 'Failed to save settings' })
  }
})

// Note: OAuth routes removed - using customer-token approach instead

// Test Shippo connection
router.get('/shippo/test', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const result = await testShippoConnection(userId)
    
    if (result.success) {
      res.json({
        success: true,
        message: 'Shippo connection test successful',
        accountInfo: result.accountInfo
      })
    } else {
      res.status(400).json({
        success: false,
        error: result.error
      })
    }
  } catch (err) {
    console.error('Shippo connection test failed:', err)
    res.status(500).json({ error: 'Connection test failed' })
  }
})

// Shippo API proxy for specific endpoints (can add more as needed)
router.post('/shippo/api/labels', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const { method = 'POST', data } = req.body
    
    const options = { method }
    if (data) options.body = JSON.stringify(data)
    
    const result = await makeShippoAPICall(userId, '/shipments', options)
    res.json(result)
  } catch (err) {
    console.error('Shippo API proxy error:', err)
    res.status(500).json({ error: err.message })
  }
})

router.post('/shippo/api/rates', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const { shipmentId } = req.body
    
    const result = await makeShippoAPICall(userId, `/shipments/${shipmentId}/rates`)
    res.json(result)
  } catch (err) {
    console.error('Shippo API proxy error:', err)
    res.status(500).json({ error: err.message })
  }
})

// Customer Token Management Endpoints

// Validate and save customer's Shippo token
router.post('/shippo/validate-token', decodeToken, async (req, res) => {
  console.log('[Route Validation] POST /ship54/shippo/validate-token - HANDLER REACHED')
  try {
    const { token } = req.body
    const userId = req.user.userId
    
    console.log('[Token Validation] Starting validation for user:', userId)
    console.log('[Token Validation] Token received (redacted):', token ? 'token_present' : 'no_token')
    
    if (!token) {
      console.log('[Token Validation] ERROR: No token provided')
      return res.status(400).json({ error: 'Token is required' })
    }
    
    // Validate token format
    if (!/^shippo_(test|live)_[a-f0-9]{40}$/.test(token)) {
      return res.status(400).json({ error: 'Invalid Shippo token format' })
    }
    
    // Test token with Shippo API - try shipments endpoint for validation
    console.log('[Token Validation] Testing token with Shippo API...')
    const testResponse = await fetch('https://api.goshippo.com/shipments/', {
      headers: {
        'Authorization': `ShippoToken ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    console.log('[Token Validation] Shippo API response status:', testResponse.status)
    console.log('[Token Validation] Shippo API response headers:', Object.fromEntries(testResponse.headers))
    
    if (!testResponse.ok) {
      const errorData = await testResponse.text()
      console.error('[Token Validation] Shippo token validation failed:')
      console.error('[Token Validation] Status:', testResponse.status)
      console.error('[Token Validation] Status text:', testResponse.statusText)
      console.error('[Token Validation] Error data:', errorData)
      return res.status(400).json({ error: 'Invalid or expired Shippo token' })
    }
    
    const accountInfo = await testResponse.json()
    const environment = token.startsWith('shippo_test_') ? 'test' : 'live'
    
    // Find user's company and encrypt token
    const user = await User.findById(userId).populate('companyId')
    if (!user || !user.companyId) {
      return res.status(404).json({ error: 'User or company not found' })
    }
    
    // Encrypt the token for storage
    const encryptedToken = encryptToken(token)
    
    // Update company settings
    await Company.findByIdAndUpdate(user.companyId._id, {
      '$set': {
        'ship54Settings.shippo.customerToken.encrypted': encryptedToken,
        'ship54Settings.shippo.customerToken.isValid': true,
        'ship54Settings.shippo.customerToken.lastTested': new Date(),
        'ship54Settings.shippo.customerToken.testResults': {
          account: {
            email: accountInfo.email,
            name: accountInfo.name,
            object_id: accountInfo.object_id
          }
        },
        'ship54Settings.shippo.customerToken.environment': environment,
        'ship54Settings.shippo.connected': true
      }
    })
    
    console.log(`✅ Shippo token validated and saved for company ${user.companyId.companyCode}`)
    
    res.json({
      success: true,
      environment,
      accountInfo: {
        account: {
          email: accountInfo.email,
          name: accountInfo.name,
          object_id: accountInfo.object_id
        }
      },
      encrypted: encryptedToken
    })
    
  } catch (err) {
    console.error('[Token Validation] CATCH BLOCK REACHED - Error:', err)
    console.error('[Token Validation] Error stack:', err.stack)
    res.status(500).json({ error: 'Failed to validate token' })
  }
})

// Error handler specifically for this router
router.use((err, req, res, next) => {
  console.error('[Ship54 Router] ERROR HANDLER:', err)
  console.error('[Ship54 Router] Error stack:', err.stack)
  res.status(500).json({ error: 'Internal server error in Ship54 router' })
})

// Test existing customer token
router.post('/shippo/test-token', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const user = await User.findById(userId).populate('companyId')
    
    if (!user?.companyId?.ship54Settings?.shippo?.customerToken?.encrypted) {
      return res.status(400).json({ error: 'No Shippo token found' })
    }
    
    // Decrypt token
    const encryptedToken = user.companyId.ship54Settings.shippo.customerToken.encrypted
    const token = decryptToken(encryptedToken)
    
    // Test token with Shippo API - try shipments endpoint for validation
    const testResponse = await fetch('https://api.goshippo.com/shipments/', {
      headers: {
        'Authorization': `ShippoToken ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!testResponse.ok) {
      // Mark token as invalid
      await Company.findByIdAndUpdate(user.companyId._id, {
        '$set': {
          'ship54Settings.shippo.customerToken.isValid': false,
          'ship54Settings.shippo.connected': false
        }
      })
      
      return res.status(400).json({ error: 'Token is no longer valid' })
    }
    
    const accountInfo = await testResponse.json()
    
    // Update last tested time
    await Company.findByIdAndUpdate(user.companyId._id, {
      '$set': {
        'ship54Settings.shippo.customerToken.lastTested': new Date(),
        'ship54Settings.shippo.customerToken.testResults': {
          account: {
            email: accountInfo.email,
            name: accountInfo.name,
            object_id: accountInfo.object_id
          }
        }
      }
    })
    
    res.json({
      success: true,
      accountInfo: {
        account: {
          email: accountInfo.email,
          name: accountInfo.name,
          object_id: accountInfo.object_id
        }
      }
    })
    
  } catch (err) {
    console.error('Token test error:', err)
    res.status(500).json({ error: 'Failed to test token' })
  }
})

// Remove customer token
router.delete('/shippo/remove-token', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const user = await User.findById(userId).populate('companyId')
    
    await Company.findByIdAndUpdate(user.companyId._id, {
      '$set': {
        'ship54Settings.shippo.customerToken.encrypted': null,
        'ship54Settings.shippo.customerToken.isValid': false,
        'ship54Settings.shippo.customerToken.lastTested': null,
        'ship54Settings.shippo.customerToken.testResults': null,
        'ship54Settings.shippo.connected': false
      }
    })
    
    console.log(`🗑️ Shippo token removed for company ${user.companyId.companyCode}`)
    res.json({ success: true })
    
  } catch (err) {
    console.error('Token removal error:', err)
    res.status(500).json({ error: 'Failed to remove token' })
  }
})

export default router