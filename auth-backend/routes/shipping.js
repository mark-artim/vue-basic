import express from 'express'
import decodeToken from '../middleware/decodeToken.js'

const router = express.Router()

// POST /api/shipping/validate-address - Validate shipping address using Shippo
router.post('/validate-address', decodeToken, async (req, res) => {
  try {
    const { name, street1, street2, city, state, zip, country = 'US' } = req.body
    const companyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    
    console.log('[ADDRESS VALIDATION] Validating address for company:', companyId)
    console.log('[ADDRESS VALIDATION] Request data:', { name, street1, street2, city, state, zip, country })
    
    // Validate required fields
    if (!street1 || !city || !state || !zip) {
      console.log('[ADDRESS VALIDATION] Missing required fields')
      return res.status(400).json({ error: 'Missing required address fields' })
    }
    
    // Get company's Shippo token
    console.log('[ADDRESS VALIDATION] Loading company data...')
    const Company = (await import('../models/Company.js')).default
    const company = await Company.findById(companyId)
    
    if (!company) {
      console.log('[ADDRESS VALIDATION] Company not found:', companyId)
      return res.status(400).json({ error: 'Company not found' })
    }
    
    const shippoSettings = company.ship54Settings?.shippo
    if (!shippoSettings?.customerToken?.encrypted) {
      console.log('[ADDRESS VALIDATION] No Shippo token configured for company')
      return res.status(400).json({ error: 'Company Shippo token not configured' })
    }
    
    console.log('[ADDRESS VALIDATION] Company found, decrypting token...')
    // Decrypt and use Shippo token
    const { decryptToken } = await import('../utils/encryption.js')
    const shippoToken = decryptToken(shippoSettings.customerToken.encrypted)
    console.log('[ADDRESS VALIDATION] Token decrypted, calling Shippo API...')
    
    // Call Shippo address validation API
    const validationResponse = await fetch('https://api.goshippo.com/addresses/', {
      method: 'POST',
      headers: {
        'Authorization': `ShippoToken ${shippoToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: name || '',
        street1,
        street2: street2 || '',
        city,
        state,
        zip,
        country,
        validate: true
      })
    })
    
    if (!validationResponse.ok) {
      const errorText = await validationResponse.text()
      console.error('[ADDRESS VALIDATION] Shippo API error:', errorText)
      return res.status(400).json({ error: 'Address validation failed', details: errorText })
    }
    
    const validationData = await validationResponse.json()
    console.log('[ADDRESS VALIDATION] Shippo response:', JSON.stringify(validationData, null, 2))
    
    // Process the response
    const result = {
      is_valid: validationData.validation_results.is_valid,
      messages: validationData.validation_results.messages || []
    }
    
    // If Shippo provided a corrected address, include it
    if (validationData.validation_results.is_valid && 
        (validationData.street1 !== street1 || 
         validationData.city !== city || 
         validationData.state !== state || 
         validationData.zip !== zip)) {
      
      result.suggested_address = {
        name: validationData.name,
        street1: validationData.street1,
        street2: validationData.street2 || '',
        city: validationData.city,
        state: validationData.state,
        zip: validationData.zip,
        country: validationData.country
      }
    }
    
    res.json(result)
    
  } catch (error) {
    console.error('[ADDRESS VALIDATION] Error validating address:', error)
    res.status(500).json({ 
      error: 'Address validation failed',
      details: error.message 
    })
  }
})

export default router