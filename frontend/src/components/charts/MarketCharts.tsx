import {
  PieChart,
  Pie,
  Cell,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from 'recharts';
import type { StatsBucket } from '@/types/api';

interface Props {
  byCategory: StatsBucket[];
  bySize: StatsBucket[];
}

// Predefined color palette for up to 10 categories
const COLORS = [
  '#0284c7',
  '#0ea5e9',
  '#38bdf8',
  '#0891b2',
  '#7dd3fc',
  '#22d3ee',
  '#06b6d4',
  '#67e8f9',
  '#0e7490',
  '#083344',
];

export default function MarketCharts({ byCategory, bySize }: Props) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="h-80 bg-white rounded-lg shadow p-4">
        <h3 className="text-md font-medium text-neutral-700 mb-2">Market segmentation (by category)</h3>
        <ResponsiveContainer width="100%" height="90%">
          <PieChart>
            <Pie
              data={byCategory}
              dataKey="count"
              nameKey="label"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={(entry) => `${entry.label}: ${entry.count}`}
            >
              {byCategory.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <RechartsTooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="h-80 bg-white rounded-lg shadow p-4">
        <h3 className="text-md font-medium text-neutral-700 mb-2">Company scale (estimated employees)</h3>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={bySize}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
            <RechartsTooltip />
            <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}