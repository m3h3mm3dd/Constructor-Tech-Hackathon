import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCompanies } from '@/hooks/useCompanies';
import { useStatsOverview } from '@/hooks/useStatsOverview';
import MarketCharts from '@/components/charts/MarketCharts';
import CompetitorCard from '@/components/companies/CompetitorCard';
import { exportCompanies } from '@/api/companies';

export default function Dashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const { data: stats, isLoading: statsLoading, error: statsError } = useStatsOverview();
  const { data: companies, isLoading: companiesLoading, error: companiesError } = useCompanies({ search: search || undefined });

  // Compute size buckets counts for bar chart
  const sizeBuckets = useMemo(() => {
    const map: Record<string, number> = {};
    companies?.forEach((c) => {
      const bucket = c.size_bucket || 'Unknown';
      map[bucket] = (map[bucket] || 0) + 1;
    });
    return Object.entries(map).map(([label, count]) => ({ label, count }));
  }, [companies]);

  // Filtered companies based on search term
  const filtered = useMemo(() => {
    if (!companies) return [];
    return companies.filter((c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.description ? c.description.toLowerCase().includes(search.toLowerCase()) : false),
    );
  }, [companies, search]);

  const handleExport = async () => {
    try {
      const blob = await exportCompanies();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'companies.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert('Failed to export CSV.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Market Intelligence</h1>
          <p className="text-sm text-neutral-500">{companies?.length ?? 0} companies tracked</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleExport}
            className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark"
          >
            Export CSV
          </button>
          <button
            onClick={() => navigate('/lab')}
            className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark"
          >
            New Research Task
          </button>
        </div>
      </div>
      {/* Charts */}
      {statsLoading ? (
        <div className="text-neutral-500">Loading charts…</div>
      ) : statsError ? (
        <div className="text-red-600">Failed to load stats: {statsError.message}</div>
      ) : stats ? (
        <MarketCharts byCategory={stats.by_category} bySize={sizeBuckets} />
      ) : null}
      {/* Search bar */}
        <div className="bg-white rounded-lg shadow p-4">
        <input
          type="text"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
          placeholder="Search companies by name or description"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      {/* Competitor grid */}
      {companiesLoading ? (
        <div className="text-neutral-500">Loading companies…</div>
      ) : companiesError ? (
        <div className="text-red-600">{companiesError.message}</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {/* CTA card */}
          <div
            className="flex flex-col items-center justify-center bg-white rounded-lg border-2 border-dashed border-gray-300 p-4 cursor-pointer hover:bg-gray-50"
            onClick={() => navigate('/lab')}
          >
            <div className="text-4xl font-bold text-brand">+</div>
            <p className="mt-2 text-sm text-brand">Discover new companies</p>
          </div>
          {filtered.map((company) => (
            <CompetitorCard key={company.id} company={company} />
          ))}
        </div>
      )}
    </div>
  );
}