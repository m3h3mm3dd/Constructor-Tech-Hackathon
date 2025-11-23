import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Bar,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ZAxis,
} from 'recharts';
import { useSession, useSessionLogs, useRefreshSession } from '@/hooks/useSessions';
import type { SessionLog } from '@/types/api';
import { formatDistanceToNow } from 'date-fns';

const SEGMENT_COLORS = ['#6C5DD3', '#F97316', '#10B981', '#3B82F6', '#F43F5E', '#F59E0B', '#14B8A6', '#6366F1', '#06B6D4'];

export default function SessionPage() {
  const { id } = useParams();
  const sessionId = id || '';
  const { data: session, isLoading, error } = useSession(sessionId);
  const { data: logs } = useSessionLogs(sessionId, !!sessionId);
  const refresh = useRefreshSession();
  const navigate = useNavigate();

  const companies = session?.companies || [];
  const hasCompanies = companies.length > 0;

  const segmentation = session?.charts?.segmentation || [];
  const companyScale = session?.charts?.company_scale || [];
  const performance = session?.charts?.performance_matrix || [];
  const evolution = session?.charts?.market_evolution || [];

  return (
    <div className="min-h-screen bg-[#f6f7fb] text-neutral-900 pb-12">
      <header className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="h-10 w-10 rounded-full bg-white border border-neutral-200 flex items-center justify-center shadow-sm hover:bg-neutral-50"
            aria-label="Back"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-semibold capitalize">{session?.label || 'Session'}</h1>
              <span className="text-sm text-neutral-500">Research Session · {companies.length} Companies Found</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-white border border-neutral-200 text-sm font-medium shadow-sm hover:shadow transition"
          >
            <Cog6ToothIcon className="h-5 w-5" />
            Configure Scoring
          </button>
          <button
            type="button"
            onClick={() => refresh.mutateAsync({ sessionId })}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition"
            disabled={refresh.isLoading}
          >
            <ArrowPathIcon className={clsx('h-5 w-5', refresh.isLoading && 'animate-spin')} />
            {refresh.isLoading ? 'Running…' : 'Refresh Scout'}
          </button>
        </div>
      </header>

      <main className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {error && (
          <div className="bg-white border border-amber-200 text-amber-800 rounded-lg p-4 text-sm shadow-sm">
            {error.message}
          </div>
        )}
        {isLoading && <div className="bg-white rounded-2xl h-48 animate-pulse" />}

        {/* Console */}
        <ScoutConsole logs={logs || []} status={session?.status || 'PENDING'} />

        {/* Charts */}
        {hasCompanies ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Market Segmentation" subtitle="By category tag">
              {segmentation.length === 0 ? (
                <div className="text-neutral-500 text-sm">No data yet.</div>
              ) : (
                <div className="flex flex-col sm:flex-row items-center gap-4">
                  <PieChart width={260} height={260}>
                    <Pie
                      data={segmentation}
                      dataKey="value"
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={110}
                      paddingAngle={3}
                    >
                      {segmentation.map((entry, idx) => (
                        <Cell key={entry.label} fill={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                  <div className="space-y-2">
                    {segmentation.map((entry, idx) => (
                      <div key={entry.label} className="flex items-center gap-2 text-sm">
                        <span className="h-3 w-3 rounded-full" style={{ background: SEGMENT_COLORS[idx % SEGMENT_COLORS.length] }} />
                        <span className="text-neutral-700">{entry.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </ChartCard>

            <ChartCard title="Company Scale" subtitle="Estimated employee count">
              {companyScale.length === 0 ? (
                <div className="text-neutral-500 text-sm">No data yet.</div>
              ) : (
                <BarChart width={520} height={240} data={companyScale} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <RechartsTooltip />
                  <Bar dataKey="employees" fill="#6366F1" radius={[6, 6, 0, 0]} />
                </BarChart>
              )}
            </ChartCard>

            <ChartCard title="Performance Matrix" subtitle="AI score analysis">
              {performance.length === 0 ? (
                <div className="text-neutral-500 text-sm">No companies to score yet.</div>
              ) : (
                <AreaChart width={520} height={260} data={performance} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.6} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="x" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <RechartsTooltip />
                  <Area type="monotone" dataKey="score" stroke="#6366F1" fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              )}
            </ChartCard>

            <ChartCard title="Market Evolution" subtitle="Company founding timeline">
              {evolution.length === 0 ? (
                <div className="text-neutral-500 text-sm">No timeline data yet.</div>
              ) : (
                <ScatterChart width={520} height={260} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" dataKey="year" name="Year" tick={{ fontSize: 11 }} />
                  <YAxis type="number" dataKey="score" name="Signal" tick={{ fontSize: 11 }} />
                  <ZAxis type="number" dataKey="size" range={[40, 200]} />
                  <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter data={evolution} fill="#F43F5E" />
                </ScatterChart>
              )}
            </ChartCard>
          </div>
        ) : (
          <div className="bg-white border border-dashed border-neutral-300 rounded-2xl p-8 text-neutral-500 text-sm shadow-sm text-center">
            <div className="text-neutral-700 mb-2">No companies found yet.</div>
            <button
              type="button"
              onClick={() => refresh.mutateAsync({ sessionId })}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition disabled:opacity-50"
              disabled={refresh.isLoading}
            >
              <ArrowPathIcon className={clsx('h-5 w-5', refresh.isLoading && 'animate-spin')} />
              Start Scout
            </button>
          </div>
        )}

        {/* Companies */}
        {hasCompanies && (
          <div className="space-y-4">
            <div className="text-lg font-semibold text-neutral-900">Companies</div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {companies.map((company) => (
                <CompanyCard key={company.id} company={company} onOpenProfile={() => navigate(`/companies/${company.id}`)} />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function ScoutConsole({ logs, status }: { logs: SessionLog[]; status: string }) {
  return (
    <div className="bg-gradient-to-b from-neutral-900 to-neutral-950 text-neutral-100 rounded-2xl shadow-2xl border border-neutral-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-neutral-950/60 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-red-500" />
          <span className="h-3 w-3 rounded-full bg-amber-400" />
          <span className="h-3 w-3 rounded-full bg-emerald-400" />
          <span className="text-xs uppercase tracking-wide text-neutral-400 ml-3">Scout Console</span>
        </div>
        <div
          className={clsx(
            'text-[11px] px-3 py-1 rounded-full border',
            status === 'RUNNING'
              ? 'border-emerald-400 text-emerald-200 bg-emerald-400/10 animate-pulse'
              : 'border-neutral-800 text-neutral-500',
          )}
        >
          ● {status === 'RUNNING' ? 'PROCESSING DATA' : 'SYSTEM IDLE'}
        </div>
      </div>
      <div className="p-4 font-mono text-[13px] leading-6 space-y-1 min-h-[260px] bg-neutral-950">
        {logs.length === 0 && <div className="text-neutral-600">Awaiting command. Enter a market and start scout.</div>}
        {logs.map((log) => (
          <div
            key={log.id}
            className={clsx(
              'transition duration-200',
              log.level === 'success' && 'text-emerald-300',
              log.level === 'info' && 'text-cyan-300',
              log.level === 'warning' && 'text-amber-300',
              log.level === 'error' && 'text-red-300',
            )}
          >
            <span className="text-neutral-500 mr-2">{formatTime(log.ts)}</span>
            {log.message}
          </div>
        ))}
      </div>
    </div>
  );
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch (e) {
    return '—';
  }
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
      <div className="text-sm text-neutral-500 uppercase tracking-wide">{title}</div>
      <h3 className="text-lg font-semibold text-neutral-900 mb-4">{subtitle}</h3>
      {children}
    </div>
  );
}

function CompanyCard({ company, onOpenProfile }: { company: any; onOpenProfile: () => void }) {
  const tags = company.primary_tags || [];
  return (
    <div
      className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 flex flex-col gap-3 hover:-translate-y-1 hover:shadow-lg transition cursor-pointer"
      onClick={onOpenProfile}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="h-12 w-12 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500 text-lg font-semibold">
            {company.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="text-lg font-semibold text-neutral-900 leading-tight">{company.name}</div>
            {company.domain && <div className="text-sm text-neutral-500">{company.domain}</div>}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold text-emerald-600 leading-none">{company.score ?? '—'}</div>
          <div className="text-xs uppercase tracking-wide text-neutral-500">Score</div>
        </div>
      </div>
      <p className="text-sm text-neutral-600 leading-relaxed min-h-[60px] line-clamp-3">{company.summary || 'Profile is being generated.'}</p>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag: string) => (
          <span key={tag} className="inline-flex items-center px-2.5 py-1 rounded-full bg-neutral-100 text-xs font-medium text-neutral-700">
            {tag}
          </span>
        ))}
      </div>
      <div className="inline-flex items-center gap-2 text-sm text-emerald-600 font-medium pt-2">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        Complete
      </div>
    </div>
  );
}
