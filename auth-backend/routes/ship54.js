import express from 'express'
import jwt from 'jsonwebtoken'
import User from '../models/User.js'
import decodeToken from '../middleware/decodeToken.js'

const router = express.Router()

// Get user's Ship54 settings
router.get('/settings', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const user = await User.findById(userId)
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }

    // Return Ship54 settings or defaults
    const settings = user.ship54Settings || {
      shippo: {
        connected: false,
        accountInfo: null
      },
      freight: {
        defaultMethod: 'filedrop',
        productId: ''
      },
      shipping: {
        enableAutoSearch: true,
        defaultShipViaKeywords: 'UPS, FEDEX',
        defaultBranch: ''
      }
    }

    res.json(settings)
  } catch (err) {
    console.error('Failed to get Ship54 settings:', err)
    res.status(500).json({ error: 'Failed to load settings' })
  }
})

// Update user's Ship54 settings
router.put('/settings', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const newSettings = req.body

    // Validate settings structure
    if (!newSettings || typeof newSettings !== 'object') {
      return res.status(400).json({ error: 'Invalid settings format' })
    }

    const user = await User.findById(userId)
    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }

    // Update settings
    user.ship54Settings = {
      ...user.ship54Settings,
      ...newSettings
    }

    await user.save()

    res.json({ 
      success: true, 
      message: 'Settings updated successfully',
      settings: user.ship54Settings 
    })
  } catch (err) {
    console.error('Failed to update Ship54 settings:', err)
    res.status(500).json({ error: 'Failed to save settings' })
  }
})

// Initiate Shippo OAuth connection
router.post('/shippo/connect', decodeToken, async (req, res) => {
  try {
    // TODO: Implement when Shippo OAuth credentials are available
    // For now, return a placeholder
    res.status(501).json({ 
      error: 'Shippo OAuth not yet implemented',
      message: 'Waiting for Shippo partner credentials to implement OAuth flow'
    })
  } catch (err) {
    console.error('Shippo connection error:', err)
    res.status(500).json({ error: 'Failed to initiate Shippo connection' })
  }
})

// Handle Shippo OAuth callback
router.get('/shippo/callback', async (req, res) => {
  try {
    // TODO: Implement when Shippo OAuth credentials are available
    res.status(501).json({ 
      error: 'Shippo OAuth not yet implemented',
      message: 'Waiting for Shippo partner credentials to implement OAuth flow'
    })
  } catch (err) {
    console.error('Shippo callback error:', err)
    res.status(500).json({ error: 'OAuth callback failed' })
  }
})

// Disconnect Shippo account
router.delete('/shippo/disconnect', decodeToken, async (req, res) => {
  try {
    const userId = req.user.userId
    const user = await User.findById(userId)
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }

    // Clear Shippo connection
    if (user.ship54Settings) {
      user.ship54Settings.shippo = {
        connected: false,
        accountInfo: null
      }
      // Note: In production, we'd also revoke the OAuth token with Shippo
    }

    await user.save()

    res.json({ 
      success: true, 
      message: 'Shippo account disconnected successfully' 
    })
  } catch (err) {
    console.error('Failed to disconnect Shippo:', err)
    res.status(500).json({ error: 'Failed to disconnect Shippo account' })
  }
})

export default router