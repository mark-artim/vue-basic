import mongoose from 'mongoose'

const productSchema = new mongoose.Schema({
  _id: String,         // e.g. 'eclipse'
  name: String,        // e.g. 'Eclipse ERP Extensions'
  roles: [String]      // optional: predefined allowed roles per product
})

export default mongoose.model('Product', productSchema)
