import { getAccessToken } from './authService';

export interface DashboardMetrics {
  total_organizations: number;
  total_users: number;
  online_users: number;
  suspended_users: number;
  total_roles: number;
  server_health: string;
  api_requests_today: number;
  avg_response_time_ms: number;
  platform: string;
  cpu_count: number;
  python_version: string;
  timestamp: string;
}

export interface DashboardUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  status: string;
  role_id: string;
  role_name: string;
  created_at: string | null;
  last_login: string | null;
}

export interface DashboardRole {
  id: string;
  name: string;
  description: string;
  permissions: { id: string; name: string }[];
  permissions_count: number;
}

export interface OrganizationDetails {
  id: string;
  name: string;
  slug: string;
  status: string;
  user_count: number;
  created_at: string | null;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  description: string;
  resource: string;
  resource_id: string;
  created_at: string | null;
}

export interface DashboardOverview {
  backendStatus: string;
  uptime: string;
  organizations: number;
  users: number;
  onlineUsers: number;
  todayLeads: number;
  qualifiedLeads: number;
  spamLeads: number;
  todayCalls: number;
  todayMeetings: number;
  todayTasks: number;
  openDeals: number;
  wonDeals: number;
  revenue: number;
  campaignsRunning: number;
  facebookLeads: number;
  instagramLeads: number;
  whatsappLeads: number;
  emailQueue: number;
  serverHealth: string;
  apiRequests: number;
  responseTime: number;
  tokenUsage: number;
  tokenUsageInput: number;
  tokenUsageOutput: number;
  timestamp: string;
}

export interface DashboardTask {
  id: string;
  text: string;
  completed: boolean;
  created_at: string | null;
}

export interface DashboardCampaign {
  id: string;
  name: string;
  channel: string;
  status: 'running' | 'paused';
  progress: number;
}

export interface DashboardMeeting {
  id: string;
  title: string;
  scheduled_at: string | null;
}

const API_BASE = '/api/v1/dashboard';

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const res = await fetch(`${API_BASE}/metrics`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchDashboardUsers(): Promise<{ users: DashboardUser[]; total: number }> {
  const res = await fetch(`${API_BASE}/users`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function fetchDashboardRoles(): Promise<{ roles: DashboardRole[]; total: number }> {
  const res = await fetch(`${API_BASE}/roles`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch roles');
  return res.json();
}

export async function fetchOrganizationDetails(): Promise<OrganizationDetails> {
  const res = await fetch(`${API_BASE}/organization`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch organization');
  return res.json();
}

export async function fetchAuditLogs(): Promise<{ logs: AuditLogEntry[]; total: number }> {
  const res = await fetch(`${API_BASE}/audit-logs`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const res = await fetch(`${API_BASE}/overview`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch dashboard overview');
  return res.json();
}

export async function fetchTasks(): Promise<{ tasks: DashboardTask[] }> {
  const res = await fetch(`${API_BASE}/tasks`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
}

export async function createTask(text: string): Promise<DashboardTask> {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
}

export async function toggleTask(taskId: string): Promise<{ id: string; completed: boolean }> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, { method: 'PATCH', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to update task');
  return res.json();
}

export async function deleteTask(taskId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete task');
  return res.json();
}

export async function fetchCampaigns(): Promise<{ campaigns: DashboardCampaign[] }> {
  const res = await fetch(`${API_BASE}/campaigns`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch campaigns');
  return res.json();
}

export async function createCampaign(name: string, channel: string = 'general'): Promise<DashboardCampaign> {
  const res = await fetch(`${API_BASE}/campaigns`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, channel }),
  });
  if (!res.ok) throw new Error('Failed to create campaign');
  return res.json();
}

export async function toggleCampaignStatus(campaignId: string): Promise<{ id: string; status: string }> {
  const res = await fetch(`${API_BASE}/campaigns/${campaignId}/toggle`, { method: 'PATCH', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to toggle campaign');
  return res.json();
}

export async function deleteCampaign(campaignId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/campaigns/${campaignId}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete campaign');
  return res.json();
}

export async function fetchMeetings(): Promise<{ meetings: DashboardMeeting[] }> {
  const res = await fetch(`${API_BASE}/meetings`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch meetings');
  return res.json();
}

export async function createMeeting(title: string, scheduledAt: string): Promise<DashboardMeeting> {
  const res = await fetch(`${API_BASE}/meetings`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, scheduled_at: scheduledAt }),
  });
  if (!res.ok) throw new Error('Failed to create meeting');
  return res.json();
}

export async function deleteMeeting(meetingId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/meetings/${meetingId}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete meeting');
  return res.json();
}
