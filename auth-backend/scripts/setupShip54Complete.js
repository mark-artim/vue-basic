import mongoose from 'mongoose'
import Menu from '../models/Menu.js'
import Company from '../models/Company.js'
import User from '../models/User.js'
import dotenv from 'dotenv'

dotenv.config()

async function setupShip54Complete() {
  try {
    await mongoose.connect(process.env.MONGODB_URI)
    console.log('🔗 Connected to MongoDB')

    // 1. Create Ship54 Settings menu
    console.log('\n📋 Setting up Ship54 menu...')
    const existingMenu = await Menu.findOne({ 
      path: '/ship54-settings',
      product: 'ship54' 
    })

    if (!existingMenu) {
      const ship54Menu = new Menu({
        name: 'Ship54 Settings',
        path: '/ship54-settings',
        product: 'ship54',
        roles: ['customer', 'shipping_manager']
      })
      await ship54Menu.save()
      console.log('✅ Ship54 Settings menu created')
    } else {
      console.log('✅ Ship54 Settings menu already exists')
    }

    // 2. Find and update companies to include ship54 product
    console.log('\n🏢 Adding ship54 product to companies...')
    const companies = await Company.find({})
    
    for (const company of companies) {
      if (!company.products.includes('ship54')) {
        company.products.push('ship54')
        await company.save()
        console.log(`✅ Added ship54 to company: ${company.name} (${company.companyCode})`)
      } else {
        console.log(`✅ Company ${company.name} already has ship54`)
      }
    }

    // 3. Find customer users and give them ship54 roles
    console.log('\n👥 Adding ship54 roles to customer users...')
    const customerUsers = await User.find({ userType: 'customer' })
    
    for (const user of customerUsers) {
      try {
        // Handle both array and Map/object formats for roles
        let userRoles = user.roles || {}
        
        // If roles is an array, convert to object
        if (Array.isArray(userRoles)) {
          console.log(`   🔄 Converting roles array to object for: ${user.email}`)
          userRoles = {}
        }
        
        // Ensure userRoles is an object/Map
        if (!(userRoles instanceof Map)) {
          userRoles = new Map(Object.entries(userRoles))
        }
        
        const ship54Roles = userRoles.get('ship54') || []
        
        if (!ship54Roles.includes('customer')) {
          ship54Roles.push('customer')
          userRoles.set('ship54', ship54Roles)
          
          // Convert Map back to plain object for MongoDB
          const rolesObject = Object.fromEntries(userRoles)
          
          // Use updateOne to avoid potential schema conflicts
          await User.updateOne(
            { _id: user._id },
            { $set: { roles: rolesObject } }
          )
          
          console.log(`✅ Added ship54 customer role to: ${user.email}`)
        } else {
          console.log(`✅ User ${user.email} already has ship54 access`)
        }
      } catch (userError) {
        console.log(`❌ Error updating user ${user.email}:`, userError.message)
        
        // Try alternative approach - direct update
        try {
          await User.updateOne(
            { _id: user._id },
            { $set: { 'roles.ship54': ['customer'] } }
          )
          console.log(`✅ Added ship54 role to ${user.email} (alternative method)`)
        } catch (altError) {
          console.log(`❌ Failed alternative update for ${user.email}:`, altError.message)
        }
      }
    }

    // 4. Summary
    console.log('\n📊 Setup Summary:')
    const totalCompanies = await Company.countDocuments({})
    const companiesWithShip54 = await Company.countDocuments({ products: 'ship54' })
    const usersWithShip54 = await User.countDocuments({ 'roles.ship54': { $exists: true } })
    
    console.log(`   • Companies: ${companiesWithShip54}/${totalCompanies} have ship54`)
    console.log(`   • Users: ${usersWithShip54} have ship54 access`)
    console.log(`   • Menu: Ship54 Settings available`)

    console.log('\n🎉 Ship54 setup complete!')
    console.log('\n📋 Next steps:')
    console.log('   1. Restart your backend server')
    console.log('   2. Login to the frontend')
    console.log('   3. Look for "Ship54 Settings" in the navigation menu')
    console.log('   4. Test the settings page functionality')

  } catch (err) {
    console.error('❌ Setup error:', err)
  } finally {
    await mongoose.disconnect()
    console.log('\n🔌 Disconnected from MongoDB')
  }
}

setupShip54Complete()