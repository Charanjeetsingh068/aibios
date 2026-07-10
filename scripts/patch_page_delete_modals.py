import re

file_path = "d:/react-website/aibios/frontend/src/app/page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add Delete Modal State
delete_states = """
  const [deleteConfirmInfo, setDeleteConfirmInfo] = useState<{ type: 'user' | 'role', id: str, name: string } | null>(null);
"""
if "deleteConfirmInfo" not in content:
    content = content.replace("  const [assignPermissionInput, setAssignPermissionInput] = useState('');", "  const [assignPermissionInput, setAssignPermissionInput] = useState('');\n" + delete_states)

# Replace window.confirm for Users
delete_user_old = """onClick={() => {
                          if (window.confirm("Are you sure you want to delete this user?")) {
                            deleteUserMutation.mutate(u.id);
                          }
                        }}"""
delete_user_new = """onClick={() => setDeleteConfirmInfo({ type: 'user', id: u.id, name: u.first_name })}"""
content = content.replace(delete_user_old, delete_user_new)

# Replace window.confirm for Roles
delete_role_old = """onClick={() => {
                    if (window.confirm(`Delete role ${role.name}?`)) {
                      deleteRoleMutation.mutate(role.id);
                    }
                  }}"""
delete_role_new = """onClick={() => setDeleteConfirmInfo({ type: 'role', id: role.id, name: role.name })}"""
content = content.replace(delete_role_old, delete_role_new)

# Inject Delete Modal
delete_modal_jsx = """
      <Modal isOpen={!!deleteConfirmInfo} onClose={() => setDeleteConfirmInfo(null)} title={`Confirm Deletion`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-secondary)' }}>
            Are you sure you want to delete the {deleteConfirmInfo?.type} <strong>{deleteConfirmInfo?.name}</strong>? This action cannot be undone.
          </p>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className="btn-secondary" onClick={() => setDeleteConfirmInfo(null)}>Cancel</button>
            <button className="btn-primary" style={{ backgroundColor: 'var(--danger)', borderColor: 'var(--danger)' }} onClick={() => {
              if (deleteConfirmInfo?.type === 'user') deleteUserMutation.mutate(deleteConfirmInfo.id);
              if (deleteConfirmInfo?.type === 'role') deleteRoleMutation.mutate(deleteConfirmInfo.id);
              setDeleteConfirmInfo(null);
            }}>
              Confirm Delete
            </button>
          </div>
        </div>
      </Modal>
"""
if "title={`Confirm Deletion`}" not in content:
    content = content.replace("    </div>\n  );\n}", delete_modal_jsx + "\n    </div>\n  );\n}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Delete Modal patch applied.")
