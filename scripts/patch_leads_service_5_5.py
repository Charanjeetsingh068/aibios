import re

service_file = "frontend/src/services/leadsService.ts"

with open(service_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update Lead Interface
lead_interface_new = """export interface Lead {
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
  meta_lead_id?: string | null;
  crm_lead_id?: string | null;
  whatsapp_number?: string | null;
  facebook_page_id?: string | null;
  instagram_account_id?: string | null;
  ad_set?: string | null;
  ad?: string | null;
  lead_form?: string | null;
  country?: string | null;
  state?: string | null;
  city?: string | null;
  address?: string | null;
  priority: string;
  score: number;
  created_at: string;
  updated_at: string;
}"""

content = re.sub(r'export interface Lead \{.*?\n\}', lead_interface_new, content, flags=re.DOTALL, count=1)

# 2. Add export and import endpoints
import_export_endpoints = """
export async function importLeads(file: File): Promise<{ imported: number, errors: string[] }> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axiosInstance.post('/leads/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
}

export async function exportLeads(): Promise<{ leads: Lead[] }> {
  const response = await axiosInstance.get('/leads/export');
  return response.data;
}
"""

if "export async function importLeads" not in content:
    content += "\n" + import_export_endpoints

with open(service_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched leadsService.ts")
