import os

file_path = "frontend/src/services/leadsService.ts"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_functions = """

export interface LeadNote {
  id: string;
  lead_id: string;
  author_id?: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export async function bulkUpdateLeads(leadIds: string[], data: { status?: string; assigned_to?: string; campaign_id?: string }): Promise<{ updated: number }> {
  const response = await axiosInstance.post('/leads/bulk/update', { lead_ids: leadIds, ...data });
  return response.data;
}

export async function bulkDeleteLeads(leadIds: string[]): Promise<{ deleted: number }> {
  const response = await axiosInstance.post('/leads/bulk/delete', { lead_ids: leadIds });
  return response.data;
}

export async function mergeLeads(targetLeadId: string, sourceLeadId: string): Promise<Lead> {
  const response = await axiosInstance.post(`/leads/${targetLeadId}/merge`, { source_lead_id: sourceLeadId, target_lead_id: targetLeadId });
  return response.data;
}

export async function fetchLeadNotes(id: string): Promise<LeadNote[]> {
  const response = await axiosInstance.get(`/leads/${id}/notes`);
  return response.data;
}

export async function createLeadNote(id: string, content: string): Promise<LeadNote> {
  const response = await axiosInstance.post(`/leads/${id}/notes`, { content });
  return response.data;
}

export async function fetchLeadTags(id: string): Promise<Tag[]> {
  const response = await axiosInstance.get(`/leads/${id}/tags`);
  return response.data;
}

export async function addLeadTag(id: string, name: string, color: string = '#CCCCCC'): Promise<{ success: boolean; tag: Tag }> {
  const response = await axiosInstance.post(`/leads/${id}/tags`, { name, color });
  return response.data;
}
"""

if "bulkUpdateLeads" not in content:
    content += new_functions

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("leadsService.ts patched")
