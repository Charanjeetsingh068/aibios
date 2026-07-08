import { getAccessToken } from './authService';

export interface Deal {
  id: string;
  organization_id: string;
  lead_id?: string | null;
  name: string;
  company?: string | null;
  stage: string;
  value: number;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
}

const API_BASE = '/api/v1/deals';

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function fetchDeals(): Promise<{ deals: Deal[] }> {
  const res = await fetch(API_BASE, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch deals');
  return res.json();
}

export async function createDeal(data: { name: string; company?: string; value?: number; stage?: string; lead_id?: string }): Promise<Deal> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create deal');
  return res.json();
}

export async function updateDeal(id: string, data: Partial<Pick<Deal, 'name' | 'company' | 'value' | 'stage' | 'assigned_to'>>): Promise<Deal> {
  const res = await fetch(`${API_BASE}/${id}`, {
    method: 'PATCH',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update deal');
  return res.json();
}

export async function deleteDeal(id: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to delete deal');
  return res.json();
}
