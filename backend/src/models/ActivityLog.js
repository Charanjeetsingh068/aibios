import mongoose from 'mongoose';

const activityLogSchema = new mongoose.Schema({
  user_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  company_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Company'
  },
  workspace_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Workspace'
  },
  action: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  resource: {
    type: String
  },
  resource_id: {
    type: String
  },
  ip_address: {
    type: String
  },
  device_info: {
    type: String
  }
}, {
  timestamps: { createdAt: 'created_at', updatedAt: false }
});

const ActivityLog = mongoose.model('ActivityLog', activityLogSchema);
export default ActivityLog;
