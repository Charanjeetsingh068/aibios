import os

filepath = "c:/react/aibios/frontend/src/app/page.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add imports
content = content.replace(
    "import { fetchIntegrations, connectIntegration as apiConnectIntegration } from '../services/integrationsService';",
    "import { fetchIntegrations, connectIntegration as apiConnectIntegration, fetchLeadMappings, createLeadMapping, deleteLeadMapping } from '../services/integrationsService';"
)

# Add state
state_block = """
  const [notifications, setNotifications] = useState<LiveNotification[]>([]);
  const [leadMappings, setLeadMappings] = useState<any[]>([]);
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [newMappingFormId, setNewMappingFormId] = useState('');
  const [newMappingMetaField, setNewMappingMetaField] = useState('');
  const [newMappingCrmField, setNewMappingCrmField] = useState('');
"""
content = content.replace("  const [notifications, setNotifications] = useState<LiveNotification[]>([]);", state_block.strip())

# Add button
button_old = """
        <div className="module-header">
          <div className="module-title" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ color }}>{channelIcon}</div>
            <div><h2>{channelName} Leads</h2><span>Captured leads from {channelName} integrations</span></div>
          </div>
          <button className="btn-primary" onClick={() => connectChannel(channelKey)} disabled={connectIntegrationMutation.isPending}>
            <RefreshCw size={14} /> {integration?.status === 'connected' ? 'Reconnect' : 'Connect Account'}
          </button>
        </div>
"""
button_new = """
        <div className="module-header">
          <div className="module-title" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ color }}>{channelIcon}</div>
            <div><h2>{channelName} Leads</h2><span>Captured leads from {channelName} integrations</span></div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {channelKey === 'facebook' && (
              <button className="btn-secondary" onClick={() => {
                fetchLeadMappings().then(res => setLeadMappings(res.mappings)).catch(() => {});
                setShowMappingModal(true);
              }}>
                <Link size={14} /> Mappings
              </button>
            )}
            <button className="btn-primary" onClick={() => connectChannel(channelKey)} disabled={connectIntegrationMutation.isPending}>
              <RefreshCw size={14} /> {integration?.status === 'connected' ? 'Reconnect' : 'Connect Account'}
            </button>
          </div>
        </div>
"""
content = content.replace(button_old.strip(), button_new.strip())

# Add Modal
modal_jsx = """
      <Modal isOpen={showMappingModal} onClose={() => setShowMappingModal(false)} title="Meta Lead Mappings">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead><tr><th>Form ID</th><th>Meta Field</th><th>CRM Field</th><th>Action</th></tr></thead>
              <tbody>
                {leadMappings.map(m => (
                  <tr key={m.id}>
                    <td>{m.form_id}</td>
                    <td>{m.meta_field}</td>
                    <td>{m.crm_field}</td>
                    <td>
                      <button className="task-delete-btn" style={{ color: 'var(--danger)' }} onClick={() => {
                        deleteLeadMapping(m.id).then(() => fetchLeadMappings().then(res => setLeadMappings(res.mappings)));
                      }}><Trash2 size={14} /></button>
                    </td>
                  </tr>
                ))}
                {leadMappings.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center' }}>No mappings configured.</td></tr>}
              </tbody>
            </table>
          </div>
          <h4 style={{ margin: 0 }}>Add New Mapping</h4>
          <form onSubmit={(e) => {
            e.preventDefault();
            createLeadMapping({ form_id: newMappingFormId, meta_field: newMappingMetaField, crm_field: newMappingCrmField })
              .then(() => {
                setNewMappingFormId(''); setNewMappingMetaField(''); setNewMappingCrmField('');
                fetchLeadMappings().then(res => setLeadMappings(res.mappings));
              }).catch(err => pushNotification("Failed to add mapping"));
          }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <input type="text" className="task-input-field" placeholder="Form ID (or * for all)" value={newMappingFormId} onChange={e => setNewMappingFormId(e.target.value)} required />
              <input type="text" className="task-input-field" placeholder="Meta Field (e.g. first_name)" value={newMappingMetaField} onChange={e => setNewMappingMetaField(e.target.value)} required />
              <select className="task-input-field" value={newMappingCrmField} onChange={e => setNewMappingCrmField(e.target.value)} required>
                <option value="" disabled>Select CRM Field...</option>
                <option value="name">Name</option>
                <option value="email">Email</option>
                <option value="phone">Phone</option>
                <option value="company">Company</option>
              </select>
            </div>
            <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start' }}>Add Mapping</button>
          </form>
        </div>
      </Modal>
"""
content = content.replace("<Modal isOpen={!!editUserModal}", modal_jsx + "\n      <Modal isOpen={!!editUserModal}")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to page.tsx")
