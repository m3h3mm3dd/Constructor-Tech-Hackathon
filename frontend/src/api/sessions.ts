import { apiClient } from './client';
import type {
  SessionResponse,
  SessionListItem,
  SessionLog,
  TrendResponse,
  SessionCompanyProfile,
} from '@/types/api';

export async function startSession(segment: string, max_companies = 3): Promise<SessionResponse> {
  const res = await apiClient.post<SessionResponse>('/api/v1/research/sessions/start', {
    segment,
    max_companies,
  });
  return res.data;
}

export async function fetchSessions(limit = 6): Promise<SessionListItem[]> {
  const res = await apiClient.get<SessionListItem[]>('/api/v1/research/sessions', { params: { limit } });
  return res.data;
}

export async function fetchSession(sessionId: string): Promise<SessionResponse> {
  const res = await apiClient.get<SessionResponse>(`/api/v1/research/sessions/${sessionId}`);
  return res.data;
}

export async function fetchSessionLogs(sessionId: string, since?: string): Promise<SessionLog[]> {
  const res = await apiClient.get<SessionLog[]>(`/api/v1/research/sessions/${sessionId}/logs`, {
    params: since ? { since } : undefined,
  });
  return res.data;
}

export async function refreshSession(sessionId: string): Promise<SessionResponse> {
  const res = await apiClient.post<SessionResponse>(`/api/v1/research/sessions/${sessionId}/refresh`);
  return res.data;
}

export async function fetchTrends(sessionId: string): Promise<TrendResponse> {
  const res = await apiClient.get<TrendResponse>(`/api/v1/research/sessions/${sessionId}/trends`);
  return res.data;
}

export async function fetchSessionCompany(companyId: string): Promise<SessionCompanyProfile> {
  const res = await apiClient.get<SessionCompanyProfile>(`/api/v1/research/session-companies/${companyId}`);
  return res.data;
}
