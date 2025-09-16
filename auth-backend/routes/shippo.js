import express from 'express'
import Shipment from '../models/Shipment.js'

const router = express.Router()

// Webhook endpoint to receive Shippo tracking updates - with company isolation
router.post('/webhook/:companyId', express.raw({ type: 'application/json' }), async (req, res) => {
  const companyId = req.params.companyId
  console.log(`[SHIPPO WEBHOOK] Received webhook request for company: ${companyId}`)
  
  try {
    // Parse the webhook payload
    const webhookData = JSON.parse(req.body.toString())
    console.log('[SHIPPO WEBHOOK] Event type:', webhookData.event)
    console.log('[SHIPPO WEBHOOK] Test event:', webhookData.test)
    
    // Handle different webhook events
    switch (webhookData.event) {
      case 'track_updated':
        await handleTrackingUpdate(webhookData, companyId)
        break
        
      case 'transaction_created':
      case 'transaction_updated':
        console.log('[SHIPPO WEBHOOK] Transaction event received - logging only')
        // Could be used to create initial shipment records
        await handleTransactionEvent(webhookData, companyId)
        break
        
      case 'batch_created':
      case 'batch_purchased':
        console.log('[SHIPPO WEBHOOK] Batch event received - logging only')
        break
        
      default:
        console.log('[SHIPPO WEBHOOK] Unknown event type:', webhookData.event)
    }
    
    // Always respond with 200 OK to acknowledge receipt
    res.status(200).json({ 
      received: true, 
      event: webhookData.event,
      companyId: companyId 
    })
    
  } catch (error) {
    console.error(`[SHIPPO WEBHOOK] Error processing webhook for company ${companyId}:`, error)
    res.status(500).json({ error: 'Webhook processing failed' })
  }
})

// Legacy webhook endpoint (without companyId) - for backwards compatibility
router.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  console.log('[SHIPPO WEBHOOK] Received legacy webhook request (no companyId)')
  
  try {
    // Parse the webhook payload
    const webhookData = JSON.parse(req.body.toString())
    console.log('[SHIPPO WEBHOOK] Event type:', webhookData.event)
    console.log('[SHIPPO WEBHOOK] Test event:', webhookData.test)
    
    // Handle different webhook events - without company isolation
    switch (webhookData.event) {
      case 'track_updated':
        await handleTrackingUpdate(webhookData) // No companyId - searches all companies
        break
        
      case 'transaction_created':
      case 'transaction_updated':
        console.log('[SHIPPO WEBHOOK] Transaction event received - logging only')
        break
        
      default:
        console.log('[SHIPPO WEBHOOK] Unknown event type:', webhookData.event)
    }
    
    // Always respond with 200 OK to acknowledge receipt
    res.status(200).json({ received: true, event: webhookData.event })
    
  } catch (error) {
    console.error('[SHIPPO WEBHOOK] Error processing legacy webhook:', error)
    res.status(500).json({ error: 'Webhook processing failed' })
  }
})

// Handle tracking update webhooks
async function handleTrackingUpdate(webhookData, companyId = null) {
  const { data, test } = webhookData
  
  if (!data || !data.tracking_number) {
    console.warn('[SHIPPO WEBHOOK] Tracking update missing required data')
    return
  }
  
  console.log('[SHIPPO WEBHOOK] Processing tracking update for:', data.tracking_number)
  console.log('[SHIPPO WEBHOOK] Current status:', data.tracking_status?.status)
  console.log('[SHIPPO WEBHOOK] Substatus:', data.tracking_status?.substatus?.text)
  if (companyId) console.log('[SHIPPO WEBHOOK] Company ID:', companyId)
  
  try {
    // Build query filter
    let query = { tracking_number: data.tracking_number }
    if (companyId) {
      query.companyId = companyId
    }
    
    // Find shipment by tracking number (filtered by company if provided)
    let shipment = await Shipment.findOne(query)
    
    if (!shipment && data.transaction) {
      // If not found by tracking number, try by Shippo transaction ID
      query = { shippoTransactionId: data.transaction }
      if (companyId) {
        query.companyId = companyId
      }
      shipment = await Shipment.findOne(query)
    }
    
    if (!shipment) {
      console.warn(`[SHIPPO WEBHOOK] No shipment found for tracking number: ${data.tracking_number}${companyId ? ` (company: ${companyId})` : ''}`)
      
      // If we have a companyId, we can create a new shipment record
      if (companyId) {
        console.log('[SHIPPO WEBHOOK] Creating new shipment from webhook data')
        shipment = await createShipmentFromWebhook(data, companyId)
      } else {
        return
      }
    }
    
    console.log('[SHIPPO WEBHOOK] Found/created shipment:', shipment._id)
    
    // Process the webhook update
    shipment.processWebhookUpdate(webhookData)
    
    // Save the updated shipment
    await shipment.save()
    
    console.log('[SHIPPO WEBHOOK] Shipment updated successfully')
    console.log('[SHIPPO WEBHOOK] New status:', shipment.statusDisplay)
    
    // Trigger any additional business logic
    await handleBusinessLogic(shipment, webhookData)
    
  } catch (error) {
    console.error('[SHIPPO WEBHOOK] Error updating shipment:', error)
    throw error
  }
}

