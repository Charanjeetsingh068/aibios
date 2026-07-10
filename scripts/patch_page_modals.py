import re

file_path = "d:/react-website/aibios/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Modal import
if "import { Modal }" not in content:
    content = content.replace(
        "import { RequirePermission } from '../components/RequirePermission';",
        "import { RequirePermission } from '../components/RequirePermission';\nimport { Modal } from '../components/Modal';"
    )

# 2. Add Modal States
modal_states = """
  // ── Modal States ──
  const [changeRoleModalUser, setChangeRoleModalUser] = useState<any>(null);
  const [changeRoleInput, setChangeRoleInput] = useState('');
  const [assignPermissionRole, setAssignPermissionRole] = useState<any>(null);
  const [assignPermissionInput, setAssignPermissionInput] = useState('');
"""
if "changeRoleModalUser" not in content:
    content = content.replace("  // ── Roles & Users Modals/Forms ──", "  // ── Roles & Users Modals/Forms ──\n" + modal_states)

# 3. Update the Users Header (change inline button to just open modal)
users_header_old = """          <RequirePermission permission="users.invite">
            <button className="btn-primary" onClick={() => setShowInviteUser(p => !p)}>
              <UserPlus size={14} /> {showInviteUser ? 'Cancel' : 'Invite User'}
            </button>
          </RequirePermission>"""
users_header_new = """          <RequirePermission permission="users.invite">
            <button className="btn-primary" onClick={() => setShowInviteUser(true)}>
              <UserPlus size={14} /> Invite User
            </button>
          </RequirePermission>"""
content = content.replace(users_header_old, users_header_new)

# 4. Remove Inline Invite User form and wrap in Modal later
invite_inline_old = """      {showInviteUser && (
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <form onSubmit={handleInviteUser} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: 8 }}>
            <input type="email" placeholder="Email address" className="task-input-field" value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} required />
            <select className="task-input-field" value={newUserRole} onChange={e => setNewUserRole(e.target.value)}>
              {dashboardRoles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            <button type="submit" className="btn-primary" disabled={inviteUserMutation.isPending}>Send Invite</button>
          </form>
        </div>
      )}"""
content = content.replace(invite_inline_old, "")

# 5. Update Users Actions (Change Role prompt -> Modal)
users_actions_old = """                    <RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {
                        const newRole = window.prompt("Enter new role ID (e.g. manager, viewer):", u.role_id);
                        if(newRole) {
                          apiAssignUserRole(u.id, newRole).then(() => refreshDashboardUsers()).catch(err => pushNotification(err.message));
                        }
                      }} title="Change Role"><Edit2 size={14} /></button>
                    </RequirePermission>"""
users_actions_new = """                    <RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {
                        setChangeRoleModalUser(u);
                        setChangeRoleInput(u.role_id);
                      }} title="Change Role"><Edit2 size={14} /></button>
                    </RequirePermission>"""
content = content.replace(users_actions_old, users_actions_new)

# 6. Update Roles Header
roles_header_old = """          <RequirePermission permission="roles.write">
            <button className="btn-primary" onClick={() => setShowAddRole(p => !p)}>
              <Plus size={14} /> {showAddRole ? 'Cancel' : 'Create Role'}
            </button>
          </RequirePermission>"""
roles_header_new = """          <RequirePermission permission="roles.write">
            <button className="btn-primary" onClick={() => setShowAddRole(true)}>
              <Plus size={14} /> Create Role
            </button>
          </RequirePermission>"""
content = content.replace(roles_header_old, roles_header_new)

# 7. Remove Inline Create Role form
create_role_inline_old = """        {showAddRole && (
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <form onSubmit={handleCreateRole} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: 8 }}>
              <input type="text" placeholder="Role Name (e.g. Content Writer)" className="task-input-field" value={newRoleName} onChange={e => setNewRoleName(e.target.value)} required />
              <input type="text" placeholder="Description" className="task-input-field" value={newRoleDesc} onChange={e => setNewRoleDesc(e.target.value)} />
              <button type="submit" className="btn-primary" disabled={createRoleMutation.isPending}>Save Role</button>
            </form>
          </div>
        )}"""
content = content.replace(create_role_inline_old, "")

