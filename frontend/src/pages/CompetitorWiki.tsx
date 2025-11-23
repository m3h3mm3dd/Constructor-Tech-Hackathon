import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { useCompany } from '@/hooks/useCompanies';
import { refreshCompanyProfile } from '@/api/companies';

export default function CompetitorWiki() {
  const { id } = useParams<{ id: string }>();
  const companyId = id ? parseInt(id, 10) : null;
  const { data, isLoading, error, refetch } = useCompany(companyId);
  const company = data?.company;
  const sources = data?.sources;
  const [refreshing, setRefreshing] = useState(false);

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
      {isLoading ? (
        <div className="text-neutral-500">Loading profile…</div>
      ) : error ? (
        <div className="text-red-600">{error.message}</div>
      ) : company ? (
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 rounded-full bg-brand/10 flex items-center justify-center">
                <span className="text-2xl font-bold text-brand">
                  {company.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-neutral-900">{company.name}</h1>
                {company.website && (
                  <a
                    href={company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-brand hover:underline"
                  >
                    {company.website.replace(/^https?:\/\//, '')}
                  </a>
                )}
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {company.category && (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-neutral-800">
                      {company.category}
                    </span>
                  )}
                  {company.region && (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-neutral-800">
                      {company.region}
                    </span>
                  )}
                  {company.segment && (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-neutral-800">
                      {company.segment}
                    </span>
                  )}
                  {company.size_bucket && (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-neutral-800">
                      {company.size_bucket}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="inline-flex items-center px-3 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {refreshing ? 'Refreshing…' : 'Refresh profile'}
            </button>
          </div>
          {/* Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {company.description && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Summary</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.description}</p>
                </div>
              )}
              {company.background && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Company Background</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.background}</p>
                </div>
              )}
              {company.products && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Products & Services</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.products}</p>
                </div>
              )}
              {company.market_position && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Market Position</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.market_position}</p>
                </div>
              )}
              {/* Additional sections can be added here */}
              {company.strengths && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Strengths</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.strengths}</p>
                </div>
              )}
              {company.risks && (
                <div>
                  <h2 className="text-lg font-semibold mb-1 text-neutral-900">Risks</h2>
                  <p className="text-sm text-neutral-700 whitespace-pre-line">{company.risks}</p>
                </div>
              )}
            </div>
            {/* Sources sidebar */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold mb-1 text-neutral-900">Sources</h2>
              {sources && sources.length > 0 ? (
                <ul className="space-y-2 text-sm">
                  {sources.map((src, idx) => (
                    <li key={idx}>
                      <a
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand hover:underline"
                      >
                        {src.title || src.url}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-neutral-500">No sources available.</p>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}