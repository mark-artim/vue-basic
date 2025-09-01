import User from '../models/User.js'
import Company from '../models/Company.js'
import { decryptToken } from './encryption.js'

/**
 * Get valid Shippo API token for a user (from company customer token)
 */
export async function getShippoAPIToken(userId) {
  const user = await User.findById(userId).populate('companyId')
  if (!user) {
    throw new Error('User not found')
  }
  
  if (!user.companyId) {
    throw new Error('User has no associated company')
  }
  
  const company = user.companyId
  if (!company.ship54Settings?.shippo?.customerToken?.encrypted) {
    throw new Error('No Shippo API token found for this company')
  }

  if (!company.ship54Settings.shippo.customerToken.isValid) {
    throw new Error('Shippo API token is not valid for this company')
  }

  // Decrypt and return the customer token
  return decryptToken(company.ship54Settings.shippo.customerToken.encrypted)
}

/**
 * Make authenticated API call to Shippo using customer token
 */
export async function makeShippoAPICall(userId, endpoint, options = {}) {
  try {
    const apiToken = await getShippoAPIToken(userId)
    
    const response = await fetch(`https://api.goshippo.com${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `ShippoToken ${apiToken}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    if (!response.ok) {
      const errorData = await response.text()
      console.error(`[Shippo API] Request failed for ${endpoint}:`, errorData)
      throw new Error(`Shippo API request failed: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`[Shippo API] Error calling ${endpoint}:`, error)
    throw error
  }
}

/**
 * Test Shippo connection by fetching account info using customer token
 */
export async function testShippoConnection(userId) {
  try {
    const accountInfo = await makeShippoAPICall(userId, '/account/')
    return {
      success: true,
      accountInfo
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    }
  }
}