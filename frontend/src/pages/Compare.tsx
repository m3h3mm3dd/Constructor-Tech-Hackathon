import { useState } from 'react';
import { Combobox } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';
import { useCompanies, useCompare } from '@/hooks/useCompanies';
import type { CompanySummary, CompareCompanyDifferences } from '@/types/api';

/**
 * Compare page allows the user to select up to three companies and request a
 * structured comparison from the backend. The results are displayed as
 * grouped lists: common strengths, differentiators per company and
 * opportunity gaps. This replaces the previous attribute matrix with a more
 * narrative friendly layout based on the backend's response shape.
 */
export default function Compare() {
  const { data: companies, isLoading: loadingCompanies, error } = useCompanies({});
  const [selected, setSelected] = useState<CompanySummary[]>([]);
  const [query, setQuery] = useState('');
  const compareMutation = useCompare();

  // Filter companies based on search query
  const filteredCompanies = companies?.filter((company) =>
    company.name.toLowerCase().includes(query.toLowerCase()),
  );

  const handleCompare = async () => {
    if (selected.length < 2 || selected.length > 3) return;
    try {
      await compareMutation.mutateAsync({ companyIds: selected.map((c) => c.id) });
    } catch (e) {
      // error is surfaced via mutation state
    }
  };

  // Helper to map companyId to name for displaying differences
  const getCompanyName = (companyId: number): string => {
    const company = selected.find((c) => c.id === companyId);
    return company ? company.name : `Company ${companyId}`;
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Compare companies</h1>
      <p className="text-sm text-neutral-500 max-w-prose">
        Select between two and three competitors to see what they have in common,
        where they differ and which gaps they leave open. Use the search to
        quickly find names.
      </p>
      {/* Company selector */}
      <div className="w-full max-w-xl">
        <Combobox value={selected} onChange={setSelected} multiple>
          <div className="relative">
            <div className="relative w-full cursor-default overflow-hidden rounded-md bg-white text-left shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-brand text-sm">
              <Combobox.Input
                className="w-full border-none py-2 pl-3 pr-10 leading-5 text-neutral-900 focus:ring-0"
                displayValue={(value: CompanySummary[]) => value.map((v) => v.name).join(', ')}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={loadingCompanies ? 'Loading…' : 'Search companies'}
                disabled={loadingCompanies || !!error}
              />
              <Combobox.Button className="absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronUpDownIcon className="h-5 w-5 text-neutral-400" aria-hidden="true" />
              </Combobox.Button>
            </div>
            {filteredCompanies && filteredCompanies.length > 0 && (
              <Combobox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                {filteredCompanies.map((company) => (
                  <Combobox.Option
                    key={company.id}
                    value={company}
                    disabled={selected.some((c) => c.id === company.id) && selected.length >= 3}
                    className={({ active }) =>
                      `relative cursor-default select-none py-2 pl-10 pr-4 ${
                        active ? 'bg-brand/10 text-brand-dark' : 'text-neutral-900'
                      }`
                    }
                  >
                    {({ selected: isSelected, active }) => (
                      <>
                        <span className={`block truncate ${isSelected ? 'font-medium' : 'font-normal'}`}>
                          {company.name}
                        </span>
                        {isSelected ? (
                          <span
                            className={`absolute inset-y-0 left-0 flex items-center pl-3 ${active ? 'text-brand-dark' : 'text-brand-dark'}`}
                          >
                            <CheckIcon className="h-5 w-5" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Combobox.Option>
                ))}
              </Combobox.Options>
            )}
          </div>
        </Combobox>
      </div>
      {/* Compare button */}
      <div className="flex items-center space-x-3">
        <button
          onClick={handleCompare}
          disabled={selected.length < 2 || selected.length > 3 || compareMutation.isLoading}
          className="inline-flex items-center px-3 py-2 rounded-md text-sm font-medium text-white bg-brand hover:bg-brand-dark disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {compareMutation.isLoading ? 'Comparing…' : 'Compare'}
        </button>
        {compareMutation.isError && (
          <span className="text-sm text-red-600">{(compareMutation.error as Error).message}</span>
        )}
      </div>
      {/* Comparison results */}
      {compareMutation.data && (
        <div className="space-y-6">
          {/* Common strengths */}
          {compareMutation.data.common_strengths.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow space-y-2">
              <h2 className="text-lg font-semibold text-neutral-900">Common strengths</h2>
              <ul className="list-disc list-inside text-sm text-neutral-700">
                {compareMutation.data.common_strengths.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {/* Key differences per company */}
          {compareMutation.data.key_differences.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow space-y-4">
              <h2 className="text-lg font-semibold text-neutral-900">Key differences</h2>
              {compareMutation.data.key_differences.map((diff: CompareCompanyDifferences) => (
                <div key={diff.companyId} className="space-y-1">
                  <h3 className="text-md font-medium text-brand-dark">
                    {getCompanyName(diff.companyId)}
                  </h3>
                  <ul className="list-disc list-inside text-sm text-neutral-700">
                    {diff.points.map((p, idx) => (
                      <li key={idx}>{p}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
          {/* Opportunity gaps */}
          {compareMutation.data.opportunity_gaps.length > 0 && (
            <div className="bg-white p-4 rounded-lg shadow space-y-2">
              <h2 className="text-lg font-semibold text-neutral-900">Opportunity gaps</h2>
              <ul className="list-disc list-inside text-sm text-neutral-700">
                {compareMutation.data.opportunity_gaps.map((gap, idx) => (
                  <li key={idx}>{gap}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}