import express from 'express'
import Shipment from '../models/Shipment.js'
import decodeToken from '../middleware/decodeToken.js'
import { createShipmentFromShipStation } from '../controllers/shipmentController.js'

const router = express.Router()

// GET /api/shipments/tracking-test-mode - Get tracking test mode setting (supports API auth)
router.get('/tracking-test-mode', async (req, res) => {
  try {
    const { api_user, api_key } = req.query
    
    // If API credentials provided, get test mode for that specific company
    if (api_user && api_key) {
      const Company = (await import('../models/Company.js')).default
      const company = await Company.findOne({
        'ship54Tracking.authMethod': 'apiUser',
        'ship54Tracking.apiUser.username': api_user,
        'ship54Tracking.apiUser.password': api_key
      })
      
      if (company) {
        const testMode = company.ship54Settings?.shipping?.trackingTestMode || false
        return res.json({ testMode, companyName: company.name })
      }
    }
    
    // Fallback: check if any company has test mode enabled
    const Company = (await import('../models/Company.js')).default
    const company = await Company.findOne({
      'ship54Settings.shipping.trackingTestMode': true
    })
    
    const testMode = company ? true : false
    res.json({ testMode })
  } catch (error) {
    console.error('[SHIPMENTS] Error getting test mode:', error)
    res.json({ testMode: false }) // Default to false on error
  }
})

// GET /api/shipments/by-invoice/:invoiceNumber - Get all shipments for an invoice (for Eclipse ERP integration)
// Note: This endpoint supports API user authentication for Eclipse ERP integration and test mode
router.get('/by-invoice/:invoiceNumber', async (req, res) => {
  console.log('[SHIPMENTS] GET /by-invoice route hit - invoice:', req.params.invoiceNumber)
  try {
    const { invoiceNumber } = req.params
    const { api_user, api_key, testMode } = req.query
    
    // Handle test mode - generate test shipments with Shippo test tracking numbers
    if (testMode === 'true') {
      console.log('[SHIPMENTS] Test mode active - generating test shipments with Shippo test tracking numbers')
      return res.json(await generateTestShipmentData(invoiceNumber))
    }
    
    // If API credentials provided, validate them
    if (api_user && api_key) {
      const Company = (await import('../models/Company.js')).default
      const company = await Company.findOne({
        'ship54Tracking.authMethod': 'apiUser',
        'ship54Tracking.apiUser.username': api_user,
        'ship54Tracking.apiUser.password': api_key
      })
      
      if (!company) {
        return res.status(401).json({
          success: false,
          message: 'Invalid API credentials'
        })
      }
      
      console.log('[SHIPMENTS] API authentication successful for company:', company.name)
      
      // Find shipments for this company only
      const shipments = await Shipment.find({
        companyId: company._id,
        invoiceNumber: new RegExp(`^${invoiceNumber}`, 'i')
      }).sort({ createdAt: -1 })
      
      console.log(`[SHIPMENTS] Found ${shipments.length} shipments for invoice ${invoiceNumber} (company: ${company.name})`)
      
      // Return response with company context
      return res.json({
        success: true,
        invoiceNumber,
        shipmentCount: shipments.length,
        companyName: company.name,
        shipments: formatShipmentData(shipments)
      })
    }
    
    // Fallback: search all shipments (for backwards compatibility)
    const shipments = await Shipment.find({
      invoiceNumber: new RegExp(`^${invoiceNumber}`, 'i') // Match exact or with suffixes
    }).sort({ createdAt: -1 })
    
    console.log(`[SHIPMENTS] Found ${shipments.length} shipments for invoice ${invoiceNumber}`)
    
    return res.json({
      success: true,
      invoiceNumber,
      shipmentCount: shipments.length,
      shipments: formatShipmentData(shipments)
    })

  } catch (error) {
    console.error('[SHIPMENTS] Error in by-invoice route:', error)
    res.status(500).json({
      success: false,
      message: 'Failed to retrieve shipments for invoice',
      error: error.message
    })
  }
})

