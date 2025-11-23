import { useQuery, useMutation } from '@tanstack/react-query';
import {
  startSession,
  fetchSessions,
  fetchSession,
  fetchSessionLogs,
  refreshSession,
  fetchTrends,
  fetchSessionCompany,
} from '@/api/sessions';
import type { SessionListItem, SessionResponse, SessionLog, TrendResponse, SessionCompanyProfile } from '@/types/api';

export function useRecentSessions(limit = 6) {
  return useQuery<SessionListItem[], Error>(['sessions', limit], () => fetchSessions(limit));
}

export function useSession(sessionId: string) {
  return useQuery<SessionResponse, Error>(['session', sessionId], () => fetchSession(sessionId), {
    enabled: !!sessionId,
    refetchInterval: (data) => (data?.status === 'RUNNING' ? 4000 : false),
  });
}

export function useSessionLogs(sessionId: string, enabled = true) {
  return useQuery<SessionLog[], Error>(
    ['sessionLogs', sessionId],
    () => fetchSessionLogs(sessionId),
    { enabled },
  );
}

export function useStartSession() {
  return useMutation<SessionResponse, Error, { segment: string; max_companies?: number }>((vars) =>
    startSession(vars.segment, vars.max_companies),
  );
}

export function useRefreshSession() {
  return useMutation<SessionResponse, Error, { sessionId: string }>((vars) => refreshSession(vars.sessionId));
}

export function useTrends(sessionId: string, enabled = false) {
  return useQuery<TrendResponse, Error>(['trends', sessionId], () => fetchTrends(sessionId), {
    enabled,
  });
}

export function useSessionCompany(companyId: string) {
  return useQuery<SessionCompanyProfile, Error>(['sessionCompany', companyId], () => fetchSessionCompany(companyId), {
    enabled: !!companyId,
  });
}
