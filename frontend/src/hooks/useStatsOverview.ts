import { useQuery } from '@tanstack/react-query';
import { fetchStatsOverview } from '@/api/stats';
import type { StatsOverview } from '@/types/api';

export function useStatsOverview() {
  return useQuery<StatsOverview, Error>(['statsOverview'], fetchStatsOverview);
}