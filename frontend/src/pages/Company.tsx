import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeftIcon, ArrowPathIcon, ArrowDownTrayIcon, TrashIcon, GlobeAltIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useSessionCompany } from '@/hooks/useSessions';

export default function CompanyPage() {
  const { companyId } = useParams();
  const navigate = useNavigate();
  const { data: company, isLoading, error, refetch } = useSessionCompany(companyId || '');

  return (
    <div className="min-h-screen bg-[#f6f7fb] text-neutral-900 pb-12">
      <div className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm text-neutral-600 hover:text-neutral-800 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back
        </button>

        {isLoading && <div className="h-64 bg-white rounded-2xl animate-pulse" />}
        {error && <div className="text-red-600">{error.message}</div>}
        {company && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm">
              <div className="bg-indigo-50 px-6 py-4 rounded-t-2xl">
                <div className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-1">AI Scout Summary</div>
                <p className="text-sm text-indigo-900">{company.summary || 'No summary available yet.'}</p>
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
                          Score: {company.score ?? '—'}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {(company.primary_tags || []).map((tag) => (
                          <span key={tag} className="inline-flex items-center px-3 py-1 rounded-full bg-neutral-100 text-xs font-medium text-neutral-700">
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="mt-3 flex items-center gap-4 text-sm text-neutral-600 flex-wrap">
                        <span className="inline-flex items-center gap-1">
                          <GlobeAltIcon className="h-4 w-4" />
                          {company.domain || '—'}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          Last Verified: {company.last_verified_at ? new Date(company.last_verified_at).toLocaleDateString() : 'Not verified'}
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
                      onClick={() => refetch()}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-semibold hover:translate-y-[1px] transition"
                    >
                      <ArrowPathIcon className="h-5 w-5" />
                      Refresh Profile
                    </button>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm text-neutral-700">
                  <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <ShieldCheckIcon className="h-4 w-4" />
                    Data Reliability: {company.data_reliability || '—'}
                  </span>
                  <span>Verified across {company.sources.length || 1} source(s).</span>
                </div>
              </div>
            </div>

            <InfoGrid company={company} />

            <InfoCard title="Company Background" body={company.background || 'Background information will appear after the next crawl.'} />
            <InfoCard title="Recent Developments" body={company.recent_developments || 'Recent developments will appear after additional research.'} />
            <InfoCard title="Products & Services" body={company.products_services || 'Products and services will populate once discovered.'} />
            <InfoCard title="Scale & Reach" body={company.scale_reach || 'Scale & reach metrics are not available yet.'} />
            <InfoCard title="Strategic Intelligence Report" body={company.strategic_notes || 'Strategic analysis will appear after the next run.'}>
              <button
                type="button"
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 px-3 py-1 rounded-md border border-neutral-200 text-sm text-neutral-700 hover:bg-neutral-50"
              >
                <ArrowPathIcon className="h-4 w-4" />
                Refresh Analysis
              </button>
            </InfoCard>

            <InfoCard title="Sources">
              {company.sources.length > 0 ? (
                <ul className="space-y-2 text-sm">
                  {company.sources.map((s) => (
                    <li key={s.url}>
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-emerald-700 hover:underline break-all">
                        {s.label || s.url}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-neutral-600">No sources available yet.</p>
              )}
            </InfoCard>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoGrid({ company }: { company: any }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <InfoCard title="Score Analysis" body={company.score_analysis || 'Score analysis will appear after the next run.'} />
      <InfoCard title="Market Position" body={company.market_position || 'Market position will appear after the next run.'} />
      <InfoCard
        title="Stats"
        body={
          <div className="grid grid-cols-2 gap-3 text-sm text-neutral-800">
            <div>
              <div className="text-xs text-neutral-500">Founded</div>
              <div className="font-semibold">{company.founded_year || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-neutral-500">Employees</div>
              <div className="font-semibold">{company.employees || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-neutral-500">HQ City</div>
              <div className="font-semibold">{company.hq_city || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-neutral-500">HQ Country</div>
              <div className="font-semibold">{company.hq_country || '—'}</div>
            </div>
          </div>
        }
      />
    </div>
  );
}

function InfoCard({ title, body, children }: { title: string; body?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="font-semibold text-neutral-900">{title}</div>
        {children}
      </div>
      <div className="text-sm text-neutral-700 leading-relaxed">{body || 'No data yet.'}</div>
    </div>
  );
}
