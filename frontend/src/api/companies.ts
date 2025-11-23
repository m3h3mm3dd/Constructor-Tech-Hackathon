import { apiClient } from './client';
import type {
  CompanySummary,
  CompanyProfile,
  CompareRequest,
  CompareResponse,
} from '@/types/api';

/**
 * Query parameters for fetching companies. All fields are optional; the
 * backend will filter accordingly. Unknown parameters are ignored.
 */
export interface CompanyQuery {
  segment?: string;
  category?: string;
  region?: string;
  has_ai_features?: boolean;
  search?: string;
}

/**
 * Retrieve a list of companies. Supports optional filters for segment,
 * category, region, AI features and a search string. See the backend
 * documentation for details.
 */
export async function fetchCompanies(
  params: CompanyQuery = {},
): Promise<CompanySummary[]> {
  const res = await apiClient.get<CompanySummary[]>('/api/v1/research/companies', {
    params: {
      segment: params.segment,
      category: params.category,
      region: params.region,
      has_ai_features: params.has_ai_features,
      search: params.search,
    },
  });
  return res.data;
}

/**
 * Retrieve the full profile for a single company. Includes sources in the
 * response object keyed under ``sources``.
 */
export async function fetchCompany(id: number): Promise<{ company: CompanyProfile; sources: CompanyProfile['sources'] }> {
  const res = await apiClient.get(`/api/v1/research/companies/${id}`);
  return res.data as { company: CompanyProfile; sources: CompanyProfile['sources'] };
}

/**
 * Compare multiple companies. The backend will return lists of common
 * strengths, differences per company and opportunity gaps. Expects
 * between two and three company IDs.
 */
export async function compareCompanies(
  request: CompareRequest,
): Promise<CompareResponse> {
  // Transform frontend camelCase to backend snake_case
  const res = await apiClient.post<CompareResponse>(
    '/api/v1/research/companies/compare',
    { company_ids: request.companyIds },
  );
  return res.data;
}

/**
 * Download a CSV export of companies. If a segment is provided, only
 * companies belonging to that segment are included. Returns a blob
 * containing CSV data which can be used to create a downloadable URL.
 */
export async function exportCompanies(segment?: string): Promise<Blob> {
  const res = await apiClient.get('/api/v1/research/export', {
    params: { segment },
    responseType: 'blob',
  });
  return res.data as Blob;
}

/**
 * Refresh the profile for a specific company by invoking the backend's
 * profiling pipeline again. Returns the updated CompanyDetail.
 */
export async function refreshCompanyProfile(id: number): Promise<CompanyProfile> {
  const res = await apiClient.post<CompanyProfile>(`/api/v1/research/companies/${id}/refresh`);
  return res.data;
}