// Helper function to format shipment data for API response
function formatShipmentData(shipments) {
  return shipments.map(shipment => ({
    shipmentId: shipment._id,
    invoiceNumber: shipment.invoiceNumber,
    trackingNumber: shipment.tracking_number || shipment.shippoTrackingNumber,
    carrier: shipment.carrier,
    internalStatus: shipment.internalStatus,
    tracking_status: shipment.tracking_status?.status,
    tracking_status_details: shipment.tracking_status?.status_details,
    shippoLabelUrl: shipment.shippoLabelUrl,
    createdAt: shipment.createdAt,
    address_to: {
      name: shipment.address_to?.name,
      city: shipment.address_to?.city,
      state: shipment.address_to?.state
    },
    cost: shipment.cost,
    metadata: shipment.metadata,
    tracking_history: shipment.tracking_history || []
  }))
}

// GET /api/shipments - List shipments with filtering and pagination
router.get('/', decodeToken, async (req, res) => {
  console.log('[SHIPMENTS] GET / route hit - query params:', req.query)
  try {
    const { 
      page = 1, 
      limit = 50, 
      status, 
      carrier, 
      invoiceNumber,
      trackingNumber,
      dateFrom,
      dateTo,
      needsAttention,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query
    
    const companyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    
    console.log('[SHIPMENTS] Extracted company ID:', companyId)
    
    // Build filter query
    const filter = { companyId }
    
    if (status) filter.internalStatus = status
    if (carrier) filter.carrier = new RegExp(carrier, 'i')
    if (invoiceNumber) filter.invoiceNumber = new RegExp(invoiceNumber, 'i')
    if (trackingNumber) filter.tracking_number = new RegExp(trackingNumber, 'i')
    if (needsAttention === 'true') filter.needsAttention = true
    
    // Date range filter
    if (dateFrom || dateTo) {
      filter.createdAt = {}
      if (dateFrom) filter.createdAt.$gte = new Date(dateFrom)
      if (dateTo) filter.createdAt.$lte = new Date(dateTo)
    }
    
    console.log('[SHIPMENTS] Query filter:', JSON.stringify(filter, null, 2))
    
    // Build sort object
    const sort = {}
    sort[sortBy] = sortOrder === 'desc' ? -1 : 1
    
    // Execute paginated query
    const skip = (parseInt(page) - 1) * parseInt(limit)
    
    const [shipments, total] = await Promise.all([
      Shipment.find(filter)
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      Shipment.countDocuments(filter)
    ])
    
    // Add computed fields
    const enrichedShipments = shipments.map(shipment => ({
      ...shipment,
      statusDisplay: shipment.tracking_status?.substatus?.text || 
                    shipment.tracking_status?.status || 
                    shipment.internalStatus,
      daysSinceShipped: shipment.shipDate ? 
        Math.floor((new Date() - new Date(shipment.shipDate)) / (1000 * 60 * 60 * 24)) : null,
      isOverdue: shipment.eta && new Date() > new Date(shipment.eta) && 
                 !['DELIVERED', 'RETURNED'].includes(shipment.internalStatus)
    }))
    
    res.json({
      shipments: enrichedShipments,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      }
    })
    
  } catch (error) {
    console.error('[SHIPMENTS] Error fetching shipments:', error)
    res.status(500).json({ error: 'Failed to fetch shipments' })
  }
})

