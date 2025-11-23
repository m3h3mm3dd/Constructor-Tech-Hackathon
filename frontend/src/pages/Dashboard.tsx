import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, ClockIcon, ChevronRightIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { useStartSession, useRecentSessions } from '@/hooks/useSessions';

export default function Dashboard() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const start = useStartSession();
  const { data: sessions } = useRecentSessions();

  const sorted = useMemo(() => (sessions || []).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()), [sessions]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const res = await start.mutateAsync({ segment: query.trim(), max_companies: 3 });
    navigate(`/sessions/${res.id}`);
  };

  return (
    <div className="min-h-screen bg-[#f6f7fb] text-neutral-900 pb-16">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center space-y-8">
        <h1 className="text-4xl sm:text-5xl font-black leading-tight">What market are we scouting today?</h1>
        <form onSubmit={handleSubmit} className="relative max-w-3xl mx-auto">
          <div className="absolute inset-0 mx-6 blur-3xl bg-purple-200/40 rounded-full -z-10" />
          <div className="flex items-center bg-white rounded-full shadow-[0_30px_80px_-50px_rgba(79,70,229,0.6),0_25px_70px_-65px_rgba(0,0,0,0.35)] border border-white/80 px-3 py-2">
            <MagnifyingGlassIcon className="h-6 w-6 text-neutral-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. 'Next-gen battery manufacturers for EVs'..."
              className="flex-1 px-3 py-3 text-sm sm:text-base bg-transparent focus:outline-none placeholder:text-neutral-400"
            />
            <button
              type="submit"
              disabled={start.isLoading}
              className="ml-2 px-6 py-3 rounded-full bg-neutral-900 text-white font-semibold shadow-lg shadow-purple-200/60 hover:translate-y-[1px] transition transform disabled:opacity-60"
            >
              {start.isLoading ? 'Scouting…' : 'Scout'}
            </button>
          </div>
        </form>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-neutral-800">
            <ClockIcon className="h-5 w-5 text-neutral-500" aria-hidden="true" />
            <span className="text-lg font-semibold">Recent Investigations</span>
          </div>
          <button
            type="button"
            onClick={() => sessions?.[0] && navigate(`/sessions/${sessions[0].id}`)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-white border border-neutral-200 text-neutral-700 shadow-sm hover:shadow transition"
          >
            <ChartBarIcon className="h-5 w-5" aria-hidden="true" />
            Analyze Trends
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(sorted || []).map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between bg-white rounded-xl border border-neutral-200 shadow-sm p-5 cursor-pointer hover:shadow-md transition"
              onClick={() => navigate(`/sessions/${s.id}`)}
            >
              <div className="space-y-1 text-left">
                <div className="text-lg font-semibold text-neutral-900 leading-tight capitalize">{s.label}</div>
                <div className="text-sm text-neutral-500">Last updated {formatRelative(s.updated_at)}</div>
              </div>
              <div className="flex items-center gap-3">
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold text-green-700 bg-green-50 border border-green-200">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Active
                </span>
                <span className="h-10 w-10 rounded-full border border-neutral-200 bg-white flex items-center justify-center text-neutral-600">
                  <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
                </span>
              </div>
            </div>
          ))}
          {!sorted?.length && (
            <div className="col-span-full bg-white border border-dashed border-neutral-300 rounded-xl p-8 text-neutral-500 text-sm text-center shadow-sm">
              No investigations yet. Start a mission above.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatRelative(dateStr: string) {
  const date = new Date(dateStr);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min${mins === 1 ? '' : 's'} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}
