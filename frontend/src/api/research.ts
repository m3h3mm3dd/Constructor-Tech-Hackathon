import { apiClient } from './client';
import type { ResearchJob, ResearchStartRequest } from '@/types/api';

/**
 * Start a new research job by specifying a market segment and maximum number
 * of companies to discover.
 */
export async function startResearch(request: ResearchStartRequest): Promise<ResearchJob> {
  const res = await apiClient.post<ResearchJob>('/api/v1/research/start', request);
  return res.data;
}

/**
 * Retrieve the status of an existing research job and its discovered companies.
 */
export async function getResearchJob(jobId: number): Promise<ResearchJob> {
  const res = await apiClient.get<ResearchJob>(`/api/v1/research/${jobId}`);
  return res.data;
}