// GET /api/shipments/summary/stats - Get shipment statistics
router.get('/summary/stats', decodeToken, async (req, res) => {
  try {
    const companyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const { days = 30 } = req.query
    
    console.log('[SHIPMENTS STATS] Extracted company ID:', companyId)
    
    const dateFilter = {
      createdAt: { $gte: new Date(Date.now() - days * 24 * 60 * 60 * 1000) },
      companyId
    }
    
    const [
      totalShipments,
      statusBreakdown,
      carrierBreakdown,
      needingAttention,
      avgDeliveryTime,
      totalCost
    ] = await Promise.all([
      // Total shipments
      Shipment.countDocuments(dateFilter),
      
      // Status breakdown
      Shipment.aggregate([
        { $match: dateFilter },
        { $group: { _id: '$internalStatus', count: { $sum: 1 } } }
      ]),
      
      // Carrier breakdown
      Shipment.aggregate([
        { $match: dateFilter },
        { $group: { _id: '$carrier', count: { $sum: 1 } } }
      ]),
      
      // Needing attention
      Shipment.countDocuments({ ...dateFilter, needsAttention: true }),
      
      // Average delivery time (for delivered packages)
      Shipment.aggregate([
        { 
          $match: { 
            ...dateFilter, 
            internalStatus: 'DELIVERED',
            shipDate: { $exists: true },
            deliveryDate: { $exists: true }
          }
        },
        {
          $group: {
            _id: null,
            avgDays: {
              $avg: {
                $divide: [
                  { $subtract: ['$deliveryDate', '$shipDate'] },
                  1000 * 60 * 60 * 24
                ]
              }
            }
          }
        }
      ]),
      
      // Total shipping cost
      Shipment.aggregate([
        { $match: dateFilter },
        {
          $group: {
            _id: null,
            total: { $sum: { $toDouble: '$cost.amount' } }
          }
        }
      ])
    ])
    
    res.json({
      period_days: parseInt(days),
      total_shipments: totalShipments,
      status_breakdown: statusBreakdown.reduce((acc, item) => {
        acc[item._id] = item.count
        return acc
      }, {}),
      carrier_breakdown: carrierBreakdown.reduce((acc, item) => {
        acc[item._id] = item.count
        return acc
      }, {}),
      needing_attention: needingAttention,
      avg_delivery_days: avgDeliveryTime[0]?.avgDays ? 
        Math.round(avgDeliveryTime[0].avgDays * 10) / 10 : null,
      total_shipping_cost: totalCost[0]?.total || 0
    })
    
  } catch (error) {
    console.error('[SHIPMENTS] Error fetching stats:', error)
    res.status(500).json({ error: 'Failed to fetch shipment statistics' })
  }
})

// GET /api/shipments/:id - Get specific shipment details
router.get('/:id', decodeToken, async (req, res) => {
  try {
    const shipment = await Shipment.findOne({
      _id: req.params.id,
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    })
    
    if (!shipment) {
      return res.status(404).json({ error: 'Shipment not found' })
    }
    
    res.json(shipment)
    
  } catch (error) {
    console.error('[SHIPMENTS] Error fetching shipment:', error)
    res.status(500).json({ error: 'Failed to fetch shipment' })
  }
})

// POST /api/shipments/create-from-shipstation - Create shipment from ShipStation workflow
router.post('/create-from-shipstation', decodeToken, async (req, res) => {
  try {
    const { shippoData, shipmentData } = req.body
    
    const userContext = {
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId,
      userId: req.user.id
    }

    // Merge shipmentData into shippoData if provided
    const enhancedShippoData = {
      ...shippoData,
      ...(shipmentData && {
        metadata: {
          ...shippoData.metadata,
          ...shipmentData.metadata
        }
      })
    }

    const shipment = await createShipmentFromShipStation(enhancedShippoData, userContext)
    res.status(201).json(shipment)
    
  } catch (error) {
    console.error('[SHIPMENTS] Error creating shipment from ShipStation:', error)
    res.status(400).json({ 
      error: 'Failed to create shipment from ShipStation',
      details: error.message 
    })
  }
})

// POST /api/shipments - Create new shipment record (called from ShipStation)
router.post('/', decodeToken, async (req, res) => {
  try {
    const companyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const userId = req.user.id
    
    console.log('[SHIPMENTS CREATE] Extracted company ID:', companyId)
    
    const shipmentData = {
      ...req.body,
      companyId,
      userId,
      internalStatus: 'CREATED'
    }
    
    console.log('[SHIPMENTS] Creating shipment:', JSON.stringify(shipmentData, null, 2))
    
    const shipment = new Shipment(shipmentData)
    await shipment.save()
    
    console.log('[SHIPMENTS] Created shipment:', shipment._id)
    
    res.status(201).json(shipment)
    
  } catch (error) {
    console.error('[SHIPMENTS] Error creating shipment:', error)
    res.status(400).json({ 
      error: 'Failed to create shipment',
      details: error.message 
    })
  }
})

