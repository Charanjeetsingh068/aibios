import re

file_path = "c:/react/aibios/frontend/src/app/page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports
if "apiCreateUser" not in content:
    content = content.replace(
        "import { inviteUser as apiInviteUser, deleteUser as apiDeleteUser, assignUserRole as apiAssignUserRole } from '../services/userService';",
        "import { inviteUser as apiInviteUser, deleteUser as apiDeleteUser, assignUserRole as apiAssignUserRole, createUser as apiCreateUser, forceUserPassword as apiForceUserPassword } from '../services/userService';"
    )
if "import { Key" not in content and "Key," not in content:
    content = content.replace(
        "Edit2, ShieldAlert,",
        "Edit2, ShieldAlert, Key,"
    )
elif "Key" not in content:
    # lucide-react import
    content = content.replace("import { ", "import { Key, ")

# 2. Add State for Create User and Force Password
new_state = """
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [createFirstName, setCreateFirstName] = useState('');
  const [createLastName, setCreateLastName] = useState('');
  const [createPassword, setCreatePassword] = useState('');
  const [forcePasswordUser, setForcePasswordUser] = useState<any>(null);
  const [forcePasswordInput, setForcePasswordInput] = useState('');
"""
if "showCreateUser" not in content:
    content = content.replace("  const [newUserEmail, setNewUserEmail] = useState('');", new_state + "  const [newUserEmail, setNewUserEmail] = useState('');")

# 3. Add Mutation for Create User
new_mutation = """
  const createUserMutation = useMutation({
    mutationFn: (data: any) => apiCreateUser(data),
    onSuccess: () => {
      pushNotification("User created successfully");
      setShowCreateUser(false);
      setCreateFirstName('');
      setCreateLastName('');
      setNewUserEmail('');
      setCreatePassword('');
      refreshDashboardUsers();
    },
    onError: (err: any) => alert(err.response?.data?.detail || "Failed to create user")
  });
"""
if "createUserMutation" not in content:
    content = content.replace("  const inviteUserMutation = useMutation({", new_mutation + "\n  const inviteUserMutation = useMutation({")

# 4. Add Create User Button next to Invite User Button
old_users_header = """          <RequirePermission permission="users.invite">
            <button className="btn-primary" onClick={() => setShowInviteUser(true)}>
              <UserPlus size={14} /> Invite User
            </button>
          </RequirePermission>"""
new_users_header = """          <div style={{ display: 'flex', gap: 8 }}>
            <RequirePermission permission="users.invite">
              <button className="btn-primary" onClick={() => setShowInviteUser(true)}>
                <UserPlus size={14} /> Invite User
              </button>
            </RequirePermission>
            <RequirePermission permission="users.write">
              <button className="btn-secondary" onClick={() => setShowCreateUser(true)}>
                <UserPlus size={14} /> Create User
              </button>
            </RequirePermission>
          </div>"""
if "Create User" not in old_users_header and "Create User" not in content:
    content = content.replace(old_users_header, new_users_header)

# 5. Add Force Password button to user row
old_user_row_actions = """                    <RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {"""
new_user_row_actions = """                    <RequirePermission permission="users.reset_password">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {
                        setForcePasswordUser(u);
                        setForcePasswordInput('');
                      }} title="Set Password"><Key size={14} /></button>
                    </RequirePermission>
                    <RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {"""
if "setForcePasswordUser(u)" not in content:
    content = content.replace(old_user_row_actions, new_user_row_actions)

# 6. Add Modals for Create User and Force Password
modals_jsx = """
      <Modal isOpen={showCreateUser} onClose={() => setShowCreateUser(false)} title="Create New User">
        <form onSubmit={(e) => {
          e.preventDefault();
          createUserMutation.mutate({
            first_name: createFirstName,
            last_name: createLastName,
            email: newUserEmail,
            password: createPassword,
            role_id: newUserRole
          });
        }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>First Name</label>
              <input type="text" className="task-input-field" value={createFirstName} onChange={e => setCreateFirstName(e.target.value)} required />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Last Name</label>
              <input type="text" className="task-input-field" value={createLastName} onChange={e => setCreateLastName(e.target.value)} required />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Email</label>
            <input type="email" className="task-input-field" value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} required />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Password</label>
            <input type="password" minLength={8} className="task-input-field" value={createPassword} onChange={e => setCreatePassword(e.target.value)} required />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Role</label>
            <select className="task-input-field" value={newUserRole} onChange={e => setNewUserRole(e.target.value)}>
              {dashboardRoles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }} disabled={createUserMutation.isPending}>
            {createUserMutation.isPending ? 'Creating...' : 'Create User'}
          </button>
        </form>
      </Modal>

      <Modal isOpen={!!forcePasswordUser} onClose={() => setForcePasswordUser(null)} title={`Set Password: ${forcePasswordUser?.email}`}>
        <form onSubmit={(e) => {
          e.preventDefault();
          if(!forcePasswordInput.trim() || forcePasswordInput.length < 8) {
            alert("Password must be at least 8 characters");
            return;
          }
          apiForceUserPassword(forcePasswordUser.id, forcePasswordInput).then(() => {
            pushNotification('Password updated successfully');
            setForcePasswordUser(null);
          }).catch(err => alert(err.response?.data?.detail || "Error updating password"));
        }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>New Password</label>
            <input type="password" minLength={8} className="task-input-field" value={forcePasswordInput} onChange={e => setForcePasswordInput(e.target.value)} required placeholder="Min 8 characters" />
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }}>
            Force Set Password
          </button>
        </form>
      </Modal>
"""

if "Modal isOpen={showCreateUser}" not in content:
    content = content.replace("    </div>\n  );\n}", modals_jsx + "\n    </div>\n  );\n}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to page.tsx for Create User and Force Password")
