import { useQuery, useMutation } from '@tanstack/react-query';
import {
  fetchCompanies,
  fetchCompany,
  compareCompanies,
} from '@/api/companies';
import type {
  CompanySummary,
  CompanyProfile,
  CompareRequest,
  CompareResponse,
} from '@/types/api';
import type { CompanyQuery } from '@/api/companies';

export function useCompanies(params: CompanyQuery) {
  return useQuery<CompanySummary[], Error>(['companies', params], () => fetchCompanies(params));
}

export function useCompany(id: number | null) {
  return useQuery<{ company: CompanyProfile; sources: CompanyProfile['sources'] }, Error>(['company', id], () => fetchCompany(id as number), {
    enabled: !!id,
  });
}

export function useCompare() {
  return useMutation<CompareResponse, Error, CompareRequest>(compareCompanies);
}