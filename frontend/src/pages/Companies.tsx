import { useState, useMemo } from 'react';
import { useCompanies } from '@/hooks/useCompanies';
import CompanyProfileModal from '@/components/companies/CompanyProfileModal';

export default function Companies() {
  const [search, setSearch] = useState('');
  const [region, setRegion] = useState('');
  const [segment, setSegment] = useState('');
  const [category, setCategory] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: companies, isLoading, error } = useCompanies({
    search: search || undefined,
    region: region || undefined,
    segment: segment || undefined,
    category: category || undefined,
  });

  // Compute filter options dynamically from the loaded companies
  const regions = useMemo(() => {
    const vals = new Set<string>();
    companies?.forEach((c) => {
      if (c.region) vals.add(c.region);
    });
    return Array.from(vals).sort();
  }, [companies]);
  const segments = useMemo(() => {
    const vals = new Set<string>();
    companies?.forEach((c) => {
      if (c.segment) vals.add(c.segment);
    });
    return Array.from(vals).sort();
  }, [companies]);
  const categories = useMemo(() => {
    const vals = new Set<string>();
    companies?.forEach((c) => {
      if (c.category) vals.add(c.category);
    });
    return Array.from(vals).sort();
  }, [companies]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-neutral-900">Companies</h1>
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="col-span-2 md:col-span-1">
            <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="search">
              Search
            </label>
            <input
              id="search"
              type="text"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
              placeholder="Company name"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="region">
              Region
            </label>
            <select
              id="region"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              <option value="">All</option>
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="segment">
              Segment
            </label>
            <select
              id="segment"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
            >
              <option value="">All</option>
              {segments.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1" htmlFor="category">
              Category
            </label>
            <select
              id="category"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-brand focus:ring-brand text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Companies list */}
      {isLoading ? (
        <div className="text-neutral-500 animate-pulse">Loading companies…</div>
      ) : error ? (
        <div className="text-red-600">{error.message}</div>
      ) : companies && companies.length > 0 ? (
        <div className="overflow-x-auto bg-white rounded-lg shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Region
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Segment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {companies.map((company) => (
                <tr key={company.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-900">
                    {company.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-700">
                    {company.description ? company.description.substring(0, 50) + (company.description.length > 50 ? '…' : '') : '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-700">
                    {company.category || '—'}
                  </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-700">
                    {company.region || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-700">
                    {company.segment || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-neutral-700">
                    {company.size_bucket || '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => setSelectedId(company.id)}
                      className="text-brand hover:text-brand-dark"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-sm text-neutral-500">No companies found.</div>
      )}

      {selectedId !== null && (
        <CompanyProfileModal
          id={selectedId}
          isOpen={true}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}