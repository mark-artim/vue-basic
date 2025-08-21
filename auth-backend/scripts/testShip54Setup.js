import mongoose from 'mongoose'
import Menu from '../models/Menu.js'
import Company from '../models/Company.js'
import User from '../models/User.js'
import dotenv from 'dotenv'

dotenv.config()

async function testShip54Setup() {
  try {
    await mongoose.connect(process.env.MONGODB_URI)
    console.log('🔗 Connected to MongoDB for testing')

    console.log('\n🧪 Testing Ship54 Setup...\n')

    // Test 1: Check Ship54 menu exists
    const menu = await Menu.findOne({ path: '/ship54-settings' })
    console.log('1. Ship54 Menu Test:')
    if (menu) {
      console.log(`   ✅ Menu found: "${menu.name}"`)
      console.log(`   ✅ Product: ${menu.product}`)
      console.log(`   ✅ Roles: ${menu.roles.join(', ')}`)
    } else {
      console.log('   ❌ Ship54 menu not found')
    }

    // Test 2: Check companies have ship54 product
    const companiesWithShip54 = await Company.find({ products: 'ship54' })
    console.log('\n2. Company Products Test:')
    if (companiesWithShip54.length > 0) {
      console.log(`   ✅ ${companiesWithShip54.length} companies have ship54`)
      companiesWithShip54.forEach(company => {
        console.log(`   • ${company.name} (${company.companyCode})`)
      })
    } else {
      console.log('   ❌ No companies have ship54 product')
    }

    // Test 3: Check users have ship54 roles
    const usersWithShip54 = await User.find({ 'roles.ship54': { $exists: true } })
    console.log('\n3. User Roles Test:')
    if (usersWithShip54.length > 0) {
      console.log(`   ✅ ${usersWithShip54.length} users have ship54 access`)
      usersWithShip54.forEach(user => {
        const ship54Roles = user.roles.get('ship54') || []
        console.log(`   • ${user.email} (${user.userType}): ${ship54Roles.join(', ')}`)
      })
    } else {
      console.log('   ❌ No users have ship54 roles')
    }

    // Test 4: Simulate menu filtering for a user
    console.log('\n4. Menu Filtering Simulation:')
    const sampleUser = usersWithShip54[0]
    if (sampleUser) {
      const userCompany = await Company.findById(sampleUser.companyId)
      const entitledProducts = userCompany.products
      const userRoles = sampleUser.roles || new Map()
      
      const allMenus = await Menu.find({ product: { $in: entitledProducts } })
      const visibleMenus = allMenus.filter(menu => {
        const allowedRoles = menu.roles || []
        const userRolesForProduct = userRoles.get(menu.product) || []
        return userRolesForProduct.some(role => allowedRoles.includes(role))
      })
      
      console.log(`   📋 User: ${sampleUser.email}`)
      console.log(`   📦 Entitled products: ${entitledProducts.join(', ')}`)
      console.log(`   👀 Visible menus:`)
      visibleMenus.forEach(menu => {
        console.log(`     • ${menu.name} (${menu.product})`)
      })
    } else {
      console.log('   ⚠️  No users available for simulation')
    }

    console.log('\n✅ Test complete!')

  } catch (err) {
    console.error('❌ Test error:', err)
  } finally {
    await mongoose.disconnect()
  }
}

testShip54Setup()