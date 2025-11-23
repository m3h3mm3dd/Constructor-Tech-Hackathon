import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClockIcon,
  ChevronRightIcon,
  MagnifyingGlassIcon,
  RocketLaunchIcon,
  Squares2X2Icon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useRecentSessions, useStartSession } from '@/hooks/useSessions';

function formatLastUpdated(timestamp?: string | null) {
  if (!timestamp) return 'Updated moments ago';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return 'Updated recently';

  const diffMs = Date.now() - date.getTime();
  const minutes = Math.max(1, Math.round(diffMs / 60000));
  if (minutes < 60) return `Last updated about ${minutes} min${minutes === 1 ? '' : 's'} ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `Last updated about ${hours} hour${hours === 1 ? '' : 's'} ago`;

  const days = Math.round(hours / 24);
  return `Last updated about ${days} day${days === 1 ? '' : 's'} ago`;
}

export default function Landing() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const { data: sessions, isLoading, error } = useRecentSessions();
  const start = useStartSession();

  const recentInvestigations = useMemo(() => {
    if (!sessions) return [];
    return [...sessions].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()).slice(0, 6);
  }, [sessions]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = search.trim();
    if (!trimmed) return;
    start.mutateAsync({ segment: trimmed }).then((res) => {
      navigate(`/sessions/${res.id}`);
    });
  };

  return (
    <div className="min-h-screen bg-[#f6f7fb] text-neutral-900 flex flex-col">
      <header className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-11 w-11 rounded-full bg-neutral-900 text-white flex items-center justify-center shadow-lg shadow-purple-200/50">
            <RocketLaunchIcon className="h-6 w-6" aria-hidden="true" />
          </div>
          <span className="text-lg font-semibold tracking-tight">SCOUT</span>
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => navigate('/lab')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-neutral-200 text-sm font-medium shadow-sm hover:shadow transition"
          >
            <Squares2X2Icon className="h-5 w-5 text-neutral-700" />
            Missions
          </button>
          <div className="px-3 py-1 rounded-full text-xs font-semibold bg-white border border-neutral-200 text-neutral-500 uppercase tracking-wide">
            Market Intelligence v2.0
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center px-4 sm:px-6 lg:px-8 pb-16">
        <div className="w-full max-w-3xl text-center mt-6">
          <h1 className="text-4xl sm:text-5xl font-black leading-tight text-neutral-900">
            What market are we scouting today?
          </h1>
          <form onSubmit={handleSubmit} className="mt-8 relative">
            <div className="absolute inset-0 mx-6 blur-3xl bg-purple-200/40 rounded-full -z-10" />
            <div className="flex items-center bg-white rounded-full shadow-[0_30px_80px_-50px_rgba(79,70,229,0.6),0_25px_70px_-65px_rgba(0,0,0,0.35)] border border-white/80 px-2 py-2">
              <div className="pl-4 pr-2">
                <MagnifyingGlassIcon className="h-6 w-6 text-neutral-400" aria-hidden="true" />
              </div>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="E.g. 'Next-gen battery manufacturers for EVs'..."
                className="flex-1 px-2 py-3 text-sm sm:text-base bg-transparent focus:outline-none placeholder:text-neutral-400"
              />
              <button
                type="submit"
                className="ml-2 px-6 py-3 rounded-full bg-neutral-900 text-white font-semibold shadow-lg shadow-purple-200/60 hover:translate-y-[1px] transition transform"
              >
                Scout
              </button>
            </div>
          </form>
        </div>

        <section className="w-full max-w-5xl mt-14">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2 text-neutral-800">
              <ClockIcon className="h-5 w-5 text-neutral-500" aria-hidden="true" />
              <span className="text-lg font-semibold">Recent Investigations</span>
            </div>
            <button
              type="button"
              onClick={() => navigate('/compare')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-white border border-neutral-200 text-neutral-700 shadow-sm hover:shadow transition"
            >
              <ChartBarIcon className="h-5 w-5" aria-hidden="true" />
              Analyze Trends
            </button>
          </div>

          {error ? (
            <div className="bg-white border border-amber-200 text-amber-800 rounded-lg p-4 text-sm shadow-sm">
              Unable to load investigations yet. Connect the backend API to see recent activity.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isLoading && (
                <>
                  {[0, 1].map((key) => (
                    <div
                      key={key}
                      className="h-28 rounded-xl bg-white border border-neutral-200 shadow-sm animate-pulse"
                    />
                  ))}
                </>
              )}
              {!isLoading && recentInvestigations.length === 0 && (
                <div className="col-span-full bg-white border border-dashed border-neutral-300 rounded-xl p-6 text-neutral-500 text-sm text-center shadow-sm">
                  No investigations yet. Start a mission to see them here.
                </div>
              )}
              {recentInvestigations.map((session) => {
                const investigationLabel = session.label;
                return (
                <div
                  key={`${session.id}-${investigationLabel}`}
                  className="flex items-center justify-between bg-white rounded-xl border border-neutral-200 shadow-sm p-5"
                >
                  <div className="space-y-1">
                    <div className="text-lg font-semibold text-neutral-900 leading-tight">
                      {investigationLabel}
                    </div>
                    <div className="text-sm text-neutral-500">{formatLastUpdated(session.updated_at)}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold text-green-700 bg-green-50 border border-green-200">
                      <span className="h-2 w-2 rounded-full bg-green-500" />
                      Active
                    </span>
                    <button
                      type="button"
                      onClick={() => navigate(`/sessions/${session.id}`)}
                      className="h-10 w-10 rounded-full border border-neutral-200 bg-white flex items-center justify-center text-neutral-600 hover:bg-neutral-50 shadow-sm"
                    >
                      <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </div>
                </div>
                );
              })}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
