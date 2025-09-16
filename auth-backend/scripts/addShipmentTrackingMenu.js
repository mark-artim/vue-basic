import mongoose from 'mongoose'
import dotenv from 'dotenv'
import Menu from '../models/Menu.js'

dotenv.config()

async function addShipmentTrackingMenu() {
  try {
    console.log('Connecting to MongoDB...')
    await mongoose.connect(process.env.MONGODB_URI)
    console.log('Connected to MongoDB')

    // Check if Shipment Tracking menu already exists
    const existingMenu = await Menu.findOne({ name: 'Shipment Tracking' })
    
    if (existingMenu) {
      console.log('Shipment Tracking menu already exists:', existingMenu)
      return
    }

    // Create new menu item
    const shipmentTrackingMenu = new Menu({
      name: 'Shipment Tracking',
      path: '/admin/shipment-tracking',
      product: 'ship54',
      roles: ['admin'],
      isActive: true,
      order: 150, // Place it after other admin menus
      description: 'View and track shipments created through ShipStation'
    })

    await shipmentTrackingMenu.save()
    console.log('✅ Added Shipment Tracking menu item:', shipmentTrackingMenu)

  } catch (error) {
    console.error('❌ Error adding Shipment Tracking menu:', error)
  } finally {
    await mongoose.disconnect()
    console.log('Disconnected from MongoDB')
  }
}

// Run the script
addShipmentTrackingMenu()