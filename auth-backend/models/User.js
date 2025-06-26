import mongoose from 'mongoose'

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  firstName: { type: String, required: true },
  lastName: { type: String, required: true },
  erpUserName: {
    type: String,
    validate: {
      validator: function (v) {
        return this.userType !== 'customer' || !!v;
      },
      message: 'erpUsername is required for customer users.'
    }
  },
  userType: { type: String, enum: ['admin', 'customer'], required: true },
  hashedPassword: { type: String },
  companyId: { type: mongoose.Schema.Types.ObjectId, ref: 'Company' },
  lastPort: { type: String, default: '5000' }, // default port for ERP API
  roles: {
  type: Map,
  of: [String],
  default: {}
  },
  products: {
  type: [String],
  default: []
}
}, { timestamps: true })

export default mongoose.model('User', userSchema)
