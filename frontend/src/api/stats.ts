import { apiClient } from './client';
import type { StatsOverview } from '@/types/api';

/**
 * Fetch aggregated statistics used for dashboard charts and counts.
 */
export async function fetchStatsOverview(): Promise<StatsOverview> {
  const res = await apiClient.get<StatsOverview>('/api/v1/research/stats/overview');
  return res.data;
}