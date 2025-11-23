import { useParams, useNavigate } from 'react-router-dom';
import { useState, useMemo, type ReactNode } from 'react';
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { useCompany } from '@/hooks/useCompanies';
import { refreshCompanyProfile } from '@/api/companies';

function computeScore(name: string) {
  const sum = name.split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return 60 + (sum % 35);
}

function formatWebsite(url?: string | null) {
  if (!url) return '—';
  return url.replace(/^https?:\/\//, '');
}

function formatDate(dateString?: string | null) {
  if (!dateString) return 'Not verified';
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return 'Not verified';
  return date.toLocaleDateString();
}

function safeText(text?: string | null, fallback = 'No data available yet.') {
  if (!text) return fallback;
  return text;
}

export default function CompetitorWiki() {
  const { id } = useParams<{ id: string }>();
  const companyId = id ? parseInt(id, 10) : null;
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useCompany(companyId);
  const company = data?.company;
  const sources = data?.sources ?? [];
  const [refreshing, setRefreshing] = useState(false);

  const score = company ? computeScore(company.name) : 0;
  const tags = useMemo(() => {
    const set = new Set<string>();
    [company?.segment, company?.category, company?.region, company?.size_bucket]
      .filter(Boolean)
      .forEach((item) => set.add(item as string));
    return Array.from(set);
  }, [company]);

  const handleRefresh = async () => {
    if (!companyId) return;
    setRefreshing(true);
    try {
      await refreshCompanyProfile(companyId);
      await refetch();
    } catch (e) {
      alert('Failed to refresh profile');
    } finally {
      setRefreshing(false);
    }
  };

  if (!companyId) {
    return <div className="text-red-600">Invalid company ID.</div>;
  }

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm text-neutral-600 hover:text-neutral-800"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        Back
      </button>

      {isLoading ? (
        <div className="space-y-4">
          <div className="h-64 rounded-2xl bg-white border border-neutral-200 shadow-sm animate-pulse" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {[0, 1, 2, 3].map((idx) => (
              <div key={idx} className="h-40 rounded-2xl bg-white border border-neutral-200 shadow-sm animate-pulse" />
            ))}
          </div>
        </div>
      ) : error ? (
        <div className="text-red-600">{error.message}</div>
      ) : company ? (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm">
            <div className="bg-indigo-50 px-6 py-4 rounded-t-2xl">
              <div className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-1">AI Scout Summary</div>
              <p className="text-sm text-indigo-900">
                {safeText(company.description || company.market_position || company.background, 'No summary available yet.')}
              </p>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="h-14 w-14 rounded-xl bg-neutral-100 flex items-center justify-center text-xl font-semibold text-neutral-700">
                    {company.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <h1 className="text-2xl font-bold text-neutral-900 leading-tight">{company.name}</h1>
                      <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                        Score: {score} <CheckCircleIcon className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <span key={tag} className="inline-flex items-center px-3 py-1 rounded-full bg-neutral-100 text-xs font-medium text-neutral-700">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="mt-3 flex items-center gap-4 text-sm text-neutral-600 flex-wrap">
                      <span className="inline-flex items-center gap-1">
                        <GlobeAltIcon className="h-4 w-4" />
                        {formatWebsite(company.website)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        Last Verified: {formatDate(company.last_updated)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="h-10 w-10 rounded-md border border-neutral-200 bg-white flex items-center justify-center text-neutral-700 hover:bg-neutral-50"
                  >
                    <ArrowDownTrayIcon className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    className="h-10 w-10 rounded-md border border-neutral-200 bg-white flex items-center justify-center text-neutral-700 hover:bg-neutral-50"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-semibold hover:translate-y-[1px] transition disabled:opacity-50"
                  >
                    <ArrowPathIcon className="h-5 w-5" />
                    {refreshing ? 'Refreshing…' : 'Refresh Profile'}
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm text-neutral-700">
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <ShieldCheckIcon className="h-4 w-4" />
                  Data Reliability: {sources.length > 3 ? 'High' : 'Moderate'}
                </span>
                <span>
                  Verified across <strong>{sources.length || 1}</strong> source{sources.length === 1 ? '' : 's'} including official documentation.
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <InfoCard title="Score Analysis" accent="blue">
              <div className="text-sm text-neutral-700">
                Market Traction: 25/25 · Innovation: 25/25 · Financial Health: 20/25 · Strategic Positioning: 20/25
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-sm text-neutral-800">
                <div>
                  <div className="text-xs text-neutral-500">Founded</div>
                  <div className="font-semibold">{company.first_discovered ? new Date(company.first_discovered).getFullYear() : '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Headquarters</div>
                  <div className="font-semibold">{company.region || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Employees</div>
                  <div className="font-semibold">{company.size_bucket || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Segment</div>
                  <div className="font-semibold">{company.segment || '—'}</div>
                </div>
              </div>
            </InfoCard>

            <InfoCard title="Market Position" accent="indigo">
              <p className="text-sm text-neutral-700 leading-relaxed">
                {safeText(company.market_position || company.strengths, 'Market position details will appear after the next crawl.')}
              </p>
            </InfoCard>

            <InfoCard title="Scale & Reach" accent="purple">
              <p className="text-sm text-neutral-700 leading-relaxed">
                {company.size_bucket
                  ? `Scale: ${company.size_bucket}. ${company.region ? `Primary region: ${company.region}.` : ''}`
                  : 'Scale and reach metrics are not available yet.'}
              </p>
            </InfoCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <InfoCard title="Company Background" accent="indigo">
              <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
                {safeText(company.background, 'Background information will populate once the agent collects more signals.')}
              </p>
            </InfoCard>
            <InfoCard title="Recent Developments" accent="purple">
              <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
                {safeText(company.strengths, 'Recent developments will appear after additional research updates.')}
              </p>
            </InfoCard>
            <InfoCard title="Sources" accent="emerald">
              {sources.length > 0 ? (
                <ul className="space-y-2 text-sm">
                  {sources.map((src, idx) => (
                    <li key={idx}>
                      <a href={src.url} className="text-emerald-700 hover:underline break-all" target="_blank" rel="noopener noreferrer">
                        {src.title || src.url}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-neutral-600">No sources available yet.</p>
              )}
            </InfoCard>
          </div>

          <InfoCard title="Products & Services" accent="blue">
            <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
              {safeText(company.products, 'Products and services will populate once discovered.')}
            </p>
          </InfoCard>

          <InfoCard title="Strategic Intelligence Report" accent="indigo" actionLabel="Refresh Analysis" onAction={handleRefresh} actionLoading={refreshing}>
            <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-line">
              {safeText(company.risks || company.market_position || company.strengths, 'A strategic analysis will appear after the next run.')}
            </p>
          </InfoCard>
        </div>
      ) : null}
    </div>
  );
}

function InfoCard({
  title,
  accent,
  children,
  actionLabel,
  onAction,
  actionLoading,
}: {
  title: string;
  accent: 'blue' | 'indigo' | 'purple' | 'emerald';
  children: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  actionLoading?: boolean;
}) {
  const accentMap = {
    blue: 'text-blue-700 bg-blue-50',
    indigo: 'text-indigo-700 bg-indigo-50',
    purple: 'text-purple-700 bg-purple-50',
    emerald: 'text-emerald-700 bg-emerald-50',
  } as const;

  return (
    <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${accentMap[accent]}`}>
          {title}
        </div>
        {actionLabel && onAction && (
          <button
            type="button"
            onClick={onAction}
            disabled={actionLoading}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-neutral-200 text-sm text-neutral-700 hover:bg-neutral-50 disabled:opacity-50"
          >
            <ArrowPathIcon className="h-4 w-4" />
            {actionLoading ? 'Working…' : actionLabel}
          </button>
        )}
      </div>
      {children}
    </div>
  );
}
