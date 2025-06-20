import mongoose from 'mongoose'
import dotenv from 'dotenv'
import bcrypt from 'bcrypt'
import Company from '../models/Company.js'
import User from '../models/User.js'

dotenv.config()

const seed = async () => {
  await mongoose.connect(process.env.MONGODB_URI)

//   const company = await Company.create({
//     name: 'Heritage Distribution',
//     companyCode: 'heritage',
//     apiBaseUrl: 'https://eclipsemobile.wittichen-supply.com',
//     products: ['eclipse','shipli']
//   })

//   const hashedPassword = await bcrypt.hash('admin123', 10)

  const user = await User.create({
    email: 'mark.artim@heritagedistribution.com',
    // hashedPassword,
    // companyId: company._id,
    companyId: '6844e45114ac54a52c114a01', 
    roles: ['admin'],
    products: ['eclipse','shipli'],
    authType: 'erp'
  })

  console.log('Seeded admin user:', user.email)
  await mongoose.disconnect()
}

seed()
