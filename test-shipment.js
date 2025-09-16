// Simple test to see if we can create a shipment record
import mongoose from 'mongoose'
import Shipment from './auth-backend/models/Shipment.js'
import dotenv from 'dotenv'

dotenv.config({ path: './auth-backend/.env' })

async function testShipmentCreation() {
  try {
    // Connect to MongoDB
    await mongoose.connect(process.env.MONGODB_URI)
    console.log('✅ Connected to MongoDB')
    
    // Create minimal test shipment
    const testShipment = new Shipment({
      companyId: "6844e585401ce41c41ee71cf",
      carrier: "test", 
      orderId: "test-order-123",
      invoiceNumber: "TEST-001"
    })
    
    const savedShipment = await testShipment.save()
    console.log('✅ Shipment created successfully:', savedShipment._id)
    console.log('Shipment data:', JSON.stringify(savedShipment, null, 2))
    
    // Clean up - delete the test record
    await Shipment.findByIdAndDelete(savedShipment._id)
    console.log('✅ Test shipment cleaned up')
    
  } catch (error) {
    console.error('❌ Error:', error)
  } finally {
    await mongoose.disconnect()
    console.log('Disconnected from MongoDB')
  }
}

testShipmentCreation()