import axios from 'axios'
import Company from '../models/Company.js'
import { decryptToken } from '../utils/encryption.js'

const decryptShippoToken = (encryptedToken) => {
  try {
    return decryptToken(encryptedToken)
  } catch (error) {
    console.error('[WEBHOOK SERVICE] Error decrypting token:', error)
    throw new Error('Failed to decrypt Shippo token')
  }
}

const getShippoClient = (token, environment = 'test') => {
  const baseURL = environment === 'live' 
    ? 'https://api.goshippo.com/v1'
    : 'https://api.goshippo.com/v1' // Same URL for both, token determines environment
    
  return axios.create({
    baseURL,
    headers: {
      'Authorization': `ShippoToken ${token}`,
      'Content-Type': 'application/json'
    }
  })
}

export const createWebhookForCompany = async (companyId) => {
  console.log(`[WEBHOOK SERVICE] Creating webhook for company: ${companyId}`)
  
  try {
    const company = await Company.findById(companyId)
    if (!company) {
      throw new Error('Company not found')
    }

    const shippoSettings = company.ship54Settings?.shippo
    if (!shippoSettings?.customerToken?.encrypted || !shippoSettings.customerToken.isValid) {
      throw new Error('No valid Shippo API token found for company')
    }

    // Decrypt the token
    const apiToken = decryptShippoToken(shippoSettings.customerToken.encrypted)
    const environment = shippoSettings.customerToken.environment || 'test'
    
    // Create Shippo API client
    const shippoClient = getShippoClient(apiToken, environment)
    
    // Determine webhook URL - use environment variable or construct from request
    const baseUrl = process.env.WEBHOOK_BASE_URL || process.env.BASE_URL || 'https://your-domain.com'
    const webhookUrl = `${baseUrl}/shippo/webhook/${companyId}`
    
    // Check if webhook already exists
    if (shippoSettings.webhook?.id) {
      console.log(`[WEBHOOK SERVICE] Webhook already exists for company ${companyId}: ${shippoSettings.webhook.id}`)
      
      // Verify webhook still exists in Shippo
      try {
        const existingWebhook = await shippoClient.get(`/webhooks/${shippoSettings.webhook.id}`)
        if (existingWebhook.data && existingWebhook.data.url === webhookUrl) {
          console.log(`[WEBHOOK SERVICE] Existing webhook verified for company ${companyId}`)
          return {
            success: true,
            webhookId: existingWebhook.data.object_id,
            message: 'Webhook already exists and is valid'
          }
        }
      } catch (error) {
        console.log(`[WEBHOOK SERVICE] Existing webhook not found, creating new one for company ${companyId}`)
      }
    }
    
    // Create new webhook
    const webhookData = {
      url: webhookUrl,
      event: 'all', // Subscribe to all events, we'll filter in the handler
      active: true,
      is_test: environment === 'test'
    }
    
    console.log(`[WEBHOOK SERVICE] Creating webhook with data:`, webhookData)
    
    const response = await shippoClient.post('/webhooks/', webhookData)
    const webhook = response.data
    
    console.log(`[WEBHOOK SERVICE] Webhook created successfully:`, webhook)
    
    // Update company with webhook information
    await Company.findByIdAndUpdate(companyId, {
      'ship54Settings.shippo.webhook': {
        id: webhook.object_id,
        url: webhook.url,
        isActive: webhook.active,
        createdAt: new Date(),
        lastError: null,
        events: ['track_updated', 'transaction_created', 'transaction_updated']
      }
    })
    
    return {
      success: true,
      webhookId: webhook.object_id,
      webhookUrl: webhook.url,
      message: 'Webhook created successfully'
    }
    
  } catch (error) {
    console.error(`[WEBHOOK SERVICE] Error creating webhook for company ${companyId}:`, error)
    
    // Store error in company record
    await Company.findByIdAndUpdate(companyId, {
      'ship54Settings.shippo.webhook.lastError': error.message,
      'ship54Settings.shippo.webhook.isActive': false
    })
    
    return {
      success: false,
      error: error.message,
      details: error.response?.data || null
    }
  }
}

export const deleteWebhookForCompany = async (companyId) => {
  console.log(`[WEBHOOK SERVICE] Deleting webhook for company: ${companyId}`)
  
  try {
    const company = await Company.findById(companyId)
    if (!company) {
      throw new Error('Company not found')
    }

    const shippoSettings = company.ship54Settings?.shippo
    if (!shippoSettings?.webhook?.id) {
      return {
        success: true,
        message: 'No webhook to delete'
      }
    }

    if (!shippoSettings.customerToken?.encrypted || !shippoSettings.customerToken.isValid) {
      throw new Error('No valid Shippo API token found for company')
    }

    // Decrypt the token
    const apiToken = decryptShippoToken(shippoSettings.customerToken.encrypted)
    const environment = shippoSettings.customerToken.environment || 'test'
    
    // Create Shippo API client
    const shippoClient = getShippoClient(apiToken, environment)
    
    // Delete webhook
    await shippoClient.delete(`/webhooks/${shippoSettings.webhook.id}`)
    
    // Clear webhook information from company
    await Company.findByIdAndUpdate(companyId, {
      'ship54Settings.shippo.webhook': {
        id: null,
        url: null,
        isActive: false,
        createdAt: null,
        lastError: null,
        events: ['track_updated', 'transaction_created', 'transaction_updated']
      }
    })
    
    return {
      success: true,
      message: 'Webhook deleted successfully'
    }
    
  } catch (error) {
    console.error(`[WEBHOOK SERVICE] Error deleting webhook for company ${companyId}:`, error)
    
    return {
      success: false,
      error: error.message,
      details: error.response?.data || null
    }
  }
}

export const getWebhookStatusForCompany = async (companyId) => {
  try {
    const company = await Company.findById(companyId)
    if (!company) {
      throw new Error('Company not found')
    }

    const webhookInfo = company.ship54Settings?.shippo?.webhook
    const hasValidToken = company.ship54Settings?.shippo?.customerToken?.isValid
    
    return {
      success: true,
      webhook: webhookInfo || {
        id: null,
        url: null,
        isActive: false,
        createdAt: null,
        lastError: null,
        events: []
      },
      hasValidToken,
      canCreateWebhook: hasValidToken && !webhookInfo?.id
    }
    
  } catch (error) {
    console.error(`[WEBHOOK SERVICE] Error getting webhook status for company ${companyId}:`, error)
    
    return {
      success: false,
      error: error.message
    }
  }
}

export const createWebhooksForAllCompanies = async () => {
  console.log('[WEBHOOK SERVICE] Creating webhooks for all companies with valid Shippo tokens')
  
  try {
    const companies = await Company.find({
      'ship54Settings.shippo.customerToken.isValid': true,
      'ship54Settings.shippo.webhook.id': { $exists: false }
    })
    
    console.log(`[WEBHOOK SERVICE] Found ${companies.length} companies needing webhooks`)
    
    const results = []
    
    for (const company of companies) {
      console.log(`[WEBHOOK SERVICE] Processing company: ${company.name} (${company._id})`)
      
      const result = await createWebhookForCompany(company._id)
      results.push({
        companyId: company._id,
        companyName: company.name,
        ...result
      })
      
      // Add a small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    return {
      success: true,
      processed: companies.length,
      results
    }
    
  } catch (error) {
    console.error('[WEBHOOK SERVICE] Error in batch webhook creation:', error)
    
    return {
      success: false,
      error: error.message
    }
  }
}