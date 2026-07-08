import { getAccessToken } from './authService';

export interface IntegrationStatus {
  id: string;
  channel: string;
  status: 'not_configured' | 'not_connected' | 'connected' | 'error';
  external_account_id?: string | null;
  detail?: string | null;
  missing_configuration: string[];
  connected_at: string | null;
}

const API_BASE = '/api/v1/integrations';

function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function fetchIntegrations(): Promise<{ integrations: IntegrationStatus[] }> {
  const res = await fetch(API_BASE, { headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to fetch integrations');
  return res.json();
}

/** Always hits the real backend. Throws with the server's actual reason when a channel isn't configured. */
export async function connectIntegration(channel: string): Promise<IntegrationStatus> {
  const res = await fetch(`${API_BASE}/${channel}/connect`, { method: 'POST', headers: authHeaders() });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.detail || 'Failed to connect integration');
  return body;
}

export async function disconnectIntegration(channel: string): Promise<IntegrationStatus> {
  const res = await fetch(`${API_BASE}/${channel}/disconnect`, { method: 'POST', headers: authHeaders() });
  if (!res.ok) throw new Error('Failed to disconnect integration');
  return res.json();
}
