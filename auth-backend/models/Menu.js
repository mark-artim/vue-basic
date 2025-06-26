import mongoose from 'mongoose'

const menuSchema = new mongoose.Schema({
  name: { type: String, required: true },       // eg 'Invoice Lookup'
  path: { type: String, required: true },      // eg '/invoice-lookup'
  product: { type: String, required: true },   // eg 'eclipse'
  roles: { type: [String], default: [] }       // eg ['customer', 'admin']
})

export default mongoose.model('Menu', menuSchema)
