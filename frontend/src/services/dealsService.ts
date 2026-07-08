import axiosInstance from './axiosInstance';

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

export async function fetchDeals(): Promise<{ deals: Deal[] }> {
  const response = await axiosInstance.get('/deals');
  return response.data;
}

export async function createDeal(data: { name: string; company?: string; value?: number; stage?: string; lead_id?: string }): Promise<Deal> {
  const response = await axiosInstance.post('/deals', data);
  return response.data;
}

export async function updateDeal(id: string, data: Partial<Pick<Deal, 'name' | 'company' | 'value' | 'stage' | 'assigned_to'>>): Promise<Deal> {
  const response = await axiosInstance.patch(`/deals/${id}`, data);
  return response.data;
}

export async function deleteDeal(id: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/deals/${id}`);
  return response.data;
}
