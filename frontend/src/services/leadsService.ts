import { getAccessToken } from './authService';

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

const API_BASE = '/api/v1/leads';

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function fetchLeads(params?: { status?: string; source?: string; search?: string }): Promise<{ leads: Lead[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.source) qs.set('source', params.source);
  if (params?.search) qs.set('search', params.search);
  const suffix = qs.toString() ? `?${qs.toString()}` : '';
  const res = await fetch(`${API_BASE}${suffix}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch leads');
  return res.json();
}

export async function createLead(data: {
  name: string; company?: string; phone?: string; email?: string; source: string; value?: number; campaign_id?: string;
}): Promise<Lead> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail || 'Failed to create lead');
  return res.json();
}

export async function updateLead(id: string, data: Partial<Pick<Lead, 'name' | 'company' | 'phone' | 'email' | 'status' | 'value' | 'campaign_id' | 'assigned_to'>>): Promise<Lead> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'PATCH',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update lead');
  return res.json();
}

export async function deleteLead(id: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete lead');
  return res.json();
}

export async function fetchLeadEvents(id: string): Promise<{ events: LeadEvent[] }> {
  const res = await fetch(`${API_BASE}/${id}/events`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch lead events');
  return res.json();
}

export async function addLeadEvent(id: string, type: string, note: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/${id}/events`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, note }),
  });
  if (!res.ok) throw new Error('Failed to add lead event');
  return res.json();
}