// PUT /api/shipments/:id - Update shipment (manual updates)
router.put('/:id', decodeToken, async (req, res) => {
  try {
    const shipment = await Shipment.findOne({
      _id: req.params.id,
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    })
    
    if (!shipment) {
      return res.status(404).json({ error: 'Shipment not found' })
    }
    
    // Only allow certain fields to be manually updated
    const allowedUpdates = [
      'invoiceNumber', 
      'orderId', 
      'metadata', 
      'shipDate',
      'internalStatus',
      'needsAttention'
    ]
    
    const updates = {}
    allowedUpdates.forEach(field => {
      if (req.body[field] !== undefined) {
        updates[field] = req.body[field]
      }
    })
    
    Object.assign(shipment, updates)
    await shipment.save()
    
    console.log('[SHIPMENTS] Updated shipment:', shipment._id)
    
    res.json(shipment)
    
  } catch (error) {
    console.error('[SHIPMENTS] Error updating shipment:', error)
    res.status(400).json({ 
      error: 'Failed to update shipment',
      details: error.message 
    })
  }
})

// GET /api/shipments/:id/tracking - Get tracking history for shipment
router.get('/:id/tracking', decodeToken, async (req, res) => {
  try {
    const shipment = await Shipment.findOne({
      _id: req.params.id,
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    }).select('tracking_history tracking_number carrier tracking_status eta')
    
    if (!shipment) {
      return res.status(404).json({ error: 'Shipment not found' })
    }
    
    // Sort tracking history by date (newest first)
    const trackingHistory = [...shipment.tracking_history]
      .sort((a, b) => new Date(b.datetime) - new Date(a.datetime))
    
    res.json({
      tracking_number: shipment.tracking_number,
      carrier: shipment.carrier,
      current_status: shipment.tracking_status,
      eta: shipment.eta,
      tracking_history: trackingHistory
    })
    
  } catch (error) {
    console.error('[SHIPMENTS] Error fetching tracking:', error)
    res.status(500).json({ error: 'Failed to fetch tracking information' })
  }
})


// POST /api/shipments/:id/refresh-tracking - Manually refresh tracking (future feature)
router.post('/:id/refresh-tracking', decodeToken, async (req, res) => {
  try {
    const shipment = await Shipment.findOne({
      _id: req.params.id,
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    })
    
    if (!shipment) {
      return res.status(404).json({ error: 'Shipment not found' })
    }
    
    // TODO: Call Shippo API to get latest tracking info
    // For now, just return current status
    console.log('[SHIPMENTS] Manual tracking refresh requested for:', shipment.tracking_number)
    
    res.json({
      message: 'Tracking refresh requested',
      tracking_number: shipment.tracking_number,
      last_updated: shipment.lastWebhookReceived
    })
    
  } catch (error) {
    console.error('[SHIPMENTS] Error refreshing tracking:', error)
    res.status(500).json({ error: 'Failed to refresh tracking' })
  }
})