// Handle business logic after status updates
async function handleBusinessLogic(shipment, webhookData) {
  const status = webhookData.data?.tracking_status?.status
  
  try {
    // Send customer notifications for key events
    if (status === 'OUT_FOR_DELIVERY' && !shipment.customerNotified) {
      console.log('[SHIPPO WEBHOOK] Shipment out for delivery, should notify customer')
      // TODO: Implement customer notification
      shipment.customerNotified = true
      await shipment.save()
    }
    
    if (status === 'DELIVERED') {
      console.log('[SHIPPO WEBHOOK] Shipment delivered')
      // TODO: Could update Eclipse ERP or trigger other systems
    }
    
    if (webhookData.data?.tracking_status?.substatus?.action_required) {
      console.log('[SHIPPO WEBHOOK] Shipment requires attention')
      // TODO: Alert operations team
    }
    
  } catch (error) {
    console.error('[SHIPPO WEBHOOK] Error in business logic:', error)
    // Don't throw - webhook processing should still succeed
  }
}

// Optional: Create shipment from webhook if we don't have it
async function createShipmentFromWebhook(data, companyId) {
  console.log('[SHIPPO WEBHOOK] Creating new shipment record from webhook data')
  
  const shipment = new Shipment({
    companyId: companyId,
    tracking_number: data.tracking_number,
    carrier: data.carrier,
    servicelevel: data.servicelevel,
    address_from: data.address_from,
    address_to: data.address_to,
    tracking_status: data.tracking_status,
    eta: data.eta ? new Date(data.eta) : null,
    internalStatus: 'IN_TRANSIT',
    isTestShipment: data.test || false,
    shippoTransactionId: data.transaction,
    metadata: {
      createdFromWebhook: true,
      webhookTimestamp: new Date().toISOString()
    }
  })
  
  await shipment.save()
  console.log('[SHIPPO WEBHOOK] Created shipment:', shipment._id)
  
  return shipment
}

// Handle transaction events (created/updated) - could be used to create initial shipment records
async function handleTransactionEvent(webhookData, companyId) {
  const { data, event } = webhookData
  
  console.log(`[SHIPPO WEBHOOK] Processing ${event} for company ${companyId}`)
  console.log('[SHIPPO WEBHOOK] Transaction ID:', data?.object_id)
  
  // In the future, this could be used to:
  // 1. Create shipment records when labels are purchased
  // 2. Update shipping costs and service levels
  // 3. Link transactions to specific orders or invoices
  
  // For now, just log the event
  console.log('[SHIPPO WEBHOOK] Transaction event logged - no action taken')
}

// Health check endpoint for webhook testing
router.get('/webhook/health', (req, res) => {
  res.json({ 
    status: 'ok',
    message: 'Shippo webhook endpoint is ready',
    timestamp: new Date().toISOString()
  })
})

// Test endpoint to simulate webhook (for development)
router.post('/webhook/test', async (req, res) => {
  if (process.env.NODE_ENV === 'production') {
    return res.status(404).json({ error: 'Test endpoint not available in production' })
  }
  
  const testWebhookData = {
    event: 'track_updated',
    test: true,
    data: {
      tracking_number: req.body.tracking_number || 'TEST123456789',
      carrier: 'ups',
      tracking_status: {
        status: 'IN_TRANSIT',
        substatus: {
          code: 'in_transit',
          text: 'Your package is in transit',
          action_required: false
        },
        datetime: new Date().toISOString()
      }
    }
  }
  
  try {
    await handleTrackingUpdate(testWebhookData)
    res.json({ success: true, message: 'Test webhook processed' })
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

export default router