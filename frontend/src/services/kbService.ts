import axiosInstance from './axiosInstance';

export interface KbArticle {
  id: string;
  title: string;
  category: string;
  views: number;
  created_at: string | null;
  updated_at: string | null;
}

export async function fetchKbArticles(): Promise<{ articles: KbArticle[] }> {
  const response = await axiosInstance.get('/kb');
  return response.data;
}

export async function createKbArticle(data: { title: string; category: string }): Promise<KbArticle> {
  const response = await axiosInstance.post('/kb', data);
  return response.data;
}

export async function deleteKbArticle(id: string): Promise<{ success: boolean }> {
  const response = await axiosInstance.delete(`/kb/${id}`);
  return response.data;
}

export async function searchKbArticles(query: string): Promise<{ results: KbArticle[] }> {
  const response = await axiosInstance.get('/kb/search', { params: { q: query } });
  return response.data;
}
