import axiosInstance from './axiosInstance';

export interface IntegrationStatus {
  id: string;
  channel: string;
  status: 'not_configured' | 'not_connected' | 'connected' | 'error';
  external_account_id?: string | null;
  detail?: string | null;
  missing_configuration: string[];
  connected_at: string | null;
}

export async function fetchIntegrations(): Promise<{ integrations: IntegrationStatus[] }> {
  const response = await axiosInstance.get('/integrations');
  return response.data;
}

/** Always hits the real backend. Throws with the server's actual reason when a channel isn't configured. */
export async function connectIntegration(channel: string): Promise<IntegrationStatus> {
  try {
    const response = await axiosInstance.post(`/integrations/${channel}/connect`);
    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to connect integration');
  }
}

export async function disconnectIntegration(channel: string): Promise<IntegrationStatus> {
  const response = await axiosInstance.post(`/integrations/${channel}/disconnect`);
  return response.data;
}
