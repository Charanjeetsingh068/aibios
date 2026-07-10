"use client";

import { useEffect, useState, useCallback, Fragment } from 'react';
import {
  Sun, Moon, Server, Activity, Cpu, Database, Shield,
  Phone, PhoneCall, Calendar, DollarSign, Plus, Trash2, Bell,
  Play, Pause, Facebook, Instagram, MessageSquare, Check, Sparkles,
  FileText, AlertTriangle, Users, Building2, BarChart3, GitBranch,
  CheckSquare, Zap, Bot, BookOpen, File, Megaphone, CreditCard,
  Settings, ScrollText, Code, TrendingUp, TrendingDown,
  LogOut, ChevronRight, Target, Mail,
  Wifi, Search, UserPlus, Edit2, Edit3, ShieldAlert, 
  KeyRound, Link, Star, Award, RefreshCw
} from 'lucide-react';
import '../styles/dashboard.css';
import axiosInstance from '../services/axiosInstance';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSystemStatus, fetchSystemInfo, fetchDatabaseStatus, fetchAgentStatus, fetchHealth,
  SystemStatus, SystemInfo, DatabaseStatus, AgentStatus, HealthStatus
} from '../services/systemService';
import {
  fetchDashboardMetrics, fetchDashboardUsers, fetchDashboardRoles,
  fetchOrganizationDetails, fetchAuditLogs, fetchDashboardOverview,
  fetchTasks, createTask as apiCreateTask, toggleTask as apiToggleTask, deleteTask as apiDeleteTask,
  fetchCampaigns as apiFetchCampaigns, createCampaign as apiCreateCampaign,
  toggleCampaignStatus as apiToggleCampaign, deleteCampaign as apiDeleteCampaign,
  fetchMeetings as apiFetchMeetings, createMeeting as apiCreateMeeting, deleteMeeting as apiDeleteMeeting,
  DashboardMetrics, DashboardUser, DashboardRole, OrganizationDetails, AuditLogEntry,
} from '../services/dashboardService';
import { fetchLeads, createLead as apiCreateLead, updateLead as apiUpdateLead, deleteLead as apiDeleteLead, fetchLeadEvents, addLeadEvent as apiAddLeadEvent, Lead } from '../services/leadsService';
import { fetchDeals, createDeal as apiCreateDeal, updateDeal as apiUpdateDeal, Deal } from '../services/dealsService';
import { fetchIntegrations, connectIntegration as apiConnectIntegration, fetchLeadMappings, createLeadMapping, deleteLeadMapping } from '../services/integrationsService';
import { useRealtimeSocket } from '../hooks/useRealtimeSocket';
import { fetchWorkflows, createWorkflow as apiCreateWorkflow, updateWorkflow as apiUpdateWorkflow, deleteWorkflow as apiDeleteWorkflow, runWorkflow as apiRunWorkflow } from '../services/workflowService';
import { fetchKbArticles, createKbArticle as apiCreateKbArticle, deleteKbArticle as apiDeleteKbArticle, searchKbArticles as apiSearchKbArticles } from '../services/kbService';
import { fetchDocuments, uploadDocument as apiUploadDocument, deleteDocument as apiDeleteDocument, getDocumentDownloadUrl } from '../services/documentService';
import { fetchCallLogs, fetchCallTranscript as apiFetchCallTranscript } from '../services/voiceService';
import { fetchInvoices, triggerCheckout as apiTriggerCheckout } from '../services/billingService';

import { RequirePermission } from '../components/RequirePermission';
import { Modal } from '../components/Modal';
import { createRole as apiCreateRole, deleteRole as apiDeleteRole, assignPermission as apiAssignPermission } from '../services/roleService';
import { inviteUser as apiInviteUser, deleteUser as apiDeleteUser, assignUserRole as apiAssignUserRole, createUser as apiCreateUser, forceUserPassword as apiForceUserPassword, updateUser as apiUpdateUser, suspendUser as apiSuspendUser, reactivateUser as apiReactivateUser, resetUserPassword as apiResetUserPassword } from '../services/userService';


// ─── Nav Config ────────────────────────────────────────────────────────────────

const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: Cpu },
      { id: 'analytics', label: 'Analytics', icon: BarChart3 },
      { id: 'reports', label: 'Reports', icon: FileText },
    ],
  },
  {
    label: 'CRM',
    items: [
      { id: 'leads', label: 'Leads', icon: Target },
      { id: 'pipeline', label: 'Sales Pipeline', icon: GitBranch },
      { id: 'tasks', label: 'Tasks', icon: CheckSquare },
      { id: 'meetings', label: 'Meetings', icon: Calendar },
    ],
  },
  {
    label: 'Channels',
    items: [
      { id: 'campaigns', label: 'Campaigns', icon: Megaphone },
      { id: 'facebook', label: 'Facebook', icon: Facebook },
      { id: 'instagram', label: 'Instagram', icon: Instagram },
      { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
      { id: 'ai-voice', label: 'AI Voice', icon: PhoneCall },
    ],
  },
  {
    label: 'AI Platform',
    items: [
      { id: 'ai-agents', label: 'AI Agents', icon: Bot },
      { id: 'automation', label: 'Automation', icon: Zap },
      { id: 'knowledge-base', label: 'Knowledge Base', icon: BookOpen },
      { id: 'documents', label: 'Documents', icon: File },
    ],
  },
  {
    label: 'Administration',
    items: [
      { id: 'organizations', label: 'Organizations', icon: Building2 },
      { id: 'users', label: 'Users', icon: Users },
      { id: 'roles', label: 'Roles & Permissions', icon: Shield },
      { id: 'billing', label: 'Billing', icon: CreditCard },
    ],
  },
  {
    label: 'System',
    items: [
      { id: 'system-health', label: 'System Health', icon: Activity },
      { id: 'audit-logs', label: 'Audit Logs', icon: ScrollText },
      { id: 'developer', label: 'Developer', icon: Code },
      { id: 'settings', label: 'Settings', icon: Settings },
    ],
  },
];

// ─── Static config (not data) ───────────────────────────────────────────────

const PIPELINE_STAGE_CONFIG = [
  { id: 'lead', label: 'Lead', color: '#94a3b8' },
  { id: 'qualified', label: 'Qualified', color: '#3b82f6' },
  { id: 'meeting', label: 'Meeting', color: '#8b5cf6' },
  { id: 'proposal', label: 'Proposal', color: '#f59e0b' },
  { id: 'negotiation', label: 'Negotiation', color: '#f97316' },
  { id: 'won', label: 'Won', color: '#10b981' },
  { id: 'lost', label: 'Lost', color: '#ef4444' },
];

const BILLING_PLANS = [
  { id: 'startup', name: 'Startup', price: '$49', period: '/mo', features: ['3 agent nodes', '1,000 leads/mo', 'Email support'] },
  { id: 'pro', name: 'Professional', price: '$149', period: '/mo', features: ['10 agent nodes', '10,000 leads/mo', 'Priority support'] },
  { id: 'enterprise', name: 'Enterprise', price: '$499', period: '/mo', features: ['Unlimited AI agent nodes', 'Unlimited leads', 'All CRM modules', 'WhatsApp + FB + IG', 'Priority SLA support', 'Custom domain', 'Dedicated success manager'] },
];

const AI_AGENTS_CONFIG = [
  { id: 'supervisor', name: 'Supervisor AI', type: 'Orchestration', icon: Star, desc: 'Routes tasks to specialist agents based on intent classification.' },
  { id: 'voice', name: 'Voice AI', type: 'Telephony', icon: PhoneCall, desc: 'Handles outbound/inbound voice calls with LLM-driven conversations.' },
  { id: 'sales', name: 'Sales AI', type: 'CRM', icon: TrendingUp, desc: 'Qualifies leads and schedules demos through automated follow-ups.' },
  { id: 'marketing', name: 'Marketing AI', type: 'Campaigns', icon: Megaphone, desc: 'Generates personalized campaign content and A/B test variations.' },
  { id: 'support', name: 'Support AI', type: 'Customer Service', icon: MessageSquare, desc: 'Resolves support queries via chat, WhatsApp, and email.' },
  { id: 'knowledge', name: 'Knowledge AI', type: 'Retrieval', icon: BookOpen, desc: 'Performs semantic search across documents and knowledge base.' },
  { id: 'developer', name: 'Developer AI', type: 'Tooling', icon: Code, desc: 'Generates code, writes tests and deploys automation scripts.' },
  { id: 'automation', name: 'Automation AI', type: 'Workflows', icon: Zap, desc: 'Executes multi-step automation workflows triggered by events.' },
];

