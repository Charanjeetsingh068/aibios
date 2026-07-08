import axiosInstance from './axiosInstance';

export interface CallLog {
  id: string;
  direction: 'inbound' | 'outbound';
  lead_name: string;
  duration_seconds: number;
  transcript_preview: string;
  created_at: string | null;
}

export async function fetchCallLogs(): Promise<{ calls: CallLog[] }> {
  const response = await axiosInstance.get('/voice/calls');
  return response.data;
}

export async function fetchCallTranscript(id: string): Promise<{ call_id: string; transcript: string }> {
  const response = await axiosInstance.get(`/voice/calls/${id}/transcript`);
  return response.data;
}
