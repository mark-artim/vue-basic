import mongoose from 'mongoose'

// Based on Shippo webhook documentation structure
const trackingStatusSchema = new mongoose.Schema({
  status: String,                    // DELIVERED, IN_TRANSIT, etc.
  substatus: {
    code: String,                    // information_received, out_for_delivery, etc.
    text: String,                    // Human readable description
    action_required: Boolean         // Whether action is needed
  },
  location: {
    city: String,
    state: String,
    country: String,
    zip: String
  },
  datetime: Date                     // When this status occurred
}, { _id: false })

const addressSchema = new mongoose.Schema({
  name: String,
  company: String,
  street1: String,
  street2: String,
  city: String,
  state: String,
  zip: String,
  country: String,
  phone: String,
  email: String
}, { _id: false })

const shipmentSchema = new mongoose.Schema({
  // Shippo Integration Fields
  shippoTransactionId: String,       // Shippo transaction ID
  shippoTrackingNumber: String,      // Carrier tracking number from Shippo
  shippoLabelUrl: String,            // URL to shipping label PDF
  
  // Internal Reference Fields  
  orderId: String,                   // Your internal order ID
  invoiceNumber: String,             // Eclipse ERP invoice number
  companyId: String,                 // Reference to company
  userId: String,                    // User who created shipment
  
  // Core Tracking Data (from Shippo webhooks)
  carrier: String,                   // ups, fedex, usps, etc.
  servicelevel: {
    name: String,                    // Ground, Express, etc.
    token: String                    // Servicelevel token
  },
  
  // Current Status (updated by webhooks)
  tracking_status: trackingStatusSchema,  // Current status from latest webhook
  
  // Addresses (from original shipment creation)
  address_from: addressSchema,
  address_to: addressSchema,
  
  // Package Information
  packages: [{
    length: Number,
    width: Number, 
    height: Number,
    distance_unit: String,           // in, cm
    weight: Number,
    mass_unit: String                // lb, kg
  }],
  
  // Cost Information
  cost: {
    amount: String,                  // Shippo returns as string
    currency: String
  },
  retail_cost: {                     // Customer-facing cost
    amount: String,
    currency: String
  },
  
  // Tracking Details
  tracking_number: String,           // Primary tracking number
  eta: Date,                         // Estimated delivery from carrier
  tracking_history: [trackingStatusSchema], // Full history from webhooks
  
  // Metadata & Custom Fields
  metadata: {
    customerPO: String,
    specialInstructions: String,
    isInsured: Boolean,
    insuranceAmount: Number,
    orderValue: Number
  },
  
  // Important Dates
  shipDate: Date,                    // When physically shipped
  deliveryDate: Date,                // Actual delivery date
  
  // Webhook Management
  lastWebhookReceived: Date,
  webhookEvents: [{
    event: String,                   // track_updated, etc.
    test: Boolean,                   // Was this a test webhook
    receivedAt: Date,
    rawData: mongoose.Schema.Types.Mixed  // Store full webhook payload
  }],
  
  // Internal Status Tracking
  internalStatus: {
    type: String,
    enum: ['CREATED', 'LABEL_PURCHASED', 'SHIPPED', 'IN_TRANSIT', 'DELIVERED', 'EXCEPTION', 'RETURNED'],
    default: 'CREATED'
  },
  
  // Flags for business logic
  isTestShipment: { type: Boolean, default: false },
  needsAttention: { type: Boolean, default: false },
  customerNotified: { type: Boolean, default: false }
  
}, {
  timestamps: true,
  collection: 'shipments'
})

// Indexes for efficient queries
shipmentSchema.index({ shippoTransactionId: 1 }, { unique: true })
shipmentSchema.index({ tracking_number: 1 })
shipmentSchema.index({ companyId: 1, createdAt: -1 })
shipmentSchema.index({ userId: 1, createdAt: -1 })
shipmentSchema.index({ invoiceNumber: 1 })
shipmentSchema.index({ 'tracking_status.status': 1 })
shipmentSchema.index({ internalStatus: 1 })

// Virtual for display-friendly status
shipmentSchema.virtual('statusDisplay').get(function() {
  if (this.tracking_status?.substatus?.text) {
    return this.tracking_status.substatus.text
  }
  return this.tracking_status?.status || this.internalStatus
})

// Method to process Shippo webhook data
shipmentSchema.methods.processWebhookUpdate = function(webhookData) {
  const { event, test, data } = webhookData
  
  // Log the webhook event
  this.webhookEvents.push({
    event,
    test: test || false,
    receivedAt: new Date(),
    rawData: webhookData
  })
  
  if (event === 'track_updated' && data) {
    // Update tracking status
    if (data.tracking_status) {
      this.tracking_status = data.tracking_status
    }
    
    // Update ETA if provided
    if (data.eta) {
      this.eta = new Date(data.eta)
    }
    
    // Add to tracking history
    if (data.tracking_status) {
      this.tracking_history.push({
        ...data.tracking_status,
        datetime: data.tracking_status.datetime ? new Date(data.tracking_status.datetime) : new Date()
      })
    }
    
    // Update internal status based on tracking
    this.updateInternalStatus(data.tracking_status)
    
    // Set delivery date if delivered
    if (data.tracking_status?.status === 'DELIVERED') {
      this.deliveryDate = new Date(data.tracking_status.datetime || new Date())
      this.internalStatus = 'DELIVERED'
    }
  }
  
  this.lastWebhookReceived = new Date()
  
  // Check if needs attention (failure, exception, etc.)
  if (data.tracking_status?.substatus?.action_required) {
    this.needsAttention = true
  }
}

// Helper method to map Shippo status to internal status
shipmentSchema.methods.updateInternalStatus = function(trackingStatus) {
  if (!trackingStatus) return
  
  const statusMap = {
    'DELIVERED': 'DELIVERED',
    'IN_TRANSIT': 'IN_TRANSIT', 
    'OUT_FOR_DELIVERY': 'IN_TRANSIT',
    'AVAILABLE_FOR_PICKUP': 'IN_TRANSIT',
    'RETURN_TO_SENDER': 'RETURNED',
    'FAILURE': 'EXCEPTION',
    'UNKNOWN': 'SHIPPED' // Default to shipped if unknown
  }
  
  if (statusMap[trackingStatus.status]) {
    this.internalStatus = statusMap[trackingStatus.status]
  }
}

// Static method to find shipments that need manual review
shipmentSchema.statics.findNeedingAttention = function() {
  return this.find({
    $or: [
      { needsAttention: true },
      { 'tracking_status.substatus.action_required': true },
      { 
        internalStatus: { $in: ['SHIPPED', 'IN_TRANSIT'] },
        lastWebhookReceived: { $lt: new Date(Date.now() - 48 * 60 * 60 * 1000) } // No update in 48h
      }
    ]
  })
}

export default mongoose.model('Shipment', shipmentSchema)