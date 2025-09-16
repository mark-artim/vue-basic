import Shipment from '../models/Shipment.js'

/**
 * Create shipment from ShipStation workflow
 * This will be called when a label is purchased via Shippo
 */
export const createShipmentFromShipStation = async (shippoData, userContext) => {
  try {
    console.log('[SHIPMENT CONTROLLER] Creating shipment from ShipStation data')
    
    const shipment = new Shipment({
      // Shippo data
      shippoTransactionId: shippoData.object_id,
      shippoTrackingNumber: shippoData.tracking_number,
      shippoLabelUrl: shippoData.label_url,
      
      // Internal references
      companyId: userContext.companyId,
      userId: userContext.userId,
      orderId: shippoData.metadata?.orderId || shippoData.metadata?.orderNumber,
      invoiceNumber: shippoData.metadata?.invoiceNumber || shippoData.metadata?.invoice || shippoData.metadata?.fullInvoiceID,
      
      // Shipping details
      carrier: shippoData.carrier,
      servicelevel: shippoData.servicelevel,
      tracking_number: shippoData.tracking_number,
      
      // Addresses
      address_from: shippoData.address_from,
      address_to: shippoData.address_to,
      
      // Package info
      packages: shippoData.parcels || [],
      
      // Cost - Handle both transaction and rate data structures
      cost: {
        amount: shippoData.rate?.amount || shippoData.amount || '0.00',
        currency: shippoData.rate?.currency || shippoData.currency || 'USD'
      },
      retail_cost: {
        amount: shippoData.rate?.retail_amount || 
                shippoData.rate?.amount || 
                shippoData.retail_amount || 
                shippoData.amount || '0.00',
        currency: shippoData.rate?.currency || shippoData.currency || 'USD'
      },
      
      // Status
      internalStatus: 'LABEL_PURCHASED',
      shipDate: new Date(), // Assume shipped when label created
      
      // Metadata
      metadata: {
        ...shippoData.metadata,
        createdFromShipStation: true
      }
    })
    
    await shipment.save()
    console.log('[SHIPMENT CONTROLLER] Created shipment:', shipment._id)
    
    return shipment
    
  } catch (error) {
    console.error('[SHIPMENT CONTROLLER] Error creating shipment:', error)
    throw error
  }
}

/**
 * Find shipments needing attention
 * Used for dashboard alerts and maintenance tasks
 */
export const findShipmentsNeedingAttention = async (companyId) => {
  try {
    const shipments = await Shipment.find({
      companyId,
      $or: [
        { needsAttention: true },
        { 'tracking_status.substatus.action_required': true },
        {
          internalStatus: { $in: ['SHIPPED', 'IN_TRANSIT', 'LABEL_PURCHASED'] },
          lastWebhookReceived: { 
            $lt: new Date(Date.now() - 48 * 60 * 60 * 1000) // No update in 48 hours
          }
        },
        {
          eta: { $lt: new Date() }, // Past expected delivery
          internalStatus: { $nin: ['DELIVERED', 'RETURNED'] }
        }
      ]
    }).sort({ createdAt: -1 })
    
    return shipments
    
  } catch (error) {
    console.error('[SHIPMENT CONTROLLER] Error finding shipments needing attention:', error)
    throw error
  }
}

/**
 * Get recent shipments for dashboard
 */
export const getRecentShipments = async (companyId, limit = 10) => {
  try {
    const shipments = await Shipment.find({ companyId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .select('tracking_number carrier internalStatus tracking_status createdAt invoiceNumber')
      .lean()
    
    return shipments.map(shipment => ({
      ...shipment,
      statusDisplay: shipment.tracking_status?.substatus?.text || 
                    shipment.tracking_status?.status || 
                    shipment.internalStatus
    }))
    
  } catch (error) {
    console.error('[SHIPMENT CONTROLLER] Error getting recent shipments:', error)
    throw error
  }
}

/**
 * Calculate shipping costs for reporting
 */
export const calculateShippingCosts = async (companyId, dateRange = 30) => {
  try {
    const startDate = new Date(Date.now() - dateRange * 24 * 60 * 60 * 1000)
    
    const result = await Shipment.aggregate([
      {
        $match: {
          companyId,
          createdAt: { $gte: startDate }
        }
      },
      {
        $group: {
          _id: '$carrier',
          count: { $sum: 1 },
          totalCost: { $sum: { $toDouble: '$cost.amount' } },
          totalRetailCost: { $sum: { $toDouble: '$retail_cost.amount' } }
        }
      },
      {
        $sort: { totalCost: -1 }
      }
    ])
    
    const summary = {
      period_days: dateRange,
      by_carrier: result,
      total_shipments: result.reduce((sum, item) => sum + item.count, 0),
      total_cost: result.reduce((sum, item) => sum + item.totalCost, 0),
      total_retail_cost: result.reduce((sum, item) => sum + item.totalRetailCost, 0)
    }
    
    return summary
    
  } catch (error) {
    console.error('[SHIPMENT CONTROLLER] Error calculating costs:', error)
    throw error
  }
}

/**
 * Update shipment status manually (for corrections)
 */
export const updateShipmentStatus = async (shipmentId, statusData, userId) => {
  try {
    const shipment = await Shipment.findById(shipmentId)
    if (!shipment) {
      throw new Error('Shipment not found')
    }
    
    // Log manual status change
    shipment.webhookEvents.push({
      event: 'manual_update',
      test: false,
      receivedAt: new Date(),
      rawData: {
        ...statusData,
        updatedBy: userId
      }
    })
    
    // Update status
    if (statusData.internalStatus) {
      shipment.internalStatus = statusData.internalStatus
    }
    
    if (statusData.needsAttention !== undefined) {
      shipment.needsAttention = statusData.needsAttention
    }
    
    await shipment.save()
    console.log('[SHIPMENT CONTROLLER] Manually updated shipment:', shipmentId)
    
    return shipment
    
  } catch (error) {
    console.error('[SHIPMENT CONTROLLER] Error updating shipment status:', error)
    throw error
  }
}