function getRoleBadgeStyle(role: string): React.CSSProperties {
  const map: Record<string, React.CSSProperties> = {
    super_admin: { background: 'rgba(59,130,246,0.12)', color: '#60a5fa' },
    org_admin: { background: 'rgba(168,85,247,0.12)', color: '#c084fc' },
    manager: { background: 'rgba(234,179,8,0.12)', color: '#fbbf24' },
    sales_executive: { background: 'rgba(249,115,22,0.12)', color: '#fb923c' },
    marketing: { background: 'rgba(236,72,153,0.12)', color: '#f472b6' },
    support: { background: 'rgba(20,184,166,0.12)', color: '#2dd4bf' },
    developer: { background: 'rgba(99,102,241,0.12)', color: '#818cf8' },
    ai_agent: { background: 'rgba(16,185,129,0.12)', color: '#34d399' },
    finance: { background: 'rgba(100,116,139,0.12)', color: '#94a3b8' },
    viewer: { background: 'rgba(148,163,184,0.12)', color: '#94a3b8' },
  };
  return map[role] || { background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' };
}

function getRoleDisplayName(role: string) {
  return role.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function getLeadStatusStyle(status: string): React.CSSProperties {
  const map: Record<string, React.CSSProperties> = {
    new: { background: 'rgba(59,130,246,0.12)', color: '#60a5fa' },
    qualified: { background: 'rgba(16,185,129,0.12)', color: '#34d399' },
    pending: { background: 'rgba(245,158,11,0.12)', color: '#fbbf24' },
    spam: { background: 'rgba(239,68,68,0.12)', color: '#f87171' },
    assigned: { background: 'rgba(168,85,247,0.12)', color: '#c084fc' },
    closed: { background: 'rgba(100,116,139,0.12)', color: '#94a3b8' },
  };
  return map[status] || {};
}

// ─── Main Component ─────────────────────────────────────────────────────────────

interface LiveNotification { id: string | number; text: string; time: string; unread: boolean }

export default function Dashboard() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [activeTab, setActiveTab] = useState('dashboard');
  const queryClient = useQueryClient();

  // ── System API states ──
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [dbStatus, setDbStatus] = useState<DatabaseStatus | null>(null);
  const [agents, setAgents] = useState<AgentStatus | null>(null);
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [userProfile, setUserProfile] = useState<any>(null);

  // ── Dashboard metrics from new API ──
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dashboardUsers, setDashboardUsers] = useState<DashboardUser[]>([]);
  const [dashboardRoles, setDashboardRoles] = useState<DashboardRole[]>([]);
  const [orgDetails, setOrgDetails] = useState<OrganizationDetails | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  // ── Real-time notification feed (populated only by live socket events) ──
const [notifications, setNotifications] = useState<LiveNotification[]>([]);
  const [leadMappings, setLeadMappings] = useState<any[]>([]);
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [newMappingFormId, setNewMappingFormId] = useState('');
  const [newMappingMetaField, setNewMappingMetaField] = useState('');
  const [newMappingCrmField, setNewMappingCrmField] = useState('');
  const pushNotification = (text: string) => {
    setNotifications(prev => [{ id: Date.now(), text, time: 'Just now', unread: true }, ...prev.slice(0, 19)]);
  };

  // ── Leads filter ──
  const LEADS_PAGE_SIZE = 100;
  const [leadsFilter, setLeadsFilter] = useState('all');
  const [leadsSearch, setLeadsSearch] = useState('');
  const [debouncedLeadsSearch, setDebouncedLeadsSearch] = useState('');
  const [leadsPage, setLeadsPage] = useState(0);
  const [userSearch, setUserSearch] = useState('');
  const [showAddLead, setShowAddLead] = useState(false);
  const [newLead, setNewLead] = useState({ name: '', company: '', phone: '', source: 'manual', value: '' });
  const [expandedLeadId, setExpandedLeadId] = useState<string | null>(null);
  const [leadEvents, setLeadEvents] = useState<Record<string, any[]>>({});
  const [newNoteText, setNewNoteText] = useState<Record<string, string>>({});

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedLeadsSearch(leadsSearch);
      setLeadsPage(0);
    }, 300);
    return () => clearTimeout(handler);
  }, [leadsSearch]);

  // ── Pipeline / deals ──
  const [showAddDeal, setShowAddDeal] = useState(false);
  const [newDeal, setNewDeal] = useState({ name: '', company: '', value: '' });

  // ── Campaigns ──
  const [newCampaignName, setNewCampaignName] = useState('');

  // ── Tasks ──
  const [newTaskText, setNewTaskText] = useState('');

  // ── Meetings ──
  const [newMeetingTitle, setNewMeetingTitle] = useState('');
  const [newMeetingTime, setNewMeetingTime] = useState('');

  // ── Workflows ──
  const [showAddWorkflow, setShowAddWorkflow] = useState(false);
  const [newWfName, setNewWfName] = useState('');
  const [newWfTrigger, setNewWfTrigger] = useState('Lead Created');

  // ── Knowledge Base ──
  const [showAddKb, setShowAddKb] = useState(false);
  const [newKbTitle, setNewKbTitle] = useState('');
  const [newKbCategory, setNewKbCategory] = useState('General');


  // ── Roles & Users Modals/Forms ──

  // ── Modal States ──
  const [changeRoleModalUser, setChangeRoleModalUser] = useState<any>(null);
  const [changeRoleInput, setChangeRoleInput] = useState('');
  const [assignPermissionRole, setAssignPermissionRole] = useState<any>(null);
  const [assignPermissionInput, setAssignPermissionInput] = useState('');

  const [deleteConfirmInfo, setDeleteConfirmInfo] = useState<{ type: 'user' | 'role', id: string, name: string } | null>(null);


  const [showInviteUser, setShowInviteUser] = useState(false);


  const [editUserModal, setEditUserModal] = useState<any>(null);
  const [editUserFirstName, setEditUserFirstName] = useState('');
  const [editUserLastName, setEditUserLastName] = useState('');
  const [editUserEmail, setEditUserEmail] = useState('');
  const [editUserPhone, setEditUserPhone] = useState('');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [createFirstName, setCreateFirstName] = useState('');
  const [createLastName, setCreateLastName] = useState('');
  const [createPassword, setCreatePassword] = useState('');
  const [forcePasswordUser, setForcePasswordUser] = useState<any>(null);
  const [forcePasswordInput, setForcePasswordInput] = useState('');
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState('viewer');
  
  const [showAddRole, setShowAddRole] = useState(false);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDesc, setNewRoleDesc] = useState('');

  

  // Mutations


  const editUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: string, data: any }) => apiUpdateUser(id, data),
    onSuccess: () => {
      pushNotification("User updated successfully");
      setEditUserModal(null);
      refreshDashboardUsers();
    },
    onError: (err: any) => pushNotification(err.response?.data?.detail || "Failed to update user")
  });

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
    onError: (err: any) => pushNotification(err.response?.data?.detail || "Failed to create user")
  });

  const inviteUserMutation = useMutation({
    mutationFn: apiInviteUser,
    onSuccess: () => { invalidate('users'); invalidate('overview'); refreshDashboardUsers(); setShowInviteUser(false); setNewUserEmail(''); },
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to invite user')
  });

  const deleteUserMutation = useMutation({
    mutationFn: apiDeleteUser,
    onSuccess: () => { invalidate('users'); invalidate('overview'); refreshDashboardUsers(); },
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to delete user')
  });

  const createRoleMutation = useMutation({
    mutationFn: apiCreateRole,
    onSuccess: () => { 
      invalidate('roles'); 
      fetchDashboardRoles().then(r => setDashboardRoles(r.roles));
      setShowAddRole(false); setNewRoleName(''); setNewRoleDesc(''); 
    },
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to create role')
  });

  const deleteRoleMutation = useMutation({
    mutationFn: apiDeleteRole,
    onSuccess: () => { 
      invalidate('roles'); 
      fetchDashboardRoles().then(r => setDashboardRoles(r.roles));
    },
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to delete role')
  });
  
  // Handlers
  const handleInviteUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserEmail.trim()) return;
    inviteUserMutation.mutate({ email: newUserEmail.trim(), role_id: newUserRole, first_name: 'Invited', last_name: 'User' });
  };
  
  const handleCreateRole = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRoleName.trim()) return;
    const roleId = newRoleName.toLowerCase().replace(/\s+/g, '_');
    createRoleMutation.mutate({ id: roleId, name: newRoleName.trim(), description: newRoleDesc.trim() });
  };

  // ── Real backend data (React Query) ──
  const overviewQuery = useQuery({ queryKey: ['overview'], queryFn: fetchDashboardOverview, refetchInterval: 30000 });
  const overview = overviewQuery.data;

  const leadsQuery = useQuery({
    queryKey: ['leads', debouncedLeadsSearch, leadsPage],
    queryFn: () => fetchLeads({
      search: debouncedLeadsSearch || undefined,
      limit: LEADS_PAGE_SIZE,
      offset: leadsPage * LEADS_PAGE_SIZE,
    })
  });
  const leads: Lead[] = leadsQuery.data?.leads ?? [];
  const leadsTotal = leadsQuery.data?.total ?? 0;

  const dealsQuery = useQuery({ queryKey: ['deals'], queryFn: fetchDeals });
  const deals: Deal[] = dealsQuery.data?.deals ?? [];

  const campaignsQuery = useQuery({ queryKey: ['campaigns'], queryFn: apiFetchCampaigns });
  const campaigns = campaignsQuery.data?.campaigns ?? [];

  const tasksQuery = useQuery({ queryKey: ['tasks'], queryFn: fetchTasks });
  const tasks = tasksQuery.data?.tasks ?? [];

  const meetingsQuery = useQuery({ queryKey: ['meetings'], queryFn: apiFetchMeetings });
  const meetings = meetingsQuery.data?.meetings ?? [];

  const integrationsQuery = useQuery({ queryKey: ['integrations'], queryFn: fetchIntegrations });
  const integrations = integrationsQuery.data?.integrations ?? [];

  // Workflows React Query
  const workflowsQuery = useQuery({ queryKey: ['workflows'], queryFn: fetchWorkflows });
  const workflows = workflowsQuery.data?.workflows ?? [];

  // KB Articles React Query
  const [kbSearchText, setKbSearchText] = useState('');
  const kbQuery = useQuery({ queryKey: ['kb'], queryFn: fetchKbArticles });
  const kbSearchQuery = useQuery({
    queryKey: ['kb-search', kbSearchText],
    queryFn: () => apiSearchKbArticles(kbSearchText),
    enabled: !!kbSearchText
  });
  const kbArticles = kbSearchText ? (kbSearchQuery.data?.results ?? []) : (kbQuery.data?.articles ?? []);

  // Documents React Query
  const documentsQuery = useQuery({ queryKey: ['documents'], queryFn: fetchDocuments });
  const documents = documentsQuery.data?.documents ?? [];

  // Voice Calls React Query
  const voiceQuery = useQuery({ queryKey: ['calls'], queryFn: fetchCallLogs });
  const voiceCalls = voiceQuery.data?.calls ?? [];

  // Billing Invoices React Query
  const invoicesQuery = useQuery({ queryKey: ['invoices'], queryFn: fetchInvoices });
  const invoices = invoicesQuery.data?.invoices ?? [];

  // Expanded voice call transcript
  const [expandedCallId, setExpandedCallId] = useState<string | null>(null);
  const [callTranscript, setCallTranscript] = useState<string>('');

  // ── Mutations ──
  const invalidate = (key: string) => queryClient.invalidateQueries({ queryKey: [key] });

  const createLeadMutation = useMutation({
    mutationFn: apiCreateLead,
    onSuccess: () => { invalidate('leads'); invalidate('overview'); setShowAddLead(false); setNewLead({ name: '', company: '', phone: '', source: 'manual', value: '' }); },
  });
  const updateLeadMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => apiUpdateLead(id, data),
    onSuccess: () => { invalidate('leads'); invalidate('overview'); },
  });
  const deleteLeadMutation = useMutation({
    mutationFn: apiDeleteLead,
    onSuccess: () => { invalidate('leads'); invalidate('overview'); },
  });

  const createDealMutation = useMutation({
    mutationFn: apiCreateDeal,
    onSuccess: () => { invalidate('deals'); invalidate('overview'); setShowAddDeal(false); setNewDeal({ name: '', company: '', value: '' }); },
  });
  const updateDealMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => apiUpdateDeal(id, data),
    onSuccess: () => { invalidate('deals'); invalidate('overview'); },
  });

  const createCampaignMutation = useMutation({
    mutationFn: (name: string) => apiCreateCampaign(name),
    onSuccess: () => { invalidate('campaigns'); setNewCampaignName(''); },
  });
  const toggleCampaignMutation = useMutation({
    mutationFn: apiToggleCampaign,
    onSuccess: () => invalidate('campaigns'),
  });
  const deleteCampaignMutation = useMutation({
    mutationFn: apiDeleteCampaign,
    onSuccess: () => invalidate('campaigns'),
  });

  const createTaskMutation = useMutation({
    mutationFn: apiCreateTask,
    onSuccess: () => { invalidate('tasks'); setNewTaskText(''); },
  });
  const toggleTaskMutation = useMutation({ mutationFn: apiToggleTask, onSuccess: () => invalidate('tasks') });
  const deleteTaskMutation = useMutation({ mutationFn: apiDeleteTask, onSuccess: () => invalidate('tasks') });

  const createMeetingMutation = useMutation({
    mutationFn: ({ title, scheduledAt }: { title: string; scheduledAt: string }) => apiCreateMeeting(title, scheduledAt),
    onSuccess: () => { invalidate('meetings'); invalidate('overview'); setNewMeetingTitle(''); setNewMeetingTime(''); },
  });
  const deleteMeetingMutation = useMutation({ mutationFn: apiDeleteMeeting, onSuccess: () => { invalidate('meetings'); invalidate('overview'); } });

  const connectIntegrationMutation = useMutation({
    mutationFn: apiConnectIntegration,
    onError: (err: any) => pushNotification(err?.message || 'Failed to connect integration'),
    onSuccess: () => invalidate('integrations'),
  });

  const createWorkflowMutation = useMutation({
    mutationFn: apiCreateWorkflow,
    onSuccess: () => { invalidate('workflows'); },
  });
  const updateWorkflowMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => apiUpdateWorkflow(id, data),
    onSuccess: () => invalidate('workflows'),
  });
  const deleteWorkflowMutation = useMutation({
    mutationFn: apiDeleteWorkflow,
    onSuccess: () => invalidate('workflows'),
  });
  const runWorkflowMutation = useMutation({
    mutationFn: apiRunWorkflow,
    onSuccess: () => { invalidate('workflows'); invalidate('overview'); },
  });

  const createKbMutation = useMutation({
    mutationFn: apiCreateKbArticle,
    onSuccess: () => invalidate('kb'),
  });
  const deleteKbMutation = useMutation({
    mutationFn: apiDeleteKbArticle,
    onSuccess: () => invalidate('kb'),
  });

  const uploadDocMutation = useMutation({
    mutationFn: apiUploadDocument,
    onSuccess: () => invalidate('documents'),
  });
  const deleteDocMutation = useMutation({
    mutationFn: apiDeleteDocument,
    onSuccess: () => invalidate('documents'),
  });

  const checkoutMutation = useMutation({
    mutationFn: ({ planId, gateway }: { planId: string; gateway: 'stripe' | 'razorpay' }) => apiTriggerCheckout(planId, gateway),
    onSuccess: (res) => {
      if (res.checkout_url) {
        window.open(res.checkout_url, '_blank');
      }
    },
  });

  // ── Real-time socket: updates cached query data + notification feed instantly ──
  useRealtimeSocket({
    'lead:new': (data) => {
      invalidate('leads'); invalidate('overview');
      pushNotification(`New lead captured: ${data.name} via ${data.source}`);
    },
    'lead:updated': () => { invalidate('leads'); invalidate('overview'); },
    'lead:deleted': () => { invalidate('leads'); invalidate('overview'); },
    'deal:new': (data) => { invalidate('deals'); invalidate('overview'); pushNotification(`New deal created: ${data.name}`); },
    'deal:updated': () => { invalidate('deals'); invalidate('overview'); },
    'deal:deleted': () => { invalidate('deals'); invalidate('overview'); },
  });

  // ─── Auth check + profile load ─────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('aibos_access_token');
    if (!token) {
      window.location.href = '/auth/login';
      return;
    }
    import('../services/authService').then(({ getMe }) => {
      getMe().then(profile => setUserProfile(profile)).catch(() => {
        window.location.href = '/auth/login';
      });
    });
  }, []);

  // ─── Theme init ───────────────────────────────────────────────────────────
  useEffect(() => {
    const saved = document.documentElement.getAttribute('data-theme') as 'light' | 'dark';
    if (saved) setTheme(saved);
  }, []);

  // ─── System API fetch ─────────────────────────────────────────────────────
  const loadSystemData = useCallback(async () => {
    try {
      setIsError(false);
      if (!status || isError) setIsLoading(true);
      const [s, i, db, ag, h] = await Promise.all([
        fetchSystemStatus(), fetchSystemInfo(), fetchDatabaseStatus(), fetchAgentStatus(), fetchHealth(),
      ]);
      setStatus(s); setInfo(i); setDbStatus(db); setAgents(ag); setHealthData(h);
      setIsError(false);
    } catch (err: any) {
      setIsError(true);
      setErrorMessage(err?.message || 'Could not connect to FastAPI backend.');
      setStatus(null); setInfo(null); setDbStatus(null); setAgents(null); setHealthData(null);
    } finally {
      setIsLoading(false);
    }
  }, [status, isError]);

  useEffect(() => {
    loadSystemData();
    const iv = setInterval(loadSystemData, 15000);
    return () => clearInterval(iv);
  }, []);

  // ─── Dashboard metrics API fetch ──────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('aibos_access_token');
    if (!token) return;
    Promise.allSettled([
      fetchDashboardMetrics(),
      fetchDashboardUsers(),
      fetchDashboardRoles(),
      fetchOrganizationDetails(),
      fetchAuditLogs(),
    ]).then(([m, u, r, o, a]) => {
      if (m.status === 'fulfilled') setMetrics(m.value);
      if (u.status === 'fulfilled') setDashboardUsers(u.value.users);
      if (r.status === 'fulfilled') setDashboardRoles(r.value.roles);
      if (o.status === 'fulfilled') setOrgDetails(o.value);
      if (a.status === 'fulfilled') setAuditLogs(a.value.logs);
    });
  }, []);

  const refreshDashboardUsers = () => {
    fetchDashboardUsers().then(res => setDashboardUsers(res.users)).catch(() => {});
  };

  const updateUserStatusMutation = useMutation({
    mutationFn: ({ id, status: newStatus }: { id: string; status: string }) => newStatus === 'suspended' ? apiSuspendUser(id) : apiReactivateUser(id),
    onSuccess: refreshDashboardUsers,
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to update user status'),
  });
  const resetPasswordMutation = useMutation({
    mutationFn: apiResetUserPassword,
    onSuccess: (res) => pushNotification(res.email_sent ? 'Password reset email sent.' : `Reset link generated: ${res.reset_link}`),
    onError: (err: any) => pushNotification(err?.response?.data?.detail || 'Failed to generate reset link'),
  });

  const toggleUserSuspend = (u: DashboardUser) => {
    updateUserStatusMutation.mutate({ id: u.id, status: u.status === 'suspended' ? 'active' : 'suspended' });
  };

  // ─── Handlers ────────────────────────────────────────────────────────────
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('aibos-theme', next);
  };

  const addTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskText.trim()) return;
    createTaskMutation.mutate(newTaskText.trim());
  };

  const toggleTask = (id: string) => toggleTaskMutation.mutate(id);
  const deleteTask = (id: string) => deleteTaskMutation.mutate(id);
  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  const dismissNotif = (id: string | number) => setNotifications(prev => prev.filter(n => n.id !== id));
  const toggleCampaign = (id: string) => toggleCampaignMutation.mutate(id);

  const handleDownloadReport = (reportType: string) => {
    const token = localStorage.getItem('aibos_access_token');
    const baseUrl = axiosInstance.defaults.baseURL || '/api/v1';
    window.open(`${baseUrl}/reports/${reportType}/download?format=csv&token=${token}`, '_blank');
  };

  const toggleWorkflow = (id: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'active' ? 'paused' : 'active';
    updateWorkflowMutation.mutate({ id, data: { status: nextStatus } });
  };

  const toggleCallExpand = async (callId: string) => {
    if (expandedCallId === callId) {
      setExpandedCallId(null);
      setCallTranscript('');
    } else {
      setExpandedCallId(callId);
      setCallTranscript('Loading transcript...');
      try {
        const res = await apiFetchCallTranscript(callId);
        setCallTranscript(res.transcript ?? res.detail ?? 'No transcript available.');
      } catch {
        setCallTranscript('Failed to retrieve call transcript from backend.');
      }
    }
  };

  const addLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLead.name.trim()) return;
    createLeadMutation.mutate({
      name: newLead.name.trim(),
      company: newLead.company || undefined,
      phone: newLead.phone || undefined,
      source: newLead.source,
      value: newLead.value ? Number(newLead.value) : 0,
    });
  };
  const qualifyLead = (id: string) => updateLeadMutation.mutate({ id, data: { status: 'qualified' } });
  const markLeadSpam = (id: string) => updateLeadMutation.mutate({ id, data: { status: 'spam' } });
  const removeLead = (id: string) => deleteLeadMutation.mutate(id);
  const toggleLeadExpand = async (id: string) => {
    if (expandedLeadId === id) { setExpandedLeadId(null); return; }
    setExpandedLeadId(id);
    if (!leadEvents[id]) {
      const { events } = await fetchLeadEvents(id);
      setLeadEvents(prev => ({ ...prev, [id]: events }));
    }
  };

  const handleAddNote = async (leadId: string) => {
    const text = newNoteText[leadId]?.trim();
    if (!text) return;
    try {
      await apiAddLeadEvent(leadId, 'note', text);
      setNewNoteText(prev => ({ ...prev, [leadId]: '' }));
      const { events } = await fetchLeadEvents(leadId);
      setLeadEvents(prev => ({ ...prev, [leadId]: events }));
    } catch (err: any) {
      pushNotification(`Failed to add note: ${err.message}`);
    }
  };

  const addDeal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeal.name.trim()) return;
    createDealMutation.mutate({ name: newDeal.name.trim(), company: newDeal.company || undefined, value: newDeal.value ? Number(newDeal.value) : 0 });
  };
  const moveDealStage = (id: string, stage: string) => updateDealMutation.mutate({ id, data: { stage } });

  const handleDragStart = (e: React.DragEvent, dealId: string) => {
    e.dataTransfer.setData('text/plain', dealId);
  };

  const handleDrop = (e: React.DragEvent, targetStage: string) => {
    e.preventDefault();
    const dealId = e.dataTransfer.getData('text/plain');
    if (dealId) {
      updateDealMutation.mutate({ id: dealId, data: { stage: targetStage } });
    }
  };

  const addCampaign = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCampaignName.trim()) return;
    createCampaignMutation.mutate(newCampaignName.trim());
  };
  const removeCampaign = (id: string) => deleteCampaignMutation.mutate(id);

  const addMeeting = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMeetingTitle.trim() || !newMeetingTime) return;
    createMeetingMutation.mutate({ title: newMeetingTitle.trim(), scheduledAt: newMeetingTime });
  };
  const removeMeeting = (id: string) => deleteMeetingMutation.mutate(id);

  const connectChannel = (channel: string) => {
    connectIntegrationMutation.mutate(channel);
  };

  const getIndicatorClass = (connected: boolean | undefined) => {
    if (connected === true) return 'online';
    if (connected === false) return 'offline';
    return 'unknown';
  };

  const formatMeeting = (scheduledAt: string | null) => {
    if (!scheduledAt) return { day: '--', month: '', time: 'Unscheduled' };
    const d = new Date(scheduledAt);
    return {
      day: d.getDate().toString().padStart(2, '0'),
      month: d.toLocaleString('en-US', { month: 'short' }),
      time: d.toLocaleString('en-US', { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' }),
    };
  };

  const filteredUsers = dashboardUsers.filter(u =>
    userSearch === '' || `${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(userSearch.toLowerCase())
  );

  const tabLabel = NAV_GROUPS.flatMap(g => g.items).find(i => i.id === activeTab)?.label || 'Dashboard';

  // ─── Render Helpers ───────────────────────────────────────────────────────

  const renderStatCard = (
    label: string,
    value: string | number,
    icon: React.ReactNode,
    iconBg: string,
    iconColor: string,
    sub?: string,
    trend?: 'up' | 'down' | 'neutral',
    pulse?: boolean
  ) => (
    <div className="enterprise-stat-card">
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <div className="stat-card-icon" style={{ background: iconBg, color: iconColor }}>
          {icon}
        </div>
      </div>
      <div className="stat-card-value" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {isLoading ? <span style={{ color: 'var(--text-tertiary)' }}>—</span> : value}
        {pulse && <span className="pulse-dot" style={{ backgroundColor: 'var(--success)', transform: 'scale(0.7)' }}></span>}
      </div>
      {sub && (
        <div className={`stat-card-change ${trend ?? 'neutral'}`}>
          {trend === 'up' ? <TrendingUp size={10} /> : trend === 'down' ? <TrendingDown size={10} /> : null}
          {sub}
        </div>
      )}
    </div>
  );

  // ─── Tab: Dashboard ───────────────────────────────────────────────────────
  const renderDashboard = () => (
    <>
      {/* Enterprise Summary Cards — all backed by /dashboard/overview (real Postgres aggregates) */}
      <div className="enterprise-stats-grid">
        {renderStatCard('Total Organizations', metrics?.total_organizations ?? overview?.organizations ?? 0, <Building2 size={16} />, 'rgba(59,130,246,0.12)', '#60a5fa', 'Registered tenants', 'neutral')}
        {renderStatCard('Total Users', metrics?.total_users ?? overview?.users ?? 0, <Users size={16} />, 'rgba(168,85,247,0.12)', '#c084fc', 'All org members', 'neutral')}
        {renderStatCard('Online Users', metrics?.online_users ?? overview?.onlineUsers ?? 0, <Wifi size={16} />, 'rgba(16,185,129,0.12)', '#34d399', 'Active accounts', 'up', true)}
        {renderStatCard("Today's Leads", overview?.todayLeads ?? 0, <Target size={16} />, 'rgba(59,130,246,0.12)', 'var(--brand)', 'All channels', 'neutral')}
        {renderStatCard('Qualified Leads', overview?.qualifiedLeads ?? 0, <Check size={16} />, 'rgba(16,185,129,0.12)', '#34d399', overview?.todayLeads ? `${Math.round((overview.qualifiedLeads / overview.todayLeads) * 100)}% conversion` : 'No leads yet', 'neutral')}
        {renderStatCard('Spam Leads', overview?.spamLeads ?? 0, <AlertTriangle size={16} />, 'rgba(239,68,68,0.12)', '#f87171', 'Flagged & filtered', 'neutral')}
        {renderStatCard("Today's Calls", overview?.todayCalls ?? 0, <Phone size={16} />, 'rgba(99,102,241,0.12)', '#818cf8', 'Inbound + outbound', 'neutral')}
        {renderStatCard("Today's Meetings", overview?.todayMeetings ?? 0, <Calendar size={16} />, 'rgba(168,85,247,0.12)', '#c084fc', 'Scheduled sessions', 'neutral')}
        {renderStatCard("Today's Tasks", overview?.todayTasks ?? 0, <CheckSquare size={16} />, 'rgba(245,158,11,0.12)', '#fbbf24', 'Open checklist', 'neutral')}
        {renderStatCard('Open Deals', overview?.openDeals ?? 0, <DollarSign size={16} />, 'rgba(59,130,246,0.12)', '#60a5fa', 'In pipeline', 'neutral')}
        {renderStatCard('Won Deals', overview?.wonDeals ?? 0, <Award size={16} />, 'rgba(16,185,129,0.12)', '#34d399', 'All time', 'neutral')}
        {renderStatCard('Revenue', `$${(overview?.revenue ?? 0).toLocaleString()}`, <TrendingUp size={16} />, 'rgba(16,185,129,0.12)', '#34d399', 'From won deals', 'neutral')}
        {renderStatCard('Campaigns Running', overview?.campaignsRunning ?? 0, <Megaphone size={16} />, 'rgba(249,115,22,0.12)', '#fb923c', 'Across all channels', 'neutral')}
        {renderStatCard('Facebook Leads', overview?.facebookLeads ?? 0, <Facebook size={16} />, 'rgba(24,119,242,0.12)', '#1877F2', 'Today via FB', 'neutral')}
        {renderStatCard('Instagram Leads', overview?.instagramLeads ?? 0, <Instagram size={16} />, 'rgba(225,48,108,0.12)', '#E1306C', 'Today via IG', 'neutral')}
        {renderStatCard('WhatsApp Leads', overview?.whatsappLeads ?? 0, <MessageSquare size={16} />, 'rgba(37,211,102,0.12)', '#25D366', 'Today via WA', 'neutral')}
        {renderStatCard('Email Queue', overview?.emailQueue ?? 0, <Mail size={16} />, 'rgba(99,102,241,0.12)', '#818cf8', 'Pending dispatch', 'neutral')}
        {renderStatCard('Server Health', (status?.backend === 'online' ? 'Healthy' : 'Offline'), <Server size={16} />,
          status?.backend === 'online' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
          status?.backend === 'online' ? '#34d399' : '#f87171', status?.environment?.toUpperCase() || 'N/A')}
        {renderStatCard('API Requests', metrics?.api_requests_today ?? overview?.apiRequests ?? 0, <Activity size={16} />, 'rgba(59,130,246,0.12)', '#60a5fa', 'Today', 'neutral')}
        {renderStatCard('Avg Response Time', `${Math.round(metrics?.avg_response_time_ms ?? overview?.responseTime ?? 0)} ms`, <Zap size={16} />, 'rgba(245,158,11,0.12)', '#fbbf24', 'Backend latency', 'neutral')}
        {renderStatCard('AI Token Usage', (overview?.tokenUsage ?? 0).toLocaleString(), <Sparkles size={16} />, 'rgba(168,85,247,0.12)', '#c084fc', `In: ${(overview?.tokenUsageInput ?? 0).toLocaleString()}`, 'neutral')}
      </div>

      {/* Social Channels + CRM Pipeline */}
      <div className="dashboard-row-grid">
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Inbound Social Lead Channels</h3>
          <div className="social-channels-grid">
            <div className="social-card facebook">
              <div className="social-card-header"><span className="social-card-name">Facebook</span><Facebook size={16} style={{ color: '#1877F2' }} /></div>
              <div className="social-card-value">{overview?.facebookLeads ?? 0}</div>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>FB Lead Capture</span>
            </div>
            <div className="social-card instagram">
              <div className="social-card-header"><span className="social-card-name">Instagram</span><Instagram size={16} style={{ color: '#E1306C' }} /></div>
              <div className="social-card-value">{overview?.instagramLeads ?? 0}</div>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>DM Capture</span>
            </div>
            <div className="social-card whatsapp">
              <div className="social-card-header"><span className="social-card-name">WhatsApp</span><MessageSquare size={16} style={{ color: '#25D366' }} /></div>
              <div className="social-card-value">{overview?.whatsappLeads ?? 0}</div>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>WA Gateway</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>CRM Sales Pipeline</h3>
          <div className="crm-pipeline-container">
            <div className="crm-stages-row">
              {[
                { label: 'Captured', value: overview?.todayLeads ?? 0 },
                { label: 'Qualified', value: overview?.qualifiedLeads ?? 0 },
                { label: 'Open Deals', value: overview?.openDeals ?? 0 },
                { label: 'Closed-Won', value: overview?.wonDeals ?? 0 },
              ].map((stage, i) => (
                <div key={i} className={`crm-stage-node ${i === 0 ? 'active' : ''}`}>
                  <div className="crm-stage-title">{stage.label}</div>
                  <div className="crm-stage-value">{stage.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tasks + Meetings */}
      <div className="dashboard-row-grid">
        <div className="card">
          <div className="tasks-widget-container">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Check size={18} style={{ color: 'var(--brand)' }} />Productivity Tasks</h3>
            <form onSubmit={addTask} style={{ display: 'flex', gap: 8 }}>
              <input type="text" placeholder="Add new task..." className="task-input-field" value={newTaskText} onChange={e => setNewTaskText(e.target.value)} />
              <button type="submit" className="task-add-btn">Add</button>
            </form>
            <div className="task-list">
              {tasks.map(task => (
                <div key={task.id} className="task-item">
                  <label className="task-item-label">
                    <input type="checkbox" checked={task.completed} onChange={() => toggleTask(task.id)} className="task-checkbox" />
                    <span className={`task-item-text ${task.completed ? 'completed' : ''}`}>{task.text}</span>
                  </label>
                  <button onClick={() => deleteTask(task.id)} className="task-delete-btn"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-4)' }}><Calendar size={18} style={{ color: 'var(--brand)' }} />Upcoming Meetings</h3>
          <div className="meetings-list">
            {meetings.length === 0 && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>No meetings scheduled</div>}
            {meetings.map(m => {
              const fm = formatMeeting(m.scheduled_at);
              return (
                <div key={m.id} className="meeting-item">
                  <div className="meeting-date-badge">
                    <span className="meeting-day">{fm.day}</span>
                    <span className="meeting-month">{fm.month}</span>
                  </div>
                  <div className="meeting-details">
                    <div className="meeting-title">{m.title}</div>
                    <div className="meeting-time">{fm.time}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* System Telemetry + Campaigns */}
      <div className="dashboard-row-grid">
        <div className="card">
          <h3>Backend Telemetry</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', margin: '8px 0 16px' }}>Real request latency and database connectivity, measured live.</p>
          <div className="ai-usage-grid">
            <div className="ai-usage-metric">
              <svg width="60" height="60" className="ai-gauge-svg">
                <circle cx="30" cy="30" r="26" strokeWidth="4" className="ai-gauge-bg"></circle>
                <circle cx="30" cy="30" r="26" strokeWidth="4" className="ai-gauge-fill" strokeDasharray="163" strokeDashoffset={163 - (163 * Math.min(metrics?.avg_response_time_ms ?? overview?.responseTime ?? 0, 600)) / 600}></circle>
                <defs><linearGradient id="brandGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="var(--brand)"></stop><stop offset="100%" stopColor="var(--info)"></stop></linearGradient></defs>
              </svg>
              <div className="ai-usage-label">API Latency</div>
              <div className="ai-usage-value">{Math.round(metrics?.avg_response_time_ms ?? overview?.responseTime ?? 0)} ms</div>
            </div>
            <div className="ai-usage-metric">
              <svg width="60" height="60" className="ai-gauge-svg">
                <circle cx="30" cy="30" r="26" strokeWidth="4" className="ai-gauge-bg"></circle>
                <circle cx="30" cy="30" r="26" strokeWidth="4" className="ai-gauge-fill" strokeDasharray="163" strokeDashoffset={dbStatus?.qdrant?.connected ? '6' : '163'}></circle>
              </svg>
              <div className="ai-usage-label">Qdrant Vector DB</div>
              <div className="ai-usage-value">{dbStatus?.qdrant?.connected ? 'Connected' : 'Offline'}</div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3>Active Outreach Campaigns</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', margin: '8px 0 16px' }}>Real campaigns stored in Postgres — toggle to start/pause.</p>
          <div className="campaigns-list">
            {campaigns.length === 0 && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>No campaigns yet</div>}
            {campaigns.map(c => (
              <div key={c.id} className="campaign-item">
                <div className="campaign-info">
                  <span className="campaign-name">{c.name}</span>
                  <span className={`campaign-badge ${c.status}`} onClick={() => toggleCampaign(c.id)} style={{ cursor: 'pointer' }}>{c.status}</span>
                </div>
                <div className="campaign-progress-container">
                  <div className="campaign-progress-bar-bg"><div className="campaign-progress-bar-fill" style={{ width: `${c.progress}%` }}></div></div>
                  <span className="campaign-percent">{c.progress}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Notifications Hub */}
      <div className="card">
        <div className="notifications-widget">
          <div className="notifications-header">
            <h3>Real-Time Event Stream</h3>
            <button onClick={markAllRead} style={{ background: 'none', border: 'none', color: 'var(--brand)', cursor: 'pointer', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)' }}>Mark all read</button>
          </div>
          <div className="notifications-list">
            {notifications.map(n => (
              <div key={n.id} className={`notification-item ${n.unread ? 'unread' : ''}`}>
                <div className="notification-icon-wrapper"><Bell size={16} /></div>
                <div className="notification-content">
                  <div className="notification-text">{n.text}</div>
                  <div className="notification-time">{n.time}</div>
                </div>
                {n.unread && <div className="notification-dot"></div>}
                <button onClick={() => dismissNotif(n.id)} className="notification-dismiss">Dismiss</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="card">
        <h3 style={{ marginBottom: 8 }}>Server & Database Connections</h3>
        {isLoading ? (
          <div className="skeleton-grid"><div className="skeleton-item"></div><div className="skeleton-item"></div><div className="skeleton-item"></div><div className="skeleton-item"></div></div>
        ) : (
          <div className="health-grid">
            {[
              { name: 'PostgreSQL', connected: dbStatus?.postgres?.connected },
              { name: 'MongoDB', connected: dbStatus?.mongodb?.connected },
              { name: 'Redis Cache', connected: dbStatus?.redis?.connected },
              { name: 'Qdrant Vector DB', connected: dbStatus?.qdrant?.connected },
            ].map(db => (
              <div key={db.name} className="health-item">
                <span className="health-item-name">{db.name}</span>
                <span className={`health-indicator ${getIndicatorClass(db.connected)}`}></span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Orchestration Blueprint */}
      <div className="card">
        <h3 style={{ marginBottom: 'var(--space-4)' }}>Orchestration Pipeline Blueprint</h3>
        <div className="agent-flow-container">
          <div className="agent-nodes-wrapper">
            {[
              { label: 'API Gateway', sub: status?.fastapi === 'running' ? 'FastAPI Active' : 'Offline', active: status?.fastapi === 'running' },
              { label: 'Supervisor Node', sub: agents?.supervisor_agent || 'Not Installed', active: agents?.supervisor_agent === 'Running' },
              { label: 'Executor Agents', sub: agents?.executor_agent || 'Not Installed', active: agents?.executor_agent === 'Running' },
              { label: 'Vector Memory', sub: dbStatus?.qdrant?.connected ? 'Qdrant Active' : 'Offline', active: dbStatus?.qdrant?.connected },
            ].map((node, i, arr) => (
              <Fragment key={node.label}>
                <div className={`agent-node ${node.active ? 'active' : ''}`}>
                  <div className="agent-node-title">{node.label}</div>
                  <div className="agent-node-status">{node.sub}</div>
                </div>
                {i < arr.length - 1 && <div className={`connector-line ${node.active ? 'active' : ''}`}></div>}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </>
  );

  // ─── Tab: Leads ───────────────────────────────────────────────────────────
  const renderLeads = () => {
    const filteredLeads = leadsFilter === 'all' ? leads : leads.filter(l => l.status === leadsFilter);
    const countBy = (s: string) => leads.filter(l => l.status === s).length;

    return (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Leads Management</h2><span>Capture, qualify and route inbound leads across all channels</span></div>
        <div className="module-actions">
          <button className="btn-secondary" onClick={() => leadsQuery.refetch()}><RefreshCw size={14} /> Refresh</button>
          <button className="btn-primary" onClick={() => setShowAddLead(p => !p)}><Plus size={14} /> Add Lead</button>
        </div>
      </div>

      {showAddLead && (
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <form onSubmit={addLead} style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr) auto', gap: 8, alignItems: 'center' }}>
            <input required placeholder="Name" className="task-input-field" value={newLead.name} onChange={e => setNewLead({ ...newLead, name: e.target.value })} />
            <input placeholder="Company" className="task-input-field" value={newLead.company} onChange={e => setNewLead({ ...newLead, company: e.target.value })} />
            <input placeholder="Phone" className="task-input-field" value={newLead.phone} onChange={e => setNewLead({ ...newLead, phone: e.target.value })} />
            <select className="task-input-field" value={newLead.source} onChange={e => setNewLead({ ...newLead, source: e.target.value })}>
              {['manual', 'website', 'facebook', 'instagram', 'whatsapp', 'ai_voice'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <input placeholder="Value ($)" type="number" className="task-input-field" value={newLead.value} onChange={e => setNewLead({ ...newLead, value: e.target.value })} />
            <button type="submit" className="btn-primary" disabled={createLeadMutation.isPending}>Save</button>
          </form>
          {createLeadMutation.isError && <p style={{ color: 'var(--danger)', fontSize: 'var(--font-xs)', marginTop: 8 }}>{(createLeadMutation.error as Error).message}</p>}
        </div>
      )}

      <div className="module-stats-row">
        {[
          { label: "Total Leads", num: leads.length, sub: 'All channels', color: 'var(--brand)' },
          { label: 'Qualified', num: countBy('qualified'), sub: leads.length ? `${Math.round(countBy('qualified') / leads.length * 100)}% rate` : '—', color: 'var(--success)' },
          { label: 'Spam / Junk', num: countBy('spam'), sub: 'Filtered', color: 'var(--danger)' },
          { label: 'New', num: countBy('new'), sub: 'Awaiting action', color: 'var(--warning)' },
          { label: 'Facebook', num: leads.filter(l => l.source === 'facebook').length, sub: 'Total', color: '#1877F2' },
          { label: 'Instagram', num: leads.filter(l => l.source === 'instagram').length, sub: 'Total', color: '#E1306C' },
          { label: 'WhatsApp', num: leads.filter(l => l.source === 'whatsapp').length, sub: 'Total', color: '#25D366' },
          { label: 'AI Voice', num: leads.filter(l => l.source === 'ai_voice').length, sub: 'Captured via call', color: 'var(--info)' },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num" style={{ color: s.color }}>{s.num}</span>
            <span className="stat-sub">{s.sub}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)', flexWrap: 'wrap', gap: 12 }}>
          <div className="filter-tabs" style={{ marginBottom: 0 }}>
            {[
              { id: 'all', label: 'All Leads', count: leads.length },
              { id: 'new', label: 'New', count: countBy('new') },
              { id: 'qualified', label: 'Qualified', count: countBy('qualified') },
              { id: 'pending', label: 'Pending', count: countBy('pending') },
              { id: 'spam', label: 'Spam', count: countBy('spam') },
            ].map(tab => (
              <button key={tab.id} className={`filter-tab-btn ${leadsFilter === tab.id ? 'active' : ''}`} onClick={() => setLeadsFilter(tab.id)}>
                {tab.label}<span className="filter-tab-badge">{tab.count}</span>
              </button>
            ))}
          </div>
          <div className="search-input-wrapper">
            <Search size={14} className="search-input-icon" />
            <input className="search-input" placeholder="Search leads..." value={leadsSearch} onChange={e => setLeadsSearch(e.target.value)} style={{ width: 200 }} />
          </div>
        </div>

        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr><th>Lead ID</th><th>Name</th><th>Company</th><th>Source</th><th>Status</th><th>Est. Value</th><th>Date</th><th>Action</th></tr>
            </thead>
            <tbody>
              {filteredLeads.length === 0 && (
                <tr><td colSpan={8}><div className="empty-state"><Target size={32} className="empty-state-icon" /><p className="empty-state-title">No leads yet</p><p className="empty-state-desc">Add a lead manually, or connect Facebook/Instagram/WhatsApp to capture them automatically.</p></div></td></tr>
              )}
              {filteredLeads.map(lead => (
                <Fragment key={lead.id}>
                  <tr>
                    <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{lead.id.slice(0, 8)}</span></td>
                    <td><strong>{lead.name}</strong></td>
                    <td>{lead.company || '—'}</td>
                    <td><span style={{ display: 'flex', alignItems: 'center', gap: 6, textTransform: 'capitalize' }}>
                      {lead.source === 'facebook' && <Facebook size={12} style={{ color: '#1877F2' }} />}
                      {lead.source === 'instagram' && <Instagram size={12} style={{ color: '#E1306C' }} />}
                      {lead.source === 'whatsapp' && <MessageSquare size={12} style={{ color: '#25D366' }} />}
                      {lead.source === 'ai_voice' && <PhoneCall size={12} style={{ color: 'var(--brand)' }} />}
                      {lead.source}
                    </span></td>
                    <td><span className="status-badge" style={getLeadStatusStyle(lead.status)}>{lead.status}</span></td>
                    <td><strong style={{ color: 'var(--success)' }}>${lead.value.toLocaleString()}</strong></td>
                    <td style={{ color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>{new Date(lead.created_at).toLocaleDateString()}</td>
                    <td><div style={{ display: 'flex', gap: 8 }}>
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} title="View timeline" onClick={() => toggleLeadExpand(lead.id)}><ChevronRight size={14} style={{ transform: expandedLeadId === lead.id ? 'rotate(90deg)' : 'none' }} /></button>
                      <button className="task-delete-btn" title="Qualify" onClick={() => qualifyLead(lead.id)}><Check size={14} /></button>
                      <button className="task-delete-btn" style={{ color: 'var(--warning)' }} title="Mark spam" onClick={() => markLeadSpam(lead.id)}><AlertTriangle size={14} /></button>
                      <button className="task-delete-btn" style={{ color: 'var(--danger)' }} title="Delete" onClick={() => removeLead(lead.id)}><Trash2 size={14} /></button>
                    </div></td>
                  </tr>
                  {expandedLeadId === lead.id && (
                    <tr>
                      <td colSpan={8} style={{ background: 'var(--bg-tertiary)' }}>
                        <div style={{ padding: 'var(--space-3)' }}>
                          <strong style={{ fontSize: 'var(--font-xs)' }}>Activity Timeline (MongoDB)</strong>
                          {(leadEvents[lead.id] || []).length === 0 && <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Loading…</p>}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
                            {(leadEvents[lead.id] || []).map(ev => (
                              <div key={ev.id} style={{ fontSize: 'var(--font-xs)', display: 'flex', gap: 8 }}>
                                <span className="perm-chip">{ev.type}</span>
                                <span>{ev.note}</span>
                                <span style={{ color: 'var(--text-tertiary)', marginLeft: 'auto' }}>{ev.created_at ? new Date(ev.created_at).toLocaleString() : ''}</span>
                              </div>
                            ))}
                          </div>
                          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                            <input
                              placeholder="Type a note..."
                              className="task-input-field"
                              style={{ flexGrow: 1 }}
                              value={newNoteText[lead.id] || ''}
                              onChange={e => setNewNoteText(prev => ({ ...prev, [lead.id]: e.target.value }))}
                            />
                            <button
                              className="btn-primary"
                              style={{ padding: '6px 12px', fontSize: 'var(--font-xs)' }}
                              onClick={() => handleAddNote(lead.id)}
                            >
                              Add Note
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        {leadsTotal > LEADS_PAGE_SIZE && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-4)' }}>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
              Showing {leadsPage * LEADS_PAGE_SIZE + 1}–{Math.min((leadsPage + 1) * LEADS_PAGE_SIZE, leadsTotal)} of {leadsTotal}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary" disabled={leadsPage === 0} onClick={() => setLeadsPage(p => Math.max(0, p - 1))}>Previous</button>
              <button className="btn-secondary" disabled={(leadsPage + 1) * LEADS_PAGE_SIZE >= leadsTotal} onClick={() => setLeadsPage(p => p + 1)}>Next</button>
            </div>
          </div>
        )}
      </div>
    </>
    );
  };

  // ─── Tab: Pipeline ────────────────────────────────────────────────────────
  const renderPipeline = () => {
    const openDealsCount = deals.filter(d => d.stage !== 'won' && d.stage !== 'lost').length;
    const wonDealsCount = deals.filter(d => d.stage === 'won').length;
    const pipelineValue = deals.reduce((sum, d) => sum + d.value, 0);
    const avgDealSize = deals.length ? Math.round(pipelineValue / deals.length) : 0;
    const nextStage = (stage: string) => {
      const ids = PIPELINE_STAGE_CONFIG.map(s => s.id);
      const i = ids.indexOf(stage);
      return i >= 0 && i < ids.length - 1 ? ids[i + 1] : null;
    };

    return (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Sales Pipeline</h2><span>Visual CRM — Lead → Qualified → Meeting → Proposal → Negotiation → Won / Lost</span></div>
        <button className="btn-primary" onClick={() => setShowAddDeal(p => !p)}><Plus size={14} /> New Deal</button>
      </div>

      {showAddDeal && (
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <form onSubmit={addDeal} style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 1fr auto', gap: 8 }}>
            <input required placeholder="Deal name" className="task-input-field" value={newDeal.name} onChange={e => setNewDeal({ ...newDeal, name: e.target.value })} />
            <input placeholder="Company" className="task-input-field" value={newDeal.company} onChange={e => setNewDeal({ ...newDeal, company: e.target.value })} />
            <input placeholder="Value ($)" type="number" className="task-input-field" value={newDeal.value} onChange={e => setNewDeal({ ...newDeal, value: e.target.value })} />
            <button type="submit" className="btn-primary" disabled={createDealMutation.isPending}>Save</button>
          </form>
        </div>
      )}

      <div className="module-stats-row" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        {[
          { label: 'Open Deals', num: openDealsCount, color: 'var(--brand)' },
          { label: 'Won', num: wonDealsCount, color: 'var(--success)' },
          { label: 'Pipeline Value', num: `$${pipelineValue.toLocaleString()}`, color: 'var(--text-primary)' },
          { label: 'Avg Deal Size', num: `$${avgDealSize.toLocaleString()}`, color: 'var(--info)' },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num" style={{ color: s.color }}>{s.num}</span>
          </div>
        ))}
      </div>

      {dealsQuery.isLoading && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>Loading pipeline…</div>
      )}
      {dealsQuery.isError && (
        <div className="card" style={{ textAlign: 'center', color: 'var(--danger)', fontSize: 'var(--font-xs)' }}>Failed to load pipeline.</div>
      )}
      <div className="card" style={{ overflowX: 'auto' }}>
        <div className="kanban-board">
          {PIPELINE_STAGE_CONFIG.map(stage => {
            const stageDeals = deals.filter(d => d.stage === stage.id);
            return (
              <div
                key={stage.id}
                className="kanban-column"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => handleDrop(e, stage.id)}
              >
                <div className="kanban-col-header">
                  <span className="kanban-col-title" style={{ color: stage.color }}>{stage.label}</span>
                  <span className="kanban-col-count">{stageDeals.length}</span>
                </div>
                {stageDeals.map(deal => {
                  const next = nextStage(deal.stage);
                  return (
                    <div
                      key={deal.id}
                      className="kanban-deal-card"
                      draggable={true}
                      onDragStart={(e) => handleDragStart(e, deal.id)}
                    >
                      <div className="kanban-deal-name">{deal.name}</div>
                      <div className="kanban-deal-company">{deal.company}</div>
                      <div className="kanban-deal-value">${deal.value.toLocaleString()}</div>
                      {next && (
                        <button className="btn-secondary" style={{ fontSize: 10, padding: '3px 8px', marginTop: 6 }} onClick={() => moveDealStage(deal.id, next)}>
                          Move to {PIPELINE_STAGE_CONFIG.find(s => s.id === next)?.label} →
                        </button>
                      )}
                    </div>
                  );
                })}
                {stageDeals.length === 0 && (
                  <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)', border: '1px dashed var(--border-color)', borderRadius: 'var(--radius-sm)' }}>
                    No deals
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </>
    );
  };

  // ─── Tab: Tasks ───────────────────────────────────────────────────────────
  const renderTasks = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Task Management</h2><span>Track team and AI tasks across all workflows</span></div>
        <div className="module-actions">
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{tasks.filter(t => t.completed).length}/{tasks.length} completed</span>
        </div>
      </div>
      <div className="card">
        <form onSubmit={addTask} style={{ display: 'flex', gap: 8, marginBottom: 'var(--space-4)' }}>
          <input type="text" placeholder="Add a new task..." className="task-input-field" style={{ flexGrow: 1 }} value={newTaskText} onChange={e => setNewTaskText(e.target.value)} />
          <button type="submit" className="btn-primary"><Plus size={14} /> Add Task</button>
        </form>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {tasksQuery.isLoading && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>Loading tasks…</div>}
          {tasksQuery.isError && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--danger)', fontSize: 'var(--font-xs)' }}>Failed to load tasks.</div>}
          {tasks.map(task => (
            <div key={task.id} className="task-item">
              <label className="task-item-label">
                <input type="checkbox" checked={task.completed} onChange={() => toggleTask(task.id)} className="task-checkbox" />
                <span className={`task-item-text ${task.completed ? 'completed' : ''}`}>{task.text}</span>
              </label>
              <button onClick={() => deleteTask(task.id)} className="task-delete-btn"><Trash2 size={14} /></button>
            </div>
          ))}
          {!tasksQuery.isLoading && !tasksQuery.isError && tasks.length === 0 && <div className="empty-state"><CheckSquare size={32} className="empty-state-icon" /><p className="empty-state-title">No tasks</p><p className="empty-state-desc">Add a task above to get started.</p></div>}
        </div>
      </div>
    </>
  );

  // ─── Tab: Meetings ────────────────────────────────────────────────────────
  const renderMeetings = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Meetings & Calendar</h2><span>Scheduled syncs, demos, and enterprise calls</span></div>
      </div>
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <form onSubmit={addMeeting} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: 8 }}>
          <input required placeholder="Meeting title" className="task-input-field" value={newMeetingTitle} onChange={e => setNewMeetingTitle(e.target.value)} />
          <input required type="datetime-local" className="task-input-field" value={newMeetingTime} onChange={e => setNewMeetingTime(e.target.value)} />
          <button type="submit" className="btn-primary" disabled={createMeetingMutation.isPending}><Plus size={14} /> Schedule</button>
        </form>
      </div>
      <div className="card">
        <div className="meetings-list" style={{ maxHeight: 'none' }}>
          {meetingsQuery.isLoading && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>Loading meetings…</div>}
          {meetingsQuery.isError && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--danger)', fontSize: 'var(--font-xs)' }}>Failed to load meetings.</div>}
          {!meetingsQuery.isLoading && !meetingsQuery.isError && meetings.length === 0 && <div className="empty-state"><Calendar size={32} className="empty-state-icon" /><p className="empty-state-title">No meetings scheduled</p></div>}
          {meetings.map(m => {
            const fm = formatMeeting(m.scheduled_at);
            return (
              <div key={m.id} className="meeting-item" style={{ padding: 'var(--space-4)' }}>
                <div className="meeting-date-badge" style={{ width: 56, height: 56 }}>
                  <span className="meeting-day" style={{ fontSize: 'var(--font-xl)' }}>{fm.day}</span>
                  <span className="meeting-month">{fm.month}</span>
                </div>
                <div className="meeting-details" style={{ flexGrow: 1 }}>
                  <div className="meeting-title" style={{ fontSize: 'var(--font-base)' }}>{m.title}</div>
                  <div className="meeting-time">{fm.time}</div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="task-delete-btn" style={{ color: 'var(--danger)' }} onClick={() => removeMeeting(m.id)}><Trash2 size={14} /></button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );

  // ─── Tab: Campaigns ───────────────────────────────────────────────────────
  const renderCampaigns = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Campaign Management</h2><span>Outbound AI-driven campaigns across voice, WhatsApp, email and ads</span></div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <form onSubmit={addCampaign} style={{ display: 'flex', gap: 8 }}>
          <input placeholder="New campaign name" className="task-input-field" style={{ flexGrow: 1 }} value={newCampaignName} onChange={e => setNewCampaignName(e.target.value)} />
          <button type="submit" className="btn-primary" disabled={createCampaignMutation.isPending}><Plus size={14} /> New Campaign</button>
        </form>
      </div>

      <div className="module-stats-row" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
        {[
          { label: 'Total Campaigns', num: campaigns.length },
          { label: 'Running', num: campaigns.filter(c => c.status === 'running').length },
          { label: 'Paused', num: campaigns.filter(c => c.status === 'paused').length },
          { label: 'Avg Progress', num: campaigns.length ? `${Math.round(campaigns.reduce((s, c) => s + c.progress, 0) / campaigns.length)}%` : '0%' },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num">{s.num}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="campaigns-list">
          {campaignsQuery.isLoading && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>Loading campaigns…</div>}
          {campaignsQuery.isError && <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--danger)', fontSize: 'var(--font-xs)' }}>Failed to load campaigns.</div>}
          {!campaignsQuery.isLoading && !campaignsQuery.isError && campaigns.length === 0 && <div className="empty-state"><Megaphone size={32} className="empty-state-icon" /><p className="empty-state-title">No campaigns yet</p></div>}
          {campaigns.map(c => (
            <div key={c.id} className="campaign-item" style={{ padding: 'var(--space-4)' }}>
              <div className="campaign-info">
                <span className="campaign-name" style={{ fontSize: 'var(--font-base)' }}>{c.name}</span>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className={`campaign-badge ${c.status}`}>{c.status}</span>
                  <button className="task-delete-btn" onClick={() => toggleCampaign(c.id)} title="Toggle">
                    {c.status === 'running' ? <Pause size={14} /> : <Play size={14} />}
                  </button>
                  <button className="task-delete-btn" style={{ color: 'var(--danger)' }} onClick={() => removeCampaign(c.id)}><Trash2 size={14} /></button>
                </div>
              </div>
              <div className="campaign-progress-container" style={{ marginTop: 8 }}>
                <div className="campaign-progress-bar-bg"><div className="campaign-progress-bar-fill" style={{ width: `${c.progress}%` }}></div></div>
                <span className="campaign-percent">{c.progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );

  // ─── Tab: Facebook / Instagram / WhatsApp ─────────────────────────────────
  const renderChannel = (channelName: string, channelKey: string, channelIcon: React.ReactNode, color: string) => {
    const channelLeads = leads.filter(l => l.source === channelKey);
    const integration = integrations.find(i => i.channel === channelKey);
    const qualified = channelLeads.filter(l => l.status === 'qualified').length;

    return (
    <>
      <div className="module-header">
        <div className="module-title" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ color }}>{channelIcon}</div>
          <div><h2>{channelName} Leads</h2><span>Captured leads from {channelName} integrations</span></div>
        </div>
        <button className="btn-primary" onClick={() => connectChannel(channelKey)} disabled={connectIntegrationMutation.isPending}>
          <RefreshCw size={14} /> {integration?.status === 'connected' ? 'Reconnect' : 'Connect Account'}
        </button>
      </div>

      {integration && integration.status !== 'connected' && (
        <div className="card" style={{ marginBottom: 'var(--space-4)', borderColor: 'var(--warning)' }}>
          <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
            <strong style={{ color: 'var(--warning)' }}>{integration.status === 'not_configured' ? 'Not configured on this server.' : 'Not connected.'}</strong>{' '}
            {integration.status === 'not_configured' && `Missing: ${integration.missing_configuration.join(', ')}.`}
          </p>
        </div>
      )}

      <div className="module-stats-row" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
        {[
          { label: 'Total Leads', num: channelLeads.length },
          { label: 'Qualified', num: qualified },
          { label: 'Conversion', num: channelLeads.length ? `${Math.round((qualified / channelLeads.length) * 100)}%` : '0%' },
          { label: 'Status', num: integration?.status.replace('_', ' ') ?? 'unknown' },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num" style={{ color, textTransform: 'capitalize' }}>{s.num}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead><tr><th>ID</th><th>Name</th><th>Contact</th><th>Status</th><th>Captured At</th></tr></thead>
            <tbody>
              {channelLeads.map(l => (
                <tr key={l.id}>
                  <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)' }}>{l.id.slice(0, 8)}</span></td>
                  <td><strong>{l.name}</strong><div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{l.company}</div></td>
                  <td style={{ color: 'var(--text-tertiary)' }}>{l.phone || l.email || '—'}</td>
                  <td><span className="status-badge" style={getLeadStatusStyle(l.status)}>{l.status}</span></td>
                  <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{new Date(l.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {channelLeads.length === 0 && (
                <tr><td colSpan={5}><div className="empty-state" style={{ padding: 'var(--space-8)' }}>
                  <div className="empty-state-icon" style={{ color }}>{channelIcon}</div>
                  <p className="empty-state-title">No leads from {channelName} yet</p>
                  <p className="empty-state-desc">Connect your {channelName} account to start capturing leads automatically.</p>
                </div></td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
    );
  };

  // ─── Tab: AI Voice ────────────────────────────────────────────────────────
  const renderAiVoice = () => {
    const voiceIntegration = integrations.find(i => i.channel === 'ai_voice');
    const isConnected = voiceIntegration?.status === 'connected';

    return (
    <>
      <div className="module-header">
        <div className="module-title"><h2>AI Voice Calls</h2><span>Outbound and inbound AI voice agents (OpenAI Realtime / Twilio / ElevenLabs)</span></div>
        {!isConnected && (
          <button className="btn-primary" onClick={() => connectChannel('ai_voice')} disabled={connectIntegrationMutation.isPending}>
            <PhoneCall size={14} /> Connect Voice Provider
          </button>
        )}
      </div>

      <div className="module-stats-row" style={{ gridTemplateColumns: 'repeat(2,1fr)' }}>
        {[
          { label: "Today's Calls", num: voiceCalls.length, color: 'var(--brand)' },
          { label: 'Provider Status', num: voiceIntegration?.status.replace('_', ' ') ?? 'unknown', color: 'var(--warning)' },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num" style={{ color: s.color, textTransform: 'capitalize' }}>{s.num}</span>
          </div>
        ))}
      </div>

      {isConnected ? (
        <div className="card">
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Lead Name</th>
                  <th>Direction</th>
                  <th>Duration</th>
                  <th>Transcript Preview</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {voiceCalls.map(call => (
                  <Fragment key={call.id}>
                    <tr>
                      <td><strong>{call.lead_name ?? '—'}</strong></td>
                      <td><span className="role-badge" style={{ textTransform: 'capitalize' }}>{call.direction}</span></td>
                      <td>{call.duration_seconds != null ? `${call.duration_seconds}s` : '—'}</td>
                      <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{call.transcript_preview ?? 'Not available'}</td>
                      <td>
                        <button className="btn-secondary" style={{ fontSize: 11, padding: '4px 8px' }} onClick={() => toggleCallExpand(call.id)}>
                          {expandedCallId === call.id ? 'Hide' : 'Transcript'}
                        </button>
                      </td>
                    </tr>
                    {expandedCallId === call.id && (
                      <tr>
                        <td colSpan={5} style={{ background: 'var(--bg-tertiary)', padding: 'var(--space-4)' }}>
                          <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', color: 'var(--text-primary)' }}>
                            {callTranscript}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                {voiceCalls.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-tertiary)' }}>
                      No calls recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="empty-state">
            <PhoneCall size={40} className="empty-state-icon" />
            <p className="empty-state-title">No AI voice provider connected</p>
            <p className="empty-state-desc">
              {voiceIntegration?.status === 'not_configured'
                ? `Set one provider's credentials on the backend to enable AI calling: ${voiceIntegration.missing_configuration.join('; ')}`
                : 'Configure an AI voice provider to enable automatic outbound qualification calls.'}
            </p>
            <button className="btn-primary" style={{ marginTop: 8 }} onClick={() => connectChannel('ai_voice')} disabled={connectIntegrationMutation.isPending}>
              <PhoneCall size={14} /> Connect Voice Provider
            </button>
          </div>
        </div>
      )}
    </>
    );
  };

  // ─── Tab: AI Agents ───────────────────────────────────────────────────────
  const renderAiAgents = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>AI Agents</h2><span>Specialist AI workers managed by the LangGraph supervisor</span></div>
      </div>

      <div className="agent-status-grid">
        {AI_AGENTS_CONFIG.map(agent => {
          const IconComp = agent.icon;
          const isOnline = agents && (
            (agent.id === 'supervisor' && agents.supervisor_agent === 'Running') ||
            (agent.id === 'developer' && agents.developer_agent === 'Running') ||
            (agent.id !== 'supervisor' && agent.id !== 'developer' && agents.executor_agent === 'Running')
          );
          return (
            <div key={agent.id} className={`agent-status-card ${isOnline ? 'online' : 'offline'}`}>
              <div className="agent-card-header">
                <div className="agent-card-icon"><IconComp size={20} /></div>
                <div>
                  <div className="agent-card-name">{agent.name}</div>
                  <div className="agent-card-type">{agent.type}</div>
                </div>
              </div>
              <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{agent.desc}</p>
              <span className={`status-badge ${isOnline ? 'running' : 'offline'}`}>{isOnline ? 'Running' : 'Not Installed'}</span>
            </div>
          );
        })}
      </div>

      <div className="card" style={{ marginTop: 'var(--space-6)' }}>
        <h3 style={{ marginBottom: 'var(--space-4)' }}>LangGraph Workflow Definition</h3>
        <div style={{ background: 'var(--bg-tertiary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
          <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', overflowX: 'auto', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>{`# AI-BOS Multi-Agent Routing Graph
from langgraph.graph import StateGraph, END
from app.agents.graph.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_agent_node)
workflow.add_node("sales_ai",    sales_agent_node)
workflow.add_node("voice_ai",    voice_agent_node)
workflow.add_node("support_ai",  support_agent_node)
workflow.add_node("crm_agent",   crm_agent_node)
workflow.add_node("knowledge_ai", knowledge_agent_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_by_intent,
    {
        "sales":     "sales_ai",
        "voice":     "voice_ai",
        "support":   "support_ai",
        "crm":       "crm_agent",
        "knowledge": "knowledge_ai",
        "end":        END
    }
)`}</pre>
        </div>
      </div>
    </>
  );

  // ─── Tab: Automation ──────────────────────────────────────────────────────
  const renderAutomation = () => {
    const handleCreateWorkflow = (e: React.FormEvent) => {
      e.preventDefault();
      if (!newWfName.trim()) return;
      createWorkflowMutation.mutate({
        name: newWfName.trim(),
        trigger: newWfTrigger,
        status: 'active',
      });
      setNewWfName('');
      setShowAddWorkflow(false);
    };

    return (
      <>
        <div className="module-header">
          <div className="module-title"><h2>Automation Workflows</h2><span>Event-driven pipelines executed by AI agents</span></div>
          <button className="btn-primary" onClick={() => setShowAddWorkflow(p => !p)}>
            <Plus size={14} /> {showAddWorkflow ? 'Cancel' : 'New Workflow'}
          </button>
        </div>

        {showAddWorkflow && (
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <form onSubmit={handleCreateWorkflow} style={{ display: 'flex', gap: 8 }}>
              <input
                required
                placeholder="Workflow name (e.g. New Lead -> Welcome SMS)"
                className="task-input-field"
                style={{ flexGrow: 2 }}
                value={newWfName}
                onChange={e => setNewWfName(e.target.value)}
              />
              <select
                className="task-input-field"
                style={{ flexGrow: 1 }}
                value={newWfTrigger}
                onChange={e => setNewWfTrigger(e.target.value)}
              >
                <option value="Lead Created">Lead Created</option>
                <option value="FB Webhook">FB Webhook</option>
                <option value="Calendar Event">Calendar Event</option>
                <option value="Pipeline Stage">Pipeline Stage</option>
                <option value="Scheduler (daily)">Scheduler (daily)</option>
              </select>
              <button type="submit" className="btn-primary">Create</button>
            </form>
          </div>
        )}

        <div className="data-table-wrapper">
          <table className="data-table">
            <thead><tr><th>Workflow</th><th>Trigger</th><th>Status</th><th>Total Runs</th><th>Actions</th></tr></thead>
            <tbody>
              {workflows.map(wf => (
                <tr key={wf.id}>
                  <td><strong>{wf.name}</strong></td>
                  <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{wf.trigger}</span></td>
                  <td>
                    <span
                      onClick={() => toggleWorkflow(wf.id, wf.status)}
                      className={`status-badge ${wf.status}`}
                      style={{ cursor: 'pointer' }}
                      title="Click to toggle status"
                    >
                      {wf.status}
                    </span>
                  </td>
                  <td>{wf.runs.toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        className="btn-primary"
                        style={{ fontSize: 10, padding: '3px 8px' }}
                        onClick={() => runWorkflowMutation.mutate(wf.id)}
                        disabled={runWorkflowMutation.isPending}
                      >
                        Run
                      </button>
                      <button
                        className="task-delete-btn"
                        style={{ color: 'var(--danger)' }}
                        onClick={() => deleteWorkflowMutation.mutate(wf.id)}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {workflows.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-tertiary)' }}>
                    No workflows created yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </>
    );
  };

  // ─── Tab: Knowledge Base ──────────────────────────────────────────────────
  const renderKnowledgeBase = () => {
    const handleCreateArticle = (e: React.FormEvent) => {
      e.preventDefault();
      if (!newKbTitle.trim()) return;
      createKbMutation.mutate({
        title: newKbTitle.trim(),
        category: newKbCategory,
      });
      setNewKbTitle('');
      setShowAddKb(false);
    };

    return (
      <>
        <div className="module-header">
          <div className="module-title"><h2>Knowledge Base</h2><span>Semantic search-indexed documentation and articles</span></div>
          <button className="btn-primary" onClick={() => setShowAddKb(p => !p)}>
            <Plus size={14} /> {showAddKb ? 'Cancel' : 'New Article'}
          </button>
        </div>

        <div className="card" style={{ marginBottom: 'var(--space-4)', padding: 'var(--space-4)' }}>
          <div className="search-input-wrapper" style={{ width: '100%' }}>
            <Search size={14} className="search-input-icon" />
            <input
              className="search-input"
              placeholder="Search knowledge base semantically (Qdrant indexed)..."
              value={kbSearchText}
              onChange={e => setKbSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {showAddKb && (
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <form onSubmit={handleCreateArticle} style={{ display: 'flex', gap: 8 }}>
              <input
                required
                placeholder="Article title"
                className="task-input-field"
                style={{ flexGrow: 2 }}
                value={newKbTitle}
                onChange={e => setNewKbTitle(e.target.value)}
              />
              <select
                className="task-input-field"
                style={{ flexGrow: 1 }}
                value={newKbCategory}
                onChange={e => setNewKbCategory(e.target.value)}
              >
                <option value="Onboarding">Onboarding</option>
                <option value="Integrations">Integrations</option>
                <option value="Security">Security</option>
                <option value="AI Platform">AI Platform</option>
                <option value="Channels">Channels</option>
                <option value="General">General</option>
              </select>
              <button type="submit" className="btn-primary">Create</button>
            </form>
          </div>
        )}

        <div className="data-table-wrapper">
          <table className="data-table">
            <thead><tr><th>Title</th><th>Category</th><th>Views</th><th>Actions</th></tr></thead>
            <tbody>
              {kbArticles.map(a => (
                <tr key={a.id}>
                  <td><strong>{a.title}</strong></td>
                  <td><span className="perm-chip">{a.category}</span></td>
                  <td>{a.views.toLocaleString()}</td>
                  <td>
                    <button
                      className="task-delete-btn"
                      style={{ color: 'var(--danger)' }}
                      onClick={() => deleteKbMutation.mutate(a.id)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
              {kbArticles.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: 24, color: 'var(--text-tertiary)' }}>
                    No matching articles found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </>
    );
  };

  // ─── Tab: Organizations ───────────────────────────────────────────────────
  const renderOrganizations = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Organization</h2><span>Tenant configuration, subscription, and branding</span></div>
        <button className="btn-secondary" onClick={() => window.location.href = '/profile'}><Settings size={14} /> Open Settings</button>
      </div>

      <div className="dashboard-row-grid">
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Organization Profile</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {orgDetails ? [
              { label: 'Name', value: orgDetails.name },
              { label: 'Slug', value: `/${orgDetails.slug}` },
              { label: 'Status', value: <span className={`status-badge ${orgDetails.status}`}>{orgDetails.status}</span> },
              { label: 'Members', value: orgDetails.user_count },
              { label: 'Created', value: orgDetails.created_at ? new Date(orgDetails.created_at).toLocaleDateString() : 'N/A' },
            ].map(row => (
              <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{row.label}</span>
                <span style={{ fontSize: 'var(--font-sm)', fontWeight: 'var(--weight-semibold)' }}>{row.value}</span>
              </div>
            )) : (
              <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>
                Loading organization details…
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Subscription Plan</h3>
          <div className="billing-plans-grid" style={{ gridTemplateColumns: '1fr' }}>
            {BILLING_PLANS.map(plan => {
              const isCurrent = orgDetails?.subscription_plan === plan.id;
              return (
              <div key={plan.id} className={`billing-plan-card ${isCurrent ? 'current' : ''}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div className="billing-plan-name">{plan.name}</div>
                    <div className="billing-plan-price">{plan.price}<span>{plan.period}</span></div>
                  </div>
                  {isCurrent && <span className="plan-card-badge">Current</span>}
                </div>
                <div className="billing-plan-features">
                  {plan.features.map(f => (
                    <div key={f} className="billing-plan-feature"><Check size={14} style={{ color: 'var(--success)' }} />{f}</div>
                  ))}
                </div>
              </div>
              );
            })}
          </div>
          {!orgDetails?.subscription_plan && (
            <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', marginTop: 8 }}>
              No subscription plan set for this organization yet.
            </p>
          )}
        </div>
      </div>
    </>
  );

  // ─── Tab: Users ───────────────────────────────────────────────────────────
  const renderUsers = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>User Management</h2><span>Invite, edit, suspend and manage organization members</span></div>
        <div className="module-actions">
          <div className="search-input-wrapper">
            <Search size={14} className="search-input-icon" />
            <input className="search-input" placeholder="Search users..." value={userSearch} onChange={e => setUserSearch(e.target.value)} style={{ width: 200 }} />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
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
          </div>
        </div>
      </div>


      <div className="module-stats-row" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 'var(--space-4)' }}>
        {[
          { label: 'Total Users', num: metrics?.total_users ?? dashboardUsers.length },
          { label: 'Active', num: metrics?.online_users ?? dashboardUsers.filter(u => u.status === 'active').length },
          { label: 'Suspended', num: metrics?.suspended_users ?? dashboardUsers.filter(u => u.status === 'suspended').length },
          { label: 'Roles Configured', num: metrics?.total_roles ?? dashboardRoles.length },
        ].map(s => (
          <div key={s.label} className="module-stat-item">
            <span className="stat-label">{s.label}</span>
            <span className="stat-num">{s.num}</span>
          </div>
        ))}
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead><tr><th>User</th><th>Status</th><th>Role</th><th>Last Login</th><th>Joined</th><th>Actions</th></tr></thead>
          <tbody>
            {filteredUsers.length > 0 ? filteredUsers.map(u => (
              <tr key={u.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--brand-light)', color: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: 'var(--font-xs)' }}>
                      {(u.first_name?.[0] ?? '?')}{(u.last_name?.[0] ?? '')}
                    </div>
                    <div>
                      <div style={{ fontWeight: 'var(--weight-semibold)' }}>{u.first_name} {u.last_name}</div>
                      <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{u.email}</div>
                    </div>
                  </div>
                </td>
                <td><span className={`status-badge ${u.status}`}>{u.status}</span></td>
                <td><span className="role-badge" style={getRoleBadgeStyle(u.role_id)}>{getRoleDisplayName(u.role_id)}</span></td>
                <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}</td>
                <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <RequirePermission permission="users.write">
                      <button className="task-delete-btn" style={{ color: 'var(--brand)' }} onClick={() => {
                        setEditUserModal(u);
                        setEditUserFirstName(u.first_name);
                        setEditUserLastName(u.last_name);
                        setEditUserEmail(u.email);
                        setEditUserPhone(u.phone || '');
                      }} title="Edit User"><Edit3 size={14} /></button>
                    </RequirePermission>
                    <RequirePermission permission="users.reset_password">
                      <button
                        className="task-delete-btn"
                        style={{ color: 'var(--warning)' }}
                        title="Reset Password"
                        disabled={resetPasswordMutation.isPending}
                        onClick={() => resetPasswordMutation.mutate(u.id)}
                      ><KeyRound size={14} /></button>
                    </RequirePermission>
                    <RequirePermission permission="users.suspend">
                      <button
                        className="task-delete-btn"
                        style={{ color: 'var(--danger)' }}
                        title={u.status === 'suspended' ? 'Reactivate' : 'Suspend'}
                        disabled={updateUserStatusMutation.isPending}
                        onClick={() => toggleUserSuspend(u)}
                      ><ShieldAlert size={14} /></button>
                    </RequirePermission>
                    <RequirePermission permission="users.delete">
                      <button
                        className="task-delete-btn"
                        style={{ color: 'var(--danger)' }}
                        title="Delete User"
                        disabled={deleteUserMutation.isPending}
                        onClick={() => setDeleteConfirmInfo({ type: 'user', id: u.id, name: u.first_name })}
                      ><Trash2 size={14} /></button>
                    </RequirePermission>
                  </div>
                </td>
              </tr>
            )) : (
              <tr><td colSpan={6}>
                <div className="empty-state">
                  <Users size={32} className="empty-state-icon" />
                  <p className="empty-state-title">No users found</p>
                  <p className="empty-state-desc">{userSearch ? 'Try a different search term.' : 'Invite team members to get started.'}</p>
                </div>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );

  // ─── Tab: Roles ───────────────────────────────────────────────────────────
  const renderRoles = () => {
    const displayRoles = dashboardRoles;

    return (
      <>
        <div className="module-header">
          <div className="module-title"><h2>Roles & Permissions</h2><span>RBAC configuration — {displayRoles.length} roles defined</span></div>
          <RequirePermission permission="roles.write">
            <button className="btn-primary" onClick={() => setShowAddRole(true)}>
              <Plus size={14} /> Create Role
            </button>
          </RequirePermission>
        </div>
        


        {displayRoles.length === 0 && (
          <div className="card">
            <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>
              Loading roles…
            </div>
          </div>
        )}

        <div className="role-cards-grid">
          {displayRoles.map(role => (
            <div key={role.id} className="role-card">
              <div className="role-card-header">
                <span className="role-card-name" style={getRoleBadgeStyle(role.id)}>{role.name}</span>
                <span className="role-card-count">{role.permissions_count} permissions</span>
              </div>
              <p className="role-card-desc">{role.description}</p>
              <div className="role-card-perms">
                {role.permissions.slice(0, 4).map(p => <span key={p.id} className="perm-chip">{p.id}</span>)}
                {role.permissions.length > 4 && <span className="perm-chip">+{role.permissions.length - 4} more</span>}
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
                <RequirePermission permission="roles.assign_permission">
                  <button className="task-delete-btn" style={{ color: 'var(--brand)' }} title="Assign Permission" onClick={() => {
                    setAssignPermissionRole(role);
                    setAssignPermissionInput('');
                  }}><Edit2 size={14} /></button>
                </RequirePermission>
                <RequirePermission permission="roles.delete">
                  <button className="task-delete-btn" style={{ color: 'var(--danger)' }} title="Delete Role" onClick={() => setDeleteConfirmInfo({ type: 'role', id: role.id, name: role.name })}><Trash2 size={14} /></button>
                </RequirePermission>
              </div>
            </div>
          ))}
        </div>
      </>
    );
  };

  // ─── Tab: Billing ─────────────────────────────────────────────────────────
  const renderBilling = () => {
    const currentPlan = BILLING_PLANS.find(p => p.id === orgDetails?.subscription_plan);
    return (
      <>
      <div className="module-header">
        <div className="module-title"><h2>Billing & Subscription</h2><span>Manage plan, invoices and payment methods</span></div>
      </div>

      <div className="dashboard-row-grid">
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Current Plan</h3>
          {currentPlan ? (
            <div className="billing-plan-card current">
              <div className="billing-plan-name">{currentPlan.name} Plan</div>
              <div className="billing-plan-price">{currentPlan.price}<span>{currentPlan.period}</span></div>
              <div className="billing-plan-features">
                {currentPlan.features.map(f => (
                  <div key={f} className="billing-plan-feature"><Check size={14} style={{ color: 'var(--success)' }} />{f}</div>
                ))}
              </div>
              <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 12 }}>
                <button
                  className="btn-primary"
                  onClick={() => checkoutMutation.mutate({ planId: currentPlan.id, gateway: 'stripe' })}
                  disabled={checkoutMutation.isPending}
                >
                  Pay via Stripe
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => checkoutMutation.mutate({ planId: currentPlan.id, gateway: 'razorpay' })}
                  disabled={checkoutMutation.isPending}
                >
                  Pay via Razorpay
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 'var(--font-xs)' }}>
              No subscription plan set for this organization yet.
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Usage This Month</h3>
          {[
            { label: 'AI Tokens Used', used: overview?.tokenUsage ?? 0, total: null, unit: 'tokens' },
            { label: 'API Calls', used: metrics?.api_requests_today ?? 0, total: null, unit: 'calls' },
            { label: 'Active Users', used: metrics?.online_users ?? 0, total: null, unit: 'seats' },
          ].map(u => (
            <div key={u.label} style={{ marginBottom: 'var(--space-4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>{u.label}</span>
                <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{u.used.toLocaleString()} {u.unit}</span>
              </div>
            </div>
          ))}
          <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
            Storage usage is not tracked yet.
          </p>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--space-6)' }}>
        <h3 style={{ marginBottom: 'var(--space-4)' }}>Billing & Invoice History</h3>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice ID</th>
                <th>Amount</th>
                <th>Plan</th>
                <th>Gateway</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id}>
                  <td><strong>{inv.id}</strong></td>
                  <td>${inv.amount.toFixed(2)}</td>
                  <td>{inv.plan}</td>
                  <td style={{ textTransform: 'capitalize' }}>{inv.payment_gateway}</td>
                  <td><span className="status-badge active">{inv.status}</span></td>
                  <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
                    {new Date(inv.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {invoices.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--text-tertiary)' }}>
                    No invoice history available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      </>
    );
  };

  // ─── Tab: System Health ───────────────────────────────────────────────────
  const renderSystemHealth = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>System Health</h2><span>Backend, databases, CPU, memory and network status</span></div>
        <button className="btn-secondary" onClick={loadSystemData}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="system-health-grid">
        <div className="health-stat-card">
          <div className="health-stat-title">Backend Engine</div>
          <div className="health-stat-value" style={{ color: status?.backend === 'online' ? 'var(--success)' : 'var(--danger)' }}>
            {(status?.backend ?? 'OFFLINE').toUpperCase()}
          </div>
          <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>FastAPI {status?.version} · Python {status?.python_version}</div>
          <div className="health-stat-bar-bg"><div className="health-stat-bar-fill good" style={{ width: status?.backend === 'online' ? '100%' : '0%' }}></div></div>
        </div>

        <div className="health-stat-card">
          <div className="health-stat-title">Environment</div>
          <div className="health-stat-value">{(status?.environment ?? 'N/A').toUpperCase()}</div>
          <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>Uptime: {status?.uptime ?? 'N/A'}</div>
        </div>

        <div className="health-stat-card">
          <div className="health-stat-title">CPU</div>
          <div className="health-stat-value">{healthData?.cpu?.percent ?? 0}%</div>
          <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{info?.cpu_count ?? metrics?.cpu_count ?? 0} Cores · {info?.platform ?? metrics?.platform ?? 'N/A'}</div>
          <div className="health-stat-bar-bg"><div className="health-stat-bar-fill good" style={{ width: `${healthData?.cpu?.percent ?? 0}%` }}></div></div>
        </div>

        <div className="health-stat-card">
          <div className="health-stat-title">Memory</div>
          {/* info?.memory */}
          <div className="health-stat-value">{healthData?.memory?.percent ?? 0}%</div>
          <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{healthData?.memory?.used_gb ?? 0} GB / {healthData?.memory?.total_gb ?? 0} GB used</div>
          <div className="health-stat-bar-bg"><div className={`health-stat-bar-fill ${(healthData?.memory?.percent ?? 0) < 70 ? 'good' : (healthData?.memory?.percent ?? 0) < 90 ? 'warn' : 'bad'}`} style={{ width: `${healthData?.memory?.percent ?? 0}%` }}></div></div>
        </div>

        <div className="health-stat-card">
          <div className="health-stat-title">Disk Storage</div>
          <div className="health-stat-value">{healthData?.disk?.percent ?? 0}%</div>
          <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{healthData?.disk?.used_gb ?? 0} GB / {healthData?.disk?.total_gb ?? 0} GB used</div>
          <div className="health-stat-bar-bg"><div className={`health-stat-bar-fill ${(healthData?.disk?.percent ?? 0) < 70 ? 'good' : (healthData?.disk?.percent ?? 0) < 90 ? 'warn' : 'bad'}`} style={{ width: `${healthData?.disk?.percent ?? 0}%` }}></div></div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--space-6)' }}>
        <h3 style={{ marginBottom: 'var(--space-4)' }}>Database Connectivity</h3>
        <div className="health-grid">
          {[
            { name: 'PostgreSQL (Relational)', connected: dbStatus?.postgres?.connected, desc: 'Primary ACID store' },
            { name: 'MongoDB (Document)', connected: dbStatus?.mongodb?.connected, desc: 'Agent telemetry logs' },
            { name: 'Redis (Cache/Broker)', connected: dbStatus?.redis?.connected, desc: 'Session tokens & pub/sub' },
            { name: 'Qdrant (Vector DB)', connected: dbStatus?.qdrant?.connected, desc: 'Semantic search indexes' },
          ].map(db => (
            <div key={db.name} className="health-item" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                <span className="health-item-name" style={{ fontSize: 'var(--font-xs)' }}>{db.name}</span>
                <span className={`health-indicator ${getIndicatorClass(db.connected)}`}></span>
              </div>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{db.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );

  // ─── Tab: Audit Logs ──────────────────────────────────────────────────────
  const renderAuditLogs = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Audit Logs</h2><span>Security and activity trail for your organization</span></div>
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead><tr><th>Action</th><th>Description</th><th>Resource</th><th>Timestamp</th></tr></thead>
          <tbody>
            {auditLogs.length > 0 ? auditLogs.map(log => (
              <tr key={log.id}>
                <td><span className="audit-action-badge">{log.action}</span></td>
                <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>{log.description}</td>
                <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{log.resource}</span></td>
                <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</td>
              </tr>
            )) : (
              <tr><td colSpan={4}>
                <div className="empty-state">
                  <ScrollText size={32} className="empty-state-icon" />
                  <p className="empty-state-title">No audit logs yet</p>
                  <p className="empty-state-desc">Security events (logins, changes, resets) appear here as they occur.</p>
                </div>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );

  // ─── Tab: Analytics ───────────────────────────────────────────────────────
  const renderAnalytics = () => {
    const dealsByStage = PIPELINE_STAGE_CONFIG.map(s => ({ ...s, count: deals.filter(d => d.stage === s.id).length }));
    const maxStageCount = Math.max(1, ...dealsByStage.map(s => s.count));
    const sourceCounts = ['facebook', 'instagram', 'whatsapp', 'ai_voice', 'website', 'manual'].map(src => ({
      name: src, count: leads.filter(l => l.source === src).length,
    })).filter(s => s.count > 0);
    const totalLeadsForBreakdown = sourceCounts.reduce((s, c) => s + c.count, 0) || 1;
    const qualifiedCount = leads.filter(l => l.status === 'qualified').length;
    const proposalCount = deals.filter(d => d.stage === 'proposal').length;
    const wonCount = deals.filter(d => d.stage === 'won').length;

    return (
      <>
        <div className="module-header">
          <div className="module-title"><h2>Analytics</h2><span>Real lead, pipeline and revenue analytics computed from your data</span></div>
        </div>

        <div className="dashboard-row-grid">
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-2)' }}>Deals by Stage</h3>
            <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)', marginBottom: 'var(--space-6)' }}>Current pipeline distribution</p>
            <div style={{ paddingBottom: 30, position: 'relative' }}>
              <div className="bar-chart-wrapper">
                {dealsByStage.map(d => (
                  <div key={d.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <span className="bar-chart-bar-value">{d.count}</span>
                    <div className="bar-chart-bar" style={{ height: `${Math.round((d.count / maxStageCount) * 140)}px`, background: d.color }}></div>
                    <span className="bar-chart-bar-label">{d.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Lead Source Breakdown</h3>
            {sourceCounts.length === 0 && <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>No leads yet.</p>}
            {sourceCounts.map(s => {
              const pct = Math.round((s.count / totalLeadsForBreakdown) * 100);
              return (
                <div key={s.name} style={{ marginBottom: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{s.name}</span>
                    <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'bold' }}>{s.count} ({pct}%)</span>
                  </div>
                  <div className="health-stat-bar-bg"><div className="health-stat-bar-fill" style={{ width: `${pct}%` }}></div></div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="dashboard-row-grid">
          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>Conversion Funnel</h3>
            {[
              { label: 'Leads Captured', val: leads.length, color: 'var(--brand)' },
              { label: 'Qualified', val: qualifiedCount, color: '#8b5cf6' },
              { label: 'Proposal Sent', val: proposalCount, color: 'var(--warning)' },
              { label: 'Won', val: wonCount, color: 'var(--success)' },
            ].map(f => {
              const pct = leads.length ? Math.round((f.val / leads.length) * 100) : 0;
              return (
                <div key={f.label} style={{ marginBottom: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>{f.label}</span>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{f.val} ({pct}%)</span>
                  </div>
                  <div className="health-stat-bar-bg"><div className="health-stat-bar-fill" style={{ width: `${pct}%`, background: f.color }}></div></div>
                </div>
              );
            })}
          </div>

          <div className="card">
            <h3 style={{ marginBottom: 'var(--space-4)' }}>AI / Backend Usage Summary</h3>
            {[
              { label: 'Input Tokens', val: (overview?.tokenUsageInput ?? 0).toLocaleString(), icon: <Sparkles size={14} /> },
              { label: 'Output Tokens', val: (overview?.tokenUsageOutput ?? 0).toLocaleString(), icon: <Sparkles size={14} /> },
              { label: 'Total Tokens', val: (overview?.tokenUsage ?? 0).toLocaleString(), icon: <Sparkles size={14} /> },
              { label: 'Avg API Latency', val: `${Math.round(metrics?.avg_response_time_ms ?? overview?.responseTime ?? 0)} ms`, icon: <Zap size={14} /> },
              { label: 'Qdrant Vector DB', val: dbStatus?.qdrant?.connected ? 'Connected' : 'Offline', icon: <Database size={14} /> },
            ].map(s => (
              <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--brand)' }}>{s.icon}<span style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>{s.label}</span></div>
                <strong style={{ fontSize: 'var(--font-sm)' }}>{s.val}</strong>
              </div>
            ))}
          </div>
        </div>
      </>
    );
  };

  // ─── Tab: Developer ───────────────────────────────────────────────────────
  const renderDeveloper = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Developer Tools</h2><span>API reference, webhooks, agent SDK and integration guides</span></div>
      </div>

      <div className="dashboard-row-grid">
        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>API Endpoints</h3>
          {[
            { method: 'POST', path: '/api/v1/auth/login', desc: 'Authenticate and get JWT token' },
            { method: 'GET', path: '/api/v1/auth/me', desc: 'Get current user profile' },
            { method: 'GET', path: '/api/v1/dashboard/metrics', desc: 'Enterprise dashboard metrics' },
            { method: 'GET', path: '/api/v1/dashboard/users', desc: 'List organization users' },
            { method: 'GET', path: '/api/v1/dashboard/roles', desc: 'RBAC roles with permissions' },
            { method: 'GET', path: '/api/v1/system/status', desc: 'Backend system status' },
            { method: 'GET', path: '/api/v1/health', desc: 'Database health check' },
          ].map(ep => (
            <div key={ep.path} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 'var(--space-3)', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', marginBottom: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 'bold', fontFamily: 'var(--font-mono)', padding: '2px 6px', borderRadius: 'var(--radius-xs)', background: ep.method === 'GET' ? 'rgba(16,185,129,0.12)' : 'rgba(59,130,246,0.12)', color: ep.method === 'GET' ? 'var(--success)' : 'var(--brand)', minWidth: 40, textAlign: 'center' }}>{ep.method}</span>
              <code style={{ fontSize: 'var(--font-xs)', color: 'var(--text-primary)', flexGrow: 1 }}>{ep.path}</code>
              <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>{ep.desc}</span>
            </div>
          ))}
          <a href="/docs" target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--brand)', fontSize: 'var(--font-sm)', marginTop: 'var(--space-3)' }}>
            <Link size={14} /> Open Swagger UI →
          </a>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Agent SDK Sample</h3>
          <div style={{ background: 'var(--bg-tertiary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
            <pre style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: 'var(--font-xs)', overflowX: 'auto', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>{`from langgraph.graph import StateGraph, END
from app.agents.graph.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("crm_agent",   crm_agent_node)
workflow.add_node("db_agent",    db_agent_node)

workflow.set_entry_point("supervisor")
workflow.add_conditional_edges(
    "supervisor",
    should_continue,
    {
        "crm":  "crm_agent",
        "db":   "db_agent",
        "end":   END
    }
)
graph = workflow.compile()`}</pre>
          </div>
        </div>
      </div>
    </>
  );

  // ─── Tab: Settings ────────────────────────────────────────────────────────
  const renderSettings = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Settings</h2><span>Personal profile, organization branding and preferences</span></div>
      </div>
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 480 }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)' }}>
          Full settings are available in the Settings Console — including organization profile, GST, timezone, brand color, user invitations and subscription management.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <button className="btn-primary" onClick={() => window.location.href = '/profile'}><Settings size={14} /> Open Settings Console</button>
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <button className="btn-secondary" style={{ flexGrow: 1 }} onClick={toggleTheme}>
              {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
              {theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            </button>
          </div>
        </div>
      </div>
    </>
  );

  // ─── Tab: Reports ─────────────────────────────────────────────────────────
  const renderReports = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Reports</h2><span>Download detailed business and performance reports</span></div>
      </div>
      <div className="role-cards-grid">
        {[
          { key: 'leads', name: 'Weekly Lead Report', desc: 'All captured leads with source, status and value breakdown', icon: Target },
          { key: 'revenue', name: 'Revenue Summary', desc: 'Monthly revenue from won deals and billing activity', icon: DollarSign },
          { key: 'campaigns', name: 'Campaign Performance', desc: 'Reach, engagement and conversion stats per campaign', icon: Megaphone },
          { key: 'tokens', name: 'AI Token Usage Report', desc: 'LLM token consumption by agent and time period', icon: Sparkles },
          { key: 'audit', name: 'User Activity Log', desc: 'Login history, actions and session durations per user', icon: Users },
          { key: 'system', name: 'System Health Report', desc: 'Database uptime, API latency and error rates', icon: Activity },
        ].map(r => {
          const IconComp = r.icon;
          return (
            <div key={r.name} className="role-card">
              <div className="role-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{ color: 'var(--brand)' }}><IconComp size={16} /></div>
                  <span className="role-card-name" style={{ marginLeft: 8 }}>{r.name}</span>
                </div>
              </div>
              <p className="role-card-desc">{r.desc}</p>
              <button
                className="btn-secondary"
                style={{ fontSize: 'var(--font-xs)', padding: '6px 12px' }}
                onClick={() => handleDownloadReport(r.key)}
              >
                Download CSV
              </button>
            </div>
          );
        })}
      </div>
    </>
  );

  // ─── Tab: Documents ───────────────────────────────────────────────────────
  const renderDocuments = () => (
    <>
      <div className="module-header">
        <div className="module-title"><h2>Documents</h2><span>Contracts, proposals and shared files</span></div>
        <button className="btn-primary" onClick={() => document.getElementById('doc-upload-file')?.click()}>
          <Plus size={14} /> Upload
        </button>
      </div>

      <input
        type="file"
        id="doc-upload-file"
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files?.[0]) {
            uploadDocMutation.mutate(e.target.files[0]);
          }
        }}
      />

      {documents.length > 0 ? (
        <div className="card">
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map(doc => (
                  <tr key={doc.id}>
                    <td><strong>{doc.name}</strong></td>
                    <td><span className="perm-chip">{doc.file_type}</span></td>
                    <td>{Math.round(doc.size_bytes / 1024)} KB</td>
                    <td style={{ fontSize: 'var(--font-xs)', color: 'var(--text-tertiary)' }}>
                      {new Date(doc.created_at || '').toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button
                          className="btn-secondary"
                          style={{ fontSize: 10, padding: '3px 8px' }}
                          onClick={() => {
                            const token = localStorage.getItem('aibos_access_token');
                            window.open(`${getDocumentDownloadUrl(doc.id)}?token=${token}`, '_blank');
                          }}
                        >
                          Download
                        </button>
                        <button
                          className="task-delete-btn"
                          style={{ color: 'var(--danger)' }}
                          onClick={() => deleteDocMutation.mutate(doc.id)}
                          disabled={deleteDocMutation.isPending}
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
      ) : (
        <div className="card">
          <div className="empty-state">
            <File size={40} className="empty-state-icon" />
            <p className="empty-state-title">No documents yet</p>
            <p className="empty-state-desc">Upload contracts, proposals, and shared files for your organization. Supported: PDF, DOCX, XLSX.</p>
            <button
              className="btn-primary"
              style={{ marginTop: 8 }}
              onClick={() => document.getElementById('doc-upload-file')?.click()}
            >
              <Plus size={14} /> Upload Document
            </button>
          </div>
        </div>
      )}
    </>
  );

  // ─── Main Return ──────────────────────────────────────────────────────────
  return (
    <div className="dashboard-container">
      {/* Enterprise Sidebar */}
      <aside className="sidebar sidebar-enterprise">
        <div className="logo-container">
          <div className="logo-icon">Ω</div>
          <span className="logo-text">AI-BOS</span>
        </div>

        <nav className="enterprise-nav">
          {NAV_GROUPS.map(group => (
            <div key={group.label} className="nav-group">
              <span className="nav-group-label">{group.label}</span>
              <ul className="nav-list">
                {group.items.map(item => {
                  const IconComp = item.icon;
                  return (
                    <li key={item.id}>
                      <button
                        onClick={() => setActiveTab(item.id)}
                        className={`nav-item-enterprise ${activeTab === item.id ? 'active' : ''}`}
                      >
                        <IconComp size={15} />
                        {item.label}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div
              className={status?.backend === 'online' ? 'pulse-dot' : ''}
              style={{ backgroundColor: status?.backend === 'online' ? 'var(--success)' : 'var(--danger)', width: 8, height: 8, borderRadius: '50%', flexShrink: 0 }}
            ></div>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>
              {status?.backend === 'online' ? 'Backend Connected' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <div className="header-title-container">
            <h2>AI-BOS Enterprise</h2>
            <span className="header-subtitle">Phase 3 — {tabLabel}</span>
          </div>

          <div className="header-actions">
            <button onClick={toggleTheme} className="theme-toggle-btn" title="Toggle Theme" aria-label="Toggle Theme">
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <button
                onClick={() => window.location.href = '/profile'}
                title="Account Settings"
                style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--brand-light)', border: '2px solid var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 'var(--font-xs)', fontWeight: 'bold', color: 'var(--brand)', cursor: 'pointer' }}
              >
                {userProfile ? `${userProfile.first_name[0]}${userProfile.last_name[0]}` : 'U'}
              </button>
              <button
                onClick={async () => {
                  const { logout } = await import('../services/authService');
                  await logout();
                  window.location.href = '/auth/login';
                }}
                style={{ fontSize: 'var(--font-xs)', color: 'var(--danger)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'var(--weight-semibold)', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <LogOut size={14} /> Sign Out
              </button>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <div className="page-body animate-fade-in">
          {/* Error / Offline Banner */}
          {isError && (
            <div className="error-container">
              <div className="error-title">Backend Offline</div>
              <div className="error-msg">{errorMessage}</div>
              <button className="retry-btn" onClick={loadSystemData}>Retry Connection</button>
            </div>
          )}

          {activeTab === 'dashboard'      && renderDashboard()}
          {activeTab === 'leads'          && renderLeads()}
          {activeTab === 'pipeline'       && renderPipeline()}
          {activeTab === 'tasks'          && renderTasks()}
          {activeTab === 'meetings'       && renderMeetings()}
          {activeTab === 'campaigns'      && renderCampaigns()}
          {activeTab === 'facebook'       && renderChannel('Facebook', 'facebook', <Facebook size={24} />, '#1877F2')}
          {activeTab === 'instagram'      && renderChannel('Instagram', 'instagram', <Instagram size={24} />, '#E1306C')}
          {activeTab === 'whatsapp'       && renderChannel('WhatsApp', 'whatsapp', <MessageSquare size={24} />, '#25D366')}
          {activeTab === 'ai-voice'       && renderAiVoice()}
          {activeTab === 'ai-agents'      && renderAiAgents()}
          {activeTab === 'automation'     && renderAutomation()}
          {activeTab === 'knowledge-base' && renderKnowledgeBase()}
          {activeTab === 'documents'      && renderDocuments()}
          {activeTab === 'organizations'  && renderOrganizations()}
          {activeTab === 'users'          && renderUsers()}
          {activeTab === 'roles'          && renderRoles()}
          {activeTab === 'billing'        && renderBilling()}
          {activeTab === 'system-health'  && renderSystemHealth()}
          {activeTab === 'audit-logs'     && renderAuditLogs()}
          {activeTab === 'developer'      && renderDeveloper()}
          {activeTab === 'settings'       && renderSettings()}
          {activeTab === 'analytics'      && renderAnalytics()}
          {activeTab === 'reports'        && renderReports()}
          {activeTab === 'calendar'       && renderMeetings()}
        </div>
      </main>

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
          }).catch(err => pushNotification(err.response?.data?.detail || "Error assigning role"));
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
            pushNotification("Password must be at least 8 characters");
            return;
          }
          apiForceUserPassword(forcePasswordUser.id, forcePasswordInput).then(() => {
            pushNotification('Password updated successfully');
            setForcePasswordUser(null);
          }).catch(err => pushNotification(err.response?.data?.detail || "Error updating password"));
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

    </div>
  );
}
