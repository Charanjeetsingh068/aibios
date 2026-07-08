import axiosInstance from './axiosInstance';

export interface DocumentFile {
  id: string;
  name: string;
  file_type: string;
  size_bytes: number;
  created_at: string | null;
}

export async function fetchDocuments(): Promise<{ documents: DocumentFile[] }> {
  const response = await axiosInstance.get('/documents');
  return response.data;
}

export async function uploadDocument(file: File): Promise<DocumentFile> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axiosInstance.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function deleteDocument(id: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/documents/${id}`);
  return response.data;
}

export function getDocumentDownloadUrl(id: string): string {
  const baseUrl = axiosInstance.defaults.baseURL || '/api/v1';
  return `${baseUrl}/documents/${id}/download`;
}

export async function previewDocument(id: string): Promise<{ document: DocumentFile; preview_text: string }> {
  const response = await axiosInstance.get(`/documents/${id}/preview`);
  return response.data;
}
