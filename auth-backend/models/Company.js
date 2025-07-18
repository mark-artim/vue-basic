import mongoose from 'mongoose'

const companySchema = new mongoose.Schema({
  name: { type: String, required: true },
  companyCode: { type: String, required: true, unique: true },
  addressLine1: { type: String, required: true },
  addressLine2: { type: String },
  city: { type: String },
  state: { type: String },
  postalCode: { type: String, required: true },
  phone: { type: String, required: true },
  apiBaseUrl: { type: String, required: true },
  apiPorts: {
    type: [String],
    validate: [v => Array.isArray(v) && v.length > 0, 'At least one API port number is required.']
  },
  products: [{ type: String }],
  surcharge: {
    authMethod: {
      type: String,
      enum: ['loggedInUser', 'apiUser'],
      default: 'loggedInUser'
    },
    apiUser: {
      username: String,
      password: String // 🔐 consider encrypting or storing securely later
    },
    productsByPort: {
      type: Map,
      of: Number // port -> surcharge productId
    }
  }
}, { timestamps: true })

export default mongoose.model('Company', companySchema)