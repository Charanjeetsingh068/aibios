import mongoose from 'mongoose';

const sessionSchema = new mongoose.Schema({
  user_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  company_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Company',
    required: true
  },
  refresh_token: {
    type: String,
    required: true,
    unique: true
  },
  is_revoked: {
    type: Boolean,
    default: false
  },
  device_info: {
    type: String,
    default: 'Unknown'
  },
  ip_address: {
    type: String,
    default: '0.0.0.0'
  },
  expires_at: {
    type: Date,
    required: true
  }
}, {
  timestamps: { createdAt: 'created_at', updatedAt: 'updated_at' }
});

const Session = mongoose.model('Session', sessionSchema);
export default Session;
