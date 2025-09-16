import mongoose from 'mongoose'

const productSchema = new mongoose.Schema({
  _id: String,              // e.g. 'eclipse'
  name: String,             // e.g. 'Eclipse ERP Extensions'
  longDescription: String,  // detailed product description for marketing
  stripeProductId: String,  // Stripe product ID for subscription management
  features: [String],       // bullet-pointed list of product features
  roles: [String]           // optional: predefined allowed roles per product
})

export default mongoose.model('Product', productSchema)
