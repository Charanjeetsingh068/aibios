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
export async function connectIntegration(channel: string): Promise<IntegrationStatus | void> {
  if (channel === 'facebook' || channel === 'instagram') {
    // For Meta, we need to redirect the user to the OAuth URL
    try {
      const response = await axiosInstance.get('/integrations/meta/oauth/url');
      if (response.data.url) {
        window.location.href = response.data.url;
        return;
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to start Meta OAuth flow');
    }
  }

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

export async function fetchLeadMappings(): Promise<{ mappings: { id: string; form_id: string; meta_field: string; crm_field: string }[] }> {
  const response = await axiosInstance.get('/api/v1/integrations/meta/sync/mappings');
  return response.data;
}

export async function createLeadMapping(data: { form_id: string; meta_field: string; crm_field: string }): Promise<any> {
  const response = await axiosInstance.post('/api/v1/integrations/meta/sync/mappings', data);
  return response.data;
}

export async function deleteLeadMapping(mappingId: string): Promise<any> {
  const response = await axiosInstance.delete(`/api/v1/integrations/meta/sync/mappings/${mappingId}`);
  return response.data;
}
