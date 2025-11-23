import { useMutation, useQuery } from '@tanstack/react-query';
import { startResearch, getResearchJob } from '@/api/research';
import type { ResearchJob, ResearchStartRequest } from '@/types/api';

export function useStartResearch() {
  return useMutation<ResearchJob, Error, ResearchStartRequest>(startResearch);
}

export function useResearchJob(jobId: number | null) {
  return useQuery<ResearchJob, Error>(['researchJob', jobId], () => getResearchJob(jobId as number), {
    enabled: jobId !== null,
  });
}