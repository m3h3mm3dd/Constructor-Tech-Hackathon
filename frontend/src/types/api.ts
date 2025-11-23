// Shared TypeScript definitions for interacting with the backend API

// Stats overview response from /api/v1/research/stats/overview.
// Provides aggregated counts for various company attributes.
export interface StatsBucket {
  label: string;
  count: number;
}

export interface StatsOverview {
  by_category: StatsBucket[];
  by_region: StatsBucket[];
  pricing_models: StatsBucket[];
  ai_features: Record<string, number>;
}

// Research job response types
export interface ResearchJobCompanyStatus {
  id: number;
  name: string;
  status: string;
  last_updated?: string | null;
  has_profile: boolean;
}

export interface ResearchJob {
  /**
   * Unique identifier for the research job. Mirrors the ``id`` field in the
   * backend response. Note that the Python model uses ``job_id`` as the
   * internal attribute name but serialises it with the alias ``id``.
   */
  id: number;
  /** Market segment that was used to start the research job. */
  segment: string;
  /** Current status of the job: 'pending', 'running', 'completed' or 'failed'. */
  status: string;
  /** Optional error message if the job failed. */
  error_message?: string | null;
  /** Timestamp when the job was created. */
  created_at: string;
  /** Timestamp when the job finished, if applicable. */
  finished_at?: string | null;
  /** Array of company status objects discovered during the job. */
  companies: ResearchJobCompanyStatus[];
}

export interface ResearchStartRequest {
  segment: string;
  max_companies: number;
}

export interface CompanySummary {
  id: number;
  name: string;
  category?: string | null;
  region?: string | null;
  size_bucket?: string | null;
  description?: string | null;
  last_updated?: string | null;
  has_ai_features?: boolean | null;
}

export interface CompanyProfile extends CompanySummary {
  website?: string | null;
  segment?: string | null;
  background?: string | null;
  products?: string | null;
  target_segments?: string | null;
  pricing_model?: string | null;
  market_position?: string | null;
  strengths?: string | null;
  risks?: string | null;
  has_ai_features?: boolean | null;
  compliance_tags?: string | null;
  first_discovered?: string | null;
  sources?: { id: number; url: string; title?: string | null; snippet?: string | null; source_type?: string | null; relevance_score?: number | null; published_at?: string | null }[];
}


/**
 * Request payload to compare companies. Accepts a list of numeric company IDs
 * between two and three items long. The backend will analyse the companies and
 * return overlapping strengths, differentiators per company and any gaps in
 * the market that might represent opportunities.
 */
export interface CompareRequest {
  /**
   * Unique identifiers of the companies to compare. Must be numeric IDs
   * returned from list endpoints. At least two and at most three ids.
   */
  companyIds: number[];
}

/**
 * Represents the key differentiators for a single company in a comparison. The
 * ``points`` array contains textual descriptions of how this company differs
 * from the others on important attributes (e.g. unique features, pricing,
 * positioning).
 */
export interface CompareCompanyDifferences {
  companyId: number;
  points: string[];
}

/**
 * Response payload from the ``/api/v1/research/companies/compare`` endpoint. It
 * summarises common strengths shared by all compared companies, identifies
 * differentiating points for each company individually and surfaces
 * opportunity gaps that none of the selected companies address. Consumers
 * should present this data in a human‑friendly layout rather than a matrix
 * table.
 */
export interface CompareResponse {
  common_strengths: string[];
  key_differences: CompareCompanyDifferences[];
  opportunity_gaps: string[];
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  answer: string;
}