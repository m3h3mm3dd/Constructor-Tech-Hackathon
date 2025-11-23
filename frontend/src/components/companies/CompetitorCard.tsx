import { Link } from 'react-router-dom';
import type { CompanySummary } from '@/types/api';

interface Props {
  company: CompanySummary;
}

export default function CompetitorCard({ company }: Props) {
  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-col justify-between hover:shadow-md transition-shadow">
      <div className="space-y-2">
        <Link to={`/companies/${company.id}`}> 
          <h3 className="text-lg font-semibold text-neutral-900 hover:text-brand-dark truncate">
            {company.name}
          </h3>
        </Link>
        {company.description && (
          <p className="text-sm text-neutral-600 overflow-hidden text-ellipsis max-h-12">
            {company.description}
          </p>
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        {company.category && (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-800">
            {company.category}
          </span>
        )}
        {company.region && (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-800">
            {company.region}
          </span>
        )}
        {company.size_bucket && (
          <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-800">
            {company.size_bucket}
          </span>
        )}
      </div>
    </div>
  );
}