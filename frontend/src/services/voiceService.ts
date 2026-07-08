import axiosInstance from './axiosInstance';

export interface CallLog {
  id: string;
  direction: 'inbound' | 'outbound';
  lead_name: string | null;
  duration_seconds: number | null;
  transcript_preview: string | null;
  created_at: string | null;
}

export async function fetchCallLogs(): Promise<{ calls: CallLog[] }> {
  const response = await axiosInstance.get('/voice/calls');
  return response.data;
}

export async function fetchCallTranscript(id: string): Promise<{ call_id: string; transcript: string | null; detail?: string }> {
  const response = await axiosInstance.get(`/voice/calls/${id}/transcript`);
  return response.data;
}
