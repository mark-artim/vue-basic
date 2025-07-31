// models/Log.js
import mongoose from 'mongoose';

const logSchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now },
  userId: String,
  userEmail: String,
  companyId: String,
  companyCode: String,
  type: String,
  source: String,
  message: String,
  meta: Object
});

export default mongoose.model('Log', logSchema);
