"use client";

import { useState, useEffect } from 'react';
import { Mail, Phone, Globe, Shield, Calendar, Clock, ArrowLeft, Key, Building, Check, Trash2, Settings, X, UserPlus, ShieldAlert, KeyRound, Edit2, Link } from 'lucide-react';
import { getMe, UserResponse } from '../../services/authService';
import '../../styles/dashboard.css';

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Tabs Layout State
  const [activeTab, setActiveTab] = useState<'personal' | 'organization'>('personal');

  // Organization settings states
  const [orgName, setOrgName] = useState('Demo Corp');
  const [orgSlug, setOrgSlug] = useState('demo');
  const [companyLogo, setCompanyLogo] = useState('Ω');
  const [gstNumber, setGstNumber] = useState('27AAAAA0000A1Z5');
  const [officeAddress, setOfficeAddress] = useState('123 Business Tower, Suite 400, Mumbai, MH, 400001, India');
  const [orgTimezone, setOrgTimezone] = useState('Asia/Kolkata');
  const [brandColor, setBrandColor] = useState('#3b82f6');
  const [subscriptionPlan, setSubscriptionPlan] = useState('enterprise');

  // RBAC Permission Sets
  const ROLE_DEFAULT_PERMISSIONS: Record<string, string[]> = {
    super_admin: ["leads:read", "leads:write", "org:read", "org:write", "agents:read", "agents:write"],
    admin: ["leads:read", "leads:write", "org:read", "org:write", "agents:read", "agents:write"],
    manager: ["leads:read", "leads:write", "org:read", "agents:read"],
    sales: ["leads:read", "leads:write"],
    marketing: ["leads:read", "leads:write"],
    support: ["leads:read", "leads:write", "agents:read"],
    developer: ["agents:read", "agents:write"],
    ai_agent: ["leads:read", "leads:write", "agents:read"],
    finance: ["org:read"],
    viewer: ["leads:read", "org:read", "agents:read"]
  };

  const ALL_AVAILABLE_PERMISSIONS = [
    { id: "leads:read", name: "Read Leads", desc: "Access leads logs and profiles" },
    { id: "leads:write", name: "Write Leads", desc: "Create and edit lead profiles" },
    { id: "org:read", name: "Read Org", desc: "View organization attributes" },
    { id: "org:write", name: "Write Org", desc: "Modify organization configurations" },
    { id: "agents:read", name: "Read Agents", desc: "Inspect LangGraph agent states" },
    { id: "agents:write", name: "Write Agents", desc: "Modify agent workflows and states" }
  ];

  // Membership Users list state
  const [orgUsers, setOrgUsers] = useState<any[]>([
    { id: 1, name: "Charanjeet Singh", email: "charanjeet.s7730@gmail.com", role: "super_admin", status: "active", permissions: ["leads:read", "leads:write", "org:read", "org:write", "agents:read", "agents:write"] },
    { id: 2, name: "Jane Smith", email: "jane@democorp.com", role: "admin", status: "active", permissions: ["leads:read", "leads:write", "org:read", "org:write", "agents:read", "agents:write"] },
    { id: 3, name: "David Miller", email: "david@democorp.com", role: "manager", status: "active", permissions: ["leads:read", "leads:write", "org:read", "agents:read"] },
    { id: 4, name: "AI Agent Alpha", email: "alpha@democorp.com", role: "ai_agent", status: "invited", permissions: ["leads:read", "leads:write", "agents:read"] }
  ]);

  // Invite form states
  const [inviteName, setInviteName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('manager');
  const [invitePermissions, setInvitePermissions] = useState<string[]>(ROLE_DEFAULT_PERMISSIONS.manager);
  const [generatedInviteLink, setGeneratedInviteLink] = useState('');

  // Edit user modal states
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editRole, setEditRole] = useState('manager');
  const [editPermissions, setEditPermissions] = useState<string[]>([]);

  // Password reset alert links
  const [resetAlertLink, setResetAlertLink] = useState('');
  const [resetAlertUser, setResetAlertUser] = useState('');

  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error'>('success');

  const applyBrandColor = (colorHex: string) => {
    if (typeof window === 'undefined') return;
    document.documentElement.style.setProperty('--brand', colorHex);
    document.documentElement.style.setProperty('--brand-hover', colorHex + 'cc');
    document.documentElement.style.setProperty('--brand-light', colorHex + '20');
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToastMessage(message);
    setToastType(type);
    setTimeout(() => {
      setToastMessage('');
    }, 3000);
  };

  // Helper for dynamic coloring of all 10 roles
  const getRoleBadgeStyle = (role: string) => {
    switch (role) {
      case 'super_admin': return { backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--info)' };
      case 'admin': return { backgroundColor: 'rgba(168, 85, 247, 0.15)', color: '#a855f7' };
      case 'manager': return { backgroundColor: 'rgba(234, 179, 8, 0.15)', color: 'var(--warning)' };
      case 'sales': return { backgroundColor: 'rgba(249, 115, 22, 0.15)', color: '#f97316' };
      case 'marketing': return { backgroundColor: 'rgba(236, 72, 153, 0.15)', color: '#ec4899' };
      case 'support': return { backgroundColor: 'rgba(20, 184, 166, 0.15)', color: '#14b8a6' };
      case 'developer': return { backgroundColor: 'rgba(99, 102, 241, 0.15)', color: '#6366f1' };
      case 'ai_agent': return { backgroundColor: 'rgba(16, 185, 129, 0.15)', color: 'var(--success)' };
      case 'finance': return { backgroundColor: 'rgba(100, 116, 139, 0.15)', color: '#64748b' };
      case 'viewer': return { backgroundColor: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' };
      default: return { backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' };
    }
  };

  const getRoleDisplayName = (role: string) => {
    switch (role) {
      case 'super_admin': return 'Super Admin';
      case 'admin': return 'Admin';
      case 'manager': return 'Manager';
      case 'sales': return 'Sales';
      case 'marketing': return 'Marketing';
      case 'support': return 'Support';
      case 'developer': return 'Developer';
      case 'ai_agent': return 'AI Agent';
      case 'finance': return 'Finance';
      case 'viewer': return 'Viewer';
      default: return role.toUpperCase();
    }
  };

  useEffect(() => {
    // 1. Fetch Profile
    const fetchProfile = async () => {
      try {
        const data = await getMe();
        setProfile(data);
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve profile details.');
        setTimeout(() => {
          window.location.href = '/auth/login';
        }, 1500);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProfile();

    // 2. Load cached settings
    if (typeof window !== 'undefined') {
      const cachedName = localStorage.getItem('aibos_org_name');
      const cachedSlug = localStorage.getItem('aibos_org_slug');
      const cachedLogo = localStorage.getItem('aibos_org_logo');
      const cachedGst = localStorage.getItem('aibos_org_gst');
      const cachedAddress = localStorage.getItem('aibos_org_address');
      const cachedTimezone = localStorage.getItem('aibos_org_timezone');
      const cachedColor = localStorage.getItem('aibos_org_color');
      const cachedPlan = localStorage.getItem('aibos_org_plan');
      const cachedUsers = localStorage.getItem('aibos_org_users');

      if (cachedName) setOrgName(cachedName);
      if (cachedSlug) setOrgSlug(cachedSlug);
      if (cachedLogo) setCompanyLogo(cachedLogo);
      if (cachedGst) setGstNumber(cachedGst);
      if (cachedAddress) setOfficeAddress(cachedAddress);
      if (cachedTimezone) setOrgTimezone(cachedTimezone);
      if (cachedColor) {
        setBrandColor(cachedColor);
        applyBrandColor(cachedColor);
      }
      if (cachedPlan) setSubscriptionPlan(cachedPlan);
      if (cachedUsers) setOrgUsers(JSON.parse(cachedUsers));
    }
  }, []);

  const handleSaveOrganization = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== 'undefined') {
      localStorage.setItem('aibos_org_name', orgName);
      localStorage.setItem('aibos_org_slug', orgSlug);
      localStorage.setItem('aibos_org_logo', companyLogo);
      localStorage.setItem('aibos_org_gst', gstNumber);
      localStorage.setItem('aibos_org_address', officeAddress);
      localStorage.setItem('aibos_org_timezone', orgTimezone);
      localStorage.setItem('aibos_org_color', brandColor);
      localStorage.setItem('aibos_org_plan', subscriptionPlan);
      
      applyBrandColor(brandColor);
      showToast('Organization settings updated successfully!', 'success');
    }
  };

  // Invite user handler
  const handleInviteUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteName.trim() || !inviteEmail.trim()) return;

    const newUser = {
      id: Date.now(),
      name: inviteName.trim(),
      email: inviteEmail.trim(),
      role: inviteRole,
      status: 'invited',
      permissions: invitePermissions
    };

    const updatedUsers = [...orgUsers, newUser];
    setOrgUsers(updatedUsers);
    localStorage.setItem('aibos_org_users', JSON.stringify(updatedUsers));

    // Generate invite URL
    const randToken = Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
    setGeneratedInviteLink(`http://localhost:3000/auth/login?invite=${randToken}`);
    
    setInviteName('');
    setInviteEmail('');
    showToast(`User ${inviteName} invited! Copy link below.`, 'success');
  };

  const handleInviteRoleChange = (role: string) => {
    setInviteRole(role);
    setInvitePermissions(ROLE_DEFAULT_PERMISSIONS[role] || []);
  };

  const toggleInvitePermission = (permId: string) => {
    setInvitePermissions(prev => 
      prev.includes(permId) ? prev.filter(p => p !== permId) : [...prev, permId]
    );
  };

  // Delete user handler
  const handleDeleteUser = (id: number) => {
    if (id === 1) {
      showToast('Cannot remove primary organization owner!', 'error');
      return;
    }
    const updatedUsers = orgUsers.filter(u => u.id !== id);
    setOrgUsers(updatedUsers);
    localStorage.setItem('aibos_org_users', JSON.stringify(updatedUsers));
    showToast('User deleted from organization.', 'success');
  };

  // Suspend / Activate user handler
  const toggleSuspendUser = (id: number) => {
    if (id === 1) {
      showToast('Cannot suspend organization owner!', 'error');
      return;
    }
    const updatedUsers = orgUsers.map(u => {
      if (u.id === id) {
        const nextStatus = u.status === 'suspended' ? 'active' : 'suspended';
        showToast(`User account ${nextStatus === 'suspended' ? 'suspended' : 'activated'}.`, 'success');
        return { ...u, status: nextStatus };
      }
      return u;
    });
    setOrgUsers(updatedUsers);
    localStorage.setItem('aibos_org_users', JSON.stringify(updatedUsers));
  };

  // Reset password handler
  const triggerResetPassword = (userObj: any) => {
    const randToken = Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
    setResetAlertLink(`http://localhost:3000/auth/reset-password?token=${randToken}`);
    setResetAlertUser(userObj.name);
    showToast(`Password reset link created for ${userObj.name}`, 'success');
  };

  // Edit user modal open / save
  const openEditModal = (userObj: any) => {
    setEditingUserId(userObj.id);
    setEditName(userObj.name);
    setEditEmail(userObj.email);
    setEditRole(userObj.role);
    setEditPermissions(userObj.permissions || []);
    setIsEditModalOpen(true);
  };

  const handleEditRoleChange = (role: string) => {
    setEditRole(role);
    setEditPermissions(ROLE_DEFAULT_PERMISSIONS[role] || []);
  };

  const toggleEditPermission = (permId: string) => {
    setEditPermissions(prev => 
      prev.includes(permId) ? prev.filter(p => p !== permId) : [...prev, permId]
    );
  };

  const handleSaveChanges = () => {
    const updatedUsers = orgUsers.map(u => {
      if (u.id === editingUserId) {
        return {
          ...u,
          name: editName,
          email: editEmail,
          role: editRole,
          permissions: editPermissions
        };
      }
      return u;
    });
    setOrgUsers(updatedUsers);
    localStorage.setItem('aibos_org_users', JSON.stringify(updatedUsers));
    setIsEditModalOpen(false);
    showToast('User configurations saved successfully.', 'success');
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        <div className="card skeleton-card" style={{ width: '100%', maxWidth: '600px', padding: 'var(--space-8)' }}>
          <div className="skeleton-line title" style={{ width: '40%' }}></div>
          <div className="skeleton-line value"></div>
          <div className="skeleton-line desc" style={{ width: '80%' }}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        <div className="card" style={{ width: '100%', maxWidth: '400px', padding: 'var(--space-6)', textAlign: 'center', borderColor: 'var(--danger)' }}>
          <div className="error-title">Error</div>
          <div className="error-msg">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-primary)', padding: 'var(--space-8)', width: '100vw' }}>
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: toastType === 'success' ? 'var(--success)' : 'var(--danger)',
          color: '#ffffff',
          padding: 'var(--space-3) var(--space-6)',
          borderRadius: 'var(--radius-sm)',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 1000,
          fontSize: 'var(--font-sm)',
          fontWeight: 'bold',
          animation: 'fade-in 0.3s ease-out'
        }}>
          {toastMessage}
        </div>
      )}

      {/* Edit User Modal Dialog Overlay */}
      {isEditModalOpen && (
        <div className="modal-overlay">
          <div className="modal-container animate-fade-in">
            <div className="modal-header">
              <h3>Edit User & Permissions Assignments</h3>
              <button onClick={() => setIsEditModalOpen(false)} className="modal-close-btn">
                <X size={18} />
              </button>
            </div>
            
            <div className="modal-body">
              <div className="settings-form-group">
                <label htmlFor="editName">Full Name</label>
                <input 
                  type="text" 
                  id="editName" 
                  className="settings-input" 
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>

              <div className="settings-form-group">
                <label htmlFor="editEmail">Email Address</label>
                <input 
                  type="email" 
                  id="editEmail" 
                  className="settings-input" 
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                />
              </div>

              <div className="settings-form-group">
                <label htmlFor="editRole">Assign Workplace Role</label>
                <select 
                  id="editRole" 
                  className="settings-select"
                  value={editRole}
                  onChange={(e) => handleEditRoleChange(e.target.value)}
                  disabled={editingUserId === 1} // Primary Owner role cannot change
                >
                  <option value="super_admin">Super Admin</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="sales">Sales</option>
                  <option value="marketing">Marketing</option>
                  <option value="support">Support</option>
                  <option value="developer">Developer</option>
                  <option value="ai_agent">AI Agent</option>
                  <option value="finance">Finance</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              {/* Custom RBAC Permissions Checkbox overrides */}
              <div className="settings-form-group">
                <label>Modify Custom Permission Overrides</label>
                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>
                  Customize access boundaries. Unchecking will restrict the node's scope.
                </span>
                <div className="permissions-checklist-grid">
                  {ALL_AVAILABLE_PERMISSIONS.map(p => (
                    <label key={p.id} className="permission-checkbox-label">
                      <input 
                        type="checkbox" 
                        checked={editPermissions.includes(p.id)}
                        onChange={() => toggleEditPermission(p.id)}
                        disabled={editingUserId === 1} // Primary Owner permissions locked
                      />
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <strong style={{ fontSize: '11px', color: 'var(--text-primary)' }}>{p.name}</strong>
                        <span style={{ fontSize: '9px', color: 'var(--text-tertiary)' }}>{p.id}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button onClick={() => setIsEditModalOpen(false)} className="settings-input" style={{ width: 'auto', background: 'none', cursor: 'pointer' }}>
                Cancel
              </button>
              <button onClick={handleSaveChanges} className="retry-btn" style={{ width: 'auto' }}>
                Save Configurations
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ maxWidth: '900px', width: '100%', margin: '0 auto' }}>
        <header style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
          <button 
            onClick={() => window.location.href = '/'}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '50%', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer' }}
            title="Back to Dashboard"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)' }}>
              Settings Console
            </h1>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
              Manage personal configurations and tenant corporate organization profiles.
            </span>
          </div>
        </header>

        {/* Tabbed Layout Navigation */}
        <div className="settings-tabs">
          <button 
            className={`settings-tab-btn ${activeTab === 'personal' ? 'active' : ''}`}
            onClick={() => setActiveTab('personal')}
          >
            <Shield size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Personal Profile
          </button>
          <button 
            className={`settings-tab-btn ${activeTab === 'organization' ? 'active' : ''}`}
            onClick={() => setActiveTab('organization')}
          >
            <Building size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
            Organization Settings
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2.5fr', gap: 'var(--space-6)' }}>
          {/* Left Column - Avatar & Core Details */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', height: 'fit-content' }}>
            <div style={{ width: '96px', height: '96px', borderRadius: '50%', backgroundColor: 'var(--bg-tertiary)', border: '3px solid var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--font-3xl)', fontWeight: 'bold', color: 'var(--brand)', marginBottom: 'var(--space-4)', boxShadow: '0 0 12px var(--brand-light)' }}>
              {activeTab === 'personal' 
                ? (profile ? `${profile.first_name[0]}${profile.last_name[0]}` : 'U')
                : companyLogo
              }
            </div>
            <h3 style={{ fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)' }}>
              {activeTab === 'personal' 
                ? `${profile?.first_name} ${profile?.last_name}`
                : orgName
              }
            </h3>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', marginBottom: 'var(--space-4)' }}>
              {activeTab === 'personal' 
                ? `Role: ${profile?.role_id.toUpperCase().replace('_', ' ')}`
                : `Slug: /org/${orgSlug}`
              }
            </span>
            <div style={{ width: '100%', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {activeTab === 'personal' ? (
                <button 
                  onClick={() => window.location.href = '/profile/change-password'}
                  className="retry-btn"
                  style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)' }}
                >
                  <Key size={14} /> Change Password
                </button>
              ) : (
                <div style={{ background: 'var(--brand-light)', padding: 'var(--space-2)', borderRadius: 'var(--radius-xs)', border: '1px solid var(--brand)' }}>
                  <span style={{ fontSize: '10px', color: 'var(--brand)', fontWeight: 'bold', textTransform: 'uppercase' }}>
                    Active Plan: {subscriptionPlan}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - User Attributes / Organization Form */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
            
            {activeTab === 'personal' && (
              <div className="animate-fade-in">
                <h3 style={{ fontSize: 'var(--font-md)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', marginBottom: 'var(--space-4)' }}>
                  Profile Details
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <Mail size={18} style={{ color: 'var(--brand)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Email Address</span>
                      <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{profile?.email}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <Phone size={18} style={{ color: 'var(--brand)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Contact Number</span>
                      <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{profile?.phone || 'No phone registered'}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <Globe size={18} style={{ color: 'var(--brand)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Locale & Timezone</span>
                      <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>
                        Language: {(profile?.language || 'en').toUpperCase()} | Timezone: {profile?.timezone}
                      </strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <Shield size={18} style={{ color: 'var(--brand)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Tenant Organization</span>
                      <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>
                        Org ID: {profile?.organization_id} (Active)
                      </strong>
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--border-color)', marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Calendar size={16} style={{ color: 'var(--text-tertiary)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Member Since</span>
                      <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'bold' }}>
                        {profile ? new Date(profile.created_at).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <Clock size={16} style={{ color: 'var(--text-tertiary)' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Last Login Log</span>
                      <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'bold' }}>
                        {profile?.last_login ? new Date(profile.last_login).toLocaleString() : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'organization' && (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
                {/* 1. Core Profile & Config Form */}
                <form onSubmit={handleSaveOrganization} className="settings-form">
                  <h3 style={{ fontSize: 'var(--font-md)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: 'var(--space-2)' }}>
                    Organization Core Settings
                  </h3>

                  <div className="settings-form-row">
                    <div className="settings-form-group">
                      <label htmlFor="orgName">Organization / Company Name</label>
                      <input 
                        type="text" 
                        id="orgName"
                        className="settings-input"
                        value={orgName}
                        onChange={(e) => setOrgName(e.target.value)}
                        required
                      />
                    </div>

                    <div className="settings-form-group">
                      <label htmlFor="orgSlug">Company Slug URL</label>
                      <input 
                        type="text" 
                        id="orgSlug"
                        className="settings-input"
                        value={orgSlug}
                        onChange={(e) => setOrgSlug(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="settings-form-row">
                    <div className="settings-form-group">
                      <label htmlFor="gst">GST Registration Number</label>
                      <input 
                        type="text" 
                        id="gst"
                        className="settings-input"
                        placeholder="GSTIN"
                        value={gstNumber}
                        onChange={(e) => setGstNumber(e.target.value)}
                      />
                    </div>

                    <div className="settings-form-group">
                      <label htmlFor="timezone">Operational Timezone</label>
                      <select 
                        id="timezone" 
                        className="settings-select"
                        value={orgTimezone}
                        onChange={(e) => setOrgTimezone(e.target.value)}
                      >
                        <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                        <option value="UTC">UTC / Greenwich Mean</option>
                        <option value="US/Eastern">US/Eastern (EST/EDT)</option>
                        <option value="US/Pacific">US/Pacific (PST/PDT)</option>
                        <option value="Europe/London">Europe/London (GMT/BST)</option>
                      </select>
                    </div>
                  </div>

                  <div className="settings-form-group">
                    <label htmlFor="address">Billing Office Address</label>
                    <textarea 
                      id="address" 
                      rows={2} 
                      className="settings-textarea"
                      value={officeAddress}
                      onChange={(e) => setOfficeAddress(e.target.value)}
                    ></textarea>
                  </div>

                  {/* Company Logo Customizer */}
                  <div className="settings-form-group">
                    <label>Company Logo Icon Character</label>
                    <div className="logo-picker-grid">
                      {['Ω', 'Σ', 'Δ', 'Φ', 'Ψ', 'Λ'].map(logoChar => (
                        <button
                          key={logoChar}
                          type="button"
                          className={`logo-option-btn ${companyLogo === logoChar ? 'active' : ''}`}
                          onClick={() => setCompanyLogo(logoChar)}
                        >
                          {logoChar}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Brand Color Picker swatch */}
                  <div className="settings-form-group">
                    <label>Corporate Workspace Brand Color</label>
                    <div className="color-swatches-row">
                      {[
                        { hex: '#3b82f6', name: 'Standard Blue' },
                        { hex: '#8b5cf6', name: 'Royal Purple' },
                        { hex: '#6366f1', name: 'Premium Indigo' },
                        { hex: '#10b981', name: 'Emerald Green' },
                        { hex: '#ef4444', name: 'Ruby Red' },
                        { hex: '#f59e0b', name: 'Amber Orange' }
                      ].map(swatch => (
                        <button
                          key={swatch.hex}
                          type="button"
                          className={`color-swatch ${brandColor === swatch.hex ? 'active' : ''}`}
                          style={{ backgroundColor: swatch.hex }}
                          onClick={() => setBrandColor(swatch.hex)}
                          title={swatch.name}
                        >
                          {brandColor === swatch.hex && <Check size={14} />}
                        </button>
                      ))}
                      
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'var(--space-2)' }}>
                        <input 
                          type="color" 
                          className="color-picker-custom"
                          value={brandColor}
                          onChange={(e) => setBrandColor(e.target.value)}
                          title="Custom Hex Picker"
                        />
                        <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                          {brandColor.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
                    <button type="submit" className="retry-btn" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <Settings size={14} /> Save Organization Profile
                    </button>
                  </div>
                </form>

                {/* 2. Subscription plans selector */}
                <div style={{ marginTop: 'var(--space-4)' }}>
                  <h3 style={{ fontSize: 'var(--font-md)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                    Workspace Billing & Subscription Plan
                  </h3>
                  <div className="plans-grid">
                    {[
                      { id: 'startup', name: 'Startup Tier', price: '$49/mo', desc: 'Up to 3 active agent nodes' },
                      { id: 'pro', name: 'Professional Tier', price: '$149/mo', desc: 'Up to 10 active agent nodes' },
                      { id: 'enterprise', name: 'Enterprise Tier', price: '$499/mo', desc: 'Unrestricted agent routing' }
                    ].map(plan => (
                      <div 
                        key={plan.id}
                        className={`plan-card ${subscriptionPlan === plan.id ? 'active' : ''}`}
                        onClick={() => {
                          setSubscriptionPlan(plan.id);
                          localStorage.setItem('aibos_org_plan', plan.id);
                          showToast(`Selected ${plan.name}. Save changes to confirm.`, 'success');
                        }}
                      >
                        <div className="plan-card-header">
                          <span className="plan-card-name">{plan.name}</span>
                          <span className="plan-card-price">{plan.price}</span>
                          <span style={{ fontSize: '10px', color: 'var(--text-secondary)', marginTop: '4px' }}>{plan.desc}</span>
                        </div>
                        {subscriptionPlan === plan.id && <span className="plan-card-badge">Active</span>}
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Membership & User Access Control */}
                <div style={{ marginTop: 'var(--space-4)' }}>
                  <h3 style={{ fontSize: 'var(--font-md)', fontWeight: 'var(--weight-bold)', color: 'var(--text-primary)', borderBottom: '1px solid var(--border-color)', paddingBottom: 'var(--space-2)' }}>
                    Access Security & Member Registry
                  </h3>

                  {/* Generated Reset Password Link Alert box */}
                  {resetAlertLink && (
                    <div style={{ marginTop: 'var(--space-3)', padding: 'var(--space-3) var(--space-4)', background: 'rgba(234, 179, 8, 0.1)', border: '1px dashed var(--warning)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <span style={{ fontSize: '10px', color: 'var(--warning)', fontWeight: 'bold' }}>TEMP PASSWORD RESET LINK ({resetAlertUser})</span>
                          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>{resetAlertLink}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button 
                            className="retry-btn" 
                            style={{ fontSize: '10px', padding: '4px 8px' }}
                            onClick={() => {
                              navigator.clipboard.writeText(resetAlertLink);
                              showToast('Reset URL copied to clipboard!', 'success');
                            }}
                          >
                            Copy Link
                          </button>
                          <button 
                            onClick={() => setResetAlertLink('')}
                            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: '4px' }}
                          >
                            <X size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Generated Invitation Link Alert box */}
                  {generatedInviteLink && (
                    <div style={{ marginTop: 'var(--space-3)', padding: 'var(--space-3) var(--space-4)', background: 'var(--brand-light)', border: '1px dashed var(--brand)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <span style={{ fontSize: '10px', color: 'var(--brand)', fontWeight: 'bold' }}>PENDING USER INVITATION URL</span>
                          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all' }}>{generatedInviteLink}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button 
                            className="retry-btn" 
                            style={{ fontSize: '10px', padding: '4px 8px' }}
                            onClick={() => {
                              navigator.clipboard.writeText(generatedInviteLink);
                              showToast('Invitation link copied!', 'success');
                            }}
                          >
                            Copy Link
                          </button>
                          <button 
                            onClick={() => setGeneratedInviteLink('')}
                            style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer', padding: '4px' }}
                          >
                            <X size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Active Primary Owner info */}
                  <div style={{ padding: 'var(--space-3) var(--space-4)', background: 'var(--bg-tertiary)', borderLeft: '4px solid var(--brand)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginTop: 'var(--space-3)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', textTransform: 'uppercase', fontWeight: 'bold' }}>Primary Organization Owner</span>
                      <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>Charanjeet Singh</strong>
                      <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>charanjeet.s7730@gmail.com</span>
                    </div>
                    <span className="badge-role" style={getRoleBadgeStyle('super_admin')}>Primary Owner</span>
                  </div>

                  {/* Invite User Form */}
                  <form onSubmit={handleInviteUser} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginTop: 'var(--space-4)', padding: 'var(--space-4)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                    <h4 style={{ margin: 0, fontSize: 'var(--font-sm)', fontWeight: 'bold', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <UserPlus size={14} /> Invite New Organization Member
                    </h4>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
                      <div className="settings-form-group">
                        <label htmlFor="inviteName">Full Name</label>
                        <input 
                          type="text" 
                          id="inviteName"
                          className="settings-input"
                          placeholder="John Doe"
                          value={inviteName}
                          onChange={(e) => setInviteName(e.target.value)}
                          required
                        />
                      </div>
                      
                      <div className="settings-form-group">
                        <label htmlFor="inviteEmail">Corporate Email</label>
                        <input 
                          type="email" 
                          id="inviteEmail"
                          className="settings-input"
                          placeholder="john@democorp.com"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          required
                        />
                      </div>

                      <div className="settings-form-group">
                        <label htmlFor="inviteRole">Assign Initial Role</label>
                        <select 
                          id="inviteRole"
                          className="settings-select"
                          value={inviteRole}
                          onChange={(e) => handleInviteRoleChange(e.target.value)}
                        >
                          <option value="admin">Admin</option>
                          <option value="manager">Manager</option>
                          <option value="sales">Sales</option>
                          <option value="marketing">Marketing</option>
                          <option value="support">Support</option>
                          <option value="developer">Developer</option>
                          <option value="ai_agent">AI Agent</option>
                          <option value="finance">Finance</option>
                          <option value="viewer">Viewer</option>
                        </select>
                      </div>
                    </div>

                    {/* Permissions checklist inside invitation */}
                    <div className="settings-form-group">
                      <label>Configure Initial Scope Permissions</label>
                      <div className="permissions-checklist-grid">
                        {ALL_AVAILABLE_PERMISSIONS.map(p => (
                          <label key={p.id} className="permission-checkbox-label">
                            <input 
                              type="checkbox" 
                              checked={invitePermissions.includes(p.id)}
                              onChange={() => toggleInvitePermission(p.id)}
                            />
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <strong style={{ fontSize: '11px', color: 'var(--text-primary)' }}>{p.name}</strong>
                              <span style={{ fontSize: '9px', color: 'var(--text-tertiary)' }}>{p.id}</span>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-1)' }}>
                      <button type="submit" className="retry-btn" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-sm)', width: 'auto' }}>
                        <Link size={14} /> Send Invitation & Link
                      </button>
                    </div>
                  </form>

                  {/* Users Table */}
                  <div className="settings-table-wrapper" style={{ marginTop: 'var(--space-4)' }}>
                    <table className="settings-table">
                      <thead>
                        <tr>
                          <th>Member Details</th>
                          <th>Status</th>
                          <th>Role</th>
                          <th>Permissions</th>
                          <th style={{ textAlign: 'right' }}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orgUsers.map(user => (
                          <tr key={user.id}>
                            <td>
                              <div style={{ fontWeight: 'var(--weight-semibold)', color: 'var(--text-primary)' }}>{user.name}</div>
                              <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{user.email}</div>
                            </td>
                            <td>
                              <span className={`badge-status ${user.status}`}>{user.status}</span>
                            </td>
                            <td>
                              <span className="badge-role" style={getRoleBadgeStyle(user.role)}>
                                {getRoleDisplayName(user.role)}
                              </span>
                            </td>
                            <td>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', maxWidth: '240px' }}>
                                {(user.permissions || []).map((perm: string) => (
                                  <span key={perm} className="badge-permission">{perm}</span>
                                ))}
                              </div>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', gap: '6px' }}>
                                <button 
                                  onClick={() => openEditModal(user)} 
                                  className="task-delete-btn"
                                  style={{ padding: '6px', color: 'var(--brand)' }}
                                  title="Edit User Details & Permissions"
                                >
                                  <Edit2 size={14} />
                                </button>
                                <button 
                                  onClick={() => triggerResetPassword(user)} 
                                  className="task-delete-btn"
                                  style={{ padding: '6px', color: 'var(--warning)' }}
                                  title="Reset Password Credentials"
                                >
                                  <KeyRound size={14} />
                                </button>
                                <button 
                                  onClick={() => toggleSuspendUser(user.id)} 
                                  className="task-delete-btn"
                                  style={{ padding: '6px', color: user.status === 'suspended' ? 'var(--success)' : 'var(--danger)' }}
                                  title={user.status === 'suspended' ? 'Activate Account' : 'Suspend Account'}
                                  disabled={user.id === 1}
                                >
                                  <ShieldAlert size={14} />
                                </button>
                                <button 
                                  onClick={() => handleDeleteUser(user.id)} 
                                  className="task-delete-btn"
                                  style={{ padding: '6px' }}
                                  title="Delete User from Org"
                                  disabled={user.id === 1}
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