// POST /api/shipments/create-manual - Create manual shipment with Shippo integration
router.post('/create-manual', decodeToken, async (req, res) => {
  try {
    const { from, to, details, source } = req.body
    const companyId = typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    const userId = req.user.id
    
    console.log('[MANUAL SHIPMENT] Creating manual shipment for company:', companyId)
    
    // Validate required fields
    if (!to.name || !to.addressLine1 || !to.city || !to.state || !to.postalCode) {
      return res.status(400).json({ error: 'Missing required shipping address fields' })
    }
    
    if (!details.carrier || !details.weight || details.weight <= 0) {
      return res.status(400).json({ error: 'Missing required shipment details (carrier, weight)' })
    }
    
    // Get company's Shippo token
    const Company = (await import('../models/Company.js')).default
    const company = await Company.findById(companyId)
    if (!company) {
      return res.status(400).json({ error: 'Company not found' })
    }
    
    const shippoSettings = company.ship54Settings?.shippo
    if (!shippoSettings?.customerToken?.encrypted) {
      return res.status(400).json({ error: 'Company Shippo token not configured' })
    }
    
    // Decrypt and use Shippo token
    const { decryptToken } = await import('../utils/encryption.js')
    const shippoToken = decryptToken(shippoSettings.customerToken.encrypted)
    
    // Create Shippo shipment
    const shippoResponse = await fetch('https://api.goshippo.com/shipments/', {
      method: 'POST',
      headers: {
        'Authorization': `ShippoToken ${shippoToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        address_from: {
          name: from.name,
          street1: from.addressLine1,
          street2: from.addressLine2 || '',
          city: from.city,
          state: from.state,
          zip: from.postalCode,
          country: 'US',
          phone: from.phone || '',
          email: from.email || ''
        },
        address_to: {
          name: to.name,
          street1: to.addressLine1,
          street2: to.addressLine2 || '',
          city: to.city,
          state: to.state,
          zip: to.postalCode,
          country: 'US',
          phone: to.phone || ''
        },
        parcels: [{
          length: '12',
          width: '12',
          height: '6',
          distance_unit: 'in',
          weight: details.weight.toString(),
          mass_unit: 'lb'
        }],
        shipment_date: new Date().toISOString()
      })
    })
    
    if (!shippoResponse.ok) {
      const errorText = await shippoResponse.text()
      console.error('[MANUAL SHIPMENT] Shippo API error:', errorText)
      return res.status(400).json({ error: 'Failed to create Shippo shipment', details: errorText })
    }
    
    const shippoData = await shippoResponse.json()
    console.log('[MANUAL SHIPMENT] Shippo shipment created:', shippoData.object_id)
    
    // Find the best rate for the specified carrier
    const carrierMap = { ups: 'UPS', fedex: 'FedEx', usps: 'USPS' }
    const carrierName = carrierMap[details.carrier] || details.carrier.toUpperCase()
    
    const selectedRate = shippoData.rates.find(rate => 
      rate.provider.toUpperCase() === carrierName
    ) || shippoData.rates[0]
    
    if (!selectedRate) {
      return res.status(400).json({ error: 'No shipping rates available for selected carrier' })
    }
    
    // Purchase the label
    const transactionResponse = await fetch('https://api.goshippo.com/transactions/', {
      method: 'POST',
      headers: {
        'Authorization': `ShippoToken ${shippoToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        rate: selectedRate.object_id,
        label_file_type: 'PDF'
      })
    })
    
    if (!transactionResponse.ok) {
      const errorText = await transactionResponse.text()
      console.error('[MANUAL SHIPMENT] Transaction creation error:', errorText)
      return res.status(400).json({ error: 'Failed to purchase shipping label', details: errorText })
    }
    
    const transactionData = await transactionResponse.json()
    
    // Create shipment record
    const shipmentData = {
      companyId,
      userId,
      carrier: selectedRate.provider,
      servicelevel: selectedRate.servicelevel.name,
      tracking_number: transactionData.tracking_number,
      address_from: shippoData.address_from,
      address_to: shippoData.address_to,
      cost: {
        amount: selectedRate.amount || '0.00',
        currency: selectedRate.currency || 'USD'
      },
      retail_cost: {
        amount: selectedRate.amount_local || selectedRate.amount || '0.00',
        currency: selectedRate.currency_local || selectedRate.currency || 'USD'
      },
      invoiceNumber: details.invoiceNumber || null,
      orderId: details.poNumber || null,
      shipDate: new Date(),
      internalStatus: 'LABEL_PURCHASED',
      shippoTransactionId: transactionData.object_id,
      shippoShipmentId: shippoData.object_id,
      labelUrl: transactionData.label_url,
      commercialInvoiceUrl: transactionData.commercial_invoice_url,
      metadata: {
        source: source || 'manual',
        manualEntry: true,
        description: details.description,
        declaredValue: details.value
      },
      isTestShipment: transactionData.test || false
    }
    
    const shipment = new Shipment(shipmentData)
    await shipment.save()
    
    console.log('[MANUAL SHIPMENT] Created shipment record:', shipment._id)
    
    res.status(201).json({
      ...shipment.toObject(),
      label_url: transactionData.label_url,
      tracking_url: transactionData.tracking_url_provider
    })
    
  } catch (error) {
    console.error('[MANUAL SHIPMENT] Error creating manual shipment:', error)
    res.status(500).json({ 
      error: 'Failed to create manual shipment',
      details: error.message 
    })
  }
})

// DELETE /api/shipments/:id - Delete shipment (admin only)
router.delete('/:id', decodeToken, async (req, res) => {
  try {
    // Check if user has admin privileges
    if (req.user.userType !== 'admin') {
      return res.status(403).json({ error: 'Admin access required' })
    }
    
    const shipment = await Shipment.findOne({
      _id: req.params.id,
      companyId: typeof req.user.companyId === 'object' ? req.user.companyId._id : req.user.companyId
    })
    
    if (!shipment) {
      return res.status(404).json({ error: 'Shipment not found' })
    }
    
    await Shipment.findByIdAndDelete(req.params.id)
    
    console.log('[SHIPMENTS] Deleted shipment:', req.params.id)
    
    res.json({ message: 'Shipment deleted successfully' })
    
  } catch (error) {
    console.error('[SHIPMENTS] Error deleting shipment:', error)
    res.status(500).json({ error: 'Failed to delete shipment' })
  }
})

