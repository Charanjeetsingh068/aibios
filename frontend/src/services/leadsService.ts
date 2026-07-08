import axiosInstance from './axiosInstance';

export interface Lead {
  id: string;
  organization_id: string;
  name: string;
  company?: string | null;
  phone?: string | null;
  email?: string | null;
  source: string;
  status: string;
  value: number;
  campaign_id?: string | null;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadEvent {
  id: string;
  type: string;
  note: string;
  actor_user_id?: string | null;
  created_at: string | null;
}

export async function fetchLeads(params?: { status?: string; source?: string; search?: string; limit?: number; offset?: number }): Promise<{ leads: Lead[]; total: number }> {
  const response = await axiosInstance.get('/leads', { params });
  return response.data;
}

export async function createLead(data: {
  name: string; company?: string; phone?: string; email?: string; source: string; value?: number; campaign_id?: string;
}): Promise<Lead> {
  try {
    const response = await axiosInstance.post('/leads', data);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to create lead');
  }
}

export async function updateLead(id: string, data: Partial<Pick<Lead, 'name' | 'company' | 'phone' | 'email' | 'status' | 'value' | 'campaign_id' | 'assigned_to'>>): Promise<Lead> {
  const response = await axiosInstance.patch(`/leads/${id}`, data);
  return response.data;
}

export async function deleteLead(id: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/leads/${id}`);
  return response.data;
}

export async function fetchLeadEvents(id: string): Promise<{ events: LeadEvent[] }> {
  const response = await axiosInstance.get(`/leads/${id}/events`);
  return response.data;
}

export async function addLeadEvent(id: string, type: string, note: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.post(`/leads/${id}/events`, { type, note });
  return response.data;
}
