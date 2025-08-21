import mongoose from 'mongoose'
import Menu from '../models/Menu.js'
import dotenv from 'dotenv'

dotenv.config()

async function addShip54Menu() {
  try {
    await mongoose.connect(process.env.MONGODB_URI)
    console.log('Connected to MongoDB')

    // Check if Ship54 Settings menu already exists
    const existingMenu = await Menu.findOne({ 
      path: '/ship54-settings',
      product: 'ship54' 
    })

    if (existingMenu) {
      console.log('Ship54 Settings menu already exists')
      return
    }

    // Create Ship54 Settings menu
    const ship54Menu = new Menu({
      name: 'Ship54 Settings',
      path: '/ship54-settings',
      product: 'ship54',
      roles: ['customer', 'shipping_manager']
    })

    await ship54Menu.save()
    console.log('✅ Ship54 Settings menu created successfully')

  } catch (err) {
    console.error('❌ Error adding Ship54 menu:', err)
  } finally {
    await mongoose.disconnect()
  }
}

addShip54Menu()