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
  },
  alertEmail: { type: String }, // who should receive transfer alert emails
  wasabiPrefix: { type: String }, // fallback: use companyCode if missing
  ship54Settings: {
    shippo: {
      connected: { type: Boolean, default: false },
      accountInfo: { type: Object, default: null },
      // Customer-provided token approach
      customerToken: {
        encrypted: { type: String }, // Encrypted Shippo API token
        isValid: { type: Boolean, default: false },
        lastTested: { type: Date },
        testResults: { type: Object, default: null }, // Last validation response
        environment: { type: String, enum: ['test', 'live'], default: 'test' }
      }
    },
    freight: {
      defaultMethod: { type: String, default: 'filedrop' },
      productId: { type: String, default: '' }
    },
    cod: {
      termsCodes: { type: [String], default: [] },
      balancePolicy: { type: String, enum: ['warn', 'prevent'], default: 'warn' }
    }
  }

}, { timestamps: true })

export default mongoose.model('Company', companySchema)