import re

file_path = "c:/react/aibios/frontend/src/app/page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Imports
if "Edit3" not in content and "UserCog" not in content:
    content = content.replace("Edit2,", "Edit2, Edit3,")

# 2. Add Edit User State
edit_user_state = """
  const [editUserModal, setEditUserModal] = useState<any>(null);
  const [editUserFirstName, setEditUserFirstName] = useState('');
  const [editUserLastName, setEditUserLastName] = useState('');
  const [editUserEmail, setEditUserEmail] = useState('');
  const [editUserPhone, setEditUserPhone] = useState('');
"""
if "editUserModal" not in content:
    content = content.replace("  const [showCreateUser, setShowCreateUser] = useState(false);", edit_user_state + "  const [showCreateUser, setShowCreateUser] = useState(false);")

# 3. Add Mutation for Edit User
edit_user_mutation = """
  const editUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: string, data: any }) => apiUpdateUser(id, data),
    onSuccess: () => {
      pushNotification("User updated successfully");
      setEditUserModal(null);
      refreshDashboardUsers();
    },
    onError: (err: any) => alert(err.response?.data?.detail || "Failed to update user")
  });
"""
if "editUserMutation" not in content:
    content = content.replace("  const createUserMutation = useMutation({", edit_user_mutation + "\n  const createUserMutation = useMutation({")

# 4. Add Edit button to user row
old_row_actions = """<RequirePermission permission="users.reset_password">"""
new_row_actions = """<RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {
                        setEditUserModal(u);
                        setEditUserFirstName(u.first_name);
                        setEditUserLastName(u.last_name);
                        setEditUserEmail(u.email);
                        setEditUserPhone(u.phone || '');
                      }} title="Edit User"><Edit3 size={14} /></button>
                    </RequirePermission>
                    <RequirePermission permission="users.reset_password">"""
if "setEditUserModal(u)" not in content:
    content = content.replace(old_row_actions, new_row_actions)

# 5. Add Header Action for Change Password
old_header_actions = """<div className="header-actions">
              <button onClick={toggleTheme} className="theme-toggle-btn" title="Toggle Theme" aria-label="Toggle Theme">
                {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </button>"""
new_header_actions = """<div className="header-actions">
              <button onClick={() => window.location.href = '/profile/change-password'} className="theme-toggle-btn" title="Change Password" aria-label="Change Password" style={{ color: 'var(--brand)' }}>
                <Key size={18} />
              </button>
              <button onClick={toggleTheme} className="theme-toggle-btn" title="Toggle Theme" aria-label="Toggle Theme">
                {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </button>"""
if "window.location.href = '/profile/change-password'" not in content:
    content = content.replace(old_header_actions, new_header_actions)

# 6. Add Edit User Modal
edit_user_modal_jsx = """
      <Modal isOpen={!!editUserModal} onClose={() => setEditUserModal(null)} title={`Edit User: ${editUserModal?.email}`}>
        <form onSubmit={(e) => {
          e.preventDefault();
          editUserMutation.mutate({
            id: editUserModal.id,
            data: {
              first_name: editUserFirstName,
              last_name: editUserLastName,
              email: editUserEmail,
              phone: editUserPhone,
            }
          });
        }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>First Name</label>
              <input type="text" className="task-input-field" value={editUserFirstName} onChange={e => setEditUserFirstName(e.target.value)} required />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Last Name</label>
              <input type="text" className="task-input-field" value={editUserLastName} onChange={e => setEditUserLastName(e.target.value)} required />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Email</label>
            <input type="email" className="task-input-field" value={editUserEmail} onChange={e => setEditUserEmail(e.target.value)} required />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Phone (Optional)</label>
            <input type="text" className="task-input-field" value={editUserPhone} onChange={e => setEditUserPhone(e.target.value)} />
          </div>
          <button type="submit" className="btn-primary" style={{ marginTop: 8 }} disabled={editUserMutation.isPending}>
            {editUserMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </Modal>
"""
if "Modal isOpen={!!editUserModal}" not in content:
    content = content.replace("    </div>\n  );\n}", edit_user_modal_jsx + "\n    </div>\n  );\n}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to page.tsx for Edit User and Header Change Password")
