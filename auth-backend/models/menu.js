import mongoose from 'mongoose'

const menuSchema = new mongoose.Schema({
  name: { type: String, required: true },      // e.g. 'Invoice Lookup'
  path: { type: String, required: true },      // e.g. '/invoice-lookup'
  product: { type: String, required: true },   // e.g. 'eclipse'
  roles: { type: [String], default: [] }       // e.g. ['customer', 'admin']
})

export default mongoose.model('Menu', menuSchema)
