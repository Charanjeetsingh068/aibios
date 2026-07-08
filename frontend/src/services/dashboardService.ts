import axiosInstance from './axiosInstance';

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
  logo_char?: string | null;
  gst_number?: string | null;
  address?: string | null;
  timezone?: string | null;
  brand_color?: string | null;
  subscription_plan?: string | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_user?: string | null;
  smtp_pass?: string | null;
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

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  const response = await axiosInstance.get('/dashboard/metrics');
  return response.data;
}

export async function fetchDashboardUsers(): Promise<{ users: DashboardUser[]; total: number }> {
  const response = await axiosInstance.get('/dashboard/users');
  return response.data;
}

export async function fetchDashboardRoles(): Promise<{ roles: DashboardRole[]; total: number }> {
  const response = await axiosInstance.get('/dashboard/roles');
  return response.data;
}

export async function fetchOrganizationDetails(): Promise<OrganizationDetails> {
  const response = await axiosInstance.get('/dashboard/organization');
  return response.data;
}

export async function fetchAuditLogs(): Promise<{ logs: AuditLogEntry[]; total: number }> {
  const response = await axiosInstance.get('/dashboard/audit-logs');
  return response.data;
}

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const response = await axiosInstance.get('/dashboard/overview');
  return response.data;
}

export async function fetchTasks(): Promise<{ tasks: DashboardTask[] }> {
  const response = await axiosInstance.get('/dashboard/tasks');
  return response.data;
}

export async function createTask(text: string): Promise<DashboardTask> {
  const response = await axiosInstance.post('/dashboard/tasks', { text });
  return response.data;
}

export async function toggleTask(taskId: string): Promise<{ id: string; completed: boolean }> {
  const response = await axiosInstance.patch(`/dashboard/tasks/${taskId}`);
  return response.data;
}

export async function deleteTask(taskId: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/dashboard/tasks/${taskId}`);
  return response.data;
}

export async function fetchCampaigns(): Promise<{ campaigns: DashboardCampaign[] }> {
  const response = await axiosInstance.get('/dashboard/campaigns');
  return response.data;
}

export async function createCampaign(name: string, channel: string = 'general'): Promise<DashboardCampaign> {
  const response = await axiosInstance.post('/dashboard/campaigns', { name, channel });
  return response.data;
}

export async function toggleCampaignStatus(campaignId: string): Promise<{ id: string; status: string }> {
  const response = await axiosInstance.patch(`/dashboard/campaigns/${campaignId}/toggle`);
  return response.data;
}

export async function deleteCampaign(campaignId: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/dashboard/campaigns/${campaignId}`);
  return response.data;
}

export async function fetchMeetings(): Promise<{ meetings: DashboardMeeting[] }> {
  const response = await axiosInstance.get('/dashboard/meetings');
  return response.data;
}

export async function createMeeting(title: string, scheduledAt: string): Promise<DashboardMeeting> {
  const response = await axiosInstance.post('/dashboard/meetings', { title, scheduled_at: scheduledAt });
  return response.data;
}

export async function deleteMeeting(meetingId: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/dashboard/meetings/${meetingId}`);
  return response.data;
}

export async function updateOrganizationDetails(data: any): Promise<OrganizationDetails> {
  const response = await axiosInstance.patch('/dashboard/organization', data);
  return response.data;
}

export async function inviteUser(data: { name: string; email: string; role: string; permissions: string[] }): Promise<{ user: DashboardUser; invite_link: string }> {
  const response = await axiosInstance.post('/dashboard/users/invite', data);
  return response.data;
}

export async function updateUser(userId: string, data: { name?: string; email?: string; role?: string; status?: string }): Promise<DashboardUser> {
  const response = await axiosInstance.patch(`/dashboard/users/${userId}`, data);
  return response.data;
}

export async function deleteDashboardUser(userId: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/dashboard/users/${userId}`);
  return response.data;
}

export async function resetUserPassword(userId: string): Promise<{ reset_link: string }> {
  const response = await axiosInstance.post(`/dashboard/users/${userId}/reset-password`);
  return response.data;
}

export async function updateRolePermissions(roleId: string, permissions: string[]): Promise<DashboardRole> {
  const response = await axiosInstance.patch(`/dashboard/roles/${roleId}`, { permissions });
  return response.data;
}
