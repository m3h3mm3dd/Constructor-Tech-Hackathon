import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeftIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
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
import clsx from 'clsx';
import { useCompanies } from '@/hooks/useCompanies';
import { useStartResearch, useResearchJob } from '@/hooks/useResearch';
import type { CompanySummary } from '@/types/api';

const SEGMENT_COLORS = ['#6C5DD3', '#F97316', '#10B981', '#3B82F6', '#F43F5E', '#F59E0B', '#14B8A6', '#6366F1', '#06B6D4'];

function computeScore(name: string, idx: number) {
  const base = name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0) + idx * 31;
  return 60 + (base % 40);
}

function formatWebsite(url?: string | null) {
  if (!url) return '';
  return url.replace(/^https?:\/\//, '');
}

function trimText(text?: string | null, max = 160) {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export default function Investigation() {
  const { segment } = useParams();
  const navigate = useNavigate();
  const decodedSegment = segment ? decodeURIComponent(segment) : '';
  const [query, setQuery] = useState(decodedSegment);
  const activeSegment = query || decodedSegment;
  const [logs, setLogs] = useState<{ text: string; tone: 'muted' | 'info' | 'success' }[]>([]);
  const [progress, setProgress] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [jobId, setJobId] = useState<number | null>(null);
  const startMutation = useStartResearch();
  const { data: job, refetch: refetchJob } = useResearchJob(jobId);
  const { data: companies, isLoading, error, refetch } = useCompanies(activeSegment ? { segment: activeSegment } : {});
  const logIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const chartCompanies = companies ?? [];

  const marketSegmentation = useMemo(() => {
    const map: Record<string, number> = {};
    chartCompanies.forEach((c) => {
      const key = c.category || 'Uncategorized';
      map[key] = (map[key] || 0) + 1;
    });
    return Object.entries(map).map(([name, value], i) => ({ name, value, color: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }));
  }, [chartCompanies]);

  const sizeBuckets = useMemo(() => {
    const map: Record<string, number> = {};
    chartCompanies.forEach((c) => {
      const key = c.size_bucket || 'Unknown';
      map[key] = (map[key] || 0) + 1;
    });
    return Object.entries(map).map(([label, count]) => ({ label, count }));
  }, [chartCompanies]);

  const performanceSeries = useMemo(() => {
    return chartCompanies.map((c, idx) => ({
      name: c.name,
      score: computeScore(c.name, idx),
    }));
  }, [chartCompanies]);

  const foundingTimeline = useMemo(() => {
    const points: { x: number; y: number; z: number; name: string }[] = [];
    chartCompanies.forEach((c, idx) => {
      const dateStr = c.first_discovered || c.last_updated;
      const parsed = dateStr ? new Date(dateStr) : null;
      const year = parsed && !Number.isNaN(parsed.getTime()) ? parsed.getFullYear() : null;
      if (year) {
        points.push({
          x: year,
          y: computeScore(c.name, idx) / 2,
          z: 60 + (idx * 20) % 120,
          name: c.name,
        });
      }
    });
    return points;
  }, [chartCompanies]);

  const companiesFound = activeSegment ? chartCompanies.filter((c) => (c.segment || '').toLowerCase() === activeSegment.toLowerCase()) : chartCompanies;

  useEffect(() => {
    if (!jobId) return;
    const interval = setInterval(() => {
      refetchJob();
    }, 4000);
    return () => clearInterval(interval);
  }, [jobId, refetchJob]);

  useEffect(() => {
    const total = job?.companies.length || 0;
    const done = job?.companies.filter((c) => c.status === 'profiled').length || 0;
    if (total > 0) {
      setProgress(Math.round((done / total) * 100));
    }
  }, [job]);

  useEffect(() => {
    if (!isAnimating) {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
      return;
    }
    const scripted = [
      { text: `SCOUT Activated. Target: "${activeSegment}"`, tone: 'success' as const },
      { text: 'Scanning for key players...', tone: 'muted' as const },
      { text: 'Generating smart queries for the segment...', tone: 'muted' as const },
      { text: 'Crawling landing pages and docs…', tone: 'info' as const },
      { text: 'Parsing signals and extracting structured fields…', tone: 'muted' as const },
    ];
    let idx = 0;
    setLogs([scripted[0]]);
    logIntervalRef.current = setInterval(() => {
      idx += 1;
      if (idx >= scripted.length) {
        if (logIntervalRef.current) clearInterval(logIntervalRef.current);
        return;
      }
      setLogs((prev) => [...prev, scripted[idx]]);
      setProgress((p) => Math.min(90, p + 6));
    }, 900);
    return () => {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    };
  }, [isAnimating, query, decodedSegment]);

  const handleStart = async () => {
    const target = query || decodedSegment;
    if (!target) return;
    if (target !== decodedSegment) {
      navigate(`/investigations/${encodeURIComponent(target)}`, { replace: true });
    }
    setLogs([]);
    setProgress(12);
    setIsAnimating(true);
    try {
      const res = await startMutation.mutateAsync({ segment: target, max_companies: 6 });
      setJobId(res.job_id);
      setProgress(96);
      const built = res.companies.map((c) => c.name).filter(Boolean);
      if (built.length) {
        setLogs((prev) => [
          ...prev,
          { text: `Found candidates: ${built.join(', ')}`, tone: 'success' },
          { text: 'Profiles built for discovered companies.', tone: 'success' },
        ]);
      }
      await refetch();
      setProgress(100);
    } catch (e) {
      setLogs((prev) => [...prev, { text: (e as Error).message || 'Failed to start scout.', tone: 'muted' }]);
    } finally {
      setIsAnimating(false);
    }
  };

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
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="E.g. next-gen battery manufacturers"
                className="text-2xl sm:text-3xl font-semibold capitalize bg-transparent border-b border-transparent focus:border-neutral-800 focus:outline-none placeholder:text-neutral-400"
              />
              <button
                type="button"
                onClick={handleStart}
                disabled={startMutation.isLoading || !query}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition disabled:opacity-50"
              >
                {startMutation.isLoading ? 'Running…' : 'Start Scout'}
              </button>
            </div>
            <span className="text-sm text-neutral-500">Research Session · {companiesFound.length} Companies Found</span>
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
            onClick={handleStart}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition"
            disabled={startMutation.isLoading}
          >
            <ArrowPathIcon className={clsx('h-5 w-5', startMutation.isLoading && 'animate-spin')} />
            {startMutation.isLoading ? 'Running…' : 'Refresh Scout'}
          </button>
        </div>
      </header>

      <main className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {error && (
          <div className="bg-white border border-amber-200 text-amber-800 rounded-lg p-4 text-sm shadow-sm">
            Unable to load this investigation yet. Connect the backend API and try again.
          </div>
        )}

        <div className="bg-gradient-to-b from-neutral-900 to-neutral-950 text-neutral-100 rounded-2xl shadow-2xl border border-neutral-800 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-neutral-950/60 border-b border-neutral-800">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500" />
              <span className="h-3 w-3 rounded-full bg-amber-400" />
              <span className="h-3 w-3 rounded-full bg-emerald-400" />
              <span className="text-xs uppercase tracking-wide text-neutral-400 ml-3">Scout Console</span>
            </div>
            <div className="text-[11px] text-neutral-500 px-3 py-1 rounded-full border border-neutral-800">
              System {startMutation.isLoading ? 'Active' : 'Idle'}
            </div>
          </div>
          <div className="p-4 font-mono text-[13px] leading-6 space-y-1 min-h-[260px] bg-neutral-950">
            {logs.length === 0 && (
              <div className="text-neutral-600">Awaiting command. Enter a market and start scout.</div>
            )}
            {logs.map((log, idx) => (
              <div
                key={idx}
                className={clsx(
                  log.tone === 'success' && 'text-emerald-300',
                  log.tone === 'info' && 'text-cyan-300',
                  log.tone === 'muted' && 'text-neutral-300',
                )}
              >
                <span className="text-neutral-500 mr-2">▹</span>
                {log.text}
              </div>
            ))}
          </div>
          <div className="px-4 pb-4 pt-2">
            <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 to-sky-400 transition-all duration-500"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
            <div className="text-sm text-neutral-500 uppercase tracking-wide">Market Segmentation</div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">By category tag</h3>
            {marketSegmentation.length === 0 ? (
              <div className="text-neutral-500 text-sm">No category data yet.</div>
            ) : (
              <div className="flex flex-col sm:flex-row items-center gap-4">
                <PieChart width={260} height={260}>
                  <Pie
                    data={marketSegmentation}
                    dataKey="value"
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={110}
                    paddingAngle={3}
                  >
                    {marketSegmentation.map((entry, idx) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
                <div className="space-y-2">
                  {marketSegmentation.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2 text-sm">
                      <span className="h-3 w-3 rounded-full" style={{ background: entry.color }} />
                      <span className="text-neutral-700">{entry.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
            <div className="text-sm text-neutral-500 uppercase tracking-wide">Company Scale</div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Estimated employee count</h3>
            {sizeBuckets.length === 0 ? (
              <div className="text-neutral-500 text-sm">No size data yet.</div>
            ) : (
              <ResponsiveBar data={sizeBuckets} />
            )}
          </div>

          <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
            <div className="text-sm text-neutral-500 uppercase tracking-wide">Performance Matrix</div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">AI score analysis</h3>
            {performanceSeries.length === 0 ? (
              <div className="text-neutral-500 text-sm">No companies to score yet.</div>
            ) : (
              <AreaChart width={520} height={260} data={performanceSeries} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.6} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <RechartsTooltip />
                <Area type="monotone" dataKey="score" stroke="#6366F1" fillOpacity={1} fill="url(#colorScore)" />
              </AreaChart>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
            <div className="text-sm text-neutral-500 uppercase tracking-wide">Market Evolution</div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Company founding timeline</h3>
            {foundingTimeline.length === 0 ? (
              <div className="text-neutral-500 text-sm">No timeline data yet.</div>
            ) : (
              <ScatterChart width={520} height={260} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" dataKey="x" name="Year" tick={{ fontSize: 11 }} />
                <YAxis type="number" dataKey="y" name="Signal" tick={{ fontSize: 11 }} />
                <ZAxis type="number" dataKey="z" range={[40, 200]} />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter data={foundingTimeline} fill="#F43F5E" />
              </ScatterChart>
            )}
          </div>
        </div>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-lg font-semibold text-neutral-900">Companies</div>
            <button
              type="button"
              onClick={handleStart}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition disabled:opacity-50"
              disabled={startMutation.isLoading}
            >
              <ArrowPathIcon className={clsx('h-5 w-5', startMutation.isLoading && 'animate-spin')} />
              {companiesFound.length === 0 ? 'Start Scout' : 'Re-run Scout'}
            </button>
          </div>
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[0, 1, 2].map((key) => (
                <div key={key} className="h-52 rounded-2xl bg-white border border-neutral-200 shadow-sm animate-pulse" />
              ))}
            </div>
          ) : companiesFound.length === 0 ? (
            <div className="bg-white border border-dashed border-neutral-300 rounded-2xl p-8 text-neutral-500 text-sm shadow-sm text-center">
              <div className="text-neutral-700 mb-2">No companies found yet.</div>
              <button
                type="button"
                onClick={handleStart}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-neutral-900 text-white text-sm font-semibold shadow-sm hover:translate-y-[1px] transition disabled:opacity-50"
                disabled={startMutation.isLoading}
              >
                <ArrowPathIcon className={clsx('h-5 w-5', startMutation.isLoading && 'animate-spin')} />
                Start Scout
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {companiesFound.map((company, idx) => (
                <CompanyCard key={company.id} company={company} score={computeScore(company.name, idx)} onOpenProfile={() => navigate(`/companies/${company.id}`)} />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function ResponsiveBar({ data }: { data: { label: string; count: number }[] }) {
  return (
    <div className="w-full overflow-x-auto">
      <BarChart width={520} height={240} data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
        <RechartsTooltip />
        <Bar dataKey="count" fill="#6366F1" radius={[6, 6, 0, 0]} />
      </BarChart>
    </div>
  );
}

function CompanyCard({ company, score, onOpenProfile }: { company: CompanySummary; score: number; onOpenProfile: () => void }) {
  const tags = [company.segment, company.category, company.region].filter(Boolean) as string[];
  return (
    <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="h-12 w-12 rounded-lg bg-neutral-100 flex items-center justify-center text-neutral-500 text-lg font-semibold">
            {company.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <div className="text-lg font-semibold text-neutral-900 leading-tight">{company.name}</div>
            {company.website && (
              <div className="flex items-center gap-1 text-sm text-neutral-500">
                <GlobeAltIcon className="h-4 w-4" />
                {formatWebsite(company.website)}
              </div>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold text-emerald-600 leading-none">{score}</div>
          <div className="text-xs uppercase tracking-wide text-neutral-500">Score</div>
        </div>
      </div>
      <p className="text-sm text-neutral-600 leading-relaxed min-h-[60px]">{trimText(company.description)}</p>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <span key={tag} className="inline-flex items-center px-2.5 py-1 rounded-full bg-neutral-100 text-xs font-medium text-neutral-700">
            {tag}
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between pt-2">
        <div className="inline-flex items-center gap-2 text-sm text-emerald-600 font-medium">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Complete
        </div>
        <button
          type="button"
          onClick={onOpenProfile}
          className="text-sm font-semibold text-neutral-900 hover:text-neutral-700 inline-flex items-center gap-1"
        >
          View Profile <ArrowRight />
        </button>
      </div>
    </div>
  );
}

function ArrowRight() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12l-7.5 7.5M21 12H3" />
    </svg>
  );
}
