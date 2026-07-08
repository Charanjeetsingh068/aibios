import axiosInstance from './axiosInstance';

export interface Workflow {
  id: string;
  name: string;
  trigger: string;
  status: 'active' | 'paused';
  runs: number;
  created_at: string | null;
}

export interface WorkflowRunLog {
  id: string;
  status: 'completed' | 'failed';
  execution_time_ms: number;
  timestamp: string;
}

export async function fetchWorkflows(): Promise<{ workflows: Workflow[] }> {
  const response = await axiosInstance.get('/workflows');
  return response.data;
}

export async function createWorkflow(data: { name: string; trigger: string; status?: string }): Promise<Workflow> {
  const response = await axiosInstance.post('/workflows', data);
  return response.data;
}

export async function updateWorkflow(id: string, data: Partial<Pick<Workflow, 'name' | 'trigger' | 'status'>>): Promise<Workflow> {
  const response = await axiosInstance.patch(`/workflows/${id}`, data);
  return response.data;
}

export async function deleteWorkflow(id: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/workflows/${id}`);
  return response.data;
}

export async function runWorkflow(id: string): Promise<{ success: boolean; runs: number }> {
  const response = await axiosInstance.post(`/workflows/${id}/run`);
  return response.data;
}

export async function fetchWorkflowHistory(id: string): Promise<{ history: WorkflowRunLog[] }> {
  const response = await axiosInstance.get(`/workflows/${id}/history`);
  return response.data;
}