# 8. Update Roles Actions (Assign Permission prompt -> Modal)
roles_actions_old = """                <RequirePermission permission="roles.assign_permission">
                  <button className="task-delete-btn" style={{ color: 'var(--brand)' }} title="Assign Permission" onClick={() => {
                    const p = window.prompt("Enter permission ID to assign (e.g., users.read):");
                    if(p) {
                      apiAssignPermission(role.id, p).then(() => {
                        invalidate('roles');
                        fetchDashboardRoles().then(r => setDashboardRoles(r.roles));
                      }).catch(e => alert(e.response?.data?.detail || "Error assigning permission"));
                    }
                  }}><Edit2 size={14} /></button>
                </RequirePermission>"""
roles_actions_new = """                <RequirePermission permission="roles.assign_permission">
                  <button className="task-delete-btn" style={{ color: 'var(--brand)' }} title="Assign Permission" onClick={() => {
                    setAssignPermissionRole(role);
                    setAssignPermissionInput('');
                  }}><Edit2 size={14} /></button>
                </RequirePermission>"""
content = content.replace(roles_actions_old, roles_actions_new)

# 9. Inject Modals into Layout (At the bottom of return statement)
modals_jsx = """
      {/* ── Modals ── */}
      <Modal isOpen={showInviteUser} onClose={() => setShowInviteUser(false)} title="Invite User">
        <form onSubmit={handleInviteUser} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Email Address</label>
            <input type="email" className="task-input-field" value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} required placeholder="user@company.com" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Assign Role</label>
            <select className="task-input-field" value={newUserRole} onChange={e => setNewUserRole(e.target.value)}>
              {dashboardRoles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }} disabled={inviteUserMutation.isPending}>
            {inviteUserMutation.isPending ? 'Sending...' : 'Send Invite'}
          </button>
        </form>
      </Modal>

      <Modal isOpen={showAddRole} onClose={() => setShowAddRole(false)} title="Create New Role">
        <form onSubmit={handleCreateRole} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Role Name</label>
            <input type="text" className="task-input-field" value={newRoleName} onChange={e => setNewRoleName(e.target.value)} required placeholder="e.g. Project Manager" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Description</label>
            <input type="text" className="task-input-field" value={newRoleDesc} onChange={e => setNewRoleDesc(e.target.value)} placeholder="Optional description..." />
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }} disabled={createRoleMutation.isPending}>
            {createRoleMutation.isPending ? 'Saving...' : 'Create Role'}
          </button>
        </form>
      </Modal>

      <Modal isOpen={!!changeRoleModalUser} onClose={() => setChangeRoleModalUser(null)} title={`Change Role: ${changeRoleModalUser?.first_name}`}>
        <form onSubmit={(e) => {
          e.preventDefault();
          if(!changeRoleInput.trim()) return;
          apiAssignUserRole(changeRoleModalUser.id, changeRoleInput.trim()).then(() => {
            refreshDashboardUsers();
            setChangeRoleModalUser(null);
          }).catch(err => pushNotification(err.message || 'Failed to update role'));
        }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Select New Role</label>
            <select className="task-input-field" value={changeRoleInput} onChange={e => setChangeRoleInput(e.target.value)}>
              {dashboardRoles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }}>
            Save Changes
          </button>
        </form>
      </Modal>

      <Modal isOpen={!!assignPermissionRole} onClose={() => setAssignPermissionRole(null)} title={`Assign Permission to ${assignPermissionRole?.name}`}>
        <form onSubmit={(e) => {
          e.preventDefault();
          if(!assignPermissionInput.trim()) return;
          apiAssignPermission(assignPermissionRole.id, assignPermissionInput.trim()).then(() => {
            invalidate('roles');
            fetchDashboardRoles().then(r => setDashboardRoles(r.roles));
            setAssignPermissionRole(null);
          }).catch(err => alert(err.response?.data?.detail || "Error assigning permission"));
        }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Permission ID</label>
            <input type="text" className="task-input-field" value={assignPermissionInput} onChange={e => setAssignPermissionInput(e.target.value)} required placeholder="e.g. users.read" />
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }}>
            Assign Permission
          </button>
        </form>
      </Modal>
"""

# Inject before the very last `</div>` or inside the main return block.
if "Modal isOpen={showInviteUser}" not in content:
    content = content.replace("    </div>\n  );\n}", modals_jsx + "\n    </div>\n  );\n}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to page.tsx to use Modals")