// Generate test shipment data using real Shippo test tracking numbers
async function generateTestShipmentData(invoiceNumber) {
  const testTrackingNumbers = [
    'SHIPPO_PRE_TRANSIT',
    'SHIPPO_TRANSIT', 
    'SHIPPO_DELIVERED',
    'SHIPPO_RETURNED',
    'SHIPPO_FAILURE',
    'SHIPPO_UNKNOWN'
  ]
  
  const testShipments = []
  
  // Create test shipments for different scenarios
  for (let i = 0; i < Math.min(3, testTrackingNumbers.length); i++) {
    const trackingNumber = testTrackingNumbers[i]
    const shipmentId = `test-${invoiceNumber}-${i + 1}`
    
    // Get real tracking data from Shippo using test tracking number
    let shippoTrackingData = null
    try {
      // Use Shippo test API with test tracking number
      const shippoResponse = await fetch('https://api.goshippo.com/tracks/', {
        method: 'POST',
        headers: {
          'Authorization': `ShippoToken ${process.env.VITE_SHIPPO_API_KEY || 'shippo_test_fb4523a2ea15b8fba292d70ca41b939e2ea0d096'}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          carrier: 'shippo',
          tracking_number: trackingNumber
        })
      })
      
      if (shippoResponse.ok) {
        shippoTrackingData = await shippoResponse.json()
        console.log(`[TEST MODE] Got Shippo test data for ${trackingNumber}:`, shippoTrackingData.tracking_status?.status)
      } else {
        console.warn(`[TEST MODE] Failed to get Shippo data for ${trackingNumber}`)
      }
    } catch (error) {
      console.error(`[TEST MODE] Error fetching Shippo test data for ${trackingNumber}:`, error)
    }
    
    // Create test shipment record
    const testShipment = {
      shipmentId,
      invoiceNumber,
      trackingNumber,
      carrier: 'shippo',
      internalStatus: mapShippoStatusToInternal(shippoTrackingData?.tracking_status?.status || 'UNKNOWN'),
      tracking_status: shippoTrackingData?.tracking_status?.status || 'UNKNOWN',
      tracking_status_details: shippoTrackingData?.tracking_status?.status_details || `Test tracking for ${trackingNumber}`,
      shippoLabelUrl: '#test-label',
      createdAt: new Date(Date.now() - (i + 1) * 24 * 60 * 60 * 1000).toISOString(),
      address_to: {
        name: `Test Customer ${i + 1}`,
        city: ['Chicago', 'New York', 'Los Angeles'][i] || 'Test City',
        state: ['IL', 'NY', 'CA'][i] || 'TS'
      },
      cost: { 
        amount: (12.99 + i * 5).toFixed(2), 
        currency: 'USD' 
      },
      tracking_history: shippoTrackingData?.tracking_history || [
        {
          status: 'PACKAGE_ACCEPTED',
          status_details: `Test package accepted for ${trackingNumber}`,
          status_date: new Date(Date.now() - (i + 2) * 24 * 60 * 60 * 1000).toISOString(),
          location: { city: 'Test Origin', state: 'TX', country: 'US' }
        }
      ],
      metadata: {
        testMode: true,
        shippoTestNumber: trackingNumber
      }
    }
    
    testShipments.push(testShipment)
  }
  
  return {
    success: true,
    invoiceNumber,
    shipmentCount: testShipments.length,
    companyName: 'Test Company',
    testMode: true,
    shipments: testShipments
  }
}

// Map Shippo status to internal status
function mapShippoStatusToInternal(shippoStatus) {
  const statusMap = {
    'PRE_TRANSIT': 'LABEL_PURCHASED',
    'TRANSIT': 'IN_TRANSIT', 
    'DELIVERED': 'DELIVERED',
    'RETURNED': 'RETURNED',
    'FAILURE': 'EXCEPTION',
    'UNKNOWN': 'UNKNOWN'
  }
  return statusMap[shippoStatus] || 'UNKNOWN'
}

